"""Testes da ficha de procedência e do manifesto de fontes."""

import json
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path

import pytest

from concrete_crack.domain.procedencia import FonteDados
from concrete_crack.infrastructure.manifesto import carregar_fontes

MANIFESTO = Path(__file__).resolve().parents[1] / "manifests" / "fontes.json"


def ficha_valida() -> FonteDados:
    return FonteDados(
        id="exemplo",
        nome="Dataset de exemplo",
        versao="v1",
        papel="primario",
        autores=("Fulano",),
        publicacao="Fulano (2020). Exemplo.",
        url="https://exemplo.org/dataset",
        doi=None,
        licenca="CC BY 4.0",
        licenca_permite_redistribuir=True,
        exige_aceite_termos=False,
        data_consulta="2026-10-27",
        finalidade_original="Teste.",
        n_imagens=10,
        resolucao="a medir",
        anotacoes="Máscaras binárias.",
    )


def test_ficha_valida_e_aceita() -> None:
    assert ficha_valida().id == "exemplo"


@pytest.mark.parametrize("campo", ["nome", "versao", "publicacao", "url", "licenca"])
def test_campo_obrigatorio_vazio_e_recusado(campo: str) -> None:
    with pytest.raises(ValueError, match="vazios"):
        replace(ficha_valida(), **{campo: "   "})


def test_id_com_maiuscula_ou_espaco_e_recusado() -> None:
    with pytest.raises(ValueError, match="minúsculo"):
        replace(ficha_valida(), id="Meu Id")


def test_ficha_sem_autores_e_recusada() -> None:
    with pytest.raises(ValueError, match="autor"):
        replace(ficha_valida(), autores=())


def test_papel_invalido_e_recusado() -> None:
    with pytest.raises(ValueError, match="Papel"):
        replace(ficha_valida(), papel="treino")


def test_url_sem_https_e_recusada() -> None:
    with pytest.raises(ValueError, match="https"):
        replace(ficha_valida(), url="http://exemplo.org")


def test_data_fora_do_formato_e_recusada() -> None:
    with pytest.raises(ValueError, match="AAAA-MM-DD"):
        replace(ficha_valida(), data_consulta="27/10/2026")


def test_numero_de_imagens_nao_positivo_e_recusado() -> None:
    with pytest.raises(ValueError, match="positivo"):
        replace(ficha_valida(), n_imagens=0)


def test_ficha_e_imutavel() -> None:
    with pytest.raises(FrozenInstanceError):
        ficha_valida().id = "outro"


def test_manifesto_real_e_valido() -> None:
    fontes = carregar_fontes(MANIFESTO)
    assert [fonte.id for fonte in fontes] == ["ccsd", "s2ds"]
    assert {fonte.id: fonte.papel for fonte in fontes} == {
        "ccsd": "primario",
        "s2ds": "externo",
    }


def test_licencas_e_aceites_do_manifesto() -> None:
    fontes = {fonte.id: fonte for fonte in carregar_fontes(MANIFESTO)}
    assert fontes["ccsd"].licenca_permite_redistribuir is True
    assert fontes["ccsd"].exige_aceite_termos is False
    assert fontes["s2ds"].licenca_permite_redistribuir is False
    assert fontes["s2ds"].exige_aceite_termos is True


def test_ids_repetidos_sao_recusados(tmp_path: Path) -> None:
    ficha = asdict(ficha_valida())
    arquivo = tmp_path / "fontes.json"
    arquivo.write_text(json.dumps({"fontes": [ficha, ficha]}), encoding="utf-8")
    with pytest.raises(ValueError, match="repetidos"):
        carregar_fontes(arquivo)
