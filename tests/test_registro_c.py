"""Testes do registro da constante c do Frangi e da sua gravação em JSON."""

from dataclasses import replace
from pathlib import Path

import pytest

from concrete_crack.domain.registro_c import ConstanteC, RegistroC
from concrete_crack.infrastructure.registro_c_json import (
    carregar_registro_c,
    gravar_registro_c,
)

REGISTRO = RegistroC(
    fonte_id="ccsd",
    sha256_split="a" * 64,
    seed=20261120,
    n_pixels_por_foto=100_000,
    escalas=(1.0, 2.0, 4.0, 8.0, 16.0),
    percentil=99.0,
    fracao=0.5,
    fotos=("rgb/001.jpg", "rgb/002.jpg"),
    constantes=(ConstanteC(0.0, 0.1234, 0.0617), ConstanteC(64.0, 0.1, 0.05)),
    versoes=(("numpy", "2.3.0"), ("scikit-image", "0.26.0"), ("scipy", "1.16.0")),
)


def test_c_de_cada_fundo() -> None:
    assert REGISTRO.c_do_fundo(0.0) == 0.0617
    assert REGISTRO.c_do_fundo(64.0) == 0.05
    with pytest.raises(KeyError, match="32"):
        REGISTRO.c_do_fundo(32.0)


def test_json_volta_igual_ao_registro(tmp_path: Path) -> None:
    destino = tmp_path / "experiments" / "frangi_c_v1.json"
    gravar_registro_c(REGISTRO, destino)
    assert carregar_registro_c(destino) == REGISTRO
    assert destino.read_bytes().endswith(b"}\n")


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("fonte_id", "", "fonte"),
        ("sha256_split", "x" * 64, "hash"),
        ("fotos", ("b", "a"), "ordem alfabética"),
        ("fotos", (), "ordem alfabética"),
        ("constantes", (), "fundo"),
        (
            "constantes",
            (ConstanteC(64.0, 0.1, 0.05), ConstanteC(0.0, 0.1, 0.05)),
            "fundo",
        ),
        ("constantes", (ConstanteC(0.0, 0.1, 0.06),), "fração x percentil"),
        ("constantes", (ConstanteC(0.0, 0.0, 0.0),), "fração x percentil"),
    ],
)
def test_registros_invalidos_sao_recusados(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGISTRO, **{campo: valor})
