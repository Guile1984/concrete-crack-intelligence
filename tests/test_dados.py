"""Testes dos comandos de dados e das convenções de caminhos."""

import shutil
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_fontes,
    caminho_manifesto_arquivos,
    pasta_dados_brutos,
)
from concrete_crack.infrastructure.manifesto_arquivos import carregar_manifesto
from concrete_crack.presentation.dados import main, registrar_fonte, verificar_fonte

FONTES_REAIS = Path(__file__).resolve().parents[1] / "manifests" / "fontes.json"
DATA = "2026-10-28"


def montar_raiz(tmp_path: Path) -> Path:
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    shutil.copy(FONTES_REAIS, caminho_fontes(raiz))
    dados = pasta_dados_brutos(raiz, "ccsd")
    (dados / "sub").mkdir(parents=True)
    (dados / "a.txt").write_bytes(b"abc")
    (dados / "sub" / "b.txt").write_bytes(b"xyz")
    return raiz


def test_registrar_cria_manifesto_com_os_arquivos(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    manifesto = registrar_fonte(raiz, "ccsd", DATA)
    assert [a.caminho for a in manifesto.arquivos] == ["a.txt", "sub/b.txt"]
    assert carregar_manifesto(caminho_manifesto_arquivos(raiz, "ccsd")) == manifesto


def test_registrar_nao_sobrescreve_o_manifesto(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    registrar_fonte(raiz, "ccsd", DATA)
    destino = caminho_manifesto_arquivos(raiz, "ccsd")
    antes = destino.read_bytes()
    (pasta_dados_brutos(raiz, "ccsd") / "a.txt").write_bytes(b"abd")
    with pytest.raises(FileExistsError):
        registrar_fonte(raiz, "ccsd", DATA)
    assert destino.read_bytes() == antes


def test_registrar_recusa_fonte_sem_ficha(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with pytest.raises(ValueError, match="ficha"):
        registrar_fonte(raiz, "desconhecida", DATA)


def test_registrar_recusa_pasta_inexistente(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)  # a pasta de s2ds não existe
    with pytest.raises(NotADirectoryError):
        registrar_fonte(raiz, "s2ds", DATA)


def test_registrar_recusa_pasta_vazia(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    pasta_dados_brutos(raiz, "s2ds").mkdir(parents=True)
    with pytest.raises(ValueError, match="ao menos um arquivo"):
        registrar_fonte(raiz, "s2ds", DATA)


def test_verificar_sem_divergencias(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    registrar_fonte(raiz, "ccsd", DATA)
    assert verificar_fonte(raiz, "ccsd").vazio


def test_verificar_detecta_alteracao_de_mesmo_tamanho(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    registrar_fonte(raiz, "ccsd", DATA)
    (pasta_dados_brutos(raiz, "ccsd") / "a.txt").write_bytes(b"abd")
    assert verificar_fonte(raiz, "ccsd").alterados == ("a.txt",)


def test_verificar_sem_manifesto_e_erro(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with pytest.raises(FileNotFoundError):
        verificar_fonte(raiz, "ccsd")


def test_verificar_recusa_manifesto_de_outra_fonte(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    registrar_fonte(raiz, "ccsd", DATA)
    shutil.copy(
        caminho_manifesto_arquivos(raiz, "ccsd"),
        caminho_manifesto_arquivos(raiz, "s2ds"),
    )
    with pytest.raises(ValueError, match="declara"):
        verificar_fonte(raiz, "s2ds")


def test_main_registra_e_verifica(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    base = ["--raiz", str(raiz)]
    assert main([*base, "registrar", "ccsd", "--data-download", DATA]) == 0
    assert "Registrados 2 arquivos" in capsys.readouterr().out
    assert main([*base, "verificar", "ccsd"]) == 0
    assert "nenhuma divergência" in capsys.readouterr().out


def test_main_devolve_1_quando_ha_divergencia(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    base = ["--raiz", str(raiz)]
    main([*base, "registrar", "ccsd", "--data-download", DATA])
    capsys.readouterr()
    (pasta_dados_brutos(raiz, "ccsd") / "a.txt").write_bytes(b"abd")
    assert main([*base, "verificar", "ccsd"]) == 1
    saida = capsys.readouterr().out
    assert "alterados (1)" in saida
    assert "a.txt" in saida


def test_main_devolve_2_em_erro_de_uso(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    assert main(["--raiz", str(raiz), "registrar", "desconhecida"]) == 2
    assert "Erro" in capsys.readouterr().err


def test_main_devolve_2_ao_registrar_duas_vezes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    base = ["--raiz", str(raiz)]
    assert main([*base, "registrar", "ccsd", "--data-download", DATA]) == 0
    capsys.readouterr()
    assert main([*base, "registrar", "ccsd", "--data-download", DATA]) == 2
    assert "já existe" in capsys.readouterr().err


def test_convencoes_de_caminhos() -> None:
    raiz = Path("projeto")
    assert caminho_fontes(raiz) == raiz / "manifests" / "fontes.json"
    assert pasta_dados_brutos(raiz, "ccsd") == raiz / "data" / "raw" / "ccsd"
    assert caminho_manifesto_arquivos(raiz, "ccsd") == (
        raiz / "manifests" / "arquivos_ccsd.json"
    )
