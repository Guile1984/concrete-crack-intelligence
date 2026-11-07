"""Recompressão JPEG em memória, para o controle positivo de duplicatas."""

import io

import numpy as np
from PIL import Image


def recomprimir_jpeg(cinza: np.ndarray, qualidade: int) -> np.ndarray:
    """Comprime uma imagem em JPEG na memória e a decodifica de volta.

    Nada é gravado em disco.

    Args:
        cinza: Imagem uint8 em tons de cinza (2D) ou RGB (altura x largura x 3).
        qualidade: Qualidade JPEG, de 1 a 95.

    Returns:
        A imagem uint8 decodificada, com a mesma forma da original.

    Raises:
        ValueError: Se a imagem não for uint8 2D ou RGB, ou a qualidade estiver
            fora de 1 a 95.
    """
    colorida = cinza.ndim == 3 and cinza.shape[2] == 3
    if cinza.dtype != np.uint8 or not (cinza.ndim == 2 or colorida):
        raise ValueError("A imagem deve ser uint8, 2D ou RGB.")
    if not 1 <= qualidade <= 95:
        raise ValueError("A qualidade JPEG deve estar entre 1 e 95.")
    memoria = io.BytesIO()
    Image.fromarray(cinza).save(memoria, format="JPEG", quality=qualidade)
    memoria.seek(0)
    with Image.open(memoria) as imagem:
        return np.array(imagem.convert("RGB" if colorida else "L"))
