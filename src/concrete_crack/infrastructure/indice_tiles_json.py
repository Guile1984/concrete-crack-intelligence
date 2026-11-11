"""Gravação e leitura do índice de tiles em JSON, com uma foto por linha."""

import json
from pathlib import Path
from typing import Any

from ..domain.indice_tiles import FotoIndexada, GradeFoto, IndiceTiles


def _foto_em_dict(foto: FotoIndexada) -> dict[str, Any]:
    """Converte uma foto indexada em dicionário, na ordem fixa das chaves."""
    return {
        "foto": foto.foto,
        "conjunto": foto.conjunto,
        "largura": foto.largura,
        "altura": foto.altura,
        "grades": [
            {"fator": grade.fator, "xs": list(grade.xs), "ys": list(grade.ys)}
            for grade in foto.grades
        ],
    }


def gravar_indice_tiles(indice: IndiceTiles, destino: Path) -> None:
    """Grava o índice em JSON determinístico, com uma linha por foto (LF).

    Args:
        indice: O índice a gravar.
        destino: Arquivo de destino.
    """
    escalas = [{"fator": fator, "lado": lado} for fator, lado in indice.escalas]
    cabecalho = [
        f'  "fonte_id": {json.dumps(indice.fonte_id, ensure_ascii=False)},',
        f'  "sha256_split": "{indice.sha256_split}",',
        f'  "sha256_manifesto_de_arquivos": "{indice.sha256_manifesto}",',
        f'  "escalas": {json.dumps(escalas)},',
        '  "fotos": [',
    ]
    fotos = [
        "    " + json.dumps(_foto_em_dict(foto), ensure_ascii=False)
        for foto in indice.fotos
    ]
    texto = "{\n" + "\n".join(cabecalho) + "\n" + ",\n".join(fotos) + "\n  ]\n}\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")


def carregar_indice_tiles(origem: Path) -> IndiceTiles:
    """Lê um índice gravado por ``gravar_indice_tiles``.

    Args:
        origem: Arquivo JSON do índice.

    Returns:
        O índice, validado.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        KeyError: Se faltar algum campo.
        ValueError: Se o índice for inválido.
    """
    conteudo = json.loads(origem.read_text(encoding="utf-8"))
    return IndiceTiles(
        fonte_id=conteudo["fonte_id"],
        sha256_split=conteudo["sha256_split"],
        sha256_manifesto=conteudo["sha256_manifesto_de_arquivos"],
        escalas=tuple((e["fator"], e["lado"]) for e in conteudo["escalas"]),
        fotos=tuple(
            FotoIndexada(
                foto=f["foto"],
                conjunto=f["conjunto"],
                largura=f["largura"],
                altura=f["altura"],
                grades=tuple(
                    GradeFoto(g["fator"], tuple(g["xs"]), tuple(g["ys"]))
                    for g in f["grades"]
                ),
            )
            for f in conteudo["fotos"]
        ),
    )
