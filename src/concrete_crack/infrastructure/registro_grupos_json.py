"""Gravação e leitura do registro de grupos de quase-duplicatas em JSON."""

import json
from pathlib import Path

from ..domain.grupos import RegistroGrupos


def gravar_registro_grupos(registro: RegistroGrupos, destino: Path) -> None:
    """Grava o registro em JSON determinístico (indentação 2, LF, quebra final).

    Os grupos saem ordenados (cada grupo pelos nomes, e os grupos pelo primeiro
    nome), para que a mesma partição gere sempre o mesmo arquivo.

    Args:
        registro: O registro a gravar.
        destino: Arquivo de destino.
    """
    grupos = sorted(sorted(grupo) for grupo in registro.grupos)
    conteudo = {
        "fonte_id": registro.fonte_id,
        "metodo": registro.metodo,
        "sha256_manifesto_de_arquivos": registro.sha256_manifesto,
        "sha256_pesos": registro.sha256_pesos,
        "limiar": registro.limiar,
        "grupos": grupos,
    }
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")


def carregar_registro_grupos(origem: Path) -> RegistroGrupos:
    """Lê um registro gravado por ``gravar_registro_grupos``.

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
    return RegistroGrupos(
        fonte_id=conteudo["fonte_id"],
        metodo=conteudo["metodo"],
        sha256_manifesto=conteudo["sha256_manifesto_de_arquivos"],
        sha256_pesos=conteudo["sha256_pesos"],
        limiar=conteudo["limiar"],
        grupos=tuple(tuple(grupo) for grupo in conteudo["grupos"]),
    )
