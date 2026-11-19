"""Testes do clDice (A62, item 9), nas duas camadas: fórmula e esqueleto real."""

import numpy as np
import pytest

from concrete_crack.domain.metricas import cldice, cldice_de_esqueletos, esqueleto

ZHANG = "zhang"


def barra(espessura: int, deslocamento: int = 0, fim: int = 90) -> np.ndarray:
    """Barra horizontal que começa na coluna 10, numa imagem de 60 x 100."""
    mascara = np.zeros((60, 100), dtype=bool)
    topo = 20 + deslocamento
    mascara[topo : topo + espessura, 10:fim] = True
    return mascara


def linha_central(espessura: int, deslocamento: int = 0, fim: int = 90) -> np.ndarray:
    """Esqueleto desenhado à mão: a linha do meio de uma barra de espessura ímpar."""
    return barra(1, deslocamento + espessura // 2, fim)


def test_formula_barra_de_3_px_deslocada_1_px_vale_1() -> None:
    valor = cldice_de_esqueletos(
        barra(3, 1), barra(3), linha_central(3, 1), linha_central(3)
    )
    assert valor == 1.0


def test_formula_barra_de_3_px_deslocada_2_px_vale_0() -> None:
    valor = cldice_de_esqueletos(
        barra(3, 2), barra(3), linha_central(3, 2), linha_central(3)
    )
    assert valor == 0.0


def test_formula_e_media_harmonica_e_nao_aritmetica() -> None:
    # previsão com metade do comprimento: Tprec = 1, Tsens = 40/80 = 1/2
    # harmônica: 2 x 1 x 1/2 / (1 + 1/2) = 2/3; a aritmética daria 3/4
    valor = cldice_de_esqueletos(
        barra(3, fim=50), barra(3), linha_central(3, fim=50), linha_central(3)
    )
    assert valor == 2 / 3


def test_gabarito_sem_fissura_fica_fora_do_cldice() -> None:
    vazio = np.zeros((60, 100), dtype=bool)
    assert cldice_de_esqueletos(barra(3), vazio, linha_central(3), vazio) is None


def test_previsao_vazia_vale_0() -> None:
    vazio = np.zeros((60, 100), dtype=bool)
    assert cldice_de_esqueletos(vazio, barra(3), vazio, linha_central(3)) == 0.0


@pytest.mark.parametrize(
    ("esqueleto_previsao", "trecho"),
    [
        (linha_central(3).astype(np.uint8), "booleano"),
        (linha_central(3, 5), "sai da máscara"),
        (np.zeros((60, 100), dtype=bool), "só pode ser vazio"),
    ],
)
def test_esqueletos_incompativeis_sao_recusados(
    esqueleto_previsao: np.ndarray, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        cldice_de_esqueletos(barra(3), barra(3), esqueleto_previsao, linha_central(3))


def test_esqueleto_de_zhang_da_barra_de_3_px_tem_uma_ponta_no_canto() -> None:
    # 79 pixels; todos na linha do meio (21), menos o último de uma ponta
    pixels = esqueleto(barra(3), ZHANG)
    assert int(pixels.sum()) == 79
    assert int(pixels[21].sum()) == 78


@pytest.mark.parametrize(
    ("espessura", "deslocamento", "esperado"),
    [(3, 1, 156 / 157), (3, 2, 0.0), (20, 1, 1.0)],
)
def test_zhang_valores_travados(
    espessura: int, deslocamento: int, esperado: float
) -> None:
    assert cldice(barra(espessura, deslocamento), barra(espessura), ZHANG) == esperado


def test_zhang_previsao_perfeita_vale_1() -> None:
    assert cldice(barra(3), barra(3), ZHANG) == 1.0
