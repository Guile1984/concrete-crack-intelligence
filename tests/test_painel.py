"""Testes da montagem de painéis lado a lado."""

import numpy as np
import pytest

from concrete_crack.domain.painel import montar_painel


def imagem(valor: int, altura: int = 4, largura: int = 6) -> np.ndarray:
    return np.full((altura, largura, 3), valor, dtype=np.uint8)


def test_painel_tem_largura_das_duas_imagens_mais_a_faixa() -> None:
    painel = montar_painel(imagem(10), imagem(20), 2)
    assert painel.shape == (4, 14, 3)
    assert painel.dtype == np.uint8


def test_painel_poe_esquerda_faixa_e_direita_nessa_ordem() -> None:
    painel = montar_painel(imagem(10), imagem(20), 2, cor_separador=(1, 2, 3))
    assert np.all(painel[:, :6] == 10)
    assert np.all(painel[:, 6:8] == (1, 2, 3))
    assert np.all(painel[:, 8:] == 20)


def test_painel_sem_faixa_nao_deixa_espaco() -> None:
    painel = montar_painel(imagem(10), imagem(20), 0)
    assert painel.shape == (4, 12, 3)


def test_painel_recusa_formas_diferentes() -> None:
    with pytest.raises(ValueError, match="Formas diferentes"):
        montar_painel(imagem(10), imagem(20, altura=5), 2)


def test_painel_recusa_imagem_que_nao_e_rgb() -> None:
    cinza = np.zeros((4, 6), dtype=np.uint8)
    with pytest.raises(ValueError, match="RGB"):
        montar_painel(cinza, imagem(20), 2)


def test_painel_recusa_separador_negativo() -> None:
    with pytest.raises(ValueError, match="negativa"):
        montar_painel(imagem(10), imagem(20), -1)
