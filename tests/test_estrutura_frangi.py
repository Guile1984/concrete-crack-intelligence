"""Testes da estrutura S* do Frangi, de onde sai o c (A66, item 3)."""

import numpy as np
import pytest
from skimage.filters import frangi

from concrete_crack.infrastructure.frangi import (
    cinza_corrigido,
    estrutura_normalizada,
)

LADO = 101
Y, X = np.mgrid[:LADO, :LADO].astype(float)


def linha(largura: float) -> np.ndarray:
    """Fissura vertical escura (100 tons abaixo de um fundo 160), em cinza."""
    cinza = 160 - 100 * np.exp(-((X - 50) ** 2) / (2 * largura**2))
    valores = np.clip(cinza, 0, 255).round().astype(np.uint8)
    return cinza_corrigido(np.stack([valores] * 3, axis=-1), 0)


def test_s_estrela_e_a_mesma_estrutura_que_o_frangi_usa() -> None:
    # com β enorme, o fator de bolha vale 1 e o Frangi é só 1 - exp(-S²/2γ²)
    imagem, sigma, c = linha(2), 2.0, 0.05
    s = estrutura_normalizada(imagem, (sigma,))[50, 50]
    resposta = frangi(imagem, sigmas=[sigma], beta=1e6, gamma=c / sigma**2)
    assert resposta[50, 50] == pytest.approx(1 - np.exp(-(s**2) / (2 * c**2)))


def test_s_estrela_nao_depende_da_largura_na_escala_certa() -> None:
    # teoria: σ² · A · w / (w² + σ²)^(3/2) com σ = w dá A / 2^(3/2) ≈ 0,1387
    fina = estrutura_normalizada(linha(2), (2.0,))[50, 50]
    larga = estrutura_normalizada(linha(6), (6.0,))[50, 50]
    assert fina == pytest.approx(larga, rel=0.01)
    assert fina == pytest.approx((100 / 255) / 2**1.5, rel=0.01)


def test_imagem_uniforme_tem_s_estrela_zero() -> None:
    uniforme = np.full((20, 20, 3), 160, dtype=np.uint8)
    assert not estrutura_normalizada(cinza_corrigido(uniforme, 0), (1.0, 2.0)).any()
