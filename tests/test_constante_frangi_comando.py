"""Testes do comando que calcula o c do Frangi, com fotos sintéticas."""

from pathlib import Path

import numpy as np
import pytest

from concrete_crack.config.caminhos import caminho_constante_c
from concrete_crack.domain.constante_c import sortear_pixels
from concrete_crack.infrastructure.frangi import cinza_corrigido, estrutura_normalizada
from concrete_crack.infrastructure.imagens import gravar_png
from concrete_crack.presentation.constante_frangi import amostrar_estrutura, main

ESCALAS, FUNDOS, SEED = (1.0, 2.0), (0.0, 8.0), 7


@pytest.fixture
def fotos(tmp_path: Path) -> list[Path]:
    """Duas fotos sintéticas de 40 x 50, com uma fissura escura cada."""
    caminhos = []
    for numero, coluna in enumerate((10, 30)):
        imagem = np.full((40, 50, 3), 160, dtype=np.uint8)
        imagem[:, coluna : coluna + 2] = 60
        caminho = tmp_path / f"foto_{numero}.png"
        gravar_png(caminho, imagem)
        caminhos.append(caminho)
    return caminhos


def test_amostra_tem_os_pixels_de_todas_as_fotos_em_cada_fundo(
    fotos: list[Path],
) -> None:
    valores = amostrar_estrutura(fotos, ESCALAS, FUNDOS, 100, SEED)
    assert set(valores) == set(FUNDOS)
    assert all(v.shape == (200,) for v in valores.values())


def test_amostra_e_s_estrela_nos_pixels_sorteados(fotos: list[Path]) -> None:
    valores = amostrar_estrutura(fotos, ESCALAS, FUNDOS, 100, SEED)
    imagem = np.full((40, 50, 3), 160, dtype=np.uint8)
    imagem[:, 30:32] = 60
    esperado = estrutura_normalizada(cinza_corrigido(imagem, 8.0), ESCALAS)
    posicoes = sortear_pixels(40 * 50, 100, SEED, 1)
    assert np.array_equal(valores[8.0][100:], esperado.ravel()[posicoes])


def test_amostra_e_reprodutivel(fotos: list[Path]) -> None:
    primeira = amostrar_estrutura(fotos, ESCALAS, FUNDOS, 100, SEED)
    segunda = amostrar_estrutura(fotos, ESCALAS, FUNDOS, 100, SEED)
    assert all(np.array_equal(primeira[f], segunda[f]) for f in FUNDOS)


def test_comando_se_recusa_a_recalcular_o_c(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    destino = caminho_constante_c(tmp_path)
    destino.parent.mkdir(parents=True)
    destino.write_text("{}\n", encoding="utf-8")
    assert main(["--raiz", str(tmp_path), "ccsd"]) == 2
    assert "uma única vez" in capsys.readouterr().err
