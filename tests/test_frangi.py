"""Testes sintéticos do adaptador Frangi (A65, item 6), sem imagens reais."""

import numpy as np
import pytest
from skimage.filters import gaussian

from concrete_crack.domain.posprocessamento import conferir_mapa
from concrete_crack.infrastructure.frangi import (
    ParametrosFrangi,
    SegmentadorFrangi,
    cinza_corrigido,
)
from concrete_crack.ports.segmentador import Segmentador

LADO, FUNDO, PROFUNDIDADE = 101, 160.0, 100.0
Y, X = np.mgrid[:LADO, :LADO].astype(float)
PARAMETROS = ParametrosFrangi(
    sigmas=(1.0, 2.0, 4.0, 6.0), sigma_fundo=0.0, c=0.05, beta=0.5
)
FRANGI = SegmentadorFrangi(PARAMETROS)


def rgb(cinza: np.ndarray) -> np.ndarray:
    """Converte uma imagem em cinza (0 a 255) para RGB uint8."""
    valores = np.clip(cinza, 0, 255).round().astype(np.uint8)
    return np.stack([valores] * 3, axis=-1)


def vale(distancia: np.ndarray, largura: float) -> np.ndarray:
    """Fissura escura de perfil gaussiano, a partir da distância ao eixo."""
    return rgb(FUNDO - PROFUNDIDADE * np.exp(-(distancia**2) / (2 * largura**2)))


def linha_vertical(largura: float) -> np.ndarray:
    """Fissura vertical no meio da imagem."""
    return vale(X - 50, largura)


def test_cumpre_o_contrato_do_segmentador() -> None:
    assert isinstance(FRANGI, Segmentador)
    conferir_mapa(FRANGI.mapear(linha_vertical(2)), (LADO, LADO))


def test_resposta_alta_na_linha_e_nula_no_fundo() -> None:
    mapa = FRANGI.mapear(linha_vertical(2))
    assert mapa[50, 50] > 0.9
    assert mapa[50, 5] < 0.01


def test_mancha_redonda_responde_bem_menos_que_a_linha() -> None:
    # o fator de bolha de uma mancha redonda é exp(-2) ≈ 0,135 com β = 0,5
    mancha = vale(np.hypot(X - 50, Y - 50), 2)
    linha = FRANGI.mapear(linha_vertical(2))[50, 50]
    assert FRANGI.mapear(mancha)[50, 50] < linha / 5


def test_linha_a_45_graus_responde_como_a_vertical() -> None:
    diagonal = vale((X - Y) / np.sqrt(2), 2)
    vertical = FRANGI.mapear(linha_vertical(2))[50, 50]
    assert FRANGI.mapear(diagonal)[50, 50] == pytest.approx(vertical, abs=0.02)


def test_fissura_larga_nao_e_penalizada() -> None:
    # sem a normalização por σ², a de 6 px cairia para perto de 0,02
    fina = FRANGI.mapear(linha_vertical(2))[50, 50]
    larga = FRANGI.mapear(linha_vertical(6))[50, 50]
    assert larga > 0.9
    assert larga == pytest.approx(fina, rel=0.05)


def test_textura_limpa_responde_baixo_com_c_fixo() -> None:
    ruido = np.random.default_rng(20261120).normal(0.0, 1.0, (LADO, LADO))
    textura = rgb(FUNDO + 20 * gaussian(ruido, sigma=1.5))
    assert FRANGI.mapear(textura).max() < 0.15


def test_imagem_uniforme_da_mapa_zerado() -> None:
    assert not FRANGI.mapear(rgb(np.full((LADO, LADO), FUNDO))).any()


def test_correcao_de_iluminacao_apaga_um_degrade_suave() -> None:
    degrade = rgb(100 + X)  # de 100 a 200 da esquerda para a direita
    corrigida = cinza_corrigido(degrade, sigma_fundo=10)
    miolo = corrigida[40:60, 45:55]
    assert np.abs(miolo).max() < 0.01
    assert cinza_corrigido(rgb(np.full((3, 3), FUNDO)), 0)[1, 1] == pytest.approx(
        FUNDO / 255
    )


@pytest.mark.parametrize(
    ("campos", "trecho"),
    [
        ({"sigmas": ()}, "positivas"),
        ({"sigmas": (0.0, 1.0)}, "positivas"),
        ({"sigmas": (2.0, 1.0)}, "crescentes"),
        ({"sigma_fundo": -1.0}, "fundo"),
        ({"c": 0.0}, "positivos"),
    ],
)
def test_parametros_invalidos_sao_recusados(
    campos: dict[str, object], trecho: str
) -> None:
    valores = {"sigmas": (1.0,), "sigma_fundo": 0.0, "c": 0.05, "beta": 0.5}
    with pytest.raises(ValueError, match=trecho):
        ParametrosFrangi(**{**valores, **campos})


@pytest.mark.parametrize(
    "imagem",
    [np.zeros((5, 5, 3), dtype=np.float64), np.zeros((5, 5), dtype=np.uint8)],
)
def test_imagem_que_nao_e_rgb_uint8_e_recusada(imagem: np.ndarray) -> None:
    with pytest.raises(ValueError, match="RGB uint8"):
        FRANGI.mapear(imagem)
