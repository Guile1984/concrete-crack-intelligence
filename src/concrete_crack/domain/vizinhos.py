"""Distância de cada imagem ao vizinho mais próximo (análise descritiva, A47).

Funções puras sobre matrizes numpy. O resultado descreve a que distância as
fotos reais ficam do limiar T; não altera nenhuma decisão.
"""

from collections.abc import Sequence

import numpy as np

QUANTIS = (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0)


def distancias_ao_vizinho_mais_proximo(distancias: np.ndarray) -> np.ndarray:
    """Devolve, para cada imagem, a menor distância até qualquer outra.

    A diagonal (a distância de cada imagem a si mesma) é ignorada.

    Args:
        distancias: Matriz n x n de distâncias, com n >= 2.

    Returns:
        Vetor float64 de n distâncias.

    Raises:
        ValueError: Se a matriz não for quadrada com pelo menos 2 imagens.
    """
    if distancias.ndim != 2 or distancias.shape[0] != distancias.shape[1]:
        raise ValueError("A matriz de distâncias deve ser quadrada.")
    if distancias.shape[0] < 2:
        raise ValueError("São necessárias pelo menos 2 imagens.")
    copia = distancias.astype(np.float64)
    np.fill_diagonal(copia, np.inf)
    return copia.min(axis=1)


def contar_por_faixas(valores: np.ndarray, limites: Sequence[float]) -> list[int]:
    """Conta os valores em cada faixa: até o 1º limite, entre limites e acima.

    Cada limite pertence à faixa de baixo: um valor igual a T conta em "até T".

    Args:
        valores: Valores a contar.
        limites: Limites crescentes, pelo menos 1.

    Returns:
        ``len(limites) + 1`` contagens, da faixa mais baixa para a mais alta.

    Raises:
        ValueError: Se não houver limites ou eles não forem crescentes.
    """
    if not limites or list(limites) != sorted(set(limites)):
        raise ValueError("Os limites devem ser crescentes, sem repetição.")
    indices = np.searchsorted(np.asarray(limites), valores, side="left")
    return np.bincount(indices, minlength=len(limites) + 1).tolist()


def quantis(valores: np.ndarray) -> list[float]:
    """Calcula mínimo, 5%, 25%, mediana, 75%, 95% e máximo.

    Args:
        valores: Valores, pelo menos 1.

    Returns:
        Os sete quantis, na ordem de ``QUANTIS``.
    """
    return np.quantile(valores, QUANTIS).tolist()


def quase_ligadas(valores: np.ndarray, limiar: float, multiplo: float) -> int:
    """Conta as imagens com vizinho acima de T e até ``multiplo`` vezes T.

    Args:
        valores: Distâncias ao vizinho mais próximo.
        limiar: O limiar T.
        multiplo: O múltiplo de T que fecha a faixa.

    Returns:
        A quantidade de imagens quase ligadas.
    """
    return int(np.count_nonzero((valores > limiar) & (valores <= multiplo * limiar)))


def limitacao_relevante(n_quase_ligadas: int, n_imagens: int, fracao: float) -> bool:
    """Diz se a limitação de T é declarada relevante (mais que ``fracao``).

    Args:
        n_quase_ligadas: Imagens quase ligadas.
        n_imagens: Total de imagens.
        fracao: Fração máxima pré-registrada.

    Returns:
        Verdadeiro se as quase ligadas passarem de ``fracao`` das imagens.
    """
    return n_quase_ligadas > fracao * n_imagens
