"""Testes do registro de procedência dos pesos (sem torch)."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from concrete_crack.domain.pesos import RegistroPesos
from concrete_crack.infrastructure.registro_pesos_json import (
    carregar_registro_pesos,
    gravar_registro_pesos,
)

REGISTRO = RegistroPesos(
    repositorio="timm/vit_small_patch14_dinov2.lvd142m",
    revisao="0123456789abcdef0123456789abcdef01234567",
    arquivo="model.safetensors",
    tamanho_bytes=88240512,
    sha256="a" * 64,
    data_download="2026-11-07",
)


def test_registro_valido_e_aceito() -> None:
    assert REGISTRO.arquivo == "model.safetensors"


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("repositorio", "sem-barra", "Repositório"),
        ("repositorio", "timm/", "Repositório"),
        ("revisao", "main", "revisão"),
        ("revisao", "A" * 40, "revisão"),
        ("arquivo", "", "nome simples"),
        ("arquivo", "pasta/model.safetensors", "nome simples"),
        ("arquivo", "pasta\\model.safetensors", "nome simples"),
        ("tamanho_bytes", 0, "positivo"),
        ("sha256", "A" * 64, "SHA-256"),
        ("sha256", "a" * 63, "SHA-256"),
        ("data_download", "07/11/2026", "AAAA-MM-DD"),
    ],
)
def test_campos_invalidos_sao_recusados(campo: str, valor: object, trecho: str) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGISTRO, **{campo: valor})


def test_gravar_e_carregar_devolve_o_mesmo_registro(tmp_path: Path) -> None:
    destino = tmp_path / "pesos.json"
    gravar_registro_pesos(REGISTRO, destino)
    assert carregar_registro_pesos(destino) == REGISTRO


def test_gravacao_e_deterministica_com_lf_e_quebra_final(tmp_path: Path) -> None:
    destino = tmp_path / "pesos.json"
    gravar_registro_pesos(REGISTRO, destino)
    bruto = destino.read_bytes()
    assert b"\r\n" not in bruto
    assert bruto.endswith(b"}\n")
    assert list(json.loads(bruto)) == [
        "repositorio",
        "revisao",
        "arquivo",
        "tamanho_bytes",
        "sha256",
        "data_download",
    ]


@pytest.mark.parametrize("mudanca", ["falta", "sobra"])
def test_campo_faltando_ou_sobrando_e_recusado(tmp_path: Path, mudanca: str) -> None:
    destino = tmp_path / "pesos.json"
    gravar_registro_pesos(REGISTRO, destino)
    conteudo = json.loads(destino.read_text(encoding="utf-8"))
    if mudanca == "falta":
        del conteudo["sha256"]
    else:
        conteudo["licenca"] = "apache-2.0"
    destino.write_text(json.dumps(conteudo), encoding="utf-8")
    with pytest.raises(ValueError, match="Campos do registro"):
        carregar_registro_pesos(destino)
