"""Testes das métricas de uma imagem (A62), com respostas conferidas à mão."""

import numpy as np
import pytest

from concrete_crack.domain.metricas import (
    Contagens,
    acuracia,
    contar,
    dice,
    precisao,
    recall,
)


def barra(espessura: int, deslocamento: int = 0) -> np.ndarray:
    """Barra horizontal de 80 px de comprimento numa imagem de 60 x 100."""
    mascara = np.zeros((60, 100), dtype=bool)
    topo = 20 + deslocamento
    mascara[topo : topo + espessura, 10:90] = True
    return mascara


def test_barra_de_3_px_deslocada_1_px() -> None:
    # 2 das 3 linhas se sobrepõem: VP = 2 x 80; sobra 1 linha de cada lado
    contagens = contar(barra(3, 1), barra(3))
    assert contagens == Contagens(vp=160, fp=80, fn=80, vn=6000 - 320)
    assert dice(contagens) == 2 / 3
    assert precisao(contagens) == recall(contagens) == 2 / 3


def test_barra_de_3_px_deslocada_2_px() -> None:
    contagens = contar(barra(3, 2), barra(3))
    assert (contagens.vp, contagens.fp, contagens.fn) == (80, 160, 160)
    assert dice(contagens) == 1 / 3


def test_barra_de_20_px_deslocada_1_px() -> None:
    contagens = contar(barra(20, 1), barra(20))
    assert (contagens.vp, contagens.fp, contagens.fn) == (19 * 80, 80, 80)
    assert dice(contagens) == 0.95


@pytest.mark.parametrize(
    "contagens",
    [Contagens(160, 80, 80, 0), Contagens(80, 160, 160, 0), Contagens(7, 3, 11, 0)],
)
def test_dice_e_funcao_do_iou(contagens: Contagens) -> None:
    iou = contagens.vp / (contagens.vp + contagens.fp + contagens.fn)
    assert dice(contagens) == pytest.approx(2 * iou / (1 + iou))


def test_previsao_perfeita_vale_1_em_tudo() -> None:
    contagens = contar(barra(3), barra(3))
    assert dice(contagens) == precisao(contagens) == recall(contagens) == 1.0


def test_preditor_trivial_tudo_e_fundo() -> None:
    # 240 px de fissura em 6.000: acerta 96% dos pixels sem achar nenhuma
    contagens = contar(np.zeros((60, 100), dtype=bool), barra(3))
    assert (dice(contagens), recall(contagens)) == (0.0, 0.0)
    assert precisao(contagens) is None
    assert acuracia(contagens) == 0.96


def test_gabarito_sem_fissura_fica_fora_de_dice_e_recall() -> None:
    sem_fissura = np.zeros((60, 100), dtype=bool)
    com_alarme = contar(barra(3), sem_fissura)
    assert (dice(com_alarme), recall(com_alarme)) == (None, None)
    assert precisao(com_alarme) == 0.0
    assert precisao(contar(sem_fissura, sem_fissura)) is None


def test_metricas_ficam_entre_0_e_1_em_mascaras_aleatorias() -> None:
    gerador = np.random.default_rng(20261117)
    for _ in range(50):
        previsao = gerador.random((20, 30)) < gerador.random()
        gabarito = gerador.random((20, 30)) < gerador.random()
        contagens = contar(previsao, gabarito)
        assert contagens.total == 600
        for metrica in (dice, precisao, recall, acuracia):
            valor = metrica(contagens)
            assert valor is None or 0.0 <= valor <= 1.0


def test_mascaras_nao_booleanas_ou_de_formatos_diferentes_sao_recusadas() -> None:
    with pytest.raises(ValueError, match="booleanas"):
        contar(barra(3).astype(np.uint8), barra(3))
    with pytest.raises(ValueError, match="Formatos diferentes"):
        contar(barra(3), barra(3)[:, :50])


def test_contagens_negativas_sao_recusadas() -> None:
    with pytest.raises(ValueError, match="negativas"):
        Contagens(vp=-1, fp=0, fn=0, vn=0)
