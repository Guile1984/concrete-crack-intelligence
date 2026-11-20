"""Testes do pós-processamento comum (A65, item 2), com contas à mão."""

import numpy as np
import pytest

from concrete_crack.domain.posprocessamento import (
    binarizar,
    conferir_mapa,
    remover_componentes_pequenos,
)


def diagonal(n: int) -> np.ndarray:
    """Fissura diagonal de n pixels, que só se liga pelas quinas."""
    return np.eye(n, dtype=bool)


def test_mapa_valido_passa_na_conferencia() -> None:
    conferir_mapa(np.linspace(0, 1, 12).reshape(3, 4), (3, 4))


@pytest.mark.parametrize(
    ("mapa", "trecho"),
    [
        (np.zeros((3, 4), dtype=np.uint8), "float"),
        (np.zeros((4, 3)), "formato"),
        (np.full((3, 4), np.nan), "não finitos"),
        (np.full((3, 4), 1.5), r"\[0, 1\]"),
        (np.full((3, 4), -0.1), r"\[0, 1\]"),
    ],
)
def test_mapa_fora_do_contrato_e_recusado(mapa: np.ndarray, trecho: str) -> None:
    with pytest.raises(ValueError, match=trecho):
        conferir_mapa(mapa, (3, 4))


def test_binarizar_inclui_o_proprio_limiar() -> None:
    mapa = np.array([[0.2, 0.5, 0.8]])
    assert binarizar(mapa, 0.5).tolist() == [[False, True, True]]


@pytest.mark.parametrize("limiar", [-0.1, 1.1])
def test_limiar_fora_de_0_a_1_e_recusado(limiar: float) -> None:
    with pytest.raises(ValueError, match="limiar"):
        binarizar(np.zeros((2, 2)), limiar)


def test_diagonal_e_um_componente_so_com_vizinhanca_de_8() -> None:
    # 5 pixels ligados pelas quinas: com 8, um componente de 5, que fica
    assert remover_componentes_pequenos(diagonal(5), 5, 8).sum() == 5


def test_diagonal_vira_pixels_soltos_com_vizinhanca_de_4() -> None:
    # com 4, são 5 componentes de 1 pixel, todos abaixo de 2
    assert remover_componentes_pequenos(diagonal(5), 2, 4).sum() == 0


def test_componente_do_tamanho_exato_fica() -> None:
    mascara = np.zeros((10, 10), dtype=bool)
    mascara[1, 1:4] = True  # 3 pixels
    mascara[6, 1:6] = True  # 5 pixels
    limpa = remover_componentes_pequenos(mascara, 5, 8)
    assert limpa.sum() == 5
    assert limpa[6, 1:6].all() and not limpa[1].any()


def test_tamanho_0_desliga_a_limpeza_e_nao_altera_a_entrada() -> None:
    mascara = diagonal(4)
    limpa = remover_componentes_pequenos(mascara, 0, 8)
    assert limpa is not mascara
    assert (limpa == mascara).all()


@pytest.mark.parametrize(
    ("mascara", "tamanho", "conectividade", "trecho"),
    [
        (diagonal(3).astype(np.uint8), 2, 8, "booleana"),
        (diagonal(3), -1, 8, "negativo"),
        (diagonal(3), 2, 6, "4 ou 8"),
    ],
)
def test_entradas_invalidas_da_limpeza_sao_recusadas(
    mascara: np.ndarray, tamanho: int, conectividade: int, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        remover_componentes_pequenos(mascara, tamanho, conectividade)
