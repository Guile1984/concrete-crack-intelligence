"""Testes da gravação atômica e da leitura do registro de vereditos."""

import os
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import caminho_vereditos_inspecao
from concrete_crack.domain.registro_vereditos import RegistroVereditos
from concrete_crack.domain.veredito import Veredito
from concrete_crack.infrastructure.registro_vereditos_json import (
    carregar_registro,
    gravar_registro,
)

SHA = "b" * 64
H1 = "2026-11-02T15:00:00+00:00"
H2 = "2026-11-02T15:05:00+00:00"
AMOSTRA = ("BW/001.jpg", "BW/002.jpg")


def registro_completo() -> RegistroVereditos:
    return (
        RegistroVereditos("ccsd", SHA, AMOSTRA)
        .julgar("BW/001.jpg", Veredito.ADEQUADA, H1, "máscara fina, ok")
        .julgar("BW/002.jpg", Veredito.DUVIDOSA, H1)
        .corrigir("BW/002.jpg", Veredito.INADEQUADA, "excesso na borda", H2)
    )


def test_ida_e_volta_preserva_o_registro(tmp_path: Path) -> None:
    destino = tmp_path / "v.json"
    registro = registro_completo()
    gravar_registro(registro, destino)
    assert carregar_registro(destino) == registro


def test_formato_e_estavel_com_acentos_lf_e_quebra_final(tmp_path: Path) -> None:
    destino = tmp_path / "v.json"
    gravar_registro(registro_completo(), destino)
    bruto = destino.read_bytes()
    assert b"\r" not in bruto
    assert bruto.endswith(b"}\n")
    assert "máscara fina, ok" in bruto.decode("utf-8")
    assert b'\n  "fonte_id": "ccsd",' in bruto


def test_nao_sobra_arquivo_temporario(tmp_path: Path) -> None:
    gravar_registro(registro_completo(), tmp_path / "v.json")
    assert [p.name for p in tmp_path.iterdir()] == ["v.json"]


def test_regravar_substitui_o_conteudo(tmp_path: Path) -> None:
    destino = tmp_path / "v.json"
    vazio = RegistroVereditos("ccsd", SHA, AMOSTRA)
    gravar_registro(vazio, destino)
    gravar_registro(registro_completo(), destino)
    assert carregar_registro(destino) == registro_completo()


def test_falha_na_troca_preserva_o_arquivo_anterior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destino = tmp_path / "v.json"
    vazio = RegistroVereditos("ccsd", SHA, AMOSTRA)
    gravar_registro(vazio, destino)

    def falhar(*_args: object, **_kwargs: object) -> None:
        raise OSError("disco cheio")

    monkeypatch.setattr(os, "replace", falhar)
    with pytest.raises(OSError, match="disco cheio"):
        gravar_registro(registro_completo(), destino)
    assert carregar_registro(destino) == vazio


def test_veredito_invalido_no_arquivo_e_recusado(tmp_path: Path) -> None:
    destino = tmp_path / "v.json"
    gravar_registro(registro_completo(), destino)
    texto = destino.read_text(encoding="utf-8").replace('"adequada"', '"otima"')
    destino.write_text(texto, encoding="utf-8")
    with pytest.raises(ValueError, match="otima"):
        carregar_registro(destino)


def test_arquivo_inexistente_levanta_filenotfound(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        carregar_registro(tmp_path / "nao_existe.json")


def test_caminho_do_registro_segue_a_convencao(tmp_path: Path) -> None:
    assert caminho_vereditos_inspecao(tmp_path, "ccsd") == (
        tmp_path / "manifests" / "vereditos_inspecao_ccsd.json"
    )
