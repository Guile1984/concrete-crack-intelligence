"""Testes da agregação das métricas (A62, item 5, e A63), com contas à mão."""

import pytest

from concrete_crack.domain.agregacao import ImagemAvaliada, Media, media, resumir
from concrete_crack.domain.metricas import Contagens, ContagensEsqueleto


def avaliada(
    nome: str,
    vp: int,
    fp: int,
    fn: int,
    esqueletos: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> ImagemAvaliada:
    """Imagem avaliada a partir das contagens; VN não entra nas métricas."""
    return ImagemAvaliada(
        nome, Contagens(vp, fp, fn, vn=100), ContagensEsqueleto(*esqueletos)
    )


# A: precisão 8/10, recall 8/10, Dice 16/20; clDice 2·9·8 / (9·10 + 8·10) = 72/85
A = avaliada("a", vp=8, fp=2, fn=2, esqueletos=(9, 10, 8, 10))
# B: previsão vazia numa imagem com fissura: precisão indefinida, o resto 0
B = avaliada("b", vp=0, fp=0, fn=10, esqueletos=(0, 0, 0, 10))
# C: imagem limpa com alarme: precisão 0, o resto indefinido
C = avaliada("c", vp=0, fp=5, fn=0, esqueletos=(0, 4, 0, 0))


def test_media_ignora_indefinidos_e_conta_quantos_foram() -> None:
    assert media([0.5, None, 1.0]) == Media(0.75, 2, 1)
    assert media([None]) == Media(None, 0, 1)
    assert media([]) == Media(None, 0, 0)


def test_medias_por_imagem_no_recorte() -> None:
    resumo = resumir([A, B])
    assert resumo.precisao == Media(0.8, 1, 1)
    assert resumo.recall == Media(0.4, 2, 0)
    assert resumo.dice == Media(0.4, 2, 0)
    assert resumo.cldice == Media(36 / 85, 2, 0)


def test_globais_sobre_as_contagens_somadas() -> None:
    # pixels: VP 8, FP 2, FN 12; esqueletos: (9, 10, 8, 20)
    resumo = resumir([A, B])
    assert (resumo.precisao_global, resumo.recall_global) == (0.8, 0.4)
    assert resumo.dice_global == 16 / 30
    # 2·9·8 / (9·20 + 8·10) = 144/260
    assert resumo.cldice_global == 144 / 260


def test_imagem_limpa_fica_fora_de_todas_as_metricas_de_segmentacao() -> None:
    # A63: com a C, a precisão média seria (0,8 + 0) / 2 = 0,4
    com_limpa = resumir([A, B, C])
    assert (com_limpa.n_imagens, com_limpa.n_com_fissura) == (3, 2)
    assert com_limpa.precisao == Media(0.8, 1, 1)
    assert com_limpa.precisao_global == 0.8


def test_dice_global_e_media_harmonica_da_precisao_e_do_recall_globais() -> None:
    resumo = resumir([A, B, C])
    p, r = resumo.precisao_global, resumo.recall_global
    assert p is not None and r is not None
    assert resumo.dice_global == pytest.approx(2 * p * r / (p + r))


def test_so_imagens_limpas_deixam_tudo_indefinido() -> None:
    resumo = resumir([C])
    assert (resumo.n_imagens, resumo.n_com_fissura) == (1, 0)
    assert resumo.dice == Media(None, 0, 0)
    assert resumo.dice_global is None and resumo.cldice_global is None


def test_imagem_repetida_e_recusada() -> None:
    with pytest.raises(ValueError, match="única vez"):
        resumir([A, A])


def test_contagens_contraditorias_sao_recusadas() -> None:
    # pixels dizem que há fissura, mas o esqueleto do gabarito é vazio
    with pytest.raises(ValueError, match="só num dos dois"):
        avaliada("x", vp=8, fp=2, fn=2, esqueletos=(0, 10, 0, 0))
