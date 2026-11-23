"""Gravação de registros em JSON e em JSON Lines, de forma determinística."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path


def gravar_json(conteudo: Mapping[str, object], destino: Path) -> None:
    """Grava um objeto em JSON (indentação 2, UTF-8, LF, quebra final).

    Args:
        conteudo: O objeto, com valores que o ``json`` aceita.
        destino: Arquivo de destino; as pastas que faltarem são criadas.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")


def gravar_jsonl(linhas: Sequence[Mapping[str, object]], destino: Path) -> None:
    """Grava uma lista de objetos em JSON Lines: um objeto compacto por linha.

    Args:
        linhas: Os objetos, na ordem em que devem ser gravados.
        destino: Arquivo de destino; as pastas que faltarem são criadas.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = "".join(json.dumps(linha, ensure_ascii=False) + "\n" for linha in linhas)
    destino.write_text(texto, encoding="utf-8", newline="\n")


def ler_jsonl(origem: Path) -> list[dict[str, object]]:
    """Lê um arquivo gravado por ``gravar_jsonl``.

    Args:
        origem: O arquivo.

    Returns:
        Os objetos, na ordem das linhas.
    """
    texto = origem.read_text(encoding="utf-8")
    return [json.loads(linha) for linha in texto.splitlines() if linha]
