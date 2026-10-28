"""Trava das regras pré-registradas: mudar um valor exige editar este teste."""

from dataclasses import FrozenInstanceError, replace

import pytest

from concrete_crack.config.regras import REGRAS


def test_split_70_15_15() -> None:
    assert REGRAS.proporcao_treino == 0.70
    assert REGRAS.proporcao_validacao == 0.15
    assert REGRAS.proporcao_teste == 0.15


def test_seed_do_split_fixa() -> None:
    assert REGRAS.seed_split == 20261022


def test_no_maximo_tres_experimentos_adicionais() -> None:
    assert REGRAS.max_experimentos_adicionais == 3


def test_tres_seeds_por_configuracao() -> None:
    assert REGRAS.n_seeds_por_configuracao == 3


def test_teto_de_custo_de_20_dolares() -> None:
    assert REGRAS.teto_custo_usd == 20.0


def test_cldice_decide_o_criterio_1() -> None:
    assert REGRAS.metrica_decisao == "cldice"


def test_checkpoints_candidatos_por_dice_e_escolha_final_por_cldice() -> None:
    assert REGRAS.metrica_candidatos_checkpoint == "dice"
    assert REGRAS.n_candidatos_checkpoint == 3
    assert REGRAS.metrica_escolha_checkpoint == "cldice"


def test_cada_conjunto_de_teste_e_avaliado_uma_vez() -> None:
    assert REGRAS.avaliacoes_teste_por_conjunto == 1


def test_regras_sao_imutaveis() -> None:
    with pytest.raises(FrozenInstanceError):
        REGRAS.seed_split = 1


def test_proporcoes_que_nao_somam_um_sao_recusadas() -> None:
    with pytest.raises(ValueError, match="somam"):
        replace(REGRAS, proporcao_teste=0.20)


def test_inspecao_de_40_mascaras_com_seed_fixa() -> None:
    assert REGRAS.n_inspecao_mascaras == 40
    assert REGRAS.seed_inspecao_mascaras == 20261022


def test_mascaras_reprovadas_com_oito_ou_mais_inadequadas() -> None:
    assert REGRAS.limiar_reprovacao_mascaras == 8
    assert REGRAS.proporcao_relevante_mascaras == 0.25


def test_limiar_maior_que_a_amostra_e_recusado() -> None:
    with pytest.raises(ValueError, match="limiar"):
        replace(REGRAS, limiar_reprovacao_mascaras=41)
