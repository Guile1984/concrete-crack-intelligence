"""Testes do resumo das fotos e da fissura por conjunto (sem disco)."""

import pytest

from concrete_crack.domain.distribuicao import (
    MedidaFoto,
    distribuir,
    resumir_conjunto,
)
from concrete_crack.domain.divisao import Divisao

PAISAGEM = (4032, 3024)
RETRATO = (2448, 3264)

# Frações 1%, 2%, 3% e 4%, mas a última máscara tem 7 vezes mais pixels.
MEDIDAS = [
    MedidaFoto(PAISAGEM, 1, 100),
    MedidaFoto(PAISAGEM, 2, 100),
    MedidaFoto(RETRATO, 3, 100),
    MedidaFoto(PAISAGEM, 28, 700),
]


def test_fracao_de_uma_foto() -> None:
    assert MedidaFoto(PAISAGEM, 3, 200).fracao == pytest.approx(0.015)


@pytest.mark.parametrize(("fissura", "total"), [(1, 0), (-1, 10), (11, 10)])
def test_medidas_impossiveis_sao_recusadas(fissura: int, total: int) -> None:
    with pytest.raises(ValueError):
        MedidaFoto(PAISAGEM, fissura, total)


def test_quartis_com_interpolacao_linear_conferidos_a_mao() -> None:
    # posições (4 - 1) x 0,25 = 0,75; x 0,5 = 1,5; x 0,75 = 2,25
    q1, mediana, q3 = resumir_conjunto("treino", MEDIDAS).quartis
    assert q1 == pytest.approx(0.01 + 0.75 * 0.01)
    assert mediana == pytest.approx(0.025)
    assert q3 == pytest.approx(0.03 + 0.25 * 0.01)


def test_fracao_total_pondera_pelos_pixels() -> None:
    # (1 + 2 + 3 + 28) / (100 + 100 + 100 + 700) = 34 / 1000, e não a média 0,025
    assert resumir_conjunto("treino", MEDIDAS).fracao_total == pytest.approx(0.034)


def test_resolucoes_da_mais_frequente_para_a_menos() -> None:
    resumo = resumir_conjunto("treino", MEDIDAS)
    assert resumo.n_fotos == 4
    assert resumo.resolucoes == ((PAISAGEM, 3), (RETRATO, 1))


def test_uma_so_foto_tem_os_tres_quartis_iguais() -> None:
    resumo = resumir_conjunto("teste", [MedidaFoto(RETRATO, 5, 100)])
    assert resumo.quartis == pytest.approx((0.05, 0.05, 0.05))


def test_conjunto_vazio_e_recusado() -> None:
    with pytest.raises(ValueError, match="não tem fotos"):
        resumir_conjunto("teste", [])


DIVISAO = Divisao(("a", "b"), ("c",), ("d",))
POR_FOTO = dict(zip("abcd", MEDIDAS, strict=True))


def test_distribui_na_ordem_treino_validacao_teste() -> None:
    treino, validacao, teste = distribuir(DIVISAO, POR_FOTO)
    assert (treino.nome, validacao.nome, teste.nome) == ("treino", "validacao", "teste")
    assert (treino.n_fotos, validacao.n_fotos, teste.n_fotos) == (2, 1, 1)
    assert treino.fracao_total == pytest.approx(3 / 200)
    assert teste.fracao_total == pytest.approx(28 / 700)


def test_foto_sem_medida_e_recusada() -> None:
    incompleto = {k: v for k, v in POR_FOTO.items() if k != "d"}
    with pytest.raises(ValueError, match="1 foto"):
        distribuir(DIVISAO, incompleto)


def test_medida_fora_da_divisao_e_recusada() -> None:
    sobrando = {**POR_FOTO, "z": MEDIDAS[0]}
    with pytest.raises(ValueError, match="1 medida"):
        distribuir(DIVISAO, sobrando)
