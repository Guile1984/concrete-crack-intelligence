"""Gravação e leitura do manifesto de arquivos em JSON."""

import json
from pathlib import Path

from ..domain.integridade import ArquivoRegistrado, ManifestoArquivos


def gravar_manifesto(manifesto: ManifestoArquivos, destino: Path) -> None:
    """Grava o manifesto em JSON, de forma determinística.

    Os arquivos saem ordenados pelo caminho, com indentação de 2 espaços, fins
    de linha LF e uma quebra de linha no final, para que o arquivo seja estável
    no Git.

    Args:
        manifesto: O manifesto a gravar.
        destino: Arquivo de destino. Não deve ficar dentro da pasta descrita.
    """
    conteudo = {
        "fonte_id": manifesto.fonte_id,
        "data_download": manifesto.data_download,
        "arquivos": [
            {
                "caminho": arquivo.caminho,
                "tamanho_bytes": arquivo.tamanho_bytes,
                "sha256": arquivo.sha256,
            }
            for arquivo in sorted(manifesto.arquivos, key=lambda a: a.caminho)
        ],
    }
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")


def carregar_manifesto(origem: Path) -> ManifestoArquivos:
    """Lê um manifesto de arquivos e valida cada registro.

    Args:
        origem: Arquivo JSON gravado por ``gravar_manifesto``.

    Returns:
        O manifesto lido.

    Raises:
        ValueError: Se algum registro for inválido.
    """
    bruto = json.loads(origem.read_text(encoding="utf-8"))
    arquivos = tuple(ArquivoRegistrado(**item) for item in bruto["arquivos"])
    return ManifestoArquivos(bruto["fonte_id"], bruto["data_download"], arquivos)
