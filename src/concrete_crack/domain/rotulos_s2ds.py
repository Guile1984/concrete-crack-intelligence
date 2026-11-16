"""Binarização dos rótulos do S2DS, conforme a A58.

Funções puras sobre matrizes numpy, sem disco. O rótulo RGBA vira um mapa de
índices de classe, na ordem do mapa de cores recebido; pixels com alfa
diferente do exigido ou com cor fora do mapa fazem o rótulo ser recusado, sem
nenhuma correção silenciosa. A máscara binária marca só a classe de fissura.
"""

from collections.abc import Sequence

import numpy as np

SENTINELA = 255


def _codigo(cores: np.ndarray) -> np.ndarray:
    """Converte cores RGB em um único inteiro por pixel: R x 65536 + G x 256 + B."""
    cores = cores.astype(np.int64)
    return cores[..., 0] * 65536 + cores[..., 1] * 256 + cores[..., 2]


def mapa_de_classes(
    rotulo: np.ndarray,
    cores: Sequence[tuple[str, tuple[int, int, int]]],
    alfa: int,
) -> np.ndarray:
    """Converte um rótulo RGBA no mapa de índices de classe.

    Args:
        rotulo: Rótulo uint8 (altura, largura, 4).
        cores: Pares (classe, cor RGB); o índice de cada classe é a sua posição.
        alfa: Valor do canal alfa exigido em todos os pixels.

    Returns:
        Matriz uint8 (altura, largura) com o índice da classe de cada pixel.

    Raises:
        ValueError: Se o rótulo não for RGBA uint8, se algum pixel tiver outro
            alfa, se alguma cor estiver fora do mapa ou se o mapa tiver mais de
            255 classes.
    """
    if rotulo.dtype != np.uint8 or rotulo.ndim != 3 or rotulo.shape[2] != 4:
        raise ValueError("O rótulo deve ser uma matriz uint8 RGBA.")
    if len(cores) >= SENTINELA:
        raise ValueError("O mapa de cores tem classes demais.")
    outro_alfa = int((rotulo[..., 3] != alfa).sum())
    if outro_alfa:
        raise ValueError(f"{outro_alfa} pixel(s) com alfa diferente de {alfa}.")
    codigos = _codigo(rotulo[..., :3])
    classes = np.full(codigos.shape, SENTINELA, dtype=np.uint8)
    for indice, (_, cor) in enumerate(cores):
        classes[codigos == _codigo(np.array(cor))] = indice
    desconhecidos = classes == SENTINELA
    if desconhecidos.any():
        exemplo = tuple(int(c) for c in rotulo[..., :3][desconhecidos][0])
        raise ValueError(
            f"{int(desconhecidos.sum())} pixel(s) com cor fora do mapa, "
            f"por exemplo RGB {exemplo}."
        )
    return classes


def mascara_binaria(classes: np.ndarray, indice_fissura: int) -> np.ndarray:
    """Marca como fissura só os pixels da classe de fissura.

    Args:
        classes: Mapa de índices de classe.
        indice_fissura: Índice da classe de fissura.

    Returns:
        Máscara booleana, verdadeira na fissura.
    """
    return classes == indice_fissura


def contar_classes(classes: np.ndarray, n_classes: int) -> list[int]:
    """Conta os pixels de cada classe.

    Args:
        classes: Mapa de índices de classe, com valores de 0 a n_classes - 1.
        n_classes: Quantidade de classes do mapa.

    Returns:
        A contagem de cada classe, na ordem dos índices.
    """
    return np.bincount(classes.ravel(), minlength=n_classes).tolist()
