"""Trava do manifesto de arquivos real do CCSD (A29), conferida em todo CI.

O manifesto é a âncora da cadeia: a amostra da inspeção, os grupos de
quase-duplicatas e a divisão registram o SHA-256 dele. Estes testes leem o
arquivo versionado, sem os dados (que não estão no CI), e falham se alguém o
editar.
"""

from pathlib import Path

import pytest

from concrete_crack.config.caminhos import caminho_fontes, caminho_manifesto_arquivos
from concrete_crack.domain.integridade import ManifestoArquivos
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.manifesto import carregar_fontes
from concrete_crack.infrastructure.manifesto_arquivos import carregar_manifesto
from concrete_crack.presentation.estrutura import (
    PREFIXO_FOTOS,
    PREFIXO_MASCARAS,
    parear_fonte,
)

RAIZ = Path(__file__).resolve().parents[1]
SHA_MANIFESTO = "80da125a8176fdabb7974c4c2665a6aafee4d779ab68b4741971f3f05b7652ef"
RAR = "concreteCrackSegmentationDataset.rar"
TAMANHO_RAR = 745_914_150
SHA_RAR = "1b8458ab6f84dc5086e9af8579e2cabccd3d209df97b46622096a4c105d5a6b2"


@pytest.fixture(scope="module")
def manifesto() -> ManifestoArquivos:
    """O manifesto de arquivos versionado do CCSD."""
    return carregar_manifesto(caminho_manifesto_arquivos(RAIZ, "ccsd"))


def test_hash_do_manifesto_e_o_que_a_cadeia_registra() -> None:
    assert sha256_do_arquivo(caminho_manifesto_arquivos(RAIZ, "ccsd")) == SHA_MANIFESTO


def test_fonte_e_data_do_download(manifesto: ManifestoArquivos) -> None:
    assert manifesto.fonte_id == "ccsd"
    assert manifesto.data_download == "2026-10-28"


def test_917_entradas_rar_mascaras_e_fotos(manifesto: ManifestoArquivos) -> None:
    caminhos = [arquivo.caminho for arquivo in manifesto.arquivos]
    mascaras = [c for c in caminhos if c.startswith(PREFIXO_MASCARAS)]
    fotos = [c for c in caminhos if c.startswith(PREFIXO_FOTOS)]
    outros = [c for c in caminhos if c not in {*mascaras, *fotos}]
    assert len(caminhos) == 917
    assert (len(mascaras), len(fotos), outros) == (458, 458, [RAR])


def test_rar_tem_o_tamanho_e_o_hash_do_download_direto(
    manifesto: ManifestoArquivos,
) -> None:
    rar = next(a for a in manifesto.arquivos if a.caminho == RAR)
    assert (rar.tamanho_bytes, rar.sha256) == (TAMANHO_RAR, SHA_RAR)


def test_toda_mascara_tem_foto_e_toda_foto_tem_mascara() -> None:
    pareamento = parear_fonte(RAIZ, "ccsd")
    assert pareamento.completo
    assert len(pareamento.pares) == 458


def test_ficha_de_procedencia_declara_as_mesmas_458_imagens() -> None:
    ccsd = next(f for f in carregar_fontes(caminho_fontes(RAIZ)) if f.id == "ccsd")
    assert ccsd.n_imagens == 458
