"""Testes do F1 com tolerância k (A64), com respostas conferidas à mão."""

import numpy as np
import pytest

from concrete_crack.domain.metricas import contar, dice
from concrete_crack.domain.tolerancia import (
    ContagensTolerancia,
    contar_tolerancia,
    f1_tolerante,
    precisao_tolerante,
    recall_tolerante,
    vizinhanca,
)

VAZIA = np.zeros((60, 100), dtype=bool)


def barra(espessura: int, deslocamento: int = 0) -> np.ndarray:
    """Barra horizontal de 80 px de comprimento numa imagem de 60 x 100."""
    mascara = np.zeros((60, 100), dtype=bool)
    topo = 20 + deslocamento
    mascara[topo : topo + espessura, 10:90] = True
    return mascara


@pytest.mark.parametrize(
    ("deslocamento", "k", "esperado"),
    [
        (1, 0, 2 / 3),
        (1, 1, 1.0),
        (1, 2, 1.0),
        (2, 0, 1 / 3),
        (2, 1, 2 / 3),
        (2, 2, 1.0),
    ],
)
def test_barra_de_3_px_deslocada(deslocamento: int, k: int, esperado: float) -> None:
    contagens = contar_tolerancia(barra(3, deslocamento), barra(3), k)
    assert f1_tolerante(contagens) == esperado


@pytest.mark.parametrize(("k", "pixels"), [(0, 1), (1, 5), (2, 13), (3, 29)])
def test_vizinhanca_de_um_pixel_e_um_disco_euclidiano(k: int, pixels: int) -> None:
    # pontos inteiros com x² + y² <= k²; em xadrez seriam (2k + 1)²
    ponto = VAZIA.copy()
    ponto[30, 50] = True
    assert int(vizinhanca(ponto, k).sum()) == pixels


def test_com_k_0_e_exatamente_o_dice() -> None:
    gerador = np.random.default_rng(20261120)
    for _ in range(30):
        previsao = gerador.random((20, 30)) < gerador.random()
        gabarito = gerador.random((20, 30)) < 0.3
        gabarito[0, 0] = True
        assert f1_tolerante(contar_tolerancia(previsao, gabarito, 0)) == dice(
            contar(previsao, gabarito)
        )


def test_faixa_larga_em_volta_de_fissura_fina_e_toda_perdoada() -> None:
    # limitação da A64: faixa de 5 px centrada numa fissura de 1 px
    faixa, fina = barra(5, -2), barra(1)
    assert f1_tolerante(contar_tolerancia(faixa, fina, 2)) == 1.0
    assert dice(contar(faixa, fina)) == 1 / 3


def test_gabarito_sem_fissura_fica_fora() -> None:
    contagens = contar_tolerancia(barra(3), VAZIA, 2)
    assert (f1_tolerante(contagens), recall_tolerante(contagens)) == (None, None)
    assert precisao_tolerante(contagens) == 0.0


def test_previsao_vazia_vale_0() -> None:
    contagens = contar_tolerancia(VAZIA, barra(3), 2)
    assert (f1_tolerante(contagens), recall_tolerante(contagens)) == (0.0, 0.0)
    assert precisao_tolerante(contagens) is None


def test_vizinhanca_de_mascara_vazia_e_vazia() -> None:
    assert not vizinhanca(VAZIA, 3).any()


@pytest.mark.parametrize(
    ("previsao", "gabarito", "k", "trecho"),
    [
        (barra(3), barra(3), -1, "maior ou igual a 0"),
        (barra(3).astype(np.uint8), barra(3), 1, "booleana"),
        (barra(3), barra(3)[:, :50], 1, "Formatos diferentes"),
    ],
)
def test_entradas_invalidas_sao_recusadas(
    previsao: np.ndarray, gabarito: np.ndarray, k: int, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        contar_tolerancia(previsao, gabarito, k)


@pytest.mark.parametrize(
    ("contagens", "trecho"),
    [((5, 4, 0, 9), "entre 0"), ((0, 0, 3, 9), "vazia"), ((3, 9, 0, 0), "vazia")],
)
def test_contagens_impossiveis_sao_recusadas(
    contagens: tuple[int, int, int, int], trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        ContagensTolerancia(*contagens)
