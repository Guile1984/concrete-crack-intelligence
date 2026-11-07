"""Testes do registro de grupos e do comando que o grava (sem torch).

O comando usa o extrator falso e as fotos sintéticas dos testes de
``test_duplicatas_embeddings``, para não duplicar esses auxiliares.
"""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import caminho_grupos, caminho_manifesto_pesos
from concrete_crack.domain.grupos import RegistroGrupos
from concrete_crack.domain.pesos import RegistroPesos
from concrete_crack.infrastructure.registro_grupos_json import (
    carregar_registro_grupos,
    gravar_registro_grupos,
)
from concrete_crack.infrastructure.registro_pesos_json import gravar_registro_pesos
from concrete_crack.presentation.duplicatas_embeddings import detectar_por_embeddings
from concrete_crack.presentation.grupos import (
    REFERENCIA_A46,
    Referencia,
    divergencias,
    gravar_grupos,
)
from test_duplicatas_embeddings import ExtratorFalso, cena, distintas, montar_raiz

REGISTRO = RegistroGrupos(
    fonte_id="ccsd",
    metodo="teste",
    sha256_manifesto="a" * 64,
    sha256_pesos="b" * 64,
    limiar=0.005,
    grupos=(("rgb/002.JPG",), ("rgb/003.JPG", "rgb/001.JPG")),
)


def test_registro_conta_as_fotos() -> None:
    assert REGISTRO.n_fotos == 3


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("fonte_id", "", "vazios"),
        ("sha256_pesos", "B" * 64, "hashes"),
        ("limiar", -0.1, "negativo"),
        ("grupos", (), "grupos"),
        ("grupos", (("rgb/001.JPG",), ()), "grupos"),
        ("grupos", (("rgb/001.JPG",), ("rgb/001.JPG",)), "mais de um grupo"),
    ],
)
def test_registros_invalidos_sao_recusados(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGISTRO, **{campo: valor})


def test_gravacao_ordena_os_grupos_e_volta_igual(tmp_path: Path) -> None:
    destino = tmp_path / "grupos.json"
    gravar_registro_grupos(REGISTRO, destino)
    gravado = json.loads(destino.read_text(encoding="utf-8"))
    assert gravado["grupos"] == [["rgb/001.JPG", "rgb/003.JPG"], ["rgb/002.JPG"]]
    assert destino.read_bytes().endswith(b"]\n}\n")
    lido = carregar_registro_grupos(destino)
    assert sorted(map(sorted, lido.grupos)) == sorted(map(sorted, REGISTRO.grupos))
    assert lido.sha256_pesos == "b" * 64
    assert lido.limiar == 0.005


def test_referencia_da_a46() -> None:
    assert REFERENCIA_A46 == Referencia("0,0050", 7, 451, 2)


def raiz_com_par_e_pesos(tmp_path: Path) -> Path:
    """Fotos distintas mais uma cópia da foto 4 (um par), e um manifesto de pesos."""
    fotos = distintas()
    fotos.append((cena(3), None))
    raiz = montar_raiz(tmp_path, fotos)
    pesos = RegistroPesos(
        "timm/modelo", "f" * 40, "model.safetensors", 1, "c" * 64, "2026-11-07"
    )
    gravar_registro_pesos(pesos, caminho_manifesto_pesos(raiz))
    return raiz


def referencia_da_execucao(raiz: Path) -> Referencia:
    resultado = detectar_por_embeddings(raiz, "ccsd", ExtratorFalso())
    agrupamento = resultado.agrupamento
    return Referencia(
        f"{resultado.limiar:.4f}".replace(".", ","),
        agrupamento.pares_ligados,
        len(agrupamento.grupos),
        agrupamento.maior_grupo,
    )


def test_execucao_que_reproduz_a_referencia_grava_os_grupos(tmp_path: Path) -> None:
    raiz = raiz_com_par_e_pesos(tmp_path)
    referencia = referencia_da_execucao(raiz)
    registro = gravar_grupos(raiz, "ccsd", referencia, ExtratorFalso())
    assert registro.n_fotos == 46
    assert ("rgb/004.JPG", "rgb/046.JPG") in registro.grupos
    assert registro.sha256_pesos == "c" * 64
    assert carregar_registro_grupos(caminho_grupos(raiz, "ccsd")).n_fotos == 46


def test_execucao_que_nao_reproduz_a_referencia_e_recusada(tmp_path: Path) -> None:
    raiz = raiz_com_par_e_pesos(tmp_path)
    certa = referencia_da_execucao(raiz)
    errada = replace(certa, n_grupos=certa.n_grupos + 1, pares_ligados=7)
    with pytest.raises(ValueError, match="não reproduz") as erro:
        gravar_grupos(raiz, "ccsd", errada, ExtratorFalso())
    assert "grupos: esperado" in str(erro.value)
    assert "pares ligados: esperado 7, obtido 1" in str(erro.value)
    assert not caminho_grupos(raiz, "ccsd").exists()


def test_grupos_ja_gravados_nao_se_regravam(tmp_path: Path) -> None:
    raiz = raiz_com_par_e_pesos(tmp_path)
    referencia = referencia_da_execucao(raiz)
    gravar_grupos(raiz, "ccsd", referencia, ExtratorFalso())
    extrator = ExtratorFalso()
    with pytest.raises(FileExistsError, match="não se regravam"):
        gravar_grupos(raiz, "ccsd", referencia, extrator)
    assert extrator.chamadas == 0


def test_divergencias_vazias_quando_tudo_confere(tmp_path: Path) -> None:
    raiz = raiz_com_par_e_pesos(tmp_path)
    resultado = detectar_por_embeddings(raiz, "ccsd", ExtratorFalso())
    assert divergencias(resultado, referencia_da_execucao(raiz)) == []
