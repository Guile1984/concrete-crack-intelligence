"""Leitura do manifesto de fontes de dados (manifests/fontes.json)."""

import json
from pathlib import Path

from ..domain.procedencia import FonteDados


def carregar_fontes(caminho: Path) -> list[FonteDados]:
    """Lê o manifesto de fontes e valida cada ficha.

    Args:
        caminho: Caminho do arquivo JSON com a lista de fontes.

    Returns:
        As fichas, na ordem do arquivo.

    Raises:
        ValueError: Se alguma ficha for inválida ou houver ids repetidos.
    """
    bruto = json.loads(caminho.read_text(encoding="utf-8"))
    fontes = [_ficha(item) for item in bruto["fontes"]]
    ids = [fonte.id for fonte in fontes]
    if len(ids) != len(set(ids)):
        raise ValueError("O manifesto tem ids de fonte repetidos.")
    return fontes


def _ficha(item: dict[str, object]) -> FonteDados:
    """Converte um item do JSON em ficha, trocando listas por tuplas."""
    dados = dict(item)
    for campo in ("autores", "observacoes", "transformacoes_do_projeto"):
        if campo in dados:
            dados[campo] = tuple(dados[campo])
    return FonteDados(**dados)
