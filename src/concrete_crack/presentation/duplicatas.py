"""Detecção de quase-duplicatas entre as fotos de uma fonte (dHash duplo).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.duplicatas ccsd

O comando lê cada foto uma vez, reduzida e com a orientação EXIF aplicada, e
calcula o hash. Fabrica as variações do controle positivo sobre as bases
sorteadas, calcula o limiar pela cobertura pré-registrada, agrupa as fotos reais
e aplica o critério de escalada. Imprime só números agregados: nenhum nome de
foto e nenhuma imagem.
"""

import argparse
import hashlib
import statistics
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config.caminhos import caminho_manifesto_arquivos, pasta_dados_brutos
from ..config.regras import REGRAS
from ..domain.amostragem import amostrar_por_hash
from ..domain.duplicatas import (
    Agrupamento,
    AvaliacaoHash,
    agrupar,
    avaliar_hash,
    dhash_duplo,
    distancia_hamming,
    limiar_por_cobertura,
    matriz_de_distancias,
)
from ..domain.orientacao import aplicar_orientacao
from ..domain.variacoes import LADOS, ajustar_brilho, recortar
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import ler_cabecalho, ler_cinza
from ..infrastructure.manifesto_arquivos import carregar_manifesto
from ..infrastructure.recompressao import recomprimir_jpeg
from .estrutura import PREFIXO_FOTOS

INTERVALO_PROGRESSO = 50


def lado_do_recorte(seed: int, foto: str, fracao: float) -> str:
    """Sorteia o lado do recorte de uma base pelo hash de ``seed:foto:fração``.

    Como em ``amostrar_por_hash``, o resultado não depende de nenhuma biblioteca
    de números aleatórios.

    Args:
        seed: Semente do controle positivo.
        foto: Caminho da foto base no manifesto.
        fracao: Fração do recorte.

    Returns:
        Um dos ``LADOS``.
    """
    chave = hashlib.sha256(f"{seed}:{foto}:{fracao}".encode()).hexdigest()
    return LADOS[int(chave, 16) % len(LADOS)]


def variacoes_da_base(cinza: np.ndarray, foto: str) -> dict[str, np.ndarray]:
    """Fabrica as variações pré-registradas de uma foto base já orientada.

    Args:
        cinza: Foto base reduzida e orientada, uint8.
        foto: Caminho da foto base no manifesto (para sortear o lado).

    Returns:
        As variações, por nome: recompressão, brilhos e recortes, nessa ordem.
    """
    variacoes = {
        f"jpeg {REGRAS.qualidade_jpeg_controle}": recomprimir_jpeg(
            cinza, REGRAS.qualidade_jpeg_controle
        )
    }
    for fator in REGRAS.fatores_brilho_controle:
        variacoes[f"brilho x{fator}"] = ajustar_brilho(cinza, fator)
    for fracao in REGRAS.recortes_controle:
        lado = lado_do_recorte(REGRAS.seed_controle_duplicatas, foto, fracao)
        variacoes[f"recorte {fracao:.0%}"] = recortar(cinza, fracao, lado)
    return variacoes


@dataclass(frozen=True, slots=True)
class ResultadoDuplicatas:
    """Resultado da detecção de quase-duplicatas de uma fonte.

    Attributes:
        fonte_id: Identificador da fonte.
        sha256_manifesto: Hash do manifesto de arquivos usado.
        fotos: Caminhos das fotos, na ordem dos índices dos grupos.
        distancias_controle: Distâncias base-variação, por tipo de variação.
        limiar: Limiar T derivado do controle positivo.
        agrupamento: Grupos das fotos reais com distância <= T.
        avaliacao: Veredito do critério de escalada.
    """

    fonte_id: str
    sha256_manifesto: str
    fotos: tuple[str, ...]
    distancias_controle: dict[str, tuple[int, ...]]
    limiar: int
    agrupamento: Agrupamento
    avaliacao: AvaliacaoHash


