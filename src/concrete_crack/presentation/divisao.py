"""Gravação da divisão do CCSD em treino, validação e teste (A49).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.divisao ccsd

Lê os grupos de ``manifests/grupos_ccsd.json``, confere que o manifesto de
arquivos é o da gravação dos grupos, calcula os tamanhos pelas proporções
pré-registradas e sorteia pela seed da A13 com a função da A49. Grava
``manifests/split_v1.json`` uma única vez. Não lê imagens nem acessa a rede.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..config.caminhos import (
    caminho_grupos,
    caminho_manifesto_arquivos,
    caminho_split,
)
from ..config.regras import REGRAS
from ..domain.divisao import RegistroDivisao, dividir_por_grupos, tamanhos_alvo
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.registro_divisao_json import gravar_registro_divisao
from ..infrastructure.registro_grupos_json import carregar_registro_grupos


def gravar_divisao(raiz: Path, fonte_id: str) -> RegistroDivisao:
    """Sorteia a divisão conforme a A49 e grava o registro.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com grupos gravados.

    Returns:
        O registro gravado.

    Raises:
        FileExistsError: Se a divisão já tiver sido gravada.
        FileNotFoundError: Se faltar o registro de grupos ou o manifesto.
        ValueError: Se o manifesto de arquivos não for o da gravação dos grupos
            ou se a divisão não puder ser feita com os tamanhos exatos.
    """
    destino = caminho_split(raiz)
    if destino.exists():
        raise FileExistsError(
            f"A divisão já foi gravada: {destino}. Ela não se sorteia de novo."
        )
    origem_grupos = caminho_grupos(raiz, fonte_id)
    grupos = carregar_registro_grupos(origem_grupos)
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    sha_manifesto = sha256_do_arquivo(origem)
    if sha_manifesto != grupos.sha256_manifesto:
        raise ValueError("O manifesto de arquivos mudou desde a gravação dos grupos.")
    _, n_validacao, n_teste = tamanhos_alvo(
        grupos.n_fotos, REGRAS.proporcao_validacao, REGRAS.proporcao_teste
    )
    divisao = dividir_por_grupos(grupos.grupos, REGRAS.seed_split, n_validacao, n_teste)
    registro = RegistroDivisao(
        fonte_id=fonte_id,
        seed=REGRAS.seed_split,
        proporcoes=(
            REGRAS.proporcao_treino,
            REGRAS.proporcao_validacao,
            REGRAS.proporcao_teste,
        ),
        sha256_grupos=sha256_do_arquivo(origem_grupos),
        sha256_manifesto=sha_manifesto,
        divisao=divisao,
    )
    gravar_registro_divisao(registro, destino)
    return registro


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a gravação da divisão.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.divisao",
        description="Sorteia e grava a divisão por grupos (A49).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        registro = gravar_divisao(raiz, args.fonte_id)
    except (ValueError, OSError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    divisao = registro.divisao
    print(f"Divisão gravada em {caminho_split(raiz)} (seed {registro.seed})")
    print(
        f"treino: {len(divisao.treino)} fotos; validação: {len(divisao.validacao)}; "
        f"teste: {len(divisao.teste)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
