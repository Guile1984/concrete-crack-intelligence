"""Auditoria de vazamento sobre os arquivos versionados da divisão v1 (A49).

Diferente de ``test_divisao_comando.py``, que usa dados sintéticos, estes testes
leem os arquivos reais de ``manifests/``. Rodam em todo CI e falham se alguém
editar ``split_v1.json``, ``grupos_ccsd.json`` ou o manifesto de arquivos sem
refazer a cadeia inteira.
"""

from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_grupos,
    caminho_manifesto_arquivos,
    caminho_split,
)
from concrete_crack.config.regras import REGRAS
from concrete_crack.domain.divisao import (
    RegistroDivisao,
    dividir_por_grupos,
    tamanhos_alvo,
)
from concrete_crack.domain.grupos import RegistroGrupos
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.manifesto_arquivos import carregar_manifesto
from concrete_crack.infrastructure.registro_divisao_json import (
    carregar_registro_divisao,
    gravar_registro_divisao,
)
from concrete_crack.infrastructure.registro_grupos_json import (
    carregar_registro_grupos,
)
from concrete_crack.presentation.estrutura import PREFIXO_FOTOS

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def divisao() -> RegistroDivisao:
    """O registro da divisão versionado."""
    return carregar_registro_divisao(caminho_split(RAIZ))


@pytest.fixture(scope="module")
def grupos() -> RegistroGrupos:
    """O registro de grupos versionado."""
    return carregar_registro_grupos(caminho_grupos(RAIZ, "ccsd"))


def test_tamanhos_seed_e_proporcoes_sao_os_pre_registrados(
    divisao: RegistroDivisao,
) -> None:
    d = divisao.divisao
    assert (len(d.treino), len(d.validacao), len(d.teste)) == (320, 69, 69)
    assert divisao.seed == REGRAS.seed_split
    assert divisao.proporcoes == (
        REGRAS.proporcao_treino,
        REGRAS.proporcao_validacao,
        REGRAS.proporcao_teste,
    )


def test_cada_foto_do_manifesto_aparece_uma_unica_vez(
    divisao: RegistroDivisao,
) -> None:
    manifesto = carregar_manifesto(caminho_manifesto_arquivos(RAIZ, "ccsd"))
    fotos = sorted(
        a.caminho for a in manifesto.arquivos if a.caminho.startswith(PREFIXO_FOTOS)
    )
    d = divisao.divisao
    na_divisao = [*d.treino, *d.validacao, *d.teste]
    assert len(fotos) == 458
    assert sorted(na_divisao) == fotos


def test_nenhum_grupo_e_partido_entre_conjuntos(
    divisao: RegistroDivisao, grupos: RegistroGrupos
) -> None:
    partidos = [
        grupo
        for grupo in grupos.grupos
        if len({divisao.divisao.conjunto_de(foto) for foto in grupo}) > 1
    ]
    assert partidos == []


def test_hashes_registrados_sao_os_dos_arquivos_atuais(
    divisao: RegistroDivisao, grupos: RegistroGrupos
) -> None:
    sha_manifesto = sha256_do_arquivo(caminho_manifesto_arquivos(RAIZ, "ccsd"))
    assert divisao.sha256_grupos == sha256_do_arquivo(caminho_grupos(RAIZ, "ccsd"))
    assert divisao.sha256_manifesto == sha_manifesto
    assert grupos.sha256_manifesto == sha_manifesto


def test_divisao_gravada_e_a_que_a_a49_produz(
    divisao: RegistroDivisao, grupos: RegistroGrupos
) -> None:
    _, n_validacao, n_teste = tamanhos_alvo(
        grupos.n_fotos, REGRAS.proporcao_validacao, REGRAS.proporcao_teste
    )
    refeita = dividir_por_grupos(grupos.grupos, REGRAS.seed_split, n_validacao, n_teste)
    assert divisao.divisao == refeita


def test_arquivo_e_byte_a_byte_o_que_o_gravador_produz(
    divisao: RegistroDivisao, tmp_path: Path
) -> None:
    copia = tmp_path / "split_v1.json"
    gravar_registro_divisao(divisao, copia)
    assert copia.read_bytes() == caminho_split(RAIZ).read_bytes()
