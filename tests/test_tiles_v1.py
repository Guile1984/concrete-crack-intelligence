"""Auditoria do índice de tiles versionado (A52, item 6), conferida em todo CI.

Lê ``manifests/tiles_v1.json`` junto com a divisão e o manifesto versionados.
O CI não tem as fotos, então a orientação EXIF não é relida aqui; o que se
confere é a procedência, a herança do conjunto e a reprodução da grade pela
regra a partir dos tamanhos gravados no índice.
"""

from collections import Counter
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_indice_tiles,
    caminho_manifesto_arquivos,
    caminho_split,
)
from concrete_crack.config.regras import REGRAS
from concrete_crack.domain.divisao import RegistroDivisao
from concrete_crack.domain.indice_tiles import IndiceTiles, indexar_foto
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.indice_tiles_json import (
    carregar_indice_tiles,
    gravar_indice_tiles,
)
from concrete_crack.infrastructure.registro_divisao_json import (
    carregar_registro_divisao,
)

RAIZ = Path(__file__).resolve().parents[1]
ESCALAS = (
    (1, REGRAS.lado_tile_nativo),
    (REGRAS.fator_escala_reduzida, REGRAS.lado_tile_reduzido),
)


@pytest.fixture(scope="module")
def indice() -> IndiceTiles:
    """O índice de tiles versionado."""
    return carregar_indice_tiles(caminho_indice_tiles(RAIZ))


@pytest.fixture(scope="module")
def divisao() -> RegistroDivisao:
    """A divisão versionada."""
    return carregar_registro_divisao(caminho_split(RAIZ))


def test_procedencia_aponta_para_a_divisao_e_o_manifesto_atuais(
    indice: IndiceTiles,
) -> None:
    assert indice.fonte_id == "ccsd"
    assert indice.sha256_split == sha256_do_arquivo(caminho_split(RAIZ))
    assert indice.sha256_manifesto == sha256_do_arquivo(
        caminho_manifesto_arquivos(RAIZ, "ccsd")
    )


def test_cada_foto_da_divisao_aparece_uma_vez_com_o_seu_conjunto(
    indice: IndiceTiles, divisao: RegistroDivisao
) -> None:
    assert len(indice.fotos) == 458
    for foto in indice.fotos:
        assert foto.conjunto == divisao.divisao.conjunto_de(foto.foto)


def test_escalas_sao_as_pre_registradas(indice: IndiceTiles) -> None:
    assert indice.escalas == ESCALAS == ((1, 512), (2, 256))


def test_tamanhos_de_exibicao_sao_os_da_licao_1_6(indice: IndiceTiles) -> None:
    tamanhos = Counter((foto.largura, foto.altura) for foto in indice.fotos)
    assert tamanhos == {
        (4032, 3024): 259,
        (3024, 4032): 179,
        (3264, 2448): 13,
        (2448, 3264): 7,
    }


def test_grade_de_cada_foto_e_reproduzida_pela_regra(indice: IndiceTiles) -> None:
    for foto in indice.fotos:
        refeita = indexar_foto(
            foto.foto, foto.conjunto, (foto.largura, foto.altura), ESCALAS
        )
        assert refeita == foto


def test_tiles_por_conjunto_iguais_nas_duas_escalas(indice: IndiceTiles) -> None:
    for posicao in range(len(ESCALAS)):
        por_conjunto = Counter()
        for foto in indice.fotos:
            por_conjunto[foto.conjunto] += foto.grades[posicao].n_tiles
        assert por_conjunto == {"treino": 15178, "validacao": 3260, "teste": 3286}
    assert indice.n_tiles == 43448


def test_arquivo_e_byte_a_byte_o_que_o_gravador_produz(
    indice: IndiceTiles, tmp_path: Path
) -> None:
    copia = tmp_path / "tiles_v1.json"
    gravar_indice_tiles(indice, copia)
    assert copia.read_bytes() == caminho_indice_tiles(RAIZ).read_bytes()
