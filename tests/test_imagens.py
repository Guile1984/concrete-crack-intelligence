"""Testes da leitura de imagens."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.domain.dimensoes import Cabecalho
from concrete_crack.infrastructure.imagens import (
    gravar_png,
    ler_cabecalho,
    ler_cinza,
    ler_rgb,
)


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


def test_rgb_reduz_o_jpeg_pelo_fator(tmp_path: Path) -> None:
    arquivo = tmp_path / "l.jpg"
    salvar(arquivo, (80, 40))
    rgb = ler_rgb(arquivo, 8)
    assert rgb.shape == (5, 10, 3)
    assert rgb.dtype == np.uint8


def test_rgb_com_fator_1_mantem_o_tamanho(tmp_path: Path) -> None:
    arquivo = tmp_path / "m.jpg"
    salvar(arquivo, (80, 40))
    assert ler_rgb(arquivo, 1).shape == (40, 80, 3)


def test_rgb_nao_aplica_a_orientacao_exif(tmp_path: Path) -> None:
    arquivo = tmp_path / "n.jpg"
    salvar(arquivo, (20, 10), orientacao=6)
    assert ler_rgb(arquivo, 1).shape == (10, 20, 3)


def test_rgb_preserva_as_cores_e_a_posicao(tmp_path: Path) -> None:
    arquivo = tmp_path / "o.png"
    imagem = Image.new("RGB", (80, 40), (255, 0, 0))
    imagem.paste((0, 0, 255), (40, 0, 80, 40))
    imagem.save(arquivo)
    rgb = ler_rgb(arquivo, 4)
    assert np.all(rgb[:, :10] == (255, 0, 0))
    assert np.all(rgb[:, 10:] == (0, 0, 255))


def test_rgb_converte_imagem_em_cinza_para_tres_canais(tmp_path: Path) -> None:
    arquivo = tmp_path / "p.png"
    Image.new("L", (8, 8), 77).save(arquivo)
    rgb = ler_rgb(arquivo, 1)
    assert rgb.shape == (8, 8, 3)
    assert np.all(rgb == 77)


@pytest.mark.parametrize("fator", [0, -1])
def test_rgb_recusa_fator_invalido(tmp_path: Path, fator: int) -> None:
    arquivo = tmp_path / "q.png"
    Image.new("RGB", (8, 8)).save(arquivo)
    with pytest.raises(ValueError, match="fator"):
        ler_rgb(arquivo, fator)


def test_rgb_de_arquivo_que_nao_e_imagem_e_recusado(tmp_path: Path) -> None:
    arquivo = tmp_path / "r.jpg"
    arquivo.write_text("não sou uma imagem", encoding="utf-8")
    with pytest.raises(OSError):
        ler_rgb(arquivo, 1)


def test_rgb_de_arquivo_inexistente_e_recusado(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ler_rgb(tmp_path / "nao_existe.jpg", 1)


def test_gravar_png_e_ler_de_volta_da_a_mesma_matriz(tmp_path: Path) -> None:
    matriz = np.arange(60, dtype=np.uint8).reshape(4, 5, 3)
    destino = tmp_path / "s.png"
    gravar_png(destino, matriz)
    assert np.array_equal(ler_rgb(destino, 1), matriz)


def test_gravar_png_cria_as_pastas_do_destino(tmp_path: Path) -> None:
    destino = tmp_path / "a" / "b" / "t.png"
    gravar_png(destino, np.zeros((2, 2, 3), dtype=np.uint8))
    assert destino.is_file()


def test_gravar_png_recusa_matriz_que_nao_e_uint8(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="uint8"):
        gravar_png(tmp_path / "u.png", np.zeros((2, 2, 3)))
