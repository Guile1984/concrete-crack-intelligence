"""Testes da binarização dos rótulos do S2DS (A58), conferidos à mão."""

import numpy as np
import pytest

from concrete_crack.config.regras import REGRAS
from concrete_crack.domain.rotulos_s2ds import (
    contar_classes,
    mapa_de_classes,
    mascara_binaria,
)

CORES = REGRAS.cores_classes_s2ds
PRETO, BRANCO = (0, 0, 0), (255, 255, 255)
VERMELHO, AZUL = (255, 0, 0), (0, 0, 255)


def rotulo(linhas: list[list[tuple[int, int, int]]], alfa: int = 255) -> np.ndarray:
    """Monta um rótulo RGBA uint8 a partir de cores RGB."""
    rgb = np.array(linhas, dtype=np.uint8)
    canal_alfa = np.full(rgb.shape[:2] + (1,), alfa, dtype=np.uint8)
    return np.concatenate([rgb, canal_alfa], axis=2)


ROTULO = rotulo([[PRETO, BRANCO, BRANCO], [VERMELHO, AZUL, PRETO]])


def test_mapa_de_classes_na_ordem_do_regras() -> None:
    # fundo 0, fissura 1, desplacamento 2, ponto de controle 6
    assert mapa_de_classes(ROTULO, CORES, 255).tolist() == [[0, 1, 1], [2, 6, 0]]


def test_mascara_binaria_marca_so_a_fissura() -> None:
    classes = mapa_de_classes(ROTULO, CORES, 255)
    assert mascara_binaria(classes, 1).tolist() == [
        [False, True, True],
        [False, False, False],
    ]


def test_contagem_antes_e_depois_bate() -> None:
    classes = mapa_de_classes(ROTULO, CORES, 255)
    contagem = contar_classes(classes, len(CORES))
    assert contagem == [2, 2, 1, 0, 0, 0, 1]
    # pixels brancos do rótulo = pixels de fissura da máscara binária
    brancos = int((ROTULO[..., :3] == 255).all(axis=2).sum())
    assert brancos == int(mascara_binaria(classes, 1).sum()) == contagem[1]


def test_cor_fora_do_mapa_e_recusada_com_exemplo() -> None:
    intruso = rotulo([[PRETO, (128, 128, 128)], [BRANCO, (128, 128, 128)]])
    with pytest.raises(ValueError, match=r"2 pixel\(s\) com cor fora do mapa"):
        mapa_de_classes(intruso, CORES, 255)
    with pytest.raises(ValueError, match=r"RGB \(128, 128, 128\)"):
        mapa_de_classes(intruso, CORES, 255)


def test_alfa_diferente_e_recusado() -> None:
    transparente = ROTULO.copy()
    transparente[0, 0, 3] = 0
    with pytest.raises(ValueError, match=r"1 pixel\(s\) com alfa diferente de 255"):
        mapa_de_classes(transparente, CORES, 255)


@pytest.mark.parametrize(
    "forma", [(2, 3), (2, 3, 3), (2, 3, 4)], ids=["cinza", "rgb", "float"]
)
def test_rotulo_que_nao_e_rgba_uint8_e_recusado(forma: tuple[int, ...]) -> None:
    tipo = np.float64 if len(forma) == 3 and forma[2] == 4 else np.uint8
    with pytest.raises(ValueError, match="RGBA"):
        mapa_de_classes(np.zeros(forma, dtype=tipo), CORES, 255)
