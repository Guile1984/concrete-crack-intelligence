"""Trava do registro real da constante c do Frangi (A66, item 3), em todo CI.

O c é calculado uma única vez; estes testes leem o arquivo versionado em
``experiments/``, sem os dados, e falham se alguém o editar ou se ele deixar
de corresponder à divisão e às regras pré-registradas.
"""

from pathlib import Path

import pytest

from concrete_crack.config.caminhos import caminho_constante_c, caminho_split
from concrete_crack.config.regras import REGRAS
from concrete_crack.domain.constante_c import sortear_fotos
from concrete_crack.domain.registro_c import RegistroC
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.registro_c_json import carregar_registro_c
from concrete_crack.infrastructure.registro_divisao_json import (
    carregar_registro_divisao,
)

RAIZ = Path(__file__).resolve().parents[1]
SHA_REGISTRO = "6e4d6052add067ce804064c5d91afa80fa9f0be7bd700c1955b57bf3bb9499d7"


@pytest.fixture(scope="module")
def registro() -> RegistroC:
    """O registro versionado do c."""
    return carregar_registro_c(caminho_constante_c(RAIZ))


def test_hash_do_registro_e_o_da_rodada() -> None:
    assert sha256_do_arquivo(caminho_constante_c(RAIZ)) == SHA_REGISTRO


def test_registro_vem_da_divisao_v1(registro: RegistroC) -> None:
    assert registro.fonte_id == "ccsd"
    assert registro.sha256_split == sha256_do_arquivo(caminho_split(RAIZ))


def test_amostra_e_a_pre_registrada(registro: RegistroC) -> None:
    treino = carregar_registro_divisao(caminho_split(RAIZ)).divisao.treino
    sorteadas = sortear_fotos(treino, REGRAS.n_fotos_c_frangi, REGRAS.seed_c_frangi)
    assert registro.fotos == sorteadas
    assert registro.seed == REGRAS.seed_c_frangi
    assert registro.n_pixels_por_foto == REGRAS.n_pixels_c_frangi
    assert registro.escalas == REGRAS.escalas_frangi
    assert registro.percentil == REGRAS.percentil_c_frangi
    assert registro.fracao == REGRAS.fracao_c_frangi


def test_um_c_por_fundo_da_grade(registro: RegistroC) -> None:
    fundos = tuple(constante.sigma_fundo for constante in registro.constantes)
    assert fundos == REGRAS.sigmas_fundo_frangi
    assert registro.c_do_fundo(0.0) == 0.049519301144633494
    assert registro.c_do_fundo(64.0) == 0.04947206632971961
