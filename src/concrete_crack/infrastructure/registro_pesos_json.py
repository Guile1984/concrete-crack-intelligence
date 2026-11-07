"""Gravação e leitura do registro de procedência dos pesos em JSON."""

import json
from pathlib import Path

from ..domain.pesos import RegistroPesos

CAMPOS = (
    "repositorio",
    "revisao",
    "arquivo",
    "tamanho_bytes",
    "sha256",
    "data_download",
)


def gravar_registro_pesos(registro: RegistroPesos, destino: Path) -> None:
    """Grava o registro em JSON determinístico (indentação 2, LF, quebra final).

    Args:
        registro: O registro a gravar.
        destino: Arquivo de destino.
    """
    conteudo = {campo: getattr(registro, campo) for campo in CAMPOS}
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")


def carregar_registro_pesos(origem: Path) -> RegistroPesos:
    """Lê um registro gravado por ``gravar_registro_pesos``.

    Args:
        origem: Arquivo JSON do registro.

    Returns:
        O registro, validado.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se faltar ou sobrar algum campo, ou se algum for inválido.
    """
    conteudo = json.loads(origem.read_text(encoding="utf-8"))
    if set(conteudo) != set(CAMPOS):
        raise ValueError(
            f"Campos do registro de pesos: esperados {sorted(CAMPOS)}, "
            f"encontrados {sorted(conteudo)}."
        )
    return RegistroPesos(**conteudo)
