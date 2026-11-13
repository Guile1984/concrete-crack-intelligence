"""Preparação da foto e da máscara em cada escala, antes do recorte (A52, A54).

Recebe a foto já na orientação de exibição e a máscara já binarizada (A41) e
devolve, por escala, as duas imagens inteiras que serão conferidas por hash e
recortadas pela grade. Na escala nativa, a máscara é gravada como 0 e 255; nas
escalas reduzidas, como a contagem de pixels de fissura de cada bloco (de 0 a
fator²), para que a regra de volta ao binário possa ser escolhida depois sem
regerar nada (A54, escolha B). Funções puras, sem disco.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .pixels import reduzir_foto, somar_blocos

MAXIMO_UINT8 = 255


@dataclass(frozen=True, slots=True)
class ImagensEscala:
    """A foto e a máscara inteiras de uma escala.

    Attributes:
        fator: Fator de redução (1 é a escala nativa).
        foto: Foto RGB uint8.
        mascara: Máscara uint8: 0 e 255 na escala nativa; nas reduzidas, a
            contagem de pixels de fissura de cada bloco, de 0 a fator².
    """

    fator: int
    foto: np.ndarray
    mascara: np.ndarray


def preparar_escalas(
    foto: np.ndarray, mascara: np.ndarray, fatores: Sequence[int]
) -> tuple[ImagensEscala, ...]:
    """Prepara a foto e a máscara em cada escala.

    Args:
        foto: Foto RGB uint8 (altura, largura, 3), na orientação de exibição.
        mascara: Máscara booleana (altura, largura), verdadeira na fissura.
        fatores: Fatores das escalas, na ordem em que devem sair.

    Returns:
        Uma ``ImagensEscala`` por fator.

    Raises:
        ValueError: Se a máscara não for booleana, se foto e máscara tiverem
            tamanhos diferentes, se um fator não couber em uint8 (fator² acima
            de 255) ou não dividir o tamanho.
    """
    if mascara.dtype != np.bool_:
        raise ValueError("A máscara deve ser booleana.")
    if foto.shape[:2] != mascara.shape:
        raise ValueError(
            f"A foto {foto.shape[:2]} e a máscara {mascara.shape} têm tamanhos "
            "diferentes."
        )
    escalas = []
    for fator in fatores:
        if fator == 1:
            escalas.append(
                ImagensEscala(1, foto, mascara.astype(np.uint8) * MAXIMO_UINT8)
            )
            continue
        if fator * fator > MAXIMO_UINT8:
            raise ValueError(f"A contagem do fator {fator} não cabe em uint8.")
        contagem = somar_blocos(mascara, fator).astype(np.uint8)
        escalas.append(ImagensEscala(fator, reduzir_foto(foto, fator), contagem))
    return tuple(escalas)
