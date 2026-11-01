"""Testes da intensidade da máscara e da sobreposição sobre a foto."""

import numpy as np
import pytest

from concrete_crack.domain.sobreposicao import (
    intensidade_da_mascara,
    sobrepor_mascara,
)


def mascara_com_faixa(fundo: int, faixa: int) -> np.ndarray:
    matriz = np.full((10, 20), fundo, dtype=np.uint8)
    matriz[4:6, :] = faixa
    return matriz


def foto_cinza(valor: int = 100) -> np.ndarray:
    return np.full((10, 20, 3), valor, dtype=np.uint8)


def faixa(valor: float) -> np.ndarray:
    matriz = np.zeros((10, 20))
    matriz[4:6, :] = valor
    return matriz


def test_intensidade_de_fissura_branca_sobre_fundo_preto() -> None:
    intensidade = intensidade_da_mascara(mascara_com_faixa(0, 255))
    assert intensidade.dtype == np.float64
    assert np.array_equal(intensidade, faixa(1.0))


def test_intensidade_de_fissura_preta_sobre_fundo_branco_e_a_mesma() -> None:
    intensidade = intensidade_da_mascara(mascara_com_faixa(255, 0))
    assert np.array_equal(intensidade, faixa(1.0))


def test_intensidade_de_fissura_acinzentada_fica_fraca_e_nao_some() -> None:
    intensidade = intensidade_da_mascara(mascara_com_faixa(0, 60))
    assert np.allclose(intensidade, faixa(60 / 255))


def test_intensidade_de_imagem_uniforme_e_zero() -> None:
    uniforme = np.full((5, 5), 7, dtype=np.uint8)
    assert not intensidade_da_mascara(uniforme).any()


def test_intensidade_de_imagem_vazia_e_recusada() -> None:
    with pytest.raises(ValueError, match="vazia"):
        intensidade_da_mascara(np.zeros((0, 5), dtype=np.uint8))


def test_sobrepor_nao_muda_a_foto_fora_da_mascara() -> None:
    foto = foto_cinza()
    resultado = sobrepor_mascara(foto, faixa(1.0), 0.4)
    assert np.array_equal(resultado[:4], foto[:4])
    assert np.array_equal(resultado[6:], foto[6:])


def test_sobrepor_mistura_a_cor_dentro_da_mascara() -> None:
    resultado = sobrepor_mascara(foto_cinza(100), faixa(1.0), 0.4)
    assert resultado[4, 0].tolist() == [162, 60, 60]


def test_sobrepor_com_opacidade_1_e_intensidade_1_da_a_cor_exata() -> None:
    resultado = sobrepor_mascara(foto_cinza(), faixa(1.0), 1.0)
    assert resultado[4, 0].tolist() == [255, 0, 0]


def test_sobrepor_com_intensidade_parcial_mistura_menos() -> None:
    resultado = sobrepor_mascara(foto_cinza(100), faixa(0.5), 0.4)
    assert resultado[4, 0].tolist() == [131, 80, 80]


def test_sobrepor_nao_altera_a_entrada_e_devolve_uint8() -> None:
    foto = foto_cinza()
    copia = foto.copy()
    resultado = sobrepor_mascara(foto, faixa(1.0), 0.4)
    assert np.array_equal(foto, copia)
    assert resultado.dtype == np.uint8
    assert resultado.shape == foto.shape


def test_sobrepor_recusa_foto_que_nao_e_rgb() -> None:
    with pytest.raises(ValueError, match="RGB"):
        sobrepor_mascara(np.zeros((10, 20), dtype=np.uint8), faixa(1.0), 0.4)


def test_sobrepor_recusa_formas_diferentes() -> None:
    with pytest.raises(ValueError, match="Formas diferentes"):
        sobrepor_mascara(foto_cinza(), np.zeros((5, 20)), 0.4)


@pytest.mark.parametrize("opacidade", [0.0, 1.5])
def test_sobrepor_recusa_opacidade_fora_do_intervalo(opacidade: float) -> None:
    with pytest.raises(ValueError, match="opacidade"):
        sobrepor_mascara(foto_cinza(), faixa(1.0), opacidade)


def test_sobrepor_recusa_intensidade_fora_de_0_a_1() -> None:
    with pytest.raises(ValueError, match="intensidade"):
        sobrepor_mascara(foto_cinza(), faixa(1.2), 0.4)
