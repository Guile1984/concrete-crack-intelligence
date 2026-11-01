"""Testes da orientação EXIF em matrizes e do contraste da máscara."""

import numpy as np
import pytest
from PIL import Image, ImageOps

from concrete_crack.domain.orientacao import (
    aplicar_orientacao,
    contraste,
    orientacao_oposta,
    vantagem_da_orientacao_exif,
)

ORIENTACAO_QUE_DESFAZ = {None: 1, 1: 1, 3: 3, 6: 8, 8: 6}


def matriz_assimetrica() -> np.ndarray:
    return np.arange(12, dtype=np.uint8).reshape(3, 4)


def cena(orientacao: int | None) -> tuple[np.ndarray, np.ndarray]:
    """Devolve (foto armazenada, máscara exibida) com uma fissura escura."""
    rng = np.random.default_rng(0)
    exibida = rng.normal(128, 5, size=(40, 60))
    exibida[10:12, :] = 20
    mascara = np.zeros((40, 60), dtype=bool)
    mascara[10:12, :] = True
    armazenada = aplicar_orientacao(exibida, ORIENTACAO_QUE_DESFAZ[orientacao])
    return armazenada, mascara


@pytest.mark.parametrize("orientacao", [None, 1])
def test_sem_orientacao_ou_com_1_nada_muda(orientacao: int | None) -> None:
    matriz = matriz_assimetrica()
    assert np.array_equal(aplicar_orientacao(matriz, orientacao), matriz)


@pytest.mark.parametrize("orientacao", range(1, 9))
def test_aplicar_orientacao_concorda_com_o_pillow(orientacao: int) -> None:
    matriz = matriz_assimetrica()
    imagem = Image.fromarray(matriz)
    imagem.getexif()[0x0112] = orientacao
    esperado = np.asarray(ImageOps.exif_transpose(imagem))
    assert np.array_equal(aplicar_orientacao(matriz, orientacao), esperado)


@pytest.mark.parametrize("orientacao", range(1, 9))
def test_aplicar_orientacao_em_imagem_rgb_concorda_com_o_pillow(
    orientacao: int,
) -> None:
    matriz = np.arange(36, dtype=np.uint8).reshape(3, 4, 3)
    imagem = Image.fromarray(matriz)
    imagem.getexif()[0x0112] = orientacao
    esperado = np.asarray(ImageOps.exif_transpose(imagem))
    assert np.array_equal(aplicar_orientacao(matriz, orientacao), esperado)


def test_aplicar_orientacao_nao_altera_a_entrada() -> None:
    matriz = matriz_assimetrica()
    copia = matriz.copy()
    aplicar_orientacao(matriz, 6)
    assert np.array_equal(matriz, copia)


@pytest.mark.parametrize("invalida", [0, 9])
def test_aplicar_orientacao_recusa_valor_invalido(invalida: int) -> None:
    with pytest.raises(ValueError, match="inválida"):
        aplicar_orientacao(matriz_assimetrica(), invalida)


@pytest.mark.parametrize(
    ("orientacao", "oposta"),
    [(None, 3), (1, 3), (3, 1), (2, 4), (4, 2), (5, 7), (7, 5), (6, 8), (8, 6)],
)
def test_orientacao_oposta_tabela(orientacao: int | None, oposta: int) -> None:
    assert orientacao_oposta(orientacao) == oposta


@pytest.mark.parametrize("orientacao", range(1, 9))
def test_oposta_equivale_a_girar_180_graus(orientacao: int) -> None:
    matriz = matriz_assimetrica()
    girada = np.rot90(aplicar_orientacao(matriz, orientacao), 2)
    oposta = aplicar_orientacao(matriz, orientacao_oposta(orientacao))
    assert np.array_equal(girada, oposta)


@pytest.mark.parametrize("invalida", [0, 9])
def test_orientacao_oposta_recusa_valor_invalido(invalida: int) -> None:
    with pytest.raises(ValueError, match="inválida"):
        orientacao_oposta(invalida)


def test_contraste_e_positivo_quando_a_fissura_e_escura() -> None:
    cinza, mascara = cena(1)
    assert contraste(cinza, mascara) > 10


def test_contraste_recusa_formas_diferentes() -> None:
    with pytest.raises(ValueError, match="Formas diferentes"):
        contraste(np.zeros((3, 4)), np.zeros((4, 3), dtype=bool))


def test_contraste_recusa_mascara_vazia_ou_cheia() -> None:
    cinza = np.random.default_rng(0).normal(size=(5, 5))
    with pytest.raises(ValueError, match="dentro e fora"):
        contraste(cinza, np.zeros((5, 5), dtype=bool))
    with pytest.raises(ValueError, match="dentro e fora"):
        contraste(cinza, np.ones((5, 5), dtype=bool))


def test_contraste_recusa_fundo_constante() -> None:
    mascara = np.zeros((5, 5), dtype=bool)
    mascara[0, 0] = True
    with pytest.raises(ValueError, match="constante"):
        contraste(np.full((5, 5), 100.0), mascara)


def test_contraste_recusa_mascara_nao_booleana() -> None:
    with pytest.raises(ValueError, match="booleana"):
        contraste(np.zeros((3, 3)), np.zeros((3, 3), dtype=np.uint8))


def test_vantagem_positiva_quando_a_mascara_esta_alinhada() -> None:
    cinza, mascara = cena(6)
    assert vantagem_da_orientacao_exif(cinza, mascara, 6) > 10


def test_vantagem_negativa_quando_a_mascara_esta_girada_180() -> None:
    cinza, mascara = cena(6)
    girada = np.rot90(mascara, 2)
    assert vantagem_da_orientacao_exif(cinza, girada, 6) < -10


@pytest.mark.parametrize("orientacao", [None, 1, 3, 6, 8])
def test_vantagem_positiva_em_cada_orientacao_testada(
    orientacao: int | None,
) -> None:
    cinza, mascara = cena(orientacao)
    assert vantagem_da_orientacao_exif(cinza, mascara, orientacao) > 10
