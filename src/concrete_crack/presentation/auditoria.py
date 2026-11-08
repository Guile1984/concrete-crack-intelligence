"""Auditoria dos pares quase ligados da A48 diante da divisão v1 (A49).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.auditoria ccsd

Lê ``split_v1.json`` e ``quase_ligadas_<fonte>.json``, confere que os dois vêm
do registro de grupos atual e conta quantos pares cruzam a fronteira do teste.
Só relata: não grava nada, não lê imagens e não altera a divisão.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..config.caminhos import caminho_grupos, caminho_quase_ligadas, caminho_split
from ..domain.auditoria import AuditoriaPares, auditar_pares
from ..domain.divisao import TESTE
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.registro_divisao_json import carregar_registro_divisao
from ..infrastructure.registro_quase_ligadas_json import (
    carregar_registro_quase_ligadas,
)


def auditar_divisao(raiz: Path, fonte_id: str) -> AuditoriaPares:
    """Audita os pares quase ligados de uma fonte diante da divisão gravada.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte.

    Returns:
        A auditoria.

    Raises:
        FileNotFoundError: Se faltar a divisão, os pares ou os grupos.
        KeyError: Se alguma foto de um par não estiver na divisão.
        ValueError: Se a divisão for de outra fonte, ou se divisão, pares e
            grupos não vierem do mesmo registro de grupos.
    """
    divisao = carregar_registro_divisao(caminho_split(raiz))
    if divisao.fonte_id != fonte_id:
        raise ValueError(f"A divisão gravada é da fonte {divisao.fonte_id!r}.")
    quase = carregar_registro_quase_ligadas(caminho_quase_ligadas(raiz, fonte_id))
    sha_grupos = sha256_do_arquivo(caminho_grupos(raiz, fonte_id))
    if divisao.sha256_grupos != sha_grupos:
        raise ValueError("O registro de grupos mudou desde a gravação da divisão.")
    if quase.sha256_grupos != sha_grupos:
        raise ValueError("Os pares quase ligados vêm de outro registro de grupos.")
    return auditar_pares(quase.pares, divisao.divisao)


def _decimal(valor: float) -> str:
    """Formata um número com duas casas e vírgula decimal."""
    return f"{valor:.2f}".replace(".", ",")


def formatar_auditoria(auditoria: AuditoriaPares, fonte_id: str) -> str:
    """Monta o relatório da auditoria.

    Args:
        auditoria: A auditoria a relatar.
        fonte_id: Identificador da fonte.

    Returns:
        O texto do relatório, com o conjunto de cada foto de cada par.
    """
    n = len(auditoria.pares)
    linhas = [
        f"Auditoria dos pares quase ligados de {fonte_id} (A48) na divisão v1",
        f"Pares: {n} ({2 * n} fotos)",
        f"Uma foto no teste e a outra fora: {auditoria.cruzam_teste} "
        f"(esperado ao acaso: {_decimal(auditoria.esperado_cruzam_teste)})",
        f"Em conjuntos diferentes quaisquer: {auditoria.em_conjuntos_diferentes} "
        f"(esperado ao acaso: {_decimal(auditoria.esperado_diferentes)})",
        "",
        "Por par:",
    ]
    for (a, b), (x, y) in zip(auditoria.pares, auditoria.conjuntos, strict=True):
        marca = "  <- cruza o teste" if (TESTE in (x, y) and x != y) else ""
        linhas.append(f"  {a} ({x})  {b} ({y}){marca}")
    return "\n".join(linhas)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a auditoria.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.auditoria",
        description="Audita os pares quase ligados diante da divisão (A49).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    try:
        auditoria = auditar_divisao(args.raiz.resolve(), args.fonte_id)
    except (ValueError, OSError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    print(formatar_auditoria(auditoria, args.fonte_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
