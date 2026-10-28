"""Sorteio da amostra de inspeção das máscaras, a partir do manifesto de arquivos.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.inspecao sortear ccsd

O comando lê só o manifesto (nomes e hashes): não abre nenhuma imagem.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from ..config.caminhos import (
    caminho_amostra_inspecao,
    caminho_manifesto_arquivos,
)
from ..config.regras import REGRAS
from ..domain.amostragem import amostrar_por_hash
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.manifesto_arquivos import carregar_manifesto

PREFIXO_MASCARAS = "BW/"


def sortear_amostra(raiz: Path, fonte_id: str) -> dict[str, object]:
    """Sorteia as máscaras a inspecionar e grava o registro do sorteio.

    O sorteio é pré-registrado: o arquivo é criado uma única vez e nunca
    refeito, pois refazê-lo depois de ver máscaras anularia o pré-registro.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado.

    Returns:
        O registro gravado em ``manifests/inspecao_<fonte_id>.json``.

    Raises:
        FileExistsError: Se a amostra da fonte já existir.
        FileNotFoundError: Se o manifesto de arquivos não existir.
        ValueError: Se o manifesto for de outra fonte ou tiver menos máscaras
            do que o tamanho da amostra.
    """
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    destino = caminho_amostra_inspecao(raiz, fonte_id)
    if destino.exists():
        raise FileExistsError(
            f"A amostra de {fonte_id} já existe: {destino}. O sorteio é "
            "pré-registrado e não se refaz."
        )
    manifesto = carregar_manifesto(origem)
    if manifesto.fonte_id != fonte_id:
        raise ValueError(
            f"O manifesto de {fonte_id} declara a fonte {manifesto.fonte_id!r}."
        )
    mascaras = [
        arquivo.caminho
        for arquivo in manifesto.arquivos
        if arquivo.caminho.startswith(PREFIXO_MASCARAS)
    ]
    amostra = amostrar_por_hash(
        mascaras, REGRAS.n_inspecao_mascaras, REGRAS.seed_inspecao_mascaras
    )
    registro: dict[str, object] = {
        "fonte_id": fonte_id,
        "seed": REGRAS.seed_inspecao_mascaras,
        "n": REGRAS.n_inspecao_mascaras,
        "limiar_reprovacao": REGRAS.limiar_reprovacao_mascaras,
        "total_mascaras": len(mascaras),
        "sha256_manifesto_de_arquivos": sha256_do_arquivo(origem),
        "amostra": list(amostra),
    }
    texto = json.dumps(registro, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")
    return registro


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o comando de inspeção.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.inspecao",
        description="Sorteia a amostra de máscaras a inspecionar.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    sortear = comandos.add_parser("sortear", help="sorteia e grava a amostra")
    sortear.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        registro = sortear_amostra(raiz, args.fonte_id)
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    destino = caminho_amostra_inspecao(raiz, args.fonte_id)
    print(
        f"Sorteadas {registro['n']} de {registro['total_mascaras']} máscaras "
        f"em {destino}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
