"""O port MapasPorEscala, conforme a A66 (itens 1 e 6).

A busca em grade do Frangi não recalcula o filtro a cada configuração: pede o
mapa de cada foto numa única escala e num σ do fundo, e combina as escalas de
cada faixa. Quem implementa decide como guardar os mapas (o cache em disco).
"""

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class MapasPorEscala(Protocol):
    """Fonte dos mapas do Frangi, uma escala por vez."""

    def mapa(self, foto: str, sigma: float, sigma_fundo: float) -> np.ndarray:
        """Devolve o mapa de uma foto numa escala e num σ do fundo.

        Args:
            foto: Caminho da foto no manifesto.
            sigma: Uma das oitavas σ da grade.
            sigma_fundo: Um dos σ do fundo da grade.

        Returns:
            Mapa ``float`` (altura, largura) em [0, 1], na resolução de
            trabalho, com o c do registro para esse σ do fundo.
        """
        ...
