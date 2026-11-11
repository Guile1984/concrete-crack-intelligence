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


def pasta_imagens_inspecao(raiz: Path, fonte_id: str) -> Path:
    """Devolve a pasta das imagens preparadas para a inspeção das máscaras.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte (por exemplo ccsd).

    Returns:
        O caminho de ``data/interim/inspecao_<fonte_id>``.
    """
    return raiz / "data" / "interim" / f"inspecao_{fonte_id}"


def caminho_vereditos_inspecao(raiz: Path, fonte_id: str) -> Path:
    """Devolve o caminho do registro de vereditos da inspeção das máscaras.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte (por exemplo ccsd).

    Returns:
        O caminho de ``manifests/vereditos_inspecao_<fonte_id>.json``.
    """
    return raiz / "manifests" / f"vereditos_inspecao_{fonte_id}.json"


def caminho_manifesto_pesos(raiz: Path) -> Path:
    """Devolve o caminho do manifesto dos pesos da rede de embeddings.

    Args:
        raiz: Raiz do projeto.

    Returns:
        O caminho de ``manifests/pesos_embeddings.json``.
    """
    return raiz / "manifests" / "pesos_embeddings.json"


def pasta_modelos(raiz: Path) -> Path:
    """Devolve a pasta dos pesos de redes pré-treinadas (fora do Git).

    Args:
        raiz: Raiz do projeto.

    Returns:
        O caminho de ``data/modelos``.
    """
    return raiz / "data" / "modelos"


def caminho_grupos(raiz: Path, fonte_id: str) -> Path:
    """Devolve o caminho do registro dos grupos de quase-duplicatas de uma fonte.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte (por exemplo ccsd).

    Returns:
        O caminho de ``manifests/grupos_<fonte_id>.json``.
    """
    return raiz / "manifests" / f"grupos_{fonte_id}.json"


def caminho_quase_ligadas(raiz: Path, fonte_id: str) -> Path:
    """Devolve o caminho do registro dos pares quase ligados de uma fonte.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte (por exemplo ccsd).

    Returns:
        O caminho de ``manifests/quase_ligadas_<fonte_id>.json``.
    """
    return raiz / "manifests" / f"quase_ligadas_{fonte_id}.json"


def caminho_split(raiz: Path) -> Path:
    """Devolve o caminho do registro da divisão do CCSD (versão 1).

    Args:
        raiz: Raiz do projeto.

    Returns:
        O caminho de ``manifests/split_v1.json``.
    """
    return raiz / "manifests" / "split_v1.json"


def caminho_indice_tiles(raiz: Path) -> Path:
    """Devolve o caminho do índice de tiles do CCSD (versão 1).

    Args:
        raiz: Raiz do projeto.

    Returns:
        O caminho de ``manifests/tiles_v1.json``.
    """
    return raiz / "manifests" / "tiles_v1.json"
