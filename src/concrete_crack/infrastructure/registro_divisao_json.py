"""Gravação e leitura do registro da divisão em JSON."""

import json
from pathlib import Path

from ..domain.divisao import Divisao, RegistroDivisao


def gravar_registro_divisao(registro: RegistroDivisao, destino: Path) -> None:
    """Grava o registro em JSON determinístico (indentação 2, LF, quebra final).

    Args:
        registro: O registro a gravar.
        destino: Arquivo de destino.
    """
    treino, validacao, teste = registro.proporcoes
    conteudo = {
        "fonte_id": registro.fonte_id,
        "seed": registro.seed,
        "proporcoes": {"treino": treino, "validacao": validacao, "teste": teste},
        "sha256_grupos": registro.sha256_grupos,
        "sha256_manifesto_de_arquivos": registro.sha256_manifesto,
        "treino": sorted(registro.divisao.treino),
        "validacao": sorted(registro.divisao.validacao),
        "teste": sorted(registro.divisao.teste),
    }
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")


def carregar_registro_divisao(origem: Path) -> RegistroDivisao:
    """Lê um registro gravado por ``gravar_registro_divisao``.

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
    proporcoes = conteudo["proporcoes"]
    return RegistroDivisao(
        fonte_id=conteudo["fonte_id"],
        seed=conteudo["seed"],
        proporcoes=(
            proporcoes["treino"],
            proporcoes["validacao"],
            proporcoes["teste"],
        ),
        sha256_grupos=conteudo["sha256_grupos"],
        sha256_manifesto=conteudo["sha256_manifesto_de_arquivos"],
        divisao=Divisao(
            treino=tuple(conteudo["treino"]),
            validacao=tuple(conteudo["validacao"]),
            teste=tuple(conteudo["teste"]),
        ),
    )
