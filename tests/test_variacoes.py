"""Testes das variações fabricadas do controle positivo de duplicatas."""

import numpy as np
import pytest

from concrete_crack.domain.variacoes import LADOS, ajustar_brilho, recortar
from concrete_crack.infrastructure.recompressao import recomprimir_jpeg


def imagem(altura: int = 40, largura: int = 60) -> np.ndarray:
    return np.arange(altura * largura, dtype=np.int64).reshape(altura, largura)


def test_brilho_multiplica_e_arredonda() -> None:
    # 8,5 vai para o par (8); 85,85 arredonda para 86
    cinza = np.array([[10, 100, 101]], dtype=np.uint8)
    assert ajustar_brilho(cinza, 0.85).tolist() == [[8, 85, 86]]


def test_brilho_satura_em_255() -> None:
    cinza = np.array([[200, 240, 255]], dtype=np.uint8)
    resultado = ajustar_brilho(cinza, 1.15)
    assert resultado.dtype == np.uint8
    assert resultado.tolist() == [[230, 255, 255]]


@pytest.mark.parametrize(
    ("cinza", "fator", "trecho"),
    [
        (np.zeros((2, 2), dtype=np.float64), 0.85, "uint8"),
        (np.zeros((2, 2), dtype=np.uint8), 0.0, "positivo"),
    ],
)
def test_brilho_recusa_entradas_invalidas(
    cinza: np.ndarray, fator: float, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        ajustar_brilho(cinza, fator)


@pytest.mark.parametrize(
    ("lado", "forma", "primeiro"),
    [
        ("esquerda", (40, 54), 6),
        ("direita", (40, 54), 0),
        ("cima", (36, 60), 240),
        ("baixo", (36, 60), 0),
    ],
)
def test_recorte_de_10_por_cento_em_cada_lado(
    lado: str, forma: tuple[int, int], primeiro: int
) -> None:
    recortada = recortar(imagem(), 0.10, lado)
    assert recortada.shape == forma
    assert recortada[0, 0] == primeiro


def test_recorte_arredonda_a_faixa() -> None:
    # 5% de 60 colunas = 3; 5% de 50 colunas = 2,5, que vai para o par (2)
    assert recortar(imagem(40, 60), 0.05, "direita").shape == (40, 57)
    assert recortar(imagem(40, 50), 0.05, "direita").shape == (40, 48)


def test_recorte_devolve_copia() -> None:
    original = imagem()
    recortada = recortar(original, 0.10, "esquerda")
    recortada[0, 0] = -1
    assert original[0, 6] == 6


def test_os_quatro_lados_sao_conhecidos() -> None:
    assert LADOS == ("esquerda", "direita", "cima", "baixo")


@pytest.mark.parametrize(
    ("cinza", "fracao", "lado", "trecho"),
    [
        (np.zeros((4, 4, 3)), 0.10, "esquerda", "2D"),
        (imagem(), 0.0, "esquerda", "fração"),
        (imagem(), 0.5, "esquerda", "fração"),
        (imagem(), 0.10, "diagonal", "Lado"),
        (imagem(4, 4), 0.05, "esquerda", "pequena"),
    ],
)
def test_recorte_recusa_entradas_invalidas(
    cinza: np.ndarray, fracao: float, lado: str, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        recortar(cinza, fracao, lado)


def test_recompressao_mantem_forma_e_altera_levemente() -> None:
    rng = np.random.default_rng(0)
    suave = np.tile(np.linspace(0, 255, 64), (48, 1))
    cinza = np.clip(suave + rng.normal(0, 20, suave.shape), 0, 255).astype(np.uint8)
    recomprimida = recomprimir_jpeg(cinza, 70)
    assert recomprimida.shape == cinza.shape
    assert recomprimida.dtype == np.uint8
    diferenca = np.abs(recomprimida.astype(int) - cinza.astype(int))
    assert diferenca.any()
    assert diferenca.mean() < 20


def test_qualidade_menor_perde_mais_informacao() -> None:
    rng = np.random.default_rng(1)
    cinza = rng.integers(0, 256, (48, 64), dtype=np.uint8)
    erro_70 = np.abs(recomprimir_jpeg(cinza, 70).astype(int) - cinza).mean()
    erro_10 = np.abs(recomprimir_jpeg(cinza, 10).astype(int) - cinza).mean()
    assert erro_10 > erro_70


@pytest.mark.parametrize(
    ("cinza", "qualidade", "trecho"),
    [
        (np.zeros((4, 4), dtype=np.float64), 70, "uint8"),
        (np.zeros((4, 4, 3), dtype=np.uint8), 70, "2D"),
        (np.zeros((4, 4), dtype=np.uint8), 0, "qualidade"),
        (np.zeros((4, 4), dtype=np.uint8), 96, "qualidade"),
    ],
)
def test_recompressao_recusa_entradas_invalidas(
    cinza: np.ndarray, qualidade: int, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        recomprimir_jpeg(cinza, qualidade)
