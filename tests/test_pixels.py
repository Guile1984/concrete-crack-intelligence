"""Testes da redução, do recorte e do hash dos pixels (conferidos à mão)."""

import numpy as np
import pytest

from concrete_crack.domain.pixels import (
    hash_pixels,
    recortar,
    reduzir_foto,
    reduzir_mascara,
    somar_blocos,
)


def test_soma_de_blocos_2x2_conferida_a_mao() -> None:
    imagem = np.arange(16, dtype=np.uint8).reshape(4, 4)
    # blocos: [[0, 1], [4, 5]] = 10; [[2, 3], [6, 7]] = 18;
    #         [[8, 9], [12, 13]] = 42; [[10, 11], [14, 15]] = 50
    assert somar_blocos(imagem, 2).tolist() == [[10, 18], [42, 50]]


def test_foto_arredonda_meio_para_cima() -> None:
    # 1 + 2 + 3 + 4 = 10, média 2,5: (10 + 2) // 4 = 3
    # 0 + 0 + 0 + 1 = 1, média 0,25: (1 + 2) // 4 = 0
    foto = np.array([[1, 2, 0, 0], [3, 4, 0, 1]], dtype=np.uint8)
    assert reduzir_foto(foto, 2).tolist() == [[3, 0]]


def test_foto_branca_continua_255() -> None:
    assert reduzir_foto(np.full((2, 2), 255, dtype=np.uint8), 2).tolist() == [[255]]


def test_foto_rgb_reduz_cada_canal() -> None:
    foto = np.zeros((2, 2, 3), dtype=np.uint8)
    foto[..., 0] = 200
    foto[0, 0, 2] = 40
    # canal 0: 200; canal 1: 0; canal 2: 40 / 4 = 10
    assert reduzir_foto(foto, 2).tolist() == [[[200, 0, 10]]]


def test_foto_que_nao_e_uint8_e_recusada() -> None:
    with pytest.raises(ValueError, match="uint8"):
        reduzir_foto(np.zeros((2, 2), dtype=np.float64), 2)


def test_mascara_com_os_exemplos_da_licao_1_14e() -> None:
    vertical_2px = np.zeros((2, 2), dtype=bool)
    vertical_2px[:, :] = True
    vertical_1px = np.zeros((2, 2), dtype=bool)
    vertical_1px[:, 0] = True
    diagonal = np.eye(4, dtype=bool)
    assert reduzir_mascara(vertical_2px, 2).tolist() == [[1.0]]
    assert reduzir_mascara(vertical_1px, 2).tolist() == [[0.5]]
    # a diagonal de 1 px passa por dois cantos de cada bloco da diagonal
    assert reduzir_mascara(diagonal, 2).tolist() == [[0.5, 0.0], [0.0, 0.5]]
    canto = np.zeros((2, 2), dtype=bool)
    canto[0, 0] = True
    assert reduzir_mascara(canto, 2).tolist() == [[0.25]]


def test_mascara_que_nao_e_booleana_e_recusada() -> None:
    with pytest.raises(ValueError, match="booleana"):
        reduzir_mascara(np.zeros((2, 2), dtype=np.uint8), 2)


@pytest.mark.parametrize(("forma", "fator"), [((4, 3), 2), ((3, 4), 2), ((4, 4), 0)])
def test_fator_invalido_e_recusado(forma: tuple[int, int], fator: int) -> None:
    with pytest.raises(ValueError, match="fator"):
        somar_blocos(np.zeros(forma, dtype=np.uint8), fator)


def test_recorte_pega_a_regiao_certa() -> None:
    imagem = np.arange(20, dtype=np.uint8).reshape(4, 5)
    # linhas 1 e 2, colunas 3 e 4
    assert recortar(imagem, 3, 1, 2).tolist() == [[8, 9], [13, 14]]


@pytest.mark.parametrize(("x", "y", "lado"), [(4, 0, 2), (0, 3, 2), (-1, 0, 2)])
def test_recorte_fora_da_imagem_e_recusado(x: int, y: int, lado: int) -> None:
    with pytest.raises(ValueError, match="sai da imagem"):
        recortar(np.zeros((4, 5), dtype=np.uint8), x, y, lado)


def test_hash_igual_para_os_mesmos_pixels_e_diferente_se_um_muda() -> None:
    a = np.arange(12, dtype=np.uint8).reshape(3, 4)
    b = a.copy()
    assert hash_pixels(a) == hash_pixels(b)
    b[2, 3] = 0
    assert hash_pixels(a) != hash_pixels(b)


def test_hash_distingue_forma_e_tipo_com_os_mesmos_bytes() -> None:
    a = np.arange(12, dtype=np.uint8).reshape(3, 4)
    assert hash_pixels(a) != hash_pixels(a.reshape(4, 3))
    assert hash_pixels(a) != hash_pixels(a.view(np.int8))


def test_hash_de_um_recorte_e_o_da_copia() -> None:
    imagem = np.arange(20, dtype=np.uint8).reshape(4, 5)
    tile = recortar(imagem, 3, 1, 2)
    assert hash_pixels(tile) == hash_pixels(tile.copy())
