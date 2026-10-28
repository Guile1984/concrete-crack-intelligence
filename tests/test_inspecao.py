"""Testes do sorteio da amostra de inspeção das máscaras."""

import json
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_amostra_inspecao,
    caminho_manifesto_arquivos,
)
from concrete_crack.config.regras import REGRAS
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.presentation.inspecao import main, sortear_amostra

HASH = "a" * 64


def montar_raiz(tmp_path: Path, n_mascaras: int = 100, nome: str = "projeto") -> Path:
    raiz = tmp_path / nome
    (raiz / "manifests").mkdir(parents=True)
    arquivos = [ArquivoRegistrado("pacote.rar", 10, HASH)]
    for i in range(1, n_mascaras + 1):
        arquivos.append(ArquivoRegistrado(f"BW/{i:03d}.jpg", 1, HASH))
        arquivos.append(ArquivoRegistrado(f"rgb/{i:03d}.JPG", 1, HASH))
    manifesto = ManifestoArquivos("ccsd", "2026-10-28", tuple(arquivos))
    gravar_manifesto(manifesto, caminho_manifesto_arquivos(raiz, "ccsd"))
    return raiz


def test_amostra_so_tem_mascaras_e_o_tamanho_registrado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    amostra = sortear_amostra(raiz, "ccsd")["amostra"]
    assert len(amostra) == REGRAS.n_inspecao_mascaras
    assert all(caminho.startswith("BW/") for caminho in amostra)


def test_arquivo_gravado_tem_o_registro_completo(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    sortear_amostra(raiz, "ccsd")
    destino = caminho_amostra_inspecao(raiz, "ccsd")
    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["fonte_id"] == "ccsd"
    assert dados["seed"] == REGRAS.seed_inspecao_mascaras
    assert dados["n"] == REGRAS.n_inspecao_mascaras
    assert dados["limiar_reprovacao"] == REGRAS.limiar_reprovacao_mascaras
    assert dados["total_mascaras"] == 100
    assert dados["sha256_manifesto_de_arquivos"] == sha256_do_arquivo(
        caminho_manifesto_arquivos(raiz, "ccsd")
    )
    assert dados["amostra"] == sorted(dados["amostra"])
    conteudo = destino.read_bytes()
    assert conteudo.endswith(b"\n")
    assert b"\r" not in conteudo


def test_mesmo_manifesto_gera_a_mesma_amostra(tmp_path: Path) -> None:
    raiz_a = montar_raiz(tmp_path, nome="a")
    raiz_b = montar_raiz(tmp_path, nome="b")
    assert sortear_amostra(raiz_a, "ccsd") == sortear_amostra(raiz_b, "ccsd")


def test_nao_sobrescreve_a_amostra(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    sortear_amostra(raiz, "ccsd")
    destino = caminho_amostra_inspecao(raiz, "ccsd")
    antes = destino.read_bytes()
    with pytest.raises(FileExistsError):
        sortear_amostra(raiz, "ccsd")
    assert destino.read_bytes() == antes


def test_manifesto_com_poucas_mascaras_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, n_mascaras=30)
    with pytest.raises(ValueError, match="fora do intervalo"):
        sortear_amostra(raiz, "ccsd")
    assert not caminho_amostra_inspecao(raiz, "ccsd").exists()


def test_manifesto_de_outra_fonte_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    outro = ManifestoArquivos(
        "s2ds", "2026-10-28", (ArquivoRegistrado("BW/001.jpg", 1, HASH),)
    )
    gravar_manifesto(outro, caminho_manifesto_arquivos(raiz, "ccsd"))
    with pytest.raises(ValueError, match="declara"):
        sortear_amostra(raiz, "ccsd")


def test_main_sorteia_e_recusa_repetir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    base = ["--raiz", str(raiz)]
    assert main([*base, "sortear", "ccsd"]) == 0
    assert "Sorteadas 40 de 100" in capsys.readouterr().out
    assert main([*base, "sortear", "ccsd"]) == 2
    assert "já existe" in capsys.readouterr().err


def test_main_devolve_2_sem_manifesto(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = tmp_path / "vazio"
    (raiz / "manifests").mkdir(parents=True)
    assert main(["--raiz", str(raiz), "sortear", "ccsd"]) == 2
    assert "Erro" in capsys.readouterr().err


def test_convencao_do_caminho_da_amostra() -> None:
    raiz = Path("projeto")
    assert caminho_amostra_inspecao(raiz, "ccsd") == (
        raiz / "manifests" / "inspecao_ccsd.json"
    )
