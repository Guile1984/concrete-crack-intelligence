"""Testes da grade de tiles (A52), com posições conferidas à mão."""

import numpy as np
import pytest

from concrete_crack.domain.tiles import Tile, grade, inicios, tamanho_na_escala


def test_largura_de_4032_com_tile_de_512_encosta_o_ultimo_em_3520() -> None:
    # 7 tiles inteiros vão até 3584; o 8º começa em 4032 - 512 = 3520
    assert inicios(4032, 512) == (0, 512, 1024, 1536, 2048, 2560, 3072, 3520)


def test_altura_de_3024_com_tile_de_512_encosta_o_ultimo_em_2512() -> None:
    # 5 tiles inteiros vão até 2560; o 6º começa em 3024 - 512 = 2512
    assert inicios(3024, 512) == (0, 512, 1024, 1536, 2048, 2512)


def test_multiplo_exato_nao_repete_o_ultimo_tile() -> None:
    assert inicios(1024, 512) == (0, 512)
    assert inicios(512, 512) == (0,)


def test_imagem_menor_que_o_tile_e_recusada() -> None:
    with pytest.raises(ValueError, match="menor que o tile"):
        inicios(500, 512)


def test_lado_nao_positivo_e_recusado() -> None:
    with pytest.raises(ValueError, match="positivo"):
        inicios(100, 0)


@pytest.mark.parametrize(
    ("largura", "altura", "lado", "n_tiles"),
    [
        (4032, 3024, 512, 8 * 6),
        (3024, 4032, 512, 6 * 8),
        (3264, 2448, 512, 7 * 5),
        (2448, 3264, 512, 5 * 7),
        (2016, 1512, 256, 8 * 6),
        (1632, 1224, 256, 7 * 5),
    ],
)
def test_quantidade_de_tiles_das_quatro_resolucoes_nas_duas_escalas(
    largura: int, altura: int, lado: int, n_tiles: int
) -> None:
    assert len(grade(largura, altura, lado)) == n_tiles


def test_grade_em_ordem_de_leitura() -> None:
    tiles = grade(10, 7, 4)
    # colunas 0, 4, 6; linhas 0, 3
    assert tiles == (
        Tile(0, 0, 4),
        Tile(4, 0, 4),
        Tile(6, 0, 4),
        Tile(0, 3, 4),
        Tile(4, 3, 4),
        Tile(6, 3, 4),
    )


@pytest.mark.parametrize(("largura", "altura", "lado"), [(10, 7, 4), (13, 13, 5)])
def test_grade_cobre_todos_os_pixels_sem_sair_da_imagem(
    largura: int, altura: int, lado: int
) -> None:
    coberto = np.zeros((altura, largura), dtype=bool)
    for tile in grade(largura, altura, lado):
        assert tile.x + lado <= largura and tile.y + lado <= altura
        coberto[tile.y : tile.y + lado, tile.x : tile.x + lado] = True
    assert coberto.all()


def test_tamanho_reduzido_2x_das_quatro_resolucoes() -> None:
    assert tamanho_na_escala(4032, 3024, 2) == (2016, 1512)
    assert tamanho_na_escala(3264, 2448, 2) == (1632, 1224)
    assert tamanho_na_escala(4032, 3024, 1) == (4032, 3024)


def test_fator_que_nao_divide_o_tamanho_e_recusado() -> None:
    with pytest.raises(ValueError, match="não divide"):
        tamanho_na_escala(4031, 3024, 2)
    with pytest.raises(ValueError, match=">= 1"):
        tamanho_na_escala(4032, 3024, 0)
