"""Testes da marcação da fissura e do resumo de vantagens."""

import numpy as np
import pytest

from concrete_crack.domain.alinhamento import marcar_fissura, resumir_vantagens


def mascara_com_faixa(fundo: int, faixa: int) -> np.ndarray:
    matriz = np.full((10, 20), fundo, dtype=np.uint8)
    matriz[4:6, :] = faixa
    return matriz


def faixa_esperada() -> np.ndarray:
    esperado = np.zeros((10, 20), dtype=bool)
    esperado[4:6, :] = True
    return esperado


def test_fissura_branca_sobre_fundo_preto() -> None:
    marcada = marcar_fissura(mascara_com_faixa(0, 255), 32)
    assert marcada.dtype == np.bool_
    assert np.array_equal(marcada, faixa_esperada())


def test_fissura_preta_sobre_fundo_branco_da_a_mesma_marcacao() -> None:
    marcada = marcar_fissura(mascara_com_faixa(255, 0), 32)
    assert np.array_equal(marcada, faixa_esperada())


def test_ruido_pequeno_do_jpeg_nao_vira_fissura() -> None:
    matriz = mascara_com_faixa(0, 255).astype(np.int16)
    matriz[0, :] += 10
    matriz[9, :] += 20
    assert np.array_equal(marcar_fissura(matriz, 32), faixa_esperada())


def test_fissura_fina_acinzentada_pela_reducao_ainda_e_marcada() -> None:
    marcada = marcar_fissura(mascara_com_faixa(0, 60), 32)
    assert np.array_equal(marcada, faixa_esperada())


def test_imagem_uniforme_nao_tem_fissura() -> None:
    assert not marcar_fissura(np.full((5, 5), 7, dtype=np.uint8), 32).any()


@pytest.mark.parametrize("desvio", [0, -5])
def test_desvio_minimo_nao_positivo_e_recusado(desvio: int) -> None:
    with pytest.raises(ValueError, match="positivo"):
        marcar_fissura(np.zeros((3, 3), dtype=np.uint8), desvio)


def test_resumo_de_vantagens() -> None:
    resumo = resumir_vantagens([1.0, 2.0, 3.0, -1.0])
    assert resumo.n == 4
    assert resumo.positivas == 3
    assert resumo.fracao_positiva == 0.75
    assert resumo.mediana == 1.5
    assert resumo.minimo == -1.0
    assert resumo.maximo == 3.0


def test_vantagem_zero_nao_conta_como_positiva() -> None:
    resumo = resumir_vantagens([0.0])
    assert resumo.positivas == 0
    assert resumo.fracao_positiva == 0.0


def test_resumo_de_um_unico_valor() -> None:
    resumo = resumir_vantagens([2.5])
    assert (resumo.mediana, resumo.minimo, resumo.maximo) == (2.5, 2.5, 2.5)


def test_resumo_vazio_e_recusado() -> None:
    with pytest.raises(ValueError, match="Não há vantagens"):
        resumir_vantagens([])
