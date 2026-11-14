"""Medição descritiva dos tiles do treino (A52, itens 8a e 8b).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.medicao_tiles ccsd

Lê só as máscaras das fotos do treino, em resolução cheia, e as binariza pela
regra da A41. (a) Conta a fissura de cada tile nativo do índice: quantos não
têm nenhum pixel de fissura e, nos que têm, a fração de fissura. Pela A54, o
resultado vale também para a escala 2×. (b) Faz a ida e volta de cada máscara
na escala 2× com as regras pré-registradas e compara com a original. Só
relata: não grava nada e não escolhe a regra (A52, item 4).
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ..config.caminhos import (
    caminho_indice_tiles,
    caminho_manifesto_arquivos,
    caminho_split,
    pasta_dados_brutos,
)
from ..config.regras import REGRAS
from ..domain.alinhamento import marcar_fissura
from ..domain.divisao import TREINO
from ..domain.sobrevivencia import comparar, fissura_por_tile, ida_e_volta, quartis
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import ler_cinza
from ..infrastructure.indice_tiles_json import carregar_indice_tiles
from .estrutura import parear_fonte

INTERVALO_PROGRESSO = 25


@dataclass(frozen=True, slots=True)
class ResultadoRegra:
    """A ida e volta de todas as máscaras com uma regra.

    Attributes:
        regra: ``"maioria"`` ou ``"qualquer"``.
        preservados_total: Fissura preservada sobre a fissura original, somando
            as máscaras.
        a_mais_total: Pixels a mais sobre a fissura original, somando as
            máscaras.
        preservados_quartis: Quartis da fração preservada por máscara.
        a_mais_quartis: Quartis da fração a mais por máscara.
    """

    regra: str
    preservados_total: float
    a_mais_total: float
    preservados_quartis: tuple[float, float, float]
    a_mais_quartis: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class MedicaoTiles:
    """O resultado da medição descritiva.

    Attributes:
        n_fotos: Fotos do treino medidas.
        n_mascaras_sem_fissura: Máscaras sem nenhum pixel de fissura, fora dos
            quartis por máscara.
        n_tiles: Tiles nativos medidos.
        n_tiles_sem_fissura: Tiles sem nenhum pixel de fissura.
        fracao_quartis: Quartis da fração de fissura nos tiles com fissura.
        regras: Um resultado por regra pré-registrada.
    """

    n_fotos: int
    n_mascaras_sem_fissura: int
    n_tiles: int
    n_tiles_sem_fissura: int
    fracao_quartis: tuple[float, float, float]
    regras: tuple[ResultadoRegra, ...]


def medir_tiles(
    raiz: Path,
    fonte_id: str,
    progresso: Callable[[int, int], None] | None = None,
) -> MedicaoTiles:
    """Mede os tiles e a ida e volta das máscaras do treino.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte.
        progresso: Função chamada com (máscaras medidas, total) após cada uma.

    Returns:
        A medição.

    Raises:
        FileNotFoundError: Se faltar o índice, a divisão ou alguma máscara.
        OSError: Se alguma máscara não for uma imagem reconhecida.
        ValueError: Se o índice não vier da divisão e do manifesto atuais ou
            se alguma máscara não tiver o tamanho do índice.
    """
    indice = carregar_indice_tiles(caminho_indice_tiles(raiz))
    if indice.fonte_id != fonte_id:
        raise ValueError(f"O índice de tiles é da fonte {indice.fonte_id!r}.")
    if indice.sha256_split != sha256_do_arquivo(caminho_split(raiz)):
        raise ValueError("A divisão mudou desde a gravação do índice de tiles.")
    manifesto = caminho_manifesto_arquivos(raiz, fonte_id)
    if indice.sha256_manifesto != sha256_do_arquivo(manifesto):
        raise ValueError("O manifesto de arquivos mudou desde o índice de tiles.")
    mascara_de = {foto: mascara for mascara, foto in parear_fonte(raiz, fonte_id).pares}
    pasta = pasta_dados_brutos(raiz, fonte_id)
    lado = dict(indice.escalas)[1]
    fator = REGRAS.fator_escala_reduzida
    regras = REGRAS.regras_mascara_reduzida
    treino = [foto for foto in indice.fotos if foto.conjunto == TREINO]
    contagens: list[int] = []
    sem_fissura = 0
    somas = {regra: [0, 0, 0] for regra in regras}
    por_mascara: dict[str, tuple[list[float], list[float]]] = {
        regra: ([], []) for regra in regras
    }
    for numero, item in enumerate(treino, start=1):
        mascara = marcar_fissura(
            ler_cinza(pasta / mascara_de[item.foto], 1), REGRAS.limiar_binarizacao
        )
        if mascara.shape != (item.altura, item.largura):
            raise ValueError(
                f"{item.foto}: a máscara tem {mascara.shape}, e o índice registra "
                f"{(item.altura, item.largura)}."
            )
        nativa = item.grades[0]
        contagens.extend(fissura_por_tile(mascara, nativa.xs, nativa.ys, lado))
        for regra in regras:
            s = comparar(mascara, ida_e_volta(mascara, fator, regra))
            somas[regra][0] += s.fissura
            somas[regra][1] += s.preservados
            somas[regra][2] += s.a_mais
            if s.fissura:
                por_mascara[regra][0].append(s.preservados / s.fissura)
                por_mascara[regra][1].append(s.a_mais / s.fissura)
        if not mascara.any():
            sem_fissura += 1
        if progresso is not None:
            progresso(numero, len(treino))
    com_fissura = [c / (lado * lado) for c in contagens if c > 0]
    resultados = []
    for regra in regras:
        fissura, preservados, a_mais = somas[regra]
        if not fissura:
            raise ValueError("Não há fissura nas máscaras do treino.")
        resultados.append(
            ResultadoRegra(
                regra=regra,
                preservados_total=preservados / fissura,
                a_mais_total=a_mais / fissura,
                preservados_quartis=quartis(por_mascara[regra][0]),
                a_mais_quartis=quartis(por_mascara[regra][1]),
            )
        )
    return MedicaoTiles(
        n_fotos=len(treino),
        n_mascaras_sem_fissura=sem_fissura,
        n_tiles=len(contagens),
        n_tiles_sem_fissura=sum(c == 0 for c in contagens),
        fracao_quartis=quartis(com_fissura),
        regras=tuple(resultados),
    )


def _pct(valor: float) -> str:
    """Formata uma proporção como percentual com duas casas decimais."""
    return f"{valor * 100:.2f}%".replace(".", ",")


def _trio(valores: tuple[float, float, float]) -> str:
    """Formata 1º quartil, mediana e 3º quartil."""
    return " / ".join(_pct(v) for v in valores)


def formatar_medicao_tiles(medicao: MedicaoTiles) -> str:
    """Monta o relatório da medição, só com números agregados.

    Args:
        medicao: A medição a relatar.

    Returns:
        O texto do relatório.
    """
    fracao_sem = medicao.n_tiles_sem_fissura / medicao.n_tiles
    linhas = [
        "Medição descritiva dos tiles do treino (A52, item 8)",
        f"Máscaras do treino: {medicao.n_fotos} "
        f"({medicao.n_mascaras_sem_fissura} sem fissura); "
        f"tiles por escala: {medicao.n_tiles}",
        "",
        f"(a) Tiles sem fissura: {medicao.n_tiles_sem_fissura} de "
        f"{medicao.n_tiles} ({_pct(fracao_sem)})",
        "    Fissura nos tiles com fissura (1º quartil / mediana / 3º quartil): "
        f"{_trio(medicao.fracao_quartis)}",
        "",
        "(b) Ida e volta na escala 2x, relativo à fissura original",
        "    (total; por máscara: 1º quartil / mediana / 3º quartil)",
    ]
    for r in medicao.regras:
        linhas.append(
            f"  {r.regra:<9} preservados {_pct(r.preservados_total)} "
            f"({_trio(r.preservados_quartis)}); a mais {_pct(r.a_mais_total)} "
            f"({_trio(r.a_mais_quartis)})"
        )
    return "\n".join(linhas)


def _mostrar_progresso(medidas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada bloco de máscaras e ao final."""
    if medidas % INTERVALO_PROGRESSO == 0 or medidas == total:
        print(f"  {medidas}/{total} máscaras", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a medição descritiva dos tiles.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.medicao_tiles",
        description="Mede os tiles e a ida e volta das máscaras do treino (A52).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    try:
        medicao = medir_tiles(args.raiz.resolve(), args.fonte_id, _mostrar_progresso)
    except (ValueError, OSError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    print(formatar_medicao_tiles(medicao))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
