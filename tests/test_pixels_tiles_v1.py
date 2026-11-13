"""Auditoria do manifesto de hashes dos pixels versionado (A54), em todo CI.

O CI não tem as fotos e não regenera os pixels; quem confere os hashes é o
comando ``tiles``, no modo conferir. Aqui se confere que o manifesto aponta
para o índice de tiles atual, cobre as mesmas fotos e escalas, registra a
versão do Pillow e não foi editado à mão.
"""

from collections import Counter
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_indice_tiles,
    caminho_manifesto_pixels,
)
from concrete_crack.domain.manifesto_pixels import ManifestoPixels
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.indice_tiles_json import carregar_indice_tiles
from concrete_crack.infrastructure.manifesto_pixels_json import (
    carregar_manifesto_pixels,
    gravar_manifesto_pixels,
)

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def manifesto() -> ManifestoPixels:
    """O manifesto de hashes dos pixels versionado."""
    return carregar_manifesto_pixels(caminho_manifesto_pixels(RAIZ))


def test_aponta_para_o_indice_de_tiles_atual(manifesto: ManifestoPixels) -> None:
    assert manifesto.fonte_id == "ccsd"
    assert manifesto.sha256_indice == sha256_do_arquivo(caminho_indice_tiles(RAIZ))


def test_cobre_as_mesmas_fotos_e_escalas_do_indice(
    manifesto: ManifestoPixels,
) -> None:
    indice = carregar_indice_tiles(caminho_indice_tiles(RAIZ))
    assert [f.foto for f in manifesto.fotos] == [f.foto for f in indice.fotos]
    fatores = [fator for fator, _ in indice.escalas]
    for foto in manifesto.fotos:
        assert [e.fator for e in foto.escalas] == fatores


def test_registra_1832_hashes_e_a_versao_do_pillow(
    manifesto: ManifestoPixels,
) -> None:
    hashes = [
        valor
        for foto in manifesto.fotos
        for escala in foto.escalas
        for valor in (escala.foto, escala.mascara)
    ]
    assert len(hashes) == 1832
    assert manifesto.versao_pillow == "13.0.0"


def test_nenhuma_imagem_preparada_se_repete(manifesto: ManifestoPixels) -> None:
    fotos = Counter(e.foto for f in manifesto.fotos for e in f.escalas)
    assert max(fotos.values()) == 1


def test_arquivo_e_byte_a_byte_o_que_o_gravador_produz(
    manifesto: ManifestoPixels, tmp_path: Path
) -> None:
    copia = tmp_path / "pixels_tiles_v1.json"
    gravar_manifesto_pixels(manifesto, copia)
    assert copia.read_bytes() == caminho_manifesto_pixels(RAIZ).read_bytes()
