"""Testes da leitura do cabeçalho de imagens."""

from pathlib import Path

import pytest
from PIL import Image

from concrete_crack.domain.dimensoes import Cabecalho
from concrete_crack.infrastructure.imagens import ler_cabecalho


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
