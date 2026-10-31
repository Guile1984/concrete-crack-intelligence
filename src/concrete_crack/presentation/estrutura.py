"""Comandos de estrutura dos dados: pareamento e dimensões de máscaras e fotos.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.estrutura parear ccsd
    python -m concrete_crack.presentation.estrutura dimensoes ccsd

O ``parear`` lê só o manifesto de arquivos (nomes). O ``dimensoes`` lê também o
cabeçalho de cada imagem (largura, altura, orientação), sem mostrar imagens.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..config.caminhos import caminho_manifesto_arquivos, pasta_dados_brutos
from ..domain.dimensoes import (
    Cabecalho,
    ContagemOrientacoes,
    ContagemTamanhos,
    ResultadoDimensoes,
    conferir_dimensoes,
)
from ..domain.pareamento import Pareamento, parear
from ..infrastructure.imagens import ler_cabecalho
from ..infrastructure.manifesto_arquivos import carregar_manifesto

PREFIXO_MASCARAS = "BW/"
PREFIXO_FOTOS = "rgb/"
LIMITE_LISTA = 20


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
    print(f"Tamanhos das máscaras: {tam_m}")
    print(f"Tamanhos das fotos: {tam_f}")
    print(f"Orientações EXIF das máscaras: {ori_m}")
    print(f"Orientações EXIF das fotos: {ori_f}")
    print(f"Pares com tamanho diferente: {len(resultado.diferentes)}")
    _imprimir_pares(resultado.diferentes)
    print(f"Pares com eixos trocados: {len(resultado.eixos_trocados)}")
    _imprimir_pares(resultado.eixos_trocados)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa os comandos de estrutura.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 se tudo conferir; 1 se houver arquivos sem par ou pares de tamanhos
        diferentes; 2 em erro.
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
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        if args.comando == "parear":
            pareamento = parear_fonte(raiz, args.fonte_id)
            _imprimir(pareamento)
            return 0 if pareamento.completo else 1
        resultado = dimensoes_da_fonte(raiz, args.fonte_id)
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    _imprimir_dimensoes(resultado)
    return 1 if resultado.diferentes else 0


if __name__ == "__main__":
    raise SystemExit(main())
