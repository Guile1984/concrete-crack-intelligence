"""Testes da amostra e do cálculo da constante c do Frangi (A65 e A66)."""

import numpy as np
import pytest

from concrete_crack.domain.constante_c import (
    constante_c,
    sortear_fotos,
    sortear_pixels,
)

FOTOS = tuple(f"rgb/{i:03d}.jpg" for i in range(320))
SEED = 20261120


def test_sorteio_de_fotos_e_reprodutivel_e_ordenado() -> None:
    primeiro = sortear_fotos(FOTOS, 40, SEED)
    assert sortear_fotos(FOTOS, 40, SEED) == primeiro
    assert len(set(primeiro)) == 40 and set(primeiro) <= set(FOTOS)
    assert list(primeiro) == sorted(primeiro)


def test_sorteio_de_fotos_nao_depende_da_ordem_de_entrada() -> None:
    assert sortear_fotos(FOTOS[::-1], 40, SEED) == sortear_fotos(FOTOS, 40, SEED)


def test_outra_seed_sorteia_outras_fotos() -> None:
    assert sortear_fotos(FOTOS, 40, SEED + 1) != sortear_fotos(FOTOS, 40, SEED)


@pytest.mark.parametrize(
    ("fotos", "n", "trecho"),
    [
        (FOTOS, 0, "sortear 0"),
        (FOTOS, 321, "sortear 321"),
        (("a", "a"), 1, "repetir"),
    ],
)
def test_sorteio_de_fotos_invalido_e_recusado(
    fotos: tuple[str, ...], n: int, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        sortear_fotos(fotos, n, SEED)


def test_sorteio_de_pixels_distintos_reprodutivel_e_por_foto() -> None:
    total = 4032 * 3024
    pixels = sortear_pixels(total, 100_000, SEED, 0)
    assert pixels.size == 100_000 and np.unique(pixels).size == 100_000
    assert pixels.min() >= 0 and pixels.max() < total
    assert np.array_equal(sortear_pixels(total, 100_000, SEED, 0), pixels)
    assert not np.array_equal(sortear_pixels(total, 100_000, SEED, 1), pixels)


@pytest.mark.parametrize(
    ("total", "n", "indice", "trecho"),
    [(100, 0, 0, "sortear 0"), (100, 101, 0, "sortear 101"), (100, 5, -1, "negativo")],
)
def test_sorteio_de_pixels_invalido_e_recusado(
    total: int, n: int, indice: int, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        sortear_pixels(total, n, SEED, indice)


def test_c_e_metade_do_percentil_99_pelo_metodo_linear() -> None:
    # valores 0, 1, ..., 100: o percentil 99 cai exatamente em 99
    assert constante_c(np.arange(101.0), 0.5, 99.0) == 49.5


def test_c_com_percentil_entre_dois_valores_interpola() -> None:
    # 0, 10, 20, 30, 40: posição (5 - 1) x 0,99 = 3,96, entre 30 e 40
    # 30 + 0,96 x (40 - 30) = 39,6; metade: 19,8
    assert constante_c(np.array([0.0, 10, 20, 30, 40]), 0.5, 99.0) == pytest.approx(
        19.8
    )


@pytest.mark.parametrize(
    ("valores", "trecho"),
    [
        (np.array([]), "Não há valores"),
        (np.array([1.0, np.nan]), "finitos"),
        (np.array([1.0, -1.0]), "não negativos"),
        (np.zeros(10), "não é positivo"),
    ],
)
def test_valores_invalidos_para_o_c_sao_recusados(
    valores: np.ndarray, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        constante_c(valores, 0.5, 99.0)
