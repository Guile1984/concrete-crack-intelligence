"""Testes da medição descritiva dos tiles e da sobrevivência (A52, item 8)."""

import numpy as np
import pytest

from concrete_crack.domain.sobrevivencia import (
    comparar,
    fissura_por_tile,
    ida_e_volta,
    quartis,
)


def test_fissura_por_tile_em_ordem_de_leitura() -> None:
    mascara = np.zeros((4, 6), dtype=bool)
    mascara[0, 0] = True
    mascara[3, 5] = True
    mascara[1, 3] = True
    # colunas 0, 2, 4 e linhas 0, 2, com tiles de 2 x 2
    assert fissura_por_tile(mascara, (0, 2, 4), (0, 2), 2) == [1, 1, 0, 0, 0, 1]


def test_fissura_vertical_de_1_px_na_maioria_dobra_de_largura() -> None:
    mascara = np.zeros((4, 4), dtype=bool)
    mascara[:, 1] = True
    volta = ida_e_volta(mascara, 2, "maioria")
    # cada bloco da coluna 0 tem 2 de 4: fica, e volta com 2 px de largura
    assert volta[:, :2].all() and not volta[:, 2:].any()
    resultado = comparar(mascara, volta)
    assert (resultado.fissura, resultado.preservados, resultado.a_mais) == (4, 4, 4)


def test_ponto_isolado_some_na_maioria_e_vira_bloco_na_qualquer() -> None:
    mascara = np.zeros((2, 2), dtype=bool)
    mascara[0, 0] = True
    maioria = comparar(mascara, ida_e_volta(mascara, 2, "maioria"))
    qualquer = comparar(mascara, ida_e_volta(mascara, 2, "qualquer"))
    assert (maioria.preservados, maioria.a_mais) == (0, 0)
    assert (qualquer.preservados, qualquer.a_mais) == (1, 3)


def test_fissura_larga_alinhada_atravessa_sem_perda_nem_acrescimo() -> None:
    mascara = np.zeros((4, 4), dtype=bool)
    mascara[:, 0:2] = True
    for regra in ("maioria", "qualquer"):
        resultado = comparar(mascara, ida_e_volta(mascara, 2, regra))
        assert (resultado.preservados, resultado.a_mais) == (8, 0)


def test_qualquer_preserva_sempre_toda_a_fissura() -> None:
    gerador = np.random.default_rng(20261114)
    mascara = gerador.random((8, 8)) < 0.2
    resultado = comparar(mascara, ida_e_volta(mascara, 2, "qualquer"))
    assert resultado.preservados == resultado.fissura


def test_regra_desconhecida_e_mascara_nao_booleana_sao_recusadas() -> None:
    with pytest.raises(ValueError, match="Regra desconhecida"):
        ida_e_volta(np.zeros((2, 2), dtype=bool), 2, "suave")
    with pytest.raises(ValueError, match="booleana"):
        ida_e_volta(np.zeros((2, 2), dtype=np.uint8), 2, "maioria")


def test_comparar_recusa_tamanhos_diferentes() -> None:
    with pytest.raises(ValueError, match="tamanhos diferentes"):
        comparar(np.zeros((2, 2), dtype=bool), np.zeros((2, 4), dtype=bool))


def test_quartis_conferidos_a_mao() -> None:
    # posições (5 - 1) x 0,25 = 1; x 0,5 = 2; x 0,75 = 3
    assert quartis([5.0, 1.0, 3.0, 2.0, 4.0]) == (2.0, 3.0, 4.0)
    with pytest.raises(ValueError, match="Não há valores"):
        quartis([])
