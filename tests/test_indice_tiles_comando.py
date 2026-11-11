"""Testes do comando que grava o índice de tiles (sem torch)."""

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.config.caminhos import (
    caminho_indice_tiles,
    caminho_manifesto_arquivos,
    caminho_split,
    pasta_dados_brutos,
)
from concrete_crack.domain.divisao import Divisao, RegistroDivisao
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.indice_tiles_json import carregar_indice_tiles
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.infrastructure.registro_divisao_json import (
    gravar_registro_divisao,
)
from concrete_crack.presentation.indice_tiles import gravar_indice, main

# Tamanho gravado (largura, altura) e orientação EXIF de cada foto.
FOTOS = {
    "rgb/a.JPG": ((1024, 768), None),
    "rgb/b.JPG": ((1024, 768), 6),
    "rgb/c.JPG": ((1536, 1024), None),
}
DIVISAO = Divisao(("rgb/b.JPG",), ("rgb/c.JPG",), ("rgb/a.JPG",))


def montar_raiz(tmp_path: Path) -> Path:
    """Fotos JPEG cinza (a b com EXIF 6), manifesto e divisão."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    pasta = pasta_dados_brutos(raiz, "ccsd") / "rgb"
    pasta.mkdir(parents=True)
    for nome, ((largura, altura), orientacao) in FOTOS.items():
        imagem = Image.fromarray(np.full((altura, largura), 128, dtype=np.uint8))
        exif = Image.Exif()
        if orientacao is not None:
            exif[0x0112] = orientacao
        imagem.save(pasta.parent / nome, "JPEG", exif=exif)
    arquivos = tuple(ArquivoRegistrado(n, 1, "a" * 64) for n in FOTOS)
    manifesto = caminho_manifesto_arquivos(raiz, "ccsd")
    gravar_manifesto(ManifestoArquivos("ccsd", "2026-11-11", arquivos), manifesto)
    registro = RegistroDivisao(
        "ccsd", 7, (0.70, 0.15, 0.15), "b" * 64, sha256_do_arquivo(manifesto), DIVISAO
    )
    gravar_registro_divisao(registro, caminho_split(raiz))
    return raiz


def test_usa_o_tamanho_de_exibicao_com_a_orientacao_exif(tmp_path: Path) -> None:
    fotos = {f.foto: f for f in gravar_indice(montar_raiz(tmp_path), "ccsd").fotos}
    # b é gravada em 1024 x 768 com EXIF 6: exibida em 768 x 1024
    assert (fotos["rgb/b.JPG"].largura, fotos["rgb/b.JPG"].altura) == (768, 1024)
    nativa = fotos["rgb/b.JPG"].grades[0]
    assert (nativa.xs, nativa.ys) == ((0, 256), (0, 512))


def test_conjuntos_escalas_e_total_de_tiles(tmp_path: Path) -> None:
    indice = gravar_indice(montar_raiz(tmp_path), "ccsd")
    assert [(f.foto, f.conjunto) for f in indice.fotos] == [
        ("rgb/a.JPG", "teste"),
        ("rgb/b.JPG", "treino"),
        ("rgb/c.JPG", "validacao"),
    ]
    assert indice.escalas == ((1, 512), (2, 256))
    # a: 4 + 4; b: 4 + 4; c (1536 x 1024): 3 x 2 nas duas escalas
    assert indice.n_tiles == 28


def test_guarda_os_hashes_da_divisao_e_do_manifesto(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    indice = gravar_indice(raiz, "ccsd")
    assert indice.sha256_split == sha256_do_arquivo(caminho_split(raiz))
    assert indice.sha256_manifesto == sha256_do_arquivo(
        caminho_manifesto_arquivos(raiz, "ccsd")
    )
    assert carregar_indice_tiles(caminho_indice_tiles(raiz)) == indice


def test_indice_nao_se_gera_de_novo(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    gravar_indice(raiz, "ccsd")
    antes = caminho_indice_tiles(raiz).read_bytes()
    with pytest.raises(FileExistsError, match="não se gera de novo"):
        gravar_indice(raiz, "ccsd")
    assert caminho_indice_tiles(raiz).read_bytes() == antes


def test_manifesto_alterado_depois_da_divisao_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with caminho_manifesto_arquivos(raiz, "ccsd").open("a", encoding="utf-8") as f:
        f.write(" ")
    with pytest.raises(ValueError, match="manifesto de arquivos mudou"):
        gravar_indice(raiz, "ccsd")
    assert not caminho_indice_tiles(raiz).exists()


def test_json_tem_uma_linha_por_foto(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    gravar_indice(raiz, "ccsd")
    bruto = caminho_indice_tiles(raiz).read_bytes()
    assert b"\r\n" not in bruto
    linhas = bruto.decode("utf-8").splitlines()
    # "{", 5 linhas de cabeçalho, 3 fotos, "  ]" e "}"
    assert len(linhas) == 11
    assert linhas[6].startswith('    {"foto": "rgb/a.JPG", "conjunto": "teste"')
    assert list(json.loads(bruto)) == [
        "fonte_id",
        "sha256_split",
        "sha256_manifesto_de_arquivos",
        "escalas",
        "fotos",
    ]


def test_main_devolve_0_e_depois_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    assert main(["--raiz", str(raiz), "ccsd"]) == 0
    saida = capsys.readouterr().out
    assert "Fotos: 3; tiles: 28" in saida
    assert "  escala 1 (tile 512): treino 4; validacao 6; teste 4" in saida
    assert "  escala 2 (tile 256): treino 4; validacao 6; teste 4" in saida
    assert main(["--raiz", str(raiz), "ccsd"]) == 2
    assert "não se gera de novo" in capsys.readouterr().err
