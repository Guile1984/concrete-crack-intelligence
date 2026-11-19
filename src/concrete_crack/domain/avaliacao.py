"""Avaliação de uma imagem e o preditor trivial "tudo é fundo" (A62, item 8).

Funções puras, sem disco. ``avaliar_imagem`` junta as contagens de pixels e
de esqueletos de uma previsão; o preditor trivial é a linha de base de todo
relatório: acerta quase todos os pixels e não encontra nenhuma fissura.
"""

from collections.abc import Sequence

import numpy as np

from .agregacao import ImagemAvaliada
from .metricas import contar, contar_esqueletos_reais


def avaliar_imagem(
    imagem: str, previsao: np.ndarray, gabarito: np.ndarray, metodo: str
) -> ImagemAvaliada:
    """Conta pixels e esqueletos de uma previsão contra o gabarito.

    Args:
        imagem: Identificador da imagem.
        previsao: Máscara booleana prevista.
        gabarito: Máscara booleana do gabarito.
        metodo: Método do esqueleto (``REGRAS.metodo_esqueleto``).

    Returns:
        A imagem avaliada, pronta para a agregação.
    """
    return ImagemAvaliada(
        imagem,
        contar(previsao, gabarito),
        contar_esqueletos_reais(previsao, gabarito, metodo),
    )


def tudo_e_fundo(gabarito: np.ndarray) -> np.ndarray:
    """Previsão do preditor trivial: nenhum pixel de fissura.

    Args:
        gabarito: Máscara booleana do gabarito; só o formato é usado.

    Returns:
        Máscara booleana toda falsa, do formato do gabarito.

    Raises:
        ValueError: Se o gabarito não for booleano.
    """
    if gabarito.dtype != np.bool_:
        raise ValueError("O gabarito deve ser booleano.")
    return np.zeros(gabarito.shape, dtype=bool)


def acuracia_global(imagens: Sequence[ImagemAvaliada]) -> float | None:
    """Fração de pixels corretos somando todas as imagens, com e sem fissura.

    Só aparece no relatório do preditor trivial, como exemplo de métrica
    enganosa quando a fissura é rara (A62, item 2).

    Returns:
        (VP + VN) / total das contagens somadas, ou ``None`` sem imagens.
    """
    corretos = sum(i.pixels.vp + i.pixels.vn for i in imagens)
    total = sum(i.pixels.total for i in imagens)
    return corretos / total if total else None
