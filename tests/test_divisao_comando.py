"""Testes do registro e do comando que grava a divisão (sem torch, sem imagens)."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_grupos,
    caminho_manifesto_arquivos,
    caminho_split,
)
from concrete_crack.domain.divisao import Divisao, RegistroDivisao, dividir_por_grupos
from concrete_crack.domain.grupos import RegistroGrupos
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.infrastructure.registro_divisao_json import (
    carregar_registro_divisao,
    gravar_registro_divisao,
)
from concrete_crack.infrastructure.registro_grupos_json import gravar_registro_grupos
from concrete_crack.presentation.divisao import gravar_divisao, main

GRUPOS = tuple((f"rgb/{i:03d}.JPG",) for i in range(1, 46)) + (
    ("rgb/046.JPG", "rgb/047.JPG"),
)


def montar_raiz(tmp_path: Path) -> Path:
    """Manifesto com 47 fotos e o registro de grupos correspondente."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    fotos = [foto for grupo in GRUPOS for foto in grupo]
    arquivos = tuple(ArquivoRegistrado(f, 1, "a" * 64) for f in ["BW/001.jpg", *fotos])
    manifesto = caminho_manifesto_arquivos(raiz, "ccsd")
    gravar_manifesto(ManifestoArquivos("ccsd", "2026-11-08", arquivos), manifesto)
    registro = RegistroGrupos(
        "ccsd", "teste", sha256_do_arquivo(manifesto), "b" * 64, 0.005, GRUPOS
    )
    gravar_registro_grupos(registro, caminho_grupos(raiz, "ccsd"))
    return raiz


def test_grava_a_divisao_com_os_tamanhos_da_a49(tmp_path: Path) -> None:
    registro = gravar_divisao(montar_raiz(tmp_path), "ccsd")
    divisao = registro.divisao
    # 15% de 47 = 7,05, arredonda para 7; o treino fica com 33
    assert (len(divisao.treino), len(divisao.validacao), len(divisao.teste)) == (
        33,
        7,
        7,
    )
    assert registro.seed == 20261022
    assert registro.proporcoes == (0.70, 0.15, 0.15)


def test_divisao_gravada_e_a_da_funcao_do_dominio(tmp_path: Path) -> None:
    registro = gravar_divisao(montar_raiz(tmp_path), "ccsd")
    assert registro.divisao == dividir_por_grupos(GRUPOS, 20261022, 7, 7)


def test_o_par_fica_inteiro_num_so_conjunto(tmp_path: Path) -> None:
    divisao = gravar_divisao(montar_raiz(tmp_path), "ccsd").divisao
    assert divisao.conjunto_de("rgb/046.JPG") == divisao.conjunto_de("rgb/047.JPG")


def test_registro_guarda_os_hashes_dos_arquivos_de_origem(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    registro = gravar_divisao(raiz, "ccsd")
    assert registro.sha256_grupos == sha256_do_arquivo(caminho_grupos(raiz, "ccsd"))
    assert registro.sha256_manifesto == sha256_do_arquivo(
        caminho_manifesto_arquivos(raiz, "ccsd")
    )
    assert carregar_registro_divisao(caminho_split(raiz)) == registro


def test_divisao_nao_se_sorteia_de_novo(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    gravar_divisao(raiz, "ccsd")
    antes = caminho_split(raiz).read_bytes()
    with pytest.raises(FileExistsError, match="não se sorteia de novo"):
        gravar_divisao(raiz, "ccsd")
    assert caminho_split(raiz).read_bytes() == antes


def test_manifesto_alterado_depois_dos_grupos_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with caminho_manifesto_arquivos(raiz, "ccsd").open("a", encoding="utf-8") as f:
        f.write(" ")
    with pytest.raises(ValueError, match="manifesto de arquivos mudou"):
        gravar_divisao(raiz, "ccsd")
    assert not caminho_split(raiz).exists()


def test_json_e_deterministico_com_conjuntos_ordenados(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    gravar_divisao(raiz, "ccsd")
    bruto = caminho_split(raiz).read_bytes()
    assert b"\r\n" not in bruto
    assert bruto.endswith(b"]\n}\n")
    conteudo = json.loads(bruto)
    assert list(conteudo) == [
        "fonte_id",
        "seed",
        "proporcoes",
        "sha256_grupos",
        "sha256_manifesto_de_arquivos",
        "treino",
        "validacao",
        "teste",
    ]
    assert conteudo["teste"] == sorted(conteudo["teste"])


def test_main_devolve_0_e_depois_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    assert main(["--raiz", str(raiz), "ccsd"]) == 0
    assert "treino: 33 fotos; validação: 7; teste: 7" in capsys.readouterr().out
    assert main(["--raiz", str(raiz), "ccsd"]) == 2
    assert "não se sorteia de novo" in capsys.readouterr().err


REGISTRO = RegistroDivisao(
    fonte_id="ccsd",
    seed=7,
    proporcoes=(0.70, 0.15, 0.15),
    sha256_grupos="a" * 64,
    sha256_manifesto="b" * 64,
    divisao=Divisao(("a.jpg",), ("b.jpg",), ("c.jpg",)),
)


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("fonte_id", "", "vazia"),
        ("sha256_grupos", "x" * 64, "hashes"),
        ("proporcoes", (0.7, 0.2, 0.2), "somar 1"),
        ("divisao", Divisao(("a.jpg",), ("a.jpg",), ()), "mais de um conjunto"),
    ],
)
def test_registros_invalidos_sao_recusados(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGISTRO, **{campo: valor})


def test_gravar_e_carregar_devolve_o_mesmo_registro(tmp_path: Path) -> None:
    destino = tmp_path / "split.json"
    gravar_registro_divisao(REGISTRO, destino)
    assert carregar_registro_divisao(destino) == REGISTRO
