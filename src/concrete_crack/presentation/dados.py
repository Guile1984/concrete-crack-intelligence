"""Comandos de dados: registrar os arquivos de uma fonte e verificar a integridade.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.dados registrar ccsd
    python -m concrete_crack.presentation.dados verificar ccsd
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from ..config.caminhos import (
    caminho_fontes,
    caminho_manifesto_arquivos,
    pasta_dados_brutos,
)
from ..domain.integridade import Divergencias, ManifestoArquivos, comparar
from ..infrastructure.arquivos import registrar_pasta
from ..infrastructure.manifesto import carregar_fontes
from ..infrastructure.manifesto_arquivos import carregar_manifesto, gravar_manifesto

LIMITE_LISTA = 20


def _exigir_ficha(raiz: Path, fonte_id: str) -> None:
    """Recusa fontes que não têm ficha de procedência em manifests/fontes.json."""
    ids = {fonte.id for fonte in carregar_fontes(caminho_fontes(raiz))}
    if fonte_id not in ids:
        conhecidas = ", ".join(sorted(ids))
        raise ValueError(
            f"A fonte {fonte_id!r} não tem ficha em manifests/fontes.json. "
            f"Fontes com ficha: {conhecidas}."
        )


def registrar_fonte(
    raiz: Path,
    fonte_id: str,
    data_download: str,
) -> ManifestoArquivos:
    """Registra os arquivos baixados de uma fonte e grava o manifesto.

    O manifesto é criado uma única vez: o primeiro registro é o que vale
    (confiança no primeiro uso), e refazê-lo aceitaria em silêncio arquivos
    alterados.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, que precisa ter ficha em fontes.json.
        data_download: Data (AAAA-MM-DD) em que os arquivos foram baixados.

    Returns:
        O manifesto gravado.

    Raises:
        ValueError: Se a fonte não tiver ficha ou a pasta não tiver arquivos.
        FileExistsError: Se o manifesto da fonte já existir.
        NotADirectoryError: Se a pasta de dados da fonte não existir.
    """
    _exigir_ficha(raiz, fonte_id)
    destino = caminho_manifesto_arquivos(raiz, fonte_id)
    if destino.exists():
        raise FileExistsError(
            f"O manifesto de {fonte_id} já existe: {destino}. O primeiro registro é "
            "o que vale; para auditar, use 'verificar'."
        )
    arquivos = registrar_pasta(pasta_dados_brutos(raiz, fonte_id))
    manifesto = ManifestoArquivos(fonte_id, data_download, arquivos)
    gravar_manifesto(manifesto, destino)
    return manifesto


def verificar_fonte(raiz: Path, fonte_id: str) -> Divergencias:
    """Compara a pasta de dados atual de uma fonte com o manifesto registrado.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, que precisa ter ficha em fontes.json.

    Returns:
        As divergências entre o manifesto e a pasta.

    Raises:
        ValueError: Se a fonte não tiver ficha ou o manifesto for de outra fonte.
        FileNotFoundError: Se o manifesto da fonte não existir.
        NotADirectoryError: Se a pasta de dados da fonte não existir.
    """
    _exigir_ficha(raiz, fonte_id)
    manifesto = carregar_manifesto(caminho_manifesto_arquivos(raiz, fonte_id))
    if manifesto.fonte_id != fonte_id:
        raise ValueError(
            f"O manifesto de {fonte_id} declara a fonte {manifesto.fonte_id!r}."
        )
    observado = registrar_pasta(pasta_dados_brutos(raiz, fonte_id))
    return comparar(manifesto, observado)


def _imprimir(fonte_id: str, divergencias: Divergencias) -> None:
    """Imprime as divergências, com no máximo 20 caminhos por grupo."""
    print(f"Divergências em {fonte_id}:")
    grupos = (
        ("ausentes", divergencias.ausentes),
        ("inesperados", divergencias.inesperados),
        ("alterados", divergencias.alterados),
    )
    for titulo, caminhos in grupos:
        if not caminhos:
            continue
        print(f"  {titulo} ({len(caminhos)}):")
        for caminho in caminhos[:LIMITE_LISTA]:
            print(f"    {caminho}")
        if len(caminhos) > LIMITE_LISTA:
            print(f"    ... e mais {len(caminhos) - LIMITE_LISTA}")


def main(argv: Sequence[str] | None = None) -> int:
    """Executa os comandos de dados.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 1 se a verificação encontrar divergências; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.dados",
        description="Registra e verifica os arquivos de uma fonte de dados.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    registrar = comandos.add_parser("registrar", help="grava o manifesto")
    registrar.add_argument("fonte_id")
    registrar.add_argument("--data-download", help="AAAA-MM-DD (padrão: hoje)")
    verificar = comandos.add_parser("verificar", help="compara com o manifesto")
    verificar.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        if args.comando == "registrar":
            data = args.data_download or date.today().isoformat()
            manifesto = registrar_fonte(raiz, args.fonte_id, data)
            destino = caminho_manifesto_arquivos(raiz, args.fonte_id)
            print(f"Registrados {len(manifesto.arquivos)} arquivos em {destino}")
            return 0
        divergencias = verificar_fonte(raiz, args.fonte_id)
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    if divergencias.vazio:
        print(f"{args.fonte_id}: nenhuma divergência.")
        return 0
    _imprimir(args.fonte_id, divergencias)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
