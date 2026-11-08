"""Testes da análise descritiva dos vizinhos mais próximos (A47)."""

import numpy as np
import pytest

from concrete_crack.domain.vizinhos import (
    contar_por_faixas,
    distancias_ao_vizinho_mais_proximo,
    limitacao_relevante,
    pares_na_faixa,
    quantis,
    quase_ligadas,
)


def test_vizinho_mais_proximo_ignora_a_propria_imagem() -> None:
    distancias = np.array([[0.0, 0.3, 0.9], [0.3, 0.0, 0.5], [0.9, 0.5, 0.0]])
    resultado = distancias_ao_vizinho_mais_proximo(distancias)
    assert resultado.tolist() == [0.3, 0.3, 0.5]


def test_vizinho_mais_proximo_nao_altera_a_matriz() -> None:
    distancias = np.array([[0.0, 0.2], [0.2, 0.0]])
    distancias_ao_vizinho_mais_proximo(distancias)
    assert distancias[0, 0] == 0.0


def test_vizinho_mais_proximo_recusa_matriz_invalida() -> None:
    with pytest.raises(ValueError, match="quadrada"):
        distancias_ao_vizinho_mais_proximo(np.zeros((2, 3)))
    with pytest.raises(ValueError, match="pelo menos 2"):
        distancias_ao_vizinho_mais_proximo(np.zeros((1, 1)))


def test_faixas_com_o_limite_na_faixa_de_baixo() -> None:
    valores = np.array([0.005, 0.0051, 0.010, 0.02, 0.2])
    assert contar_por_faixas(valores, [0.005, 0.010, 0.025]) == [1, 2, 1, 1]


def test_faixas_somam_todos_os_valores() -> None:
    valores = np.random.default_rng(0).uniform(0, 1, 100)
    assert sum(contar_por_faixas(valores, [0.1, 0.5, 0.9])) == 100


def test_faixas_recusam_limites_fora_de_ordem() -> None:
    with pytest.raises(ValueError, match="crescentes"):
        contar_por_faixas(np.zeros(3), [0.5, 0.1])
    with pytest.raises(ValueError, match="crescentes"):
        contar_por_faixas(np.zeros(3), [])


def test_quantis_de_0_a_100() -> None:
    valores = np.arange(101, dtype=np.float64)
    assert quantis(valores) == [0.0, 5.0, 25.0, 50.0, 75.0, 95.0, 100.0]


def test_quase_ligadas_ficam_acima_de_t_e_ate_2t() -> None:
    valores = np.array([0.004, 0.005, 0.0051, 0.010, 0.0101])
    assert quase_ligadas(valores, 0.005, 2.0) == 2


def test_limitacao_relevante_a_partir_de_23_em_458() -> None:
    assert not limitacao_relevante(22, 458, 0.05)
    assert limitacao_relevante(23, 458, 0.05)


def test_pares_na_faixa_excluem_o_limite_de_baixo_e_incluem_o_de_cima() -> None:
    distancias = np.array(
        [
            [0.0, 0.005, 0.006, 0.010],
            [0.005, 0.0, 0.011, 0.2],
            [0.006, 0.011, 0.0, 0.007],
            [0.010, 0.2, 0.007, 0.0],
        ]
    )
    assert pares_na_faixa(distancias, 0.005, 0.010) == [(0, 2), (0, 3), (2, 3)]
