"""Testes do registro e do comando dos pares quase ligados (sem torch)."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import caminho_grupos, caminho_quase_ligadas
from concrete_crack.domain.vizinhos import RegistroQuaseLigadas
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.registro_quase_ligadas_json import (
    carregar_registro_quase_ligadas,
    gravar_registro_quase_ligadas,
)
from concrete_crack.presentation.quase_ligadas import (
    REFERENCIA_A48,
    ReferenciaQuaseLigadas,
    gravar_quase_ligadas,
)
from test_duplicatas_embeddings import ExtratorFalso
from test_vizinhos_comando import raiz_com_grupos

REGISTRO = RegistroQuaseLigadas(
    fonte_id="ccsd",
    sha256_grupos="a" * 64,
    limiar=0.005,
    multiplo=2.0,
    pares=(("rgb/003.JPG", "rgb/009.JPG"), ("rgb/001.JPG", "rgb/002.JPG")),
)


def test_referencia_da_a48() -> None:
    assert REFERENCIA_A48 == ReferenciaQuaseLigadas(7, 14)


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("fonte_id", "", "vazia"),
        ("sha256_grupos", "A" * 64, "hash"),
        ("multiplo", 1.0, "múltiplo"),
        ("pares", (("rgb/001.JPG", "rgb/001.JPG"),), "duas fotos"),
        ("pares", (("rgb/001.JPG",),), "duas fotos"),
    ],
)
def test_registros_invalidos_sao_recusados(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGISTRO, **{campo: valor})


def test_gravacao_ordena_os_pares_e_volta_igual(tmp_path: Path) -> None:
    destino = tmp_path / "quase.json"
    gravar_registro_quase_ligadas(REGISTRO, destino)
    gravado = json.loads(destino.read_text(encoding="utf-8"))
    assert gravado["pares"][0] == ["rgb/001.JPG", "rgb/002.JPG"]
    lido = carregar_registro_quase_ligadas(destino)
    assert sorted(lido.pares) == sorted(REGISTRO.pares)
    assert lido.limiar == 0.005


def test_execucao_que_reproduz_grava_o_registro(tmp_path: Path) -> None:
    raiz = raiz_com_grupos(tmp_path)
    registro = gravar_quase_ligadas(
        raiz, "ccsd", ReferenciaQuaseLigadas(0, 0), ExtratorFalso()
    )
    assert registro.pares == ()
    assert registro.sha256_grupos == sha256_do_arquivo(caminho_grupos(raiz, "ccsd"))
    assert carregar_registro_quase_ligadas(caminho_quase_ligadas(raiz, "ccsd")) == (
        registro
    )


def test_execucao_que_nao_reproduz_a_a48_e_recusada(tmp_path: Path) -> None:
    raiz = raiz_com_grupos(tmp_path)
    with pytest.raises(ValueError, match="não reproduz a A48"):
        gravar_quase_ligadas(raiz, "ccsd", REFERENCIA_A48, ExtratorFalso())
    assert not caminho_quase_ligadas(raiz, "ccsd").exists()


def test_registro_ja_gravado_nao_se_regrava(tmp_path: Path) -> None:
    raiz = raiz_com_grupos(tmp_path)
    referencia = ReferenciaQuaseLigadas(0, 0)
    gravar_quase_ligadas(raiz, "ccsd", referencia, ExtratorFalso())
    extrator = ExtratorFalso()
    with pytest.raises(FileExistsError, match="não se regravam"):
        gravar_quase_ligadas(raiz, "ccsd", referencia, extrator)
    assert extrator.chamadas == 0
