"""Download único e conferência dos pesos da rede de embeddings.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.pesos baixar
    python -m concrete_crack.presentation.pesos conferir

O ``baixar`` consulta a revisão atual do repositório do timm no Hugging Face,
baixa o arquivo de pesos nessa revisão exata para ``data/modelos/`` e grava o
manifesto ``manifests/pesos_embeddings.json`` com o SHA-256 do arquivo recebido.
Recusa se o manifesto já existir: o primeiro download é a referência. O
``conferir`` confere o hash, carrega a rede em modo estrito e extrai um vetor.

As dependências pesadas (huggingface_hub, torch, timm) são importadas só dentro
das funções que as usam, para que o resto do módulo rode sem elas.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

import numpy as np

from ..config.caminhos import caminho_manifesto_pesos, pasta_modelos
from ..config.regras import REGRAS
from ..domain.pesos import RegistroPesos
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.registro_pesos_json import (
    carregar_registro_pesos,
    gravar_registro_pesos,
)

REPOSITORIO = f"timm/{REGRAS.modelo_embeddings}"
ARQUIVO = "model.safetensors"
LADO_IMAGEM_TESTE = 64


def baixar_pesos(
    raiz: Path,
    hoje: str,
    revisao_de: Callable[[str], str] | None = None,
    baixar: Callable[[str, str, str, Path], Path] | None = None,
) -> RegistroPesos:
    """Baixa os pesos uma única vez e grava o manifesto com o hash recebido.

    Args:
        raiz: Raiz do projeto.
        hoje: Data do download, AAAA-MM-DD.
        revisao_de: Consulta a revisão atual de um repositório; None usa o Hub.
        baixar: Baixa (repositório, arquivo, revisão, pasta); None usa o Hub.

    Returns:
        O registro gravado.

    Raises:
        FileExistsError: Se o manifesto dos pesos já existir.
    """
    manifesto = caminho_manifesto_pesos(raiz)
    if manifesto.exists():
        raise FileExistsError(
            f"O manifesto dos pesos já existe: {manifesto}. O primeiro download "
            "é a referência e não se refaz."
        )
    if revisao_de is None or baixar is None:
        from ..infrastructure.hub import baixar_do_hub, revisao_atual

        revisao_de = revisao_de or revisao_atual
        baixar = baixar or baixar_do_hub
    revisao = revisao_de(REPOSITORIO)
    pasta = pasta_modelos(raiz)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = baixar(REPOSITORIO, ARQUIVO, revisao, pasta)
    registro = RegistroPesos(
        repositorio=REPOSITORIO,
        revisao=revisao,
        arquivo=ARQUIVO,
        tamanho_bytes=caminho.stat().st_size,
        sha256=sha256_do_arquivo(caminho),
        data_download=hoje,
    )
    gravar_registro_pesos(registro, manifesto)
    return registro


def conferir_pesos(raiz: Path) -> np.ndarray:
    """Confere o hash, carrega a rede em modo estrito e extrai um vetor de teste.

    Args:
        raiz: Raiz do projeto.

    Returns:
        O vetor extraído de uma imagem cinza uniforme.

    Raises:
        FileNotFoundError: Se o manifesto ou o arquivo de pesos não existir.
        ValueError: Se o hash não conferir ou o manifesto for inválido.
        RuntimeError: Se os parâmetros do arquivo não corresponderem à rede.
    """
    registro = carregar_registro_pesos(caminho_manifesto_pesos(raiz))
    from ..infrastructure.embeddings import criar_extrator_com_pesos

    extrator = criar_extrator_com_pesos(
        REGRAS.modelo_embeddings,
        REGRAS.lado_entrada_embeddings,
        pasta_modelos(raiz) / registro.arquivo,
        registro.sha256,
    )
    cinza = np.full((LADO_IMAGEM_TESTE, LADO_IMAGEM_TESTE, 3), 128, dtype=np.uint8)
    return extrator.extrair(cinza)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o download ou a conferência dos pesos.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.pesos",
        description="Baixa uma única vez e confere os pesos da rede de embeddings.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    comandos.add_parser("baixar", help="baixa os pesos e grava o manifesto")
    comandos.add_parser("conferir", help="confere o hash e carrega a rede")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        if args.comando == "baixar":
            registro = baixar_pesos(raiz, date.today().isoformat())
            print(f"Pesos baixados de {registro.repositorio}")
            print(f"Revisão: {registro.revisao}")
            print(f"Arquivo: {registro.arquivo} ({registro.tamanho_bytes} bytes)")
            print(f"SHA-256: {registro.sha256}")
            print(f"Manifesto: {caminho_manifesto_pesos(raiz)}")
        else:
            vetor = conferir_pesos(raiz)
            print(
                f"Pesos conferidos: hash confere e a rede devolve {len(vetor)} números."
            )
    except (ValueError, OSError, RuntimeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
