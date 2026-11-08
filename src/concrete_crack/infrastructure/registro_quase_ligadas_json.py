"""Gravação e leitura do registro de pares quase ligados em JSON."""

import json
from pathlib import Path

from ..domain.vizinhos import RegistroQuaseLigadas


def gravar_registro_quase_ligadas(
    registro: RegistroQuaseLigadas, destino: Path
) -> None:
    """Grava o registro em JSON determinístico (indentação 2, LF, quebra final).

    Args:
        registro: O registro a gravar.
        destino: Arquivo de destino.
    """
    conteudo = {
        "fonte_id": registro.fonte_id,
        "sha256_grupos": registro.sha256_grupos,
        "limiar": registro.limiar,
        "multiplo": registro.multiplo,
        "pares": [list(par) for par in sorted(registro.pares)],
    }
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")


def carregar_registro_quase_ligadas(origem: Path) -> RegistroQuaseLigadas:
    """Lê um registro gravado por ``gravar_registro_quase_ligadas``.

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
    return RegistroQuaseLigadas(
        fonte_id=conteudo["fonte_id"],
        sha256_grupos=conteudo["sha256_grupos"],
        limiar=conteudo["limiar"],
        multiplo=conteudo["multiplo"],
        pares=tuple(tuple(par) for par in conteudo["pares"]),
    )
