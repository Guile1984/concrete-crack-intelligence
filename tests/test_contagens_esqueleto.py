"""Testes das contagens de esqueleto e do clDice calculado a partir delas (A62)."""

import pytest

from concrete_crack.domain.metricas import ContagensEsqueleto, cldice_de_contagens


def test_barra_de_3_px_deslocada_1_px_no_zhang() -> None:
    # 2 x 79 x 78 / (79 x 79 + 78 x 79) = 12.324 / 12.403 = 156/157
    assert cldice_de_contagens(ContagensEsqueleto(79, 79, 78, 79)) == 156 / 157


def test_gabarito_sem_fissura_e_indefinido() -> None:
    assert cldice_de_contagens(ContagensEsqueleto(0, 79, 0, 0)) is None


def test_previsao_vazia_vale_0() -> None:
    assert cldice_de_contagens(ContagensEsqueleto(0, 0, 0, 79)) == 0.0


def test_uma_das_partes_zero_basta_para_zerar() -> None:
    # Tprec = 1/79 e Tsens = 0: a média harmônica é 0
    assert cldice_de_contagens(ContagensEsqueleto(1, 79, 0, 79)) == 0.0


@pytest.mark.parametrize(
    ("contagens", "trecho"),
    [
        ((-1, 79, 0, 79), "entre 0"),
        ((80, 79, 0, 79), "entre 0"),
        ((0, 79, 80, 79), "entre 0"),
        ((0, 0, 5, 79), "vazio"),
        ((5, 79, 0, 0), "vazio"),
    ],
)
def test_contagens_impossiveis_sao_recusadas(
    contagens: tuple[int, int, int, int], trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        ContagensEsqueleto(*contagens)
