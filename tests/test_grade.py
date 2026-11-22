"""Testes da grade de ajuste do Frangi (A66), com contas à mão."""

import numpy as np
import pytest

from concrete_crack.config.regras import REGRAS
from concrete_crack.domain.grade import (
    ConfiguracaoFrangi,
    combinar_faixa,
    configuracoes_da_grade,
    segmentar,
)
from concrete_crack.infrastructure.frangi import ParametrosFrangi, SegmentadorFrangi
from concrete_crack.ports.mapas_por_escala import MapasPorEscala

GRADE = configuracoes_da_grade(
    REGRAS.faixas_escalas_frangi,
    REGRAS.sigmas_fundo_frangi,
    REGRAS.limiares_frangi,
    REGRAS.tamanhos_minimos_frangi,
)


def test_grade_pre_registrada_tem_240_configuracoes_distintas() -> None:
    assert len(GRADE) == 240
    assert len(set(GRADE)) == 240


def test_ordem_da_grade_e_a_do_desempate() -> None:
    # a faixa varia mais devagar; o tamanho mínimo, mais depressa
    assert GRADE[0] == ConfiguracaoFrangi((1.0, 2.0, 4.0), 0.0, 0.05, 0)
    assert GRADE[1] == ConfiguracaoFrangi((1.0, 2.0, 4.0), 0.0, 0.05, 100)
    assert GRADE[3] == ConfiguracaoFrangi((1.0, 2.0, 4.0), 0.0, 0.15, 0)
    assert GRADE[30] == ConfiguracaoFrangi((1.0, 2.0, 4.0), 64.0, 0.05, 0)
    assert GRADE[-1] == ConfiguracaoFrangi((1.0, 2.0, 4.0, 8.0, 16.0), 64.0, 0.95, 1000)


def test_faixa_e_o_maximo_pixel_a_pixel() -> None:
    a = np.array([[0.1, 0.7], [0.4, 0.0]])
    b = np.array([[0.5, 0.2], [0.4, 0.3]])
    assert combinar_faixa([a, b]).tolist() == [[0.5, 0.7], [0.4, 0.3]]


def test_mapas_por_escala_combinados_dao_o_mesmo_mapa_do_frangi() -> None:
    # A66, item 1: guardar uma escala por vez e combinar depois é exato
    eixo = np.arange(64, dtype=float)
    cinza = 160 - 90 * np.exp(-((eixo[None, :] - 20) ** 2) / 8)
    cinza = cinza - 60 * np.exp(-((eixo[:, None] - 40) ** 2) / 50)
    imagem = np.stack([np.clip(cinza, 0, 255).astype(np.uint8)] * 3, axis=-1)
    faixa = (1.0, 2.0, 4.0)

    def frangi(sigmas: tuple[float, ...]) -> np.ndarray:
        """Mapa do Frangi da imagem sintética com as escalas dadas."""
        parametros = ParametrosFrangi(sigmas, sigma_fundo=0.0, c=0.05, beta=0.5)
        return SegmentadorFrangi(parametros).mapear(imagem)

    por_escala = [frangi((sigma,)) for sigma in faixa]
    assert np.array_equal(combinar_faixa(por_escala), frangi(faixa))


def test_segmentar_aplica_limiar_e_depois_a_limpeza() -> None:
    mapa = np.zeros((10, 10))
    mapa[2, 1:7] = 0.8  # 6 pixels acima do limiar
    mapa[7, 1:3] = 0.9  # 2 pixels: somem com tamanho mínimo 3
    mapa[5, 1:9] = 0.2  # abaixo do limiar
    mascara = segmentar(mapa, 0.5, 3, 8)
    assert mascara.sum() == 6 and mascara[2, 1:7].all()


@pytest.mark.parametrize(
    ("mapas", "trecho"),
    [([], "pelo menos um"), ([np.zeros((2, 2)), np.zeros((2, 3))], "formato")],
)
def test_faixa_invalida_e_recusada(mapas: list[np.ndarray], trecho: str) -> None:
    with pytest.raises(ValueError, match=trecho):
        combinar_faixa(mapas)


def test_classe_com_metodo_mapa_cumpre_o_port() -> None:
    class Constante:
        """Fonte de mentira, que devolve sempre o mesmo mapa."""

        def mapa(self, foto: str, sigma: float, sigma_fundo: float) -> np.ndarray:
            """Devolve um mapa zerado."""
            return np.zeros((2, 2))

    assert isinstance(Constante(), MapasPorEscala)
