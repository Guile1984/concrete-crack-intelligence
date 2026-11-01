"""Testes da leitura de imagens."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.domain.dimensoes import Cabecalho
from concrete_crack.infrastructure.imagens import ler_cabecalho, ler_cinza


def salvar(
    caminho: Path, tamanho: tuple[int, int], orientacao: int | None = None
) -> None:
    imagem = Image.new("RGB", tamanho)
    if orientacao is None:
        imagem.save(caminho)
    else:
        exif = Image.Exif()
        exif[0x0112] = orientacao
        imagem.save(caminho, exif=exif)


def test_le_largura_e_altura_sem_orientacao(tmp_path: Path) -> None:
    arquivo = tmp_path / "a.jpg"
    salvar(arquivo, (20, 10))
    assert ler_cabecalho(arquivo) == Cabecalho(20, 10, None)


def test_le_a_orientacao_exif_sem_girar_o_tamanho(tmp_path: Path) -> None:
    arquivo = tmp_path / "b.jpg"
    salvar(arquivo, (20, 10), orientacao=6)
    assert ler_cabecalho(arquivo) == Cabecalho(20, 10, 6)


def test_orientacao_invalida_e_recusada_com_o_caminho(tmp_path: Path) -> None:
    arquivo = tmp_path / "c.jpg"
    salvar(arquivo, (20, 10), orientacao=9)
    with pytest.raises(ValueError, match="c.jpg"):
        ler_cabecalho(arquivo)


def test_arquivo_que_nao_e_imagem_e_recusado(tmp_path: Path) -> None:
    arquivo = tmp_path / "d.jpg"
    arquivo.write_text("não sou uma imagem", encoding="utf-8")
    with pytest.raises(OSError):
        ler_cabecalho(arquivo)


def test_arquivo_inexistente_e_recusado(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ler_cabecalho(tmp_path / "nao_existe.jpg")


def test_cinza_reduz_o_jpeg_pelo_fator(tmp_path: Path) -> None:
    arquivo = tmp_path / "e.jpg"
    salvar(arquivo, (80, 40))
    cinza = ler_cinza(arquivo, 8)
    assert cinza.shape == (5, 10)
    assert cinza.dtype == np.uint8


def test_cinza_com_fator_1_mantem_o_tamanho(tmp_path: Path) -> None:
    arquivo = tmp_path / "f.jpg"
    salvar(arquivo, (80, 40))
    assert ler_cinza(arquivo, 1).shape == (40, 80)


def test_cinza_nao_aplica_a_orientacao_exif(tmp_path: Path) -> None:
    arquivo = tmp_path / "g.jpg"
    salvar(arquivo, (20, 10), orientacao=6)
    assert ler_cinza(arquivo, 1).shape == (10, 20)


def test_cinza_reduz_formato_sem_draft_por_media_de_blocos(tmp_path: Path) -> None:
    arquivo = tmp_path / "h.png"
    Image.new("RGB", (80, 40), (255, 255, 255)).save(arquivo)
    cinza = ler_cinza(arquivo, 4)
    assert cinza.shape == (10, 20)
    assert np.all(cinza == 255)


def test_cinza_preserva_a_posicao_dos_pixels(tmp_path: Path) -> None:
    arquivo = tmp_path / "i.png"
    imagem = Image.new("L", (80, 40), 0)
    imagem.paste(255, (40, 0, 80, 40))
    imagem.save(arquivo)
    cinza = ler_cinza(arquivo, 4)
    assert cinza[:, :10].max() == 0
    assert cinza[:, 10:].min() == 255


@pytest.mark.parametrize("fator", [0, -1])
def test_cinza_recusa_fator_invalido(tmp_path: Path, fator: int) -> None:
    arquivo = tmp_path / "j.png"
    Image.new("L", (8, 8)).save(arquivo)
    with pytest.raises(ValueError, match="fator"):
        ler_cinza(arquivo, fator)


def test_cinza_de_arquivo_que_nao_e_imagem_e_recusado(tmp_path: Path) -> None:
    arquivo = tmp_path / "k.jpg"
    arquivo.write_text("não sou uma imagem", encoding="utf-8")
    with pytest.raises(OSError):
        ler_cinza(arquivo, 1)


def test_cinza_de_arquivo_inexistente_e_recusado(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ler_cinza(tmp_path / "nao_existe.jpg", 1)
