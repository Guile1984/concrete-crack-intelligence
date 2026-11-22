"""Amostra e cálculo da constante c do Frangi, conforme a A65 e a A66.

Funções puras, sem disco. O c sai de uma amostra fixa do treino: fotos e
pixels sorteados com a seed pré-registrada, e c = fração x percentil dos
valores de S* (a estrutura normalizada por σ²) nos pixels sorteados.
"""

from collections.abc import Sequence

import numpy as np


def sortear_fotos(fotos: Sequence[str], n: int, seed: int) -> tuple[str, ...]:
    """Sorteia n fotos distintas, sem depender da ordem de entrada.

    Args:
        fotos: As fotos candidatas (as do treino).
        n: Quantas sortear.
        seed: Semente do sorteio.

    Returns:
        As fotos sorteadas, em ordem alfabética.

    Raises:
        ValueError: Se houver fotos repetidas ou n fora de [1, len(fotos)].
    """
    ordenadas = sorted(fotos)
    if len(set(ordenadas)) != len(ordenadas):
        raise ValueError("As fotos candidatas não podem se repetir.")
    if not 1 <= n <= len(ordenadas):
        raise ValueError(f"Não dá para sortear {n} de {len(ordenadas)} fotos.")
    escolhidas = np.random.default_rng(seed).choice(len(ordenadas), n, replace=False)
    return tuple(sorted(ordenadas[i] for i in escolhidas))


def sortear_pixels(total: int, n: int, seed: int, indice: int) -> np.ndarray:
    """Sorteia n posições distintas de uma imagem achatada.

    Cada foto usa a semente (seed, índice da foto na amostra), de modo que o
    sorteio de uma foto não depende da ordem em que as outras são lidas.

    Args:
        total: Quantidade de pixels da imagem (altura x largura).
        n: Quantos pixels sortear.
        seed: Semente pré-registrada.
        indice: Posição da foto na amostra.

    Returns:
        As posições, em ordem crescente.

    Raises:
        ValueError: Se n estiver fora de [1, total] ou o índice for negativo.
    """
    if not 1 <= n <= total:
        raise ValueError(f"Não dá para sortear {n} de {total} pixels.")
    if indice < 0:
        raise ValueError("O índice da foto não pode ser negativo.")
    gerador = np.random.default_rng((seed, indice))
    return np.sort(gerador.choice(total, n, replace=False))


def constante_c(valores: np.ndarray, fracao: float, percentil: float) -> float:
    """Calcula c = fração x percentil dos valores de S*.

    Args:
        valores: Os valores de S* nos pixels sorteados.
        fracao: ``REGRAS.fracao_c_frangi``.
        percentil: ``REGRAS.percentil_c_frangi``, pelo método linear.

    Returns:
        A constante c.

    Raises:
        ValueError: Se não houver valores, se algum não for finito ou
            negativo, ou se o c resultante não for positivo.
    """
    if valores.size == 0:
        raise ValueError("Não há valores para calcular o c.")
    if not np.all(np.isfinite(valores)) or valores.min() < 0:
        raise ValueError("Os valores de S* devem ser finitos e não negativos.")
    c = fracao * float(np.percentile(valores, percentil))
    if c <= 0:
        raise ValueError("O c calculado não é positivo.")
    return c
