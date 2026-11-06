"""Recompressão JPEG em memória, para o controle positivo de duplicatas."""

import io

import numpy as np
from PIL import Image


def recomprimir_jpeg(cinza: np.ndarray, qualidade: int) -> np.ndarray:
    """Comprime uma imagem em JPEG na memória e a decodifica de volta.

    Nada é gravado em disco.

    Args:
        cinza: Imagem 2D uint8.
        qualidade: Qualidade JPEG, de 1 a 95.

    Returns:
        A imagem uint8 decodificada, com a mesma forma da original.

    Raises:
        ValueError: Se a imagem não for 2D uint8 ou a qualidade estiver fora de
            1 a 95.
    """
    if cinza.ndim != 2 or cinza.dtype != np.uint8:
        raise ValueError("A imagem deve ser 2D e uint8.")
    if not 1 <= qualidade <= 95:
        raise ValueError("A qualidade JPEG deve estar entre 1 e 95.")
    memoria = io.BytesIO()
    Image.fromarray(cinza).save(memoria, format="JPEG", quality=qualidade)
    memoria.seek(0)
    with Image.open(memoria) as imagem:
        return np.array(imagem.convert("L"))
