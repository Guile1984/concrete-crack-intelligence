"""Acesso ao Hugging Face Hub: revisão atual e download de um arquivo.

Funções finas, sem lógica própria, isoladas aqui para que o resto do projeto
possa ser testado com substitutos, sem rede.
"""

from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download


def revisao_atual(repositorio: str) -> str:
    """Consulta o commit atual do ramo principal de um repositório de modelo.

    Args:
        repositorio: Repositório no formato ``dono/nome``.

    Returns:
        O commit, com 40 caracteres hexadecimais.

    Raises:
        ValueError: Se o Hub não informar a revisão.
    """
    revisao = HfApi().model_info(repositorio).sha
    if not revisao:
        raise ValueError(f"O Hub não informou a revisão de {repositorio}.")
    return revisao


def baixar_do_hub(repositorio: str, arquivo: str, revisao: str, pasta: Path) -> Path:
    """Baixa um arquivo de um repositório, numa revisão exata, para uma pasta.

    Args:
        repositorio: Repositório no formato ``dono/nome``.
        arquivo: Nome do arquivo no repositório.
        revisao: Commit exato a baixar.
        pasta: Pasta local de destino.

    Returns:
        O caminho do arquivo baixado.
    """
    caminho = hf_hub_download(
        repo_id=repositorio, filename=arquivo, revision=revisao, local_dir=pasta
    )
    return Path(caminho)
