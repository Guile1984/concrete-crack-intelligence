"""Gravação e leitura do manifesto de hashes dos pixels, com uma foto por linha."""

import json
from pathlib import Path

from ..domain.manifesto_pixels import HashesEscala, HashesFoto, ManifestoPixels


def gravar_manifesto_pixels(manifesto: ManifestoPixels, destino: Path) -> None:
    """Grava o manifesto em JSON determinístico, com uma linha por foto (LF).

    Args:
        manifesto: O manifesto a gravar.
        destino: Arquivo de destino.
    """
    cabecalho = [
        f'  "fonte_id": {json.dumps(manifesto.fonte_id, ensure_ascii=False)},',
        f'  "sha256_indice": "{manifesto.sha256_indice}",',
        f'  "versao_pillow": {json.dumps(manifesto.versao_pillow)},',
        '  "fotos": [',
    ]
    fotos = []
    for foto in manifesto.fotos:
        escalas = [
            {"fator": e.fator, "foto": e.foto, "mascara": e.mascara}
            for e in foto.escalas
        ]
        linha = {"foto": foto.foto, "escalas": escalas}
        fotos.append("    " + json.dumps(linha, ensure_ascii=False))
    texto = "{\n" + "\n".join(cabecalho) + "\n" + ",\n".join(fotos) + "\n  ]\n}\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")


def carregar_manifesto_pixels(origem: Path) -> ManifestoPixels:
    """Lê um manifesto gravado por ``gravar_manifesto_pixels``.

    Args:
        origem: Arquivo JSON do manifesto.

    Returns:
        O manifesto, validado.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        KeyError: Se faltar algum campo.
        ValueError: Se o manifesto for inválido.
    """
    conteudo = json.loads(origem.read_text(encoding="utf-8"))
    return ManifestoPixels(
        fonte_id=conteudo["fonte_id"],
        sha256_indice=conteudo["sha256_indice"],
        versao_pillow=conteudo["versao_pillow"],
        fotos=tuple(
            HashesFoto(
                foto=f["foto"],
                escalas=tuple(
                    HashesEscala(e["fator"], e["foto"], e["mascara"])
                    for e in f["escalas"]
                ),
            )
            for f in conteudo["fotos"]
        ),
    )
