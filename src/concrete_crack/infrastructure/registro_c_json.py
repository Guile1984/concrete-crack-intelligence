"""Gravação e leitura do registro da constante c do Frangi em JSON."""

import json
from pathlib import Path

from ..domain.registro_c import ConstanteC, RegistroC


def gravar_registro_c(registro: RegistroC, destino: Path) -> None:
    """Grava o registro em JSON determinístico (indentação 2, LF, quebra final).

    Args:
        registro: O registro a gravar.
        destino: Arquivo de destino; as pastas que faltarem são criadas.
    """
    conteudo = {
        "fonte_id": registro.fonte_id,
        "sha256_split": registro.sha256_split,
        "seed": registro.seed,
        "n_pixels_por_foto": registro.n_pixels_por_foto,
        "escalas": list(registro.escalas),
        "percentil": registro.percentil,
        "fracao": registro.fracao,
        "constantes": [
            {"sigma_fundo": c.sigma_fundo, "percentil_s": c.percentil_s, "c": c.c}
            for c in registro.constantes
        ],
        "versoes": dict(registro.versoes),
        "fotos": list(registro.fotos),
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")


def carregar_registro_c(origem: Path) -> RegistroC:
    """Lê um registro gravado por ``gravar_registro_c``.

    Args:
        origem: Arquivo JSON do registro.

    Returns:
        O registro, validado.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        KeyError: Se faltar algum campo.
        ValueError: Se o registro for inválido.
    """
    conteudo = json.loads(origem.read_text(encoding="utf-8"))
    return RegistroC(
        fonte_id=conteudo["fonte_id"],
        sha256_split=conteudo["sha256_split"],
        seed=conteudo["seed"],
        n_pixels_por_foto=conteudo["n_pixels_por_foto"],
        escalas=tuple(conteudo["escalas"]),
        percentil=conteudo["percentil"],
        fracao=conteudo["fracao"],
        fotos=tuple(conteudo["fotos"]),
        constantes=tuple(
            ConstanteC(c["sigma_fundo"], c["percentil_s"], c["c"])
            for c in conteudo["constantes"]
        ),
        versoes=tuple(conteudo["versoes"].items()),
    )
