"""Testes da preparação da foto e da máscara em cada escala (A54)."""

import numpy as np
import pytest

from concrete_crack.domain.pixels import reduzir_foto, reduzir_mascara
from concrete_crack.domain.preparacao import preparar_escalas

# Foto 4 x 4 com valores diferentes em cada canal; máscara com a diagonal.
FOTO = np.arange(48, dtype=np.uint8).reshape(4, 4, 3)
DIAGONAL = np.eye(4, dtype=bool)


def test_escala_nativa_mantem_a_foto_e_grava_a_mascara_em_0_e_255() -> None:
    (nativa,) = preparar_escalas(FOTO, DIAGONAL, (1,))
    assert nativa.fator == 1
    assert np.array_equal(nativa.foto, FOTO)
    assert nativa.mascara.dtype == np.uint8
    assert nativa.mascara.tolist() == (DIAGONAL * 255).tolist()


def test_escala_2x_grava_a_contagem_de_fissura_de_cada_bloco() -> None:
    _, reduzida = preparar_escalas(FOTO, DIAGONAL, (1, 2))
    # a diagonal passa por 2 dos 4 pixels dos blocos da diagonal
    assert reduzida.mascara.tolist() == [[2, 0], [0, 2]]
    assert reduzida.mascara.dtype == np.uint8


def test_escala_2x_reduz_a_foto_pela_media_inteira() -> None:
    _, reduzida = preparar_escalas(FOTO, DIAGONAL, (1, 2))
    assert np.array_equal(reduzida.foto, reduzir_foto(FOTO, 2))
    assert reduzida.foto.shape == (2, 2, 3)


def test_contagem_permite_as_tres_regras_depois() -> None:
    mascara = np.zeros((4, 4), dtype=bool)
    mascara[:, 0] = True
    mascara[0, 2] = True
    _, reduzida = preparar_escalas(FOTO, mascara, (1, 2))
    contagem = reduzida.mascara
    # coluna de 1 px: 2 de 4 nos blocos da esquerda; canto: 1 de 4
    assert contagem.tolist() == [[2, 1], [2, 0]]
    assert ((contagem >= 2) == (reduzir_mascara(mascara, 2) >= 0.5)).all()
    assert ((contagem >= 1) == (reduzir_mascara(mascara, 2) > 0)).all()
    assert np.array_equal(contagem / 4, reduzir_mascara(mascara, 2))


def test_mascara_que_nao_e_booleana_e_recusada() -> None:
    with pytest.raises(ValueError, match="booleana"):
        preparar_escalas(FOTO, DIAGONAL.astype(np.uint8), (1,))


def test_foto_e_mascara_de_tamanhos_diferentes_sao_recusadas() -> None:
    with pytest.raises(ValueError, match="tamanhos diferentes"):
        preparar_escalas(FOTO, np.zeros((4, 2), dtype=bool), (1,))


def test_fator_cuja_contagem_nao_cabe_em_uint8_e_recusado() -> None:
    foto = np.zeros((16, 16, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="não cabe em uint8"):
        preparar_escalas(foto, np.zeros((16, 16), dtype=bool), (16,))
