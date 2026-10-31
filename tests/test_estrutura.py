"""Testes dos comandos de estrutura: pareamento e dimensões."""

from pathlib import Path

import pytest
from PIL import Image

from concrete_crack.config.caminhos import (
    caminho_manifesto_arquivos,
    pasta_dados_brutos,
)
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.presentation import estrutura, inspecao
from concrete_crack.presentation.estrutura import main, parear_fonte

HASH = "a" * 64


def montar_raiz(
    tmp_path: Path,
    mascaras: list[str],
    fotos: list[str],
    fonte_id: str = "ccsd",
) -> Path:
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    caminhos = ["pacote.rar", *mascaras, *fotos]
    arquivos = tuple(ArquivoRegistrado(c, 1, HASH) for c in caminhos)
    manifesto = ManifestoArquivos(fonte_id, "2026-10-31", arquivos)
    gravar_manifesto(manifesto, caminho_manifesto_arquivos(raiz, "ccsd"))
    return raiz


def criar_imagem(
    caminho: Path, tamanho: tuple[int, int], orientacao: int | None = None
) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    imagem = Image.new("RGB", tamanho)
    if orientacao is None:
        imagem.save(caminho)
    else:
        exif = Image.Exif()
        exif[0x0112] = orientacao
        imagem.save(caminho, exif=exif)


def montar_com_imagens(
    tmp_path: Path, tamanhos: list[tuple[tuple[int, int], tuple[int, int]]]
) -> Path:
    mascaras = [f"BW/{i:03d}.jpg" for i in range(1, len(tamanhos) + 1)]
    fotos = [f"rgb/{i:03d}.JPG" for i in range(1, len(tamanhos) + 1)]
    raiz = montar_raiz(tmp_path, mascaras, fotos)
    pasta = pasta_dados_brutos(raiz, "ccsd")
    for (tam_mascara, tam_foto), mascara, foto in zip(
        tamanhos, mascaras, fotos, strict=True
    ):
        criar_imagem(pasta / mascara, tam_mascara)
        criar_imagem(pasta / foto, tam_foto)
    return raiz


def test_pareamento_completo_ignora_arquivos_fora_das_pastas(tmp_path: Path) -> None:
    raiz = montar_raiz(
        tmp_path,
        ["BW/001.jpg", "BW/002.jpg"],
        ["rgb/001.JPG", "rgb/002.JPG"],
    )
    resultado = parear_fonte(raiz, "ccsd")
    assert resultado.completo
    assert len(resultado.pares) == 2


def test_detecta_mascara_sem_foto(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, ["BW/001.jpg", "BW/002.jpg"], ["rgb/001.JPG"])
    resultado = parear_fonte(raiz, "ccsd")
    assert not resultado.completo
    assert resultado.mascaras_sem_foto == ("BW/002.jpg",)


@pytest.mark.parametrize(
    ("mascaras", "fotos"),
    [([], ["rgb/001.JPG"]), (["BW/001.jpg"], [])],
)
def test_manifesto_sem_mascaras_ou_sem_fotos_e_recusado(
    tmp_path: Path, mascaras: list[str], fotos: list[str]
) -> None:
    raiz = montar_raiz(tmp_path, mascaras, fotos)
    with pytest.raises(ValueError, match="não tem arquivos"):
        parear_fonte(raiz, "ccsd")


def test_manifesto_de_outra_fonte_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, ["BW/001.jpg"], ["rgb/001.JPG"], fonte_id="s2ds")
    with pytest.raises(ValueError, match="declara"):
        parear_fonte(raiz, "ccsd")


def test_main_devolve_0_quando_completo(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(
        tmp_path,
        ["BW/001.jpg", "BW/002.jpg"],
        ["rgb/001.JPG", "rgb/002.JPG"],
    )
    assert main(["--raiz", str(raiz), "parear", "ccsd"]) == 0
    saida = capsys.readouterr().out
    assert "Pares: 2" in saida
    assert "Pareamento completo" in saida


def test_main_devolve_1_quando_ha_arquivo_sem_par(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path, ["BW/001.jpg", "BW/002.jpg"], ["rgb/001.JPG"])
    assert main(["--raiz", str(raiz), "parear", "ccsd"]) == 1
    saida = capsys.readouterr().out
    assert "máscaras sem foto (1)" in saida
    assert "BW/002.jpg" in saida


def test_main_devolve_2_sem_manifesto(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = tmp_path / "vazio"
    (raiz / "manifests").mkdir(parents=True)
    assert main(["--raiz", str(raiz), "parear", "ccsd"]) == 2
    assert "Erro" in capsys.readouterr().err


def test_lista_longa_e_cortada_em_vinte(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    mascaras = [f"BW/{i:03d}.jpg" for i in range(1, 26)]
    raiz = montar_raiz(tmp_path, mascaras, ["rgb/999.JPG"])
    assert main(["--raiz", str(raiz), "parear", "ccsd"]) == 1
    saida = capsys.readouterr().out
    assert "máscaras sem foto (25)" in saida
    assert "... e mais 5" in saida


def test_prefixo_das_mascaras_e_o_mesmo_da_inspecao() -> None:
    assert estrutura.PREFIXO_MASCARAS == inspecao.PREFIXO_MASCARAS


def test_main_dimensoes_devolve_0_quando_tudo_confere(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_com_imagens(tmp_path, [((8, 6), (8, 6)), ((8, 6), (8, 6))])
    assert main(["--raiz", str(raiz), "dimensoes", "ccsd"]) == 0
    saida = capsys.readouterr().out
    assert "Tamanhos das fotos: 8x6 (2)" in saida
    assert "Orientações EXIF das fotos: ausente (2)" in saida
    assert "Pares com tamanho diferente: 0" in saida


def test_main_dimensoes_devolve_1_com_tamanho_diferente(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_com_imagens(tmp_path, [((8, 6), (16, 12))])
    assert main(["--raiz", str(raiz), "dimensoes", "ccsd"]) == 1
    saida = capsys.readouterr().out
    assert "Pares com tamanho diferente: 1" in saida
    assert "BW/001.jpg <-> rgb/001.JPG" in saida
    assert "Pares com eixos trocados: 0" in saida


def test_main_dimensoes_aponta_eixos_trocados(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_com_imagens(tmp_path, [((6, 8), (8, 6))])
    assert main(["--raiz", str(raiz), "dimensoes", "ccsd"]) == 1
    assert "Pares com eixos trocados: 1" in capsys.readouterr().out


def test_main_dimensoes_devolve_2_quando_o_arquivo_falta(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path, ["BW/001.jpg"], ["rgb/001.JPG"])
    assert main(["--raiz", str(raiz), "dimensoes", "ccsd"]) == 2
    assert "Erro" in capsys.readouterr().err


def test_main_dimensoes_devolve_0_quando_a_orientacao_resolve_a_divergencia(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path, ["BW/001.jpg"], ["rgb/001.JPG"])
    pasta = pasta_dados_brutos(raiz, "ccsd")
    criar_imagem(pasta / "BW/001.jpg", (6, 8))
    criar_imagem(pasta / "rgb/001.JPG", (8, 6), orientacao=6)
    assert main(["--raiz", str(raiz), "dimensoes", "ccsd"]) == 0
    saida = capsys.readouterr().out
    assert "Pares com tamanho diferente: 1" in saida
    assert "Pares com eixos trocados: 1" in saida
    assert "Orientações EXIF das fotos nos pares trocados: 6 (1)" in saida
    assert "Pares com tamanho diferente após a orientação: 0" in saida
