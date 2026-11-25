"""Trava do ajuste real do Frangi na validação (A66), em todo CI.

A escolha é feita uma única vez; estes testes leem os dois arquivos
versionados em ``experiments/``, sem os dados, e falham se alguém os editar,
se eles deixarem de corresponder à divisão, aos grupos, ao c e à grade
pré-registrada, ou se a escolha gravada não for a que a regra da A66 tira da
própria grade gravada.
"""

import json
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_ajuste_frangi,
    caminho_constante_c,
    caminho_grade_frangi,
    caminho_grupos,
    caminho_split,
)
from concrete_crack.config.regras import REGRAS
from concrete_crack.domain.grade import ConfiguracaoFrangi, configuracoes_da_grade
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.registro_divisao_json import (
    carregar_registro_divisao,
)
from concrete_crack.infrastructure.registro_json import ler_jsonl

RAIZ = Path(__file__).resolve().parents[1]
SHA_AJUSTE = "aed13acf39911c41a2b7ba2a4c71921afdde35238c3511a8b35801ef29aa7445"
SHA_GRADE = "6a25c0af38bbf0e373c224501d99a4e70e8ae2a7a5432ff073c38b1eb95de804"
INDICE_ESCOLHIDA = 194


@pytest.fixture(scope="module")
def ajuste() -> dict:
    """O resumo versionado do ajuste."""
    return json.loads(caminho_ajuste_frangi(RAIZ).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def grade() -> list[dict]:
    """As linhas versionadas da grade, uma por configuração."""
    return ler_jsonl(caminho_grade_frangi(RAIZ))


def _configuracao(registro: dict) -> ConfiguracaoFrangi:
    """Reconstrói a configuração a partir do seu registro em JSON."""
    return ConfiguracaoFrangi(
        faixa=tuple(registro["faixa"]),
        sigma_fundo=registro["sigma_fundo"],
        limiar=registro["limiar"],
        tamanho_minimo=registro["tamanho_minimo"],
    )


def test_hashes_sao_os_da_rodada() -> None:
    assert sha256_do_arquivo(caminho_ajuste_frangi(RAIZ)) == SHA_AJUSTE
    assert sha256_do_arquivo(caminho_grade_frangi(RAIZ)) == SHA_GRADE


def test_ajuste_vem_da_divisao_dos_grupos_e_do_c(ajuste: dict) -> None:
    assert ajuste["fonte_id"] == "ccsd"
    assert ajuste["sha256_split"] == sha256_do_arquivo(caminho_split(RAIZ))
    assert ajuste["sha256_grupos"] == sha256_do_arquivo(caminho_grupos(RAIZ, "ccsd"))
    assert ajuste["sha256_registro_c"] == sha256_do_arquivo(caminho_constante_c(RAIZ))


def test_fotos_sao_toda_a_validacao_e_nada_do_teste(ajuste: dict) -> None:
    divisao = carregar_registro_divisao(caminho_split(RAIZ)).divisao
    assert ajuste["fotos"] == sorted(divisao.validacao)
    assert not set(ajuste["fotos"]) & set(divisao.teste)


def test_grade_e_a_pre_registrada_na_ordem_do_desempate(grade: list[dict]) -> None:
    esperadas = configuracoes_da_grade(
        REGRAS.faixas_escalas_frangi,
        REGRAS.sigmas_fundo_frangi,
        REGRAS.limiares_frangi,
        REGRAS.tamanhos_minimos_frangi,
    )
    assert len(grade) == len(esperadas) == 240
    assert tuple(_configuracao(linha["configuracao"]) for linha in grade) == esperadas


def test_escolha_e_a_primeira_de_maior_cldice(ajuste: dict, grade: list[dict]) -> None:
    valores = [linha["resumo"]["cldice"]["valor"] for linha in grade]
    primeira_maior = max(range(len(valores)), key=valores.__getitem__)
    escolhida = ajuste["escolhida"]
    assert primeira_maior == escolhida["indice"] == INDICE_ESCOLHIDA
    assert escolhida["configuracao"] == grade[INDICE_ESCOLHIDA]["configuracao"]
    assert escolhida["resumo"] == grade[INDICE_ESCOLHIDA]["resumo"]


def test_intervalo_segue_as_regras_e_contem_a_estimativa(ajuste: dict) -> None:
    intervalo = ajuste["escolhida"]["intervalo"]
    media = ajuste["escolhida"]["resumo"]["cldice"]["valor"]
    assert intervalo["n_reamostragens"] == REGRAS.n_reamostragens_bootstrap
    assert intervalo["nivel"] == REGRAS.nivel_confianca_bootstrap
    assert intervalo["seed"] == REGRAS.seed_bootstrap
    assert intervalo["estimativa"] == pytest.approx(media, rel=0, abs=1e-12)
    assert intervalo["inferior"] < intervalo["estimativa"] < intervalo["superior"]


def test_trivial_nao_acha_fissura_e_tem_acuracia_alta(ajuste: dict) -> None:
    trivial = ajuste["trivial"]
    assert trivial["resumo"]["cldice"]["valor"] == 0.0
    assert trivial["resumo"]["dice"]["valor"] == 0.0
    assert trivial["acuracia_global"] == 0.9865483918048988
