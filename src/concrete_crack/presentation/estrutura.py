"""Comandos de estrutura dos dados: pareamento, dimensões e alinhamento.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.estrutura parear ccsd
    python -m concrete_crack.presentation.estrutura dimensoes ccsd
    python -m concrete_crack.presentation.estrutura alinhamento ccsd

O ``parear`` lê só o manifesto de arquivos (nomes). O ``dimensoes`` lê também o
cabeçalho de cada imagem (largura, altura, orientação). O ``alinhamento`` lê os
pixels, reduzidos, e imprime só estatísticas. Nenhum deles mostra imagens.
"""

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..config.caminhos import caminho_manifesto_arquivos, pasta_dados_brutos
from ..domain.alinhamento import ResumoVantagens, marcar_fissura, resumir_vantagens
from ..domain.dimensoes import (
    Cabecalho,
    ContagemOrientacoes,
    ContagemTamanhos,
    ResultadoDimensoes,
    conferir_dimensoes,
)
from ..domain.orientacao import aplicar_orientacao, vantagem_da_orientacao_exif
from ..domain.pareamento import Pareamento, parear
from ..infrastructure.imagens import ler_cabecalho, ler_cinza
from ..infrastructure.manifesto_arquivos import carregar_manifesto

PREFIXO_MASCARAS = "BW/"
PREFIXO_FOTOS = "rgb/"
LIMITE_LISTA = 20
FATOR_REDUCAO = 8
DESVIO_MINIMO_MASCARA = 32
FRACAO_MINIMA_POSITIVA = 0.9


def parear_fonte(raiz: Path, fonte_id: str) -> Pareamento:
    """Pareia as máscaras e as fotos de uma fonte, a partir do manifesto.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado.

    Returns:
        O pareamento entre os arquivos de ``BW/`` e de ``rgb/``.

    Raises:
        FileNotFoundError: Se o manifesto de arquivos não existir.
        ValueError: Se o manifesto for de outra fonte, não tiver máscaras ou
            fotos, ou tiver nomes que colidem.
    """
    manifesto = carregar_manifesto(caminho_manifesto_arquivos(raiz, fonte_id))
    if manifesto.fonte_id != fonte_id:
        raise ValueError(
            f"O manifesto de {fonte_id} declara a fonte {manifesto.fonte_id!r}."
        )
    caminhos = [arquivo.caminho for arquivo in manifesto.arquivos]
    mascaras = [c for c in caminhos if c.startswith(PREFIXO_MASCARAS)]
    fotos = [c for c in caminhos if c.startswith(PREFIXO_FOTOS)]
    if not mascaras or not fotos:
        raise ValueError(
            f"O manifesto de {fonte_id} não tem arquivos em "
            f"{PREFIXO_MASCARAS!r} ou em {PREFIXO_FOTOS!r}."
        )
    return parear(mascaras, fotos)


def dimensoes_da_fonte(raiz: Path, fonte_id: str) -> ResultadoDimensoes:
    """Confere as dimensões de cada par máscara-foto de uma fonte.

    Só os pares existentes entram; arquivos sem par são assunto de
    ``parear_fonte``.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado.

    Returns:
        O resultado da conferência de dimensões.

    Raises:
        FileNotFoundError: Se o manifesto ou algum arquivo de imagem não existir.
        OSError: Se algum arquivo não for uma imagem reconhecida.
        ValueError: Se o manifesto for inválido ou algum cabeçalho for inválido.
    """
    pareamento = parear_fonte(raiz, fonte_id)
    pasta = pasta_dados_brutos(raiz, fonte_id)
    cabecalhos: dict[str, Cabecalho] = {}
    for mascara, foto in pareamento.pares:
        cabecalhos[mascara] = ler_cabecalho(pasta / mascara)
        cabecalhos[foto] = ler_cabecalho(pasta / foto)
    return conferir_dimensoes(pareamento.pares, cabecalhos)


def _grupo_confirmado(resumo: ResumoVantagens) -> bool:
    """Diz se a proporção de vantagens positivas atinge o critério mínimo."""
    return resumo.fracao_positiva >= FRACAO_MINIMA_POSITIVA


