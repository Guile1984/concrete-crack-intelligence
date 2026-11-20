"""Testes do contrato do port Segmentador (A65, item 1)."""

import numpy as np

from concrete_crack.domain.posprocessamento import conferir_mapa
from concrete_crack.ports.segmentador import Segmentador


class MapaConstante:
    """Segmentador de mentira, que devolve o mesmo score em toda a imagem."""

    def mapear(self, imagem: np.ndarray) -> np.ndarray:
        """Devolve 0,5 em todo pixel."""
        return np.full(imagem.shape[:2], 0.5)


def test_classe_com_mapear_cumpre_o_protocolo() -> None:
    assert isinstance(MapaConstante(), Segmentador)
    assert not isinstance(object(), Segmentador)


def test_mapa_do_segmentador_de_mentira_cumpre_o_contrato() -> None:
    imagem = np.zeros((6, 8, 3), dtype=np.uint8)
    conferir_mapa(MapaConstante().mapear(imagem), (6, 8))
