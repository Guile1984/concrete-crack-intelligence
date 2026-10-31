"""Comandos de estrutura dos dados: pareamento de máscaras e fotos.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.estrutura parear ccsd

Os comandos leem só o manifesto de arquivos (nomes): não abrem imagens.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..config.caminhos import caminho_manifesto_arquivos
from ..domain.pareamento import Pareamento, parear
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


def main(argv: Sequence[str] | None = None) -> int:
    """Executa os comandos de estrutura.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 se o pareamento estiver completo; 1 se houver arquivos sem par;
        2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.estrutura",
        description="Confere a estrutura dos dados de uma fonte.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    comando = comandos.add_parser("parear", help="confere máscara e foto por nome")
    comando.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        pareamento = parear_fonte(raiz, args.fonte_id)
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    _imprimir(pareamento)
    return 0 if pareamento.completo else 1


if __name__ == "__main__":
    raise SystemExit(main())