@dataclass(frozen=True, slots=True)
class ResultadoAlinhamento:
    """Resultado do teste de alinhamento de uma fonte.

    Attributes:
        resumos: Resumo das vantagens por orientação EXIF da foto (None é a
            ausência de etiqueta).
        sem_avaliacao: Máscaras cujo contraste não pôde ser calculado.
        formas_incompativeis: Máscaras cuja forma difere da foto já orientada.
    """

    resumos: dict[int | None, ResumoVantagens]
    sem_avaliacao: tuple[str, ...]
    formas_incompativeis: tuple[str, ...]

    @property
    def confirmado(self) -> bool:
        """Verdadeiro se há grupos, todos acima do mínimo, e formas compatíveis."""
        return (
            bool(self.resumos)
            and not self.formas_incompativeis
            and all(_grupo_confirmado(r) for r in self.resumos.values())
        )


def alinhamento_da_fonte(raiz: Path, fonte_id: str) -> ResultadoAlinhamento:
    """Testa, por contraste, se a máscara está alinhada com a foto orientada.

    Para cada par, compara o contraste sob a máscara com a foto na orientação
    EXIF e na orientação oposta (180 graus). Fotos e máscaras são lidas
    reduzidas por ``FATOR_REDUCAO``; a fissura da máscara é marcada por
    ``marcar_fissura`` com ``DESVIO_MINIMO_MASCARA``.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado.

    Returns:
        O resultado, agrupado pela orientação EXIF da foto.

    Raises:
        FileNotFoundError: Se o manifesto ou algum arquivo de imagem não existir.
        OSError: Se algum arquivo não for uma imagem reconhecida.
        ValueError: Se o manifesto for inválido ou algum cabeçalho for inválido.
    """
    pareamento = parear_fonte(raiz, fonte_id)
    pasta = pasta_dados_brutos(raiz, fonte_id)
    vantagens: dict[int | None, list[float]] = {}
    sem_avaliacao: list[str] = []
    incompativeis: list[str] = []
    for mascara, foto in pareamento.pares:
        orientacao = ler_cabecalho(pasta / foto).orientacao_exif
        cinza_foto = ler_cinza(pasta / foto, FATOR_REDUCAO)
        marcada = marcar_fissura(
            ler_cinza(pasta / mascara, FATOR_REDUCAO), DESVIO_MINIMO_MASCARA
        )
        if aplicar_orientacao(cinza_foto, orientacao).shape != marcada.shape:
            incompativeis.append(mascara)
            continue
        try:
            vantagem = vantagem_da_orientacao_exif(cinza_foto, marcada, orientacao)
        except ValueError:
            sem_avaliacao.append(mascara)
            continue
        vantagens.setdefault(orientacao, []).append(vantagem)
    resumos = {o: resumir_vantagens(v) for o, v in vantagens.items()}
    return ResultadoAlinhamento(resumos, tuple(sem_avaliacao), tuple(incompativeis))


def _imprimir(pareamento: Pareamento) -> None:
    """Imprime o pareamento, com no máximo 20 caminhos por grupo."""
    print(f"Pares: {len(pareamento.pares)}")
    if pareamento.completo:
        print("Pareamento completo.")
        return
    grupos = (
        ("máscaras sem foto", pareamento.mascaras_sem_foto),
        ("fotos sem máscara", pareamento.fotos_sem_mascara),
    )
    for titulo, caminhos in grupos:
        if not caminhos:
            continue
        print(f"  {titulo} ({len(caminhos)}):")
        for caminho in caminhos[:LIMITE_LISTA]:
            print(f"    {caminho}")
        if len(caminhos) > LIMITE_LISTA:
            print(f"    ... e mais {len(caminhos) - LIMITE_LISTA}")


def _formatar_tamanhos(contagem: ContagemTamanhos) -> str:
    """Formata a contagem de tamanhos como ``4032x3024 (458)``."""
    return ", ".join(f"{largura}x{altura} ({n})" for (largura, altura), n in contagem)


def _formatar_orientacoes(contagem: ContagemOrientacoes) -> str:
    """Formata a contagem de orientações; ``ausente`` quando não há etiqueta."""
    return ", ".join(
        f"{'ausente' if orientacao is None else orientacao} ({n})"
        for orientacao, n in contagem
    )


def _imprimir_pares(pares: tuple[tuple[str, str], ...]) -> None:
    """Imprime pares (máscara, foto), com no máximo 20."""
    for mascara, foto in pares[:LIMITE_LISTA]:
        print(f"    {mascara} <-> {foto}")
    if len(pares) > LIMITE_LISTA:
        print(f"    ... e mais {len(pares) - LIMITE_LISTA}")


