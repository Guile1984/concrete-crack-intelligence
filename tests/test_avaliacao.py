"""Testes da avaliação de uma imagem e do preditor trivial (A62, item 8)."""

import numpy as np
import pytest

from concrete_crack.domain.agregacao import Media, resumir
from concrete_crack.domain.avaliacao import (
    acuracia_global,
    avaliar_imagem,
    tudo_e_fundo,
)
from concrete_crack.domain.bootstrap import SUPERIOR, bootstrap_pareado, decidir
from concrete_crack.domain.metricas import (
    Contagens,
    ContagensEsqueleto,
    cldice_de_contagens,
)

ZHANG = "zhang"
LIMPA = np.zeros((60, 100), dtype=bool)


def barra(espessura: int, deslocamento: int = 0) -> np.ndarray:
    """Barra horizontal de 80 px de comprimento numa imagem de 60 x 100."""
    mascara = np.zeros((60, 100), dtype=bool)
    topo = 20 + deslocamento
    mascara[topo : topo + espessura, 10:90] = True
    return mascara


def test_avaliar_junta_pixels_e_esqueletos() -> None:
    avaliada = avaliar_imagem("a", barra(3, 1), barra(3), ZHANG)
    assert avaliada.pixels == Contagens(160, 80, 80, 6000 - 320)
    assert avaliada.esqueletos == ContagensEsqueleto(79, 79, 78, 79)
    assert cldice_de_contagens(avaliada.esqueletos) == 156 / 157


def test_tudo_e_fundo_nao_preve_nenhuma_fissura() -> None:
    previsao = tudo_e_fundo(barra(3))
    assert previsao.shape == (60, 100) and previsao.dtype == np.bool_
    assert not previsao.any()


def test_tudo_e_fundo_recusa_gabarito_nao_booleano() -> None:
    with pytest.raises(ValueError, match="booleano"):
        tudo_e_fundo(barra(3).astype(np.uint8))


def test_preditor_trivial_zera_a_segmentacao_e_acerta_98_por_cento() -> None:
    # uma imagem com 240 px de fissura e uma limpa: 12.000 px, 240 errados
    imagens = [
        avaliar_imagem(nome, tudo_e_fundo(gabarito), gabarito, ZHANG)
        for nome, gabarito in (("com", barra(3)), ("limpa", LIMPA))
    ]
    resumo = resumir(imagens)
    assert resumo.n_com_fissura == 1
    assert resumo.dice == resumo.recall == resumo.cldice == Media(0.0, 1, 0)
    assert resumo.precisao == Media(None, 0, 1)
    assert (resumo.dice_global, resumo.precisao_global) == (0.0, None)
    assert acuracia_global(imagens) == 0.98


def test_previsao_perfeita_supera_o_trivial_com_folga() -> None:
    gabaritos = {f"g{i}": barra(3, i) for i in range(5)}
    diferencas = []
    for nome, gabarito in gabaritos.items():
        perfeita = avaliar_imagem(nome, gabarito, gabarito, ZHANG)
        trivial = avaliar_imagem(nome, tudo_e_fundo(gabarito), gabarito, ZHANG)
        um = cldice_de_contagens(perfeita.esqueletos)
        zero = cldice_de_contagens(trivial.esqueletos)
        assert um is not None and zero is not None
        diferencas.append(um - zero)
    intervalo = bootstrap_pareado(diferencas, list(gabaritos), 10_000, 0.95, 20261117)
    assert (intervalo.inferior, intervalo.superior) == (1.0, 1.0)
    assert decidir(intervalo) == SUPERIOR


def test_acuracia_global_sem_imagens_e_indefinida() -> None:
    assert acuracia_global([]) is None
