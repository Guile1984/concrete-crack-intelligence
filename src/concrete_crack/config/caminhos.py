"""Convenções de pastas e de nomes de arquivos do projeto."""

from pathlib import Path


def caminho_fontes(raiz: Path) -> Path:
    """Devolve o caminho do manifesto de fontes (fichas de procedência).

    Args:
        raiz: Raiz do projeto.

    Returns:
        O caminho de ``manifests/fontes.json``.
    """
    return raiz / "manifests" / "fontes.json"


def pasta_dados_brutos(raiz: Path, fonte_id: str) -> Path:
    """Devolve a pasta dos dados brutos de uma fonte.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte (por exemplo ccsd).

    Returns:
        O caminho de ``data/raw/<fonte_id>``.
    """
    return raiz / "data" / "raw" / fonte_id


def caminho_manifesto_arquivos(raiz: Path, fonte_id: str) -> Path:
    """Devolve o caminho do manifesto de arquivos de uma fonte.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte (por exemplo ccsd).

    Returns:
        O caminho de ``manifests/arquivos_<fonte_id>.json``.
    """
    return raiz / "manifests" / f"arquivos_{fonte_id}.json"


def caminho_amostra_inspecao(raiz: Path, fonte_id: str) -> Path:
    """Devolve o caminho da amostra sorteada para a inspeção das máscaras.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte (por exemplo ccsd).

    Returns:
        O caminho de ``manifests/inspecao_<fonte_id>.json``.
    """
    return raiz / "manifests" / f"inspecao_{fonte_id}.json"
