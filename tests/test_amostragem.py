"""Testes da amostragem determinística por hash."""

import random

import pytest

from concrete_crack.domain.amostragem import amostrar_por_hash

NOMES_10 = [f"{i:03d}" for i in range(1, 11)]
NOMES_100 = [f"{i:03d}" for i in range(1, 101)]
SEED = 20261022


def test_vetor_conhecido() -> None:
    assert amostrar_por_hash(NOMES_10, 3, SEED) == ("001", "004", "009")


def test_amostra_tem_n_nomes_distintos_do_conjunto() -> None:
    amostra = amostrar_por_hash(NOMES_100, 10, SEED)
    assert len(amostra) == 10
    assert len(set(amostra)) == 10
    assert set(amostra) <= set(NOMES_100)


def test_resultado_vem_em_ordem_alfabetica() -> None:
    amostra = amostrar_por_hash(NOMES_100, 10, SEED)
    assert list(amostra) == sorted(amostra)


def test_mesma_seed_mesma_amostra() -> None:
    assert amostrar_por_hash(NOMES_100, 10, SEED) == amostrar_por_hash(
        NOMES_100, 10, SEED
    )


def test_ordem_da_entrada_nao_importa() -> None:
    embaralhados = NOMES_100.copy()
    random.Random(1).shuffle(embaralhados)
    assert amostrar_por_hash(embaralhados, 10, SEED) == amostrar_por_hash(
        NOMES_100, 10, SEED
    )


def test_seed_diferente_muda_a_amostra() -> None:
    assert amostrar_por_hash(NOMES_100, 10, SEED) != amostrar_por_hash(
        NOMES_100, 10, SEED + 1
    )


def test_n_zero_e_n_total_sao_validos() -> None:
    assert amostrar_por_hash(NOMES_10, 0, SEED) == ()
    assert amostrar_por_hash(NOMES_10, 10, SEED) == tuple(NOMES_10)


@pytest.mark.parametrize("n", [-1, 11])
def test_n_fora_do_intervalo_e_recusado(n: int) -> None:
    with pytest.raises(ValueError, match="fora do intervalo"):
        amostrar_por_hash(NOMES_10, n, SEED)


def test_nomes_repetidos_sao_recusados() -> None:
    with pytest.raises(ValueError, match="repetidos"):
        amostrar_por_hash(["a", "a", "b"], 1, SEED)
