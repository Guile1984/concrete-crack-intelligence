"""Gravação e leitura do registro de vereditos em JSON, com troca atômica."""

import json
import os
from pathlib import Path

from ..domain.registro_vereditos import Correcao, Julgamento, RegistroVereditos
from ..domain.veredito import Veredito


def gravar_registro(registro: RegistroVereditos, destino: Path) -> None:
    """Grava o registro em JSON, sem nunca deixar o arquivo pela metade.

    O conteúdo vai primeiro para um arquivo temporário ao lado do destino e só
    depois o substitui numa única operação. Se algo falhar no caminho, o arquivo
    anterior continua intacto. A saída é determinística: indentação de 2
    espaços, fins de linha LF e uma quebra de linha no final.

    Args:
        registro: O registro a gravar.
        destino: Arquivo de destino; um arquivo existente é substituído.
    """
    conteudo = {
        "fonte_id": registro.fonte_id,
        "sha256_amostra": registro.sha256_amostra,
        "amostra": list(registro.amostra),
        "julgamentos": [
            {
                "mascara": j.mascara,
                "veredito": j.veredito.value,
                "registrado_em": j.registrado_em,
                "observacao": j.observacao,
            }
            for j in registro.julgamentos
        ],
        "correcoes": [
            {
                "mascara": c.mascara,
                "de": c.de.value,
                "para": c.para.value,
                "motivo": c.motivo,
                "registrado_em": c.registrado_em,
            }
            for c in registro.correcoes
        ],
    }
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n"
    temporario = destino.with_name(destino.name + ".tmp")
    temporario.write_text(texto, encoding="utf-8", newline="\n")
    os.replace(temporario, destino)


def carregar_registro(origem: Path) -> RegistroVereditos:
    """Lê um registro gravado por ``gravar_registro`` e valida cada parte.

    Args:
        origem: Arquivo JSON do registro.

    Returns:
        O registro lido.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se algum veredito, hora ou vínculo for inválido.
    """
    bruto = json.loads(origem.read_text(encoding="utf-8"))
    julgamentos = tuple(
        Julgamento(
            j["mascara"],
            Veredito(j["veredito"]),
            j["registrado_em"],
            j["observacao"],
        )
        for j in bruto["julgamentos"]
    )
    correcoes = tuple(
        Correcao(
            c["mascara"],
            Veredito(c["de"]),
            Veredito(c["para"]),
            c["motivo"],
            c["registrado_em"],
        )
        for c in bruto["correcoes"]
    )
    return RegistroVereditos(
        bruto["fonte_id"],
        bruto["sha256_amostra"],
        tuple(bruto["amostra"]),
        julgamentos,
        correcoes,
    )
