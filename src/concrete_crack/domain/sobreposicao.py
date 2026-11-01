"""Sobreposição da máscara sobre a foto, para inspeção visual.

Funções puras sobre matrizes numpy, sem acesso a disco.
"""

import numpy as np

COR_PADRAO = (255, 0, 0)


def intensidade_da_mascara(cinza: np.ndarray) -> np.ndarray:
    """Converte a máscara em tons de cinza numa intensidade de 0 a 1 por pixel.

    O fundo é o valor mediano da imagem; a intensidade é a distância ao fundo,
    em fração de 255. Não depende de a fissura ser branca sobre preto ou o
    inverso e não binariza: fissuras acinzentadas pela redução ficam fracas,
    em vez de sumirem.

    Args:
        cinza: Máscara em tons de cinza (linhas x colunas), não vazia.

    Returns:
        Matriz float64 de mesma forma, com valores de 0 a 1.

    Raises:
        ValueError: Se a imagem for vazia.
    """
    if cinza.size == 0:
        raise ValueError("A imagem está vazia.")
    fundo = np.median(cinza)
    return np.abs(cinza.astype(np.float64) - fundo) / 255.0


def sobrepor_mascara(
    foto: np.ndarray,
    intensidade: np.ndarray,
    opacidade: float,
    cor: tuple[int, int, int] = COR_PADRAO,
) -> np.ndarray:
    """Mistura uma cor sobre a foto, pixel a pixel, conforme a intensidade.

    O peso da cor em cada pixel é ``opacidade * intensidade``; onde a
    intensidade é 0 a foto não muda.

    Args:
        foto: Imagem RGB uint8 (linhas x colunas x 3).
        intensidade: Matriz de 0 a 1, de mesma altura e largura da foto.
        opacidade: Peso máximo da cor, no intervalo (0, 1].
        cor: Cor da sobreposição, em RGB.

    Returns:
        Nova imagem RGB uint8; a foto de entrada não é alterada.

    Raises:
        ValueError: Se a foto não for RGB, se as formas diferirem, se a
            opacidade estiver fora de (0, 1] ou se a intensidade sair de 0 a 1.
    """
    if foto.ndim != 3 or foto.shape[2] != 3:
        raise ValueError("A foto precisa ser RGB (linhas x colunas x 3).")
    if intensidade.shape != foto.shape[:2]:
        raise ValueError(
            f"Formas diferentes: foto {foto.shape[:2]}, "
            f"intensidade {intensidade.shape}."
        )
    if not 0 < opacidade <= 1:
        raise ValueError("A opacidade deve estar em (0, 1].")
    if intensidade.min() < 0 or intensidade.max() > 1:
        raise ValueError("A intensidade deve estar entre 0 e 1.")
    peso = (opacidade * intensidade)[..., np.newaxis]
    misturada = foto.astype(np.float64) * (1 - peso) + np.array(cor) * peso
    return np.rint(misturada).astype(np.uint8)
