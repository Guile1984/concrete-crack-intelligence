"""Gravação do índice de tiles do CCSD (A52, item 6).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.indice_tiles ccsd

Lê a divisão gravada, confere que o manifesto de arquivos é o da divisão, lê
só o cabeçalho de cada foto (sem decodificar os pixels), calcula o tamanho de
exibição pela orientação EXIF (A34) e monta a grade de cada foto nas duas
escalas da A52. Grava ``manifests/tiles_v1.json`` uma única vez.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..config.caminhos import (
    caminho_indice_tiles,
    caminho_manifesto_arquivos,
    caminho_split,
    pasta_dados_brutos,
)
from ..config.regras import REGRAS
from ..domain.indice_tiles import CONJUNTOS, IndiceTiles, indexar
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import ler_cabecalho
from ..infrastructure.indice_tiles_json import gravar_indice_tiles
from ..infrastructure.registro_divisao_json import carregar_registro_divisao


def gravar_indice(raiz: Path, fonte_id: str) -> IndiceTiles:
    """Monta e grava o índice de tiles de uma fonte.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com divisão gravada.

    Returns:
        O índice gravado.

    Raises:
        FileExistsError: Se o índice já tiver sido gravado.
        FileNotFoundError: Se faltar a divisão, o manifesto ou alguma foto.
        OSError: Se alguma foto não for uma imagem reconhecida.
        ValueError: Se a divisão for de outra fonte, se o manifesto mudou desde
            a divisão ou se alguma foto for incompatível com as escalas.
    """
    destino = caminho_indice_tiles(raiz)
    if destino.exists():
        raise FileExistsError(
            f"O índice de tiles já foi gravado: {destino}. Ele não se gera de novo."
        )
    origem_split = caminho_split(raiz)
    divisao = carregar_registro_divisao(origem_split)
    if divisao.fonte_id != fonte_id:
        raise ValueError(f"A divisão gravada é da fonte {divisao.fonte_id!r}.")
    sha_manifesto = sha256_do_arquivo(caminho_manifesto_arquivos(raiz, fonte_id))
    if sha_manifesto != divisao.sha256_manifesto:
        raise ValueError("O manifesto de arquivos mudou desde a gravação da divisão.")
    pasta = pasta_dados_brutos(raiz, fonte_id)
    d = divisao.divisao
    tamanhos = {
        foto: ler_cabecalho(pasta / foto).tamanho_exibido
        for foto in (*d.treino, *d.validacao, *d.teste)
    }
    escalas = (
        (1, REGRAS.lado_tile_nativo),
        (REGRAS.fator_escala_reduzida, REGRAS.lado_tile_reduzido),
    )
    indice = IndiceTiles(
        fonte_id=fonte_id,
        sha256_split=sha256_do_arquivo(origem_split),
        sha256_manifesto=sha_manifesto,
        escalas=escalas,
        fotos=indexar(tamanhos, d, escalas),
    )
    gravar_indice_tiles(indice, destino)
    return indice


def formatar_indice(indice: IndiceTiles) -> str:
    """Resume o índice: fotos e tiles por escala e por conjunto.

    Args:
        indice: O índice a resumir.

    Returns:
        O texto do resumo, sem nomes de foto.
    """
    linhas = [f"Fotos: {len(indice.fotos)}; tiles: {indice.n_tiles}"]
    for posicao, (fator, lado) in enumerate(indice.escalas):
        por_conjunto = []
        for conjunto in CONJUNTOS:
            n = sum(
                foto.grades[posicao].n_tiles
                for foto in indice.fotos
                if foto.conjunto == conjunto
            )
            por_conjunto.append(f"{conjunto} {n}")
        linhas.append(f"  escala {fator} (tile {lado}): {'; '.join(por_conjunto)}")
    return "\n".join(linhas)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a gravação do índice de tiles.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.indice_tiles",
        description="Grava o índice de tiles da divisão (A52).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        indice = gravar_indice(raiz, args.fonte_id)
    except (ValueError, OSError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    print(f"Índice de tiles gravado em {caminho_indice_tiles(raiz)}")
    print(formatar_indice(indice))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