def _imprimir_dimensoes(resultado: ResultadoDimensoes) -> None:
    """Imprime o resumo da conferência de dimensões."""
    tam_m = _formatar_tamanhos(resultado.tamanhos_mascaras)
    tam_f = _formatar_tamanhos(resultado.tamanhos_fotos)
    ori_m = _formatar_orientacoes(resultado.orientacoes_mascaras)
    ori_f = _formatar_orientacoes(resultado.orientacoes_fotos)
    ori_t = _formatar_orientacoes(resultado.orientacoes_fotos_dos_trocados)
    apos = resultado.diferentes_apos_orientacao
    print(f"Tamanhos das máscaras: {tam_m}")
    print(f"Tamanhos das fotos: {tam_f}")
    print(f"Orientações EXIF das máscaras: {ori_m}")
    print(f"Orientações EXIF das fotos: {ori_f}")
    print(f"Pares com tamanho diferente: {len(resultado.diferentes)}")
    _imprimir_pares(resultado.diferentes)
    print(f"Pares com eixos trocados: {len(resultado.eixos_trocados)}")
    _imprimir_pares(resultado.eixos_trocados)
    print(f"Orientações EXIF das fotos nos pares trocados: {ori_t or 'nenhuma'}")
    print(f"Pares com tamanho diferente após a orientação: {len(apos)}")
    _imprimir_pares(apos)


def _imprimir_caminhos(titulo: str, caminhos: tuple[str, ...]) -> None:
    """Imprime uma contagem e, se houver, até 20 caminhos."""
    print(f"{titulo}: {len(caminhos)}")
    for caminho in caminhos[:LIMITE_LISTA]:
        print(f"    {caminho}")
    if len(caminhos) > LIMITE_LISTA:
        print(f"    ... e mais {len(caminhos) - LIMITE_LISTA}")


def _imprimir_alinhamento(resultado: ResultadoAlinhamento) -> None:
    """Imprime o resumo das vantagens por orientação e o veredito."""
    minimo = f"{FRACAO_MINIMA_POSITIVA:.0%}"
    print(
        f"Alinhamento (redução {FATOR_REDUCAO}x, desvio mínimo "
        f"{DESVIO_MINIMO_MASCARA}, critério: {minimo} de vantagens positivas)"
    )
    for orientacao in sorted(resultado.resumos, key=lambda o: (o is not None, o or 0)):
        resumo = resultado.resumos[orientacao]
        rotulo = "ausente" if orientacao is None else orientacao
        estado = "confirmado" if _grupo_confirmado(resumo) else "NÃO CONFIRMADO"
        print(
            f"  orientação {rotulo}: {resumo.n} pares, "
            f"{resumo.fracao_positiva:.1%} positivas, mediana {resumo.mediana:.2f}, "
            f"mín {resumo.minimo:.2f}, máx {resumo.maximo:.2f} [{estado}]"
        )
    _imprimir_caminhos("Máscaras sem contraste definido", resultado.sem_avaliacao)
    _imprimir_caminhos("Formas incompatíveis", resultado.formas_incompativeis)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa os comandos de estrutura.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 se tudo conferir; 1 se houver arquivos sem par ou, no ``dimensoes``,
        pares de tamanhos diferentes mesmo com a orientação EXIF aplicada ou,
        no ``alinhamento``, grupo abaixo do critério; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.estrutura",
        description="Confere a estrutura dos dados de uma fonte.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    cmd_parear = comandos.add_parser("parear", help="confere máscara e foto por nome")
    cmd_parear.add_argument("fonte_id")
    cmd_dimensoes = comandos.add_parser(
        "dimensoes", help="confere as dimensões de cada par"
    )
    cmd_dimensoes.add_argument("fonte_id")
    cmd_alinhamento = comandos.add_parser(
        "alinhamento", help="testa o alinhamento entre máscara e foto"
    )
    cmd_alinhamento.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        if args.comando == "parear":
            pareamento = parear_fonte(raiz, args.fonte_id)
            _imprimir(pareamento)
            return 0 if pareamento.completo else 1
        if args.comando == "alinhamento":
            alinhamento = alinhamento_da_fonte(raiz, args.fonte_id)
            _imprimir_alinhamento(alinhamento)
            return 0 if alinhamento.confirmado else 1
        resultado = dimensoes_da_fonte(raiz, args.fonte_id)
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    _imprimir_dimensoes(resultado)
    return 1 if resultado.diferentes_apos_orientacao else 0


if __name__ == "__main__":
    raise SystemExit(main())