def detectar_duplicatas(
    raiz: Path,
    fonte_id: str,
    progresso: Callable[[int, int], None] | None = None,
) -> ResultadoDuplicatas:
    """Calcula o limiar pelo controle positivo e agrupa as fotos reais.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado.
        progresso: Função chamada com (fotos lidas, total) após cada leitura.

    Returns:
        O resultado, com os valores pré-registrados de ``REGRAS``.

    Raises:
        FileNotFoundError: Se o manifesto ou alguma foto não existir.
        OSError: Se algum arquivo não for uma imagem reconhecida.
        ValueError: Se o manifesto for de outra fonte, tiver menos fotos que
            o controle positivo exige, ou alguma foto for pequena demais.
    """
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    manifesto = carregar_manifesto(origem)
    if manifesto.fonte_id != fonte_id:
        raise ValueError(
            f"O manifesto de {fonte_id} declara a fonte {manifesto.fonte_id!r}."
        )
    fotos = [
        arquivo.caminho
        for arquivo in manifesto.arquivos
        if arquivo.caminho.startswith(PREFIXO_FOTOS)
    ]
    if len(fotos) < REGRAS.n_bases_controle_duplicatas:
        raise ValueError(
            f"O manifesto de {fonte_id} tem {len(fotos)} fotos; o controle "
            f"positivo exige pelo menos {REGRAS.n_bases_controle_duplicatas}."
        )
    bases = set(
        amostrar_por_hash(
            fotos,
            REGRAS.n_bases_controle_duplicatas,
            REGRAS.seed_controle_duplicatas,
        )
    )
    pasta = pasta_dados_brutos(raiz, fonte_id)
    lado = REGRAS.lado_hash_duplicatas
    hashes: list[np.ndarray] = []
    distancias: dict[str, list[int]] = {}
    for numero, foto in enumerate(fotos, start=1):
        caminho = pasta / foto
        orientacao = ler_cabecalho(caminho).orientacao_exif
        cinza = aplicar_orientacao(
            ler_cinza(caminho, REGRAS.fator_leitura_duplicatas), orientacao
        )
        original = dhash_duplo(cinza, lado)
        hashes.append(original)
        if foto in bases:
            for nome, variacao in variacoes_da_base(cinza, foto).items():
                distancia = distancia_hamming(original, dhash_duplo(variacao, lado))
                distancias.setdefault(nome, []).append(distancia)
        if progresso is not None:
            progresso(numero, len(fotos))
    todas = [d for lista in distancias.values() for d in lista]
    limiar = limiar_por_cobertura(todas, REGRAS.cobertura_limiar_duplicatas)
    agrupamento = agrupar(matriz_de_distancias(hashes), limiar)
    avaliacao = avaliar_hash(
        agrupamento,
        REGRAS.fracao_maxima_grupo_duplicatas,
        REGRAS.fracao_maxima_pares_duplicatas,
    )
    return ResultadoDuplicatas(
        fonte_id=fonte_id,
        sha256_manifesto=sha256_do_arquivo(origem),
        fotos=tuple(fotos),
        distancias_controle={k: tuple(v) for k, v in distancias.items()},
        limiar=limiar,
        agrupamento=agrupamento,
        avaliacao=avaliacao,
    )


def _percentual(valor: float) -> str:
    """Formata uma proporção como percentual com duas casas decimais."""
    return f"{valor * 100:.2f}%".replace(".", ",")


def formatar_duplicatas(resultado: ResultadoDuplicatas) -> str:
    """Monta o relatório da detecção, só com números agregados.

    Args:
        resultado: O resultado a relatar.

    Returns:
        O texto do relatório, sem nenhum nome de foto.
    """
    agrupamento = resultado.agrupamento
    avaliacao = resultado.avaliacao
    n_controle = sum(len(v) for v in resultado.distancias_controle.values())
    linhas = [
        f"Quase-duplicatas das fotos de {resultado.fonte_id} (dHash duplo)",
        f"Manifesto de arquivos (sha256): {resultado.sha256_manifesto[:12]}",
        f"Fotos: {len(resultado.fotos)}; "
        f"bits por hash: {2 * REGRAS.lado_hash_duplicatas**2}",
        "",
        f"Controle positivo: {n_controle} variações fabricadas "
        f"(distância à foto base):",
    ]
    t = resultado.limiar
    for nome, valores in resultado.distancias_controle.items():
        reconhecidas = sum(d <= t for d in valores) / len(valores)
        mediana = statistics.median(valores)
        linhas.append(
            f"  {nome:<12} n={len(valores):3d}  mediana={mediana:5.1f}"
            f"  máx={max(valores):3d}  reconhecidas em T: {_percentual(reconhecidas)}"
        )
    cobertura = _percentual(REGRAS.cobertura_limiar_duplicatas)
    linhas += [
        f"Limiar T (menor inteiro que reconhece {cobertura}): {t}",
        "",
        f"Pares de fotos reais com distância <= T: {agrupamento.pares_ligados} "
        f"de {agrupamento.total_pares} "
        f"({_percentual(agrupamento.fracao_pares_ligados)}; "
        f"máximo {_percentual(REGRAS.fracao_maxima_pares_duplicatas)})",
        f"Grupos: {len(agrupamento.grupos)}; maior grupo: "
        f"{agrupamento.maior_grupo} fotos (máximo: mais de "
        f"{_percentual(REGRAS.fracao_maxima_grupo_duplicatas)} das fotos reprova)",
        "Grupos por tamanho:",
    ]
    tamanhos = Counter(len(grupo) for grupo in agrupamento.grupos)
    for tamanho in sorted(tamanhos):
        linhas.append(f"  {tamanho:3d} foto(s): {tamanhos[tamanho]} grupo(s)")
    if avaliacao.reprovado:
        motivos = []
        if avaliacao.grupo_grande_demais:
            motivos.append("maior grupo acima do máximo")
        if avaliacao.pares_demais:
            motivos.append("pares ligados acima do máximo")
        veredito = f"dHash REPROVADO ({'; '.join(motivos)}): escalar para embeddings."
    else:
        veredito = "dHash APROVADO: os grupos seguem para a divisão."
    linhas += ["", veredito]
    return "\n".join(linhas)


def _mostrar_progresso(lidas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada bloco de fotos e ao final."""
    if lidas % INTERVALO_PROGRESSO == 0 or lidas == total:
        print(f"  {lidas}/{total} fotos lidas", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a detecção de quase-duplicatas.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso (aprovado ou reprovado); 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.duplicatas",
        description="Detecta quase-duplicatas entre as fotos (dHash duplo).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    try:
        resultado = detectar_duplicatas(
            args.raiz.resolve(), args.fonte_id, _mostrar_progresso
        )
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    print(formatar_duplicatas(resultado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
