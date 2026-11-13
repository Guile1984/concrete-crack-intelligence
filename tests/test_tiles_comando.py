"""Testes do comando que gera os tiles e registra ou confere os hashes (A54)."""

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.config.caminhos import (
    caminho_manifesto_arquivos,
    caminho_manifesto_pixels,
    caminho_split,
    pasta_dados_brutos,
    pasta_tiles,
)
from concrete_crack.domain.divisao import Divisao, RegistroDivisao
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.infrastructure.manifesto_pixels_json import (
    carregar_manifesto_pixels,
)
from concrete_crack.infrastructure.registro_divisao_json import (
    gravar_registro_divisao,
)
from concrete_crack.presentation.indice_tiles import gravar_indice
from concrete_crack.presentation.tiles import gerar_tiles, main

DIVISAO = Divisao(("rgb/001.JPG",), (), ("rgb/002.JPG",))


def foto_gravada() -> np.ndarray:
    """Foto RGB 768 x 1024 (altura x largura) com um degradê por coluna."""
    colunas = np.linspace(0, 255, 1024).astype(np.uint8)
    return np.repeat(np.repeat(colunas[None, :, None], 768, axis=0), 3, axis=2)


def montar_raiz(tmp_path: Path) -> Path:
    """Duas fotos (a 001 com EXIF 6), máscaras de exibição, divisão e índice."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    pasta = pasta_dados_brutos(raiz, "ccsd")
    (pasta / "rgb").mkdir(parents=True)
    (pasta / "BW").mkdir()
    for numero, orientacao in (("001", 6), ("002", None)):
        exif = Image.Exif()
        if orientacao is not None:
            exif[0x0112] = orientacao
        Image.fromarray(foto_gravada()).save(
            pasta / f"rgb/{numero}.JPG", "PNG", exif=exif
        )
        # máscara na orientação de exibição: 1024 x 768 para a 001 (EXIF 6)
        forma = (1024, 768) if orientacao == 6 else (768, 1024)
        mascara = np.zeros(forma, dtype=np.uint8)
        mascara[:, 1] = 255
        Image.fromarray(mascara).save(pasta / f"BW/{numero}.jpg", "PNG")
    nomes = ["BW/001.jpg", "BW/002.jpg", "rgb/001.JPG", "rgb/002.JPG"]
    arquivos = tuple(ArquivoRegistrado(n, 1, "a" * 64) for n in nomes)
    manifesto = caminho_manifesto_arquivos(raiz, "ccsd")
    gravar_manifesto(ManifestoArquivos("ccsd", "2026-11-13", arquivos), manifesto)
    registro = RegistroDivisao(
        "ccsd", 7, (0.70, 0.15, 0.15), "b" * 64, sha256_do_arquivo(manifesto), DIVISAO
    )
    gravar_registro_divisao(registro, caminho_split(raiz))
    gravar_indice(raiz, "ccsd")
    return raiz


def test_registra_os_hashes_e_grava_foto_e_mascara_de_cada_tile(
    tmp_path: Path,
) -> None:
    raiz = montar_raiz(tmp_path)
    resultado = gerar_tiles(raiz, "ccsd")
    # cada foto tem 2 x 2 tiles em cada uma das duas escalas
    assert (resultado.modo, resultado.n_fotos, resultado.n_tiles) == (
        "registrado",
        2,
        16,
    )
    assert len(list(pasta_tiles(raiz, "ccsd").rglob("*.png"))) == 32
    manifesto = carregar_manifesto_pixels(caminho_manifesto_pixels(raiz))
    assert [f.foto for f in manifesto.fotos] == ["rgb/001.JPG", "rgb/002.JPG"]
    assert [e.fator for e in manifesto.fotos[0].escalas] == [1, 2]


def test_tile_da_foto_com_exif_6_vem_na_orientacao_de_exibicao(
    tmp_path: Path,
) -> None:
    raiz = montar_raiz(tmp_path)
    gerar_tiles(raiz, "ccsd")
    pasta = pasta_tiles(raiz, "ccsd") / "escala_1" / "001"
    tile = np.array(Image.open(pasta / "0_0_foto.png"))
    # EXIF 6 gira 90° no sentido horário: o degradê por coluna vira por linha
    assert tile.shape == (512, 512, 3)
    assert (tile[0] == tile[0, 0]).all()
    assert tile[511, 0, 0] > tile[0, 0, 0]


def test_mascaras_em_0_e_255_na_nativa_e_contagem_na_2x(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    gerar_tiles(raiz, "ccsd")
    pasta = pasta_tiles(raiz, "ccsd")
    nativa = np.array(Image.open(pasta / "escala_1" / "002" / "0_0_mascara.png"))
    reduzida = np.array(Image.open(pasta / "escala_2" / "002" / "0_0_mascara.png"))
    assert sorted(np.unique(nativa).tolist()) == [0, 255]
    # a coluna 1 cai inteira nos blocos da coluna 0: 2 de 4 pixels
    assert reduzida[:, 0].tolist() == [2] * 256
    assert (reduzida[:, 1:] == 0).all()


def test_segunda_execucao_confere_sem_mudar_o_manifesto(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    gerar_tiles(raiz, "ccsd")
    antes = caminho_manifesto_pixels(raiz).read_bytes()
    assert gerar_tiles(raiz, "ccsd").modo == "conferido"
    assert caminho_manifesto_pixels(raiz).read_bytes() == antes


def test_conferencia_aponta_a_mascara_alterada(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    gerar_tiles(raiz, "ccsd")
    mascara = np.zeros((768, 1024), dtype=np.uint8)
    mascara[:, 2] = 255
    Image.fromarray(mascara).save(
        pasta_dados_brutos(raiz, "ccsd") / "BW/002.jpg", "PNG"
    )
    with pytest.raises(ValueError, match="rgb/002.JPG: escala 1: máscara"):
        gerar_tiles(raiz, "ccsd")


def test_outra_versao_do_pillow_e_recusada_antes_de_gerar(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    gerar_tiles(raiz, "ccsd")
    destino = caminho_manifesto_pixels(raiz)
    conteudo = json.loads(destino.read_text(encoding="utf-8"))
    texto = destino.read_text(encoding="utf-8").replace(
        f'"versao_pillow": "{conteudo["versao_pillow"]}"', '"versao_pillow": "0.0.1"'
    )
    destino.write_text(texto, encoding="utf-8", newline="\n")
    with pytest.raises(ValueError, match="Pillow 0.0.1"):
        gerar_tiles(raiz, "ccsd")


def test_divisao_alterada_depois_do_indice_e_recusada(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with caminho_split(raiz).open("a", encoding="utf-8") as f:
        f.write(" ")
    with pytest.raises(ValueError, match="divisão mudou"):
        gerar_tiles(raiz, "ccsd")


def test_main_devolve_0_e_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    raiz = montar_raiz(tmp_path)
    assert main(["--raiz", str(raiz), "ccsd"]) == 0
    saida = capsys.readouterr()
    assert "Hashes dos pixels registrado" in saida.out
    assert "Fotos: 2; tiles: 16" in saida.out
    assert "2/2 fotos" in saida.err
    assert main(["--raiz", str(tmp_path), "ccsd"]) == 2
    assert "Erro:" in capsys.readouterr().err
