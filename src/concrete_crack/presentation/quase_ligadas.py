"""Gravação dos pares de fotos quase ligadas da A48, para a auditoria da A49.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.quase_ligadas ccsd

Refaz os vetores, conferidos contra os grupos gravados, e lista os pares com
distância acima de T e até 2T. Só grava ``manifests/quase_ligadas_ccsd.json``
se reproduzir a A48: 7 pares cobrindo exatamente as 14 fotos quase ligadas.
Recusa se o arquivo já existir. Os pares não mudam os grupos nem a divisão:
servem só para contar, depois do sorteio, quantos cruzam a fronteira do teste.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ..config.caminhos import caminho_grupos, caminho_quase_ligadas
from ..config.regras import REGRAS
from ..domain.vizinhos import (
    RegistroQuaseLigadas,
    distancias_ao_vizinho_mais_proximo,
    pares_na_faixa,
)
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.registro_quase_ligadas_json import (
    gravar_registro_quase_ligadas,
)
from .duplicatas_embeddings import Extrator
from .vizinhos import matriz_conferida

INTERVALO_PROGRESSO = 50


@dataclass(frozen=True, slots=True)
class ReferenciaQuaseLigadas:
    """O que a execução precisa reproduzir.

    Attributes:
        n_pares: Quantidade de pares quase ligados.
        n_fotos: Quantidade de fotos quase ligadas.
    """

    n_pares: int
    n_fotos: int


REFERENCIA_A48 = ReferenciaQuaseLigadas(n_pares=7, n_fotos=14)


def gravar_quase_ligadas(
    raiz: Path,
    fonte_id: str,
    referencia: ReferenciaQuaseLigadas = REFERENCIA_A48,
    extrator: Extrator | None = None,
    progresso: Callable[[int, int], None] | None = None,
) -> RegistroQuaseLigadas:
    """Identifica e grava os pares quase ligados, conferindo contra a A48.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com grupos gravados.
        referencia: Números que a execução precisa reproduzir.
        extrator: Extrator de embeddings; None usa o DINOv2 com pesos conferidos.
        progresso: Função chamada com (fotos lidas, total).

    Returns:
        O registro gravado.

    Raises:
        FileExistsError: Se o registro já existir.
        ValueError: Se a execução não reproduzir a referência, ou se as
            conferências da matriz falharem.
    """
    destino = caminho_quase_ligadas(raiz, fonte_id)
    if destino.exists():
        raise FileExistsError(
            f"Os pares quase ligados de {fonte_id} já foram gravados: {destino}. "
            "Eles não se regravam."
        )
    conferida = matriz_conferida(raiz, fonte_id, extrator, progresso)
    fotos = conferida.fotos
    limiar = conferida.registro.limiar
    superior = REGRAS.multiplo_quase_ligadas * limiar
    pares = tuple(
        sorted(
            tuple(sorted((fotos[i], fotos[j])))
            for i, j in pares_na_faixa(conferida.matriz, limiar, superior)
        )
    )
    vizinhos = distancias_ao_vizinho_mais_proximo(conferida.matriz)
    quase = {fotos[i] for i, d in enumerate(vizinhos) if limiar < d <= superior}
    nos_pares = {foto for par in pares for foto in par}
    if (
        len(pares) != referencia.n_pares
        or len(quase) != referencia.n_fotos
        or nos_pares != quase
    ):
        raise ValueError(
            f"A execução não reproduz a A48: {len(pares)} pares (esperados "
            f"{referencia.n_pares}), {len(quase)} fotos quase ligadas (esperadas "
            f"{referencia.n_fotos}), pares cobrindo as quase ligadas: "
            f"{nos_pares == quase}."
        )
    registro = RegistroQuaseLigadas(
        fonte_id=fonte_id,
        sha256_grupos=sha256_do_arquivo(caminho_grupos(raiz, fonte_id)),
        limiar=limiar,
        multiplo=REGRAS.multiplo_quase_ligadas,
        pares=pares,
    )
    gravar_registro_quase_ligadas(registro, destino)
    return registro


def _mostrar_progresso(lidas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada bloco de fotos e ao final."""
    if lidas % INTERVALO_PROGRESSO == 0 or lidas == total:
        print(f"  {lidas}/{total} fotos lidas", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a gravação dos pares quase ligados.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.quase_ligadas",
        description="Grava os pares quase ligados da A48, para a auditoria.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        registro = gravar_quase_ligadas(
            raiz, args.fonte_id, progresso=_mostrar_progresso
        )
    except (ValueError, OSError, RuntimeError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    destino = caminho_quase_ligadas(raiz, args.fonte_id)
    fotos = len({foto for par in registro.pares for foto in par})
    print(f"A execução reproduziu a A48. Pares gravados em {destino}")
    print(f"{len(registro.pares)} pares com {fotos} fotos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
