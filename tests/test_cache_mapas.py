"""Testes do cache dos mapas do Frangi por escala, com fotos sintéticas."""

from pathlib import Path

import numpy as np
import pytest

from concrete_crack.domain.registro_c import ConstanteC, RegistroC
from concrete_crack.infrastructure.cache_mapas import CacheMapasFrangi
from concrete_crack.infrastructure.frangi import ParametrosFrangi, SegmentadorFrangi
from concrete_crack.infrastructure.imagens import gravar_png
from concrete_crack.ports.mapas_por_escala import MapasPorEscala

ESCALAS = (1.0, 2.0)
REGISTRO = RegistroC(
    fonte_id="sintetica",
    sha256_split="a" * 64,
    seed=1,
    n_pixels_por_foto=10,
    escalas=ESCALAS,
    percentil=99.0,
    fracao=0.5,
    fotos=("rgb/a.png",),
    constantes=(ConstanteC(0.0, 0.1, 0.05), ConstanteC(8.0, 0.08, 0.04)),
    versoes=(),
)


def foto_sintetica() -> np.ndarray:
    """Foto de 40 x 50 com uma fissura escura e um degradê de iluminação."""
    colunas = np.arange(50, dtype=float)
    cinza = np.tile(120 + colunas, (40, 1))
    cinza[:, 20:22] -= 70
    return np.stack([cinza.astype(np.uint8)] * 3, axis=-1)


@pytest.fixture
def cache(tmp_path: Path) -> CacheMapasFrangi:
    """Um cache vazio sobre uma pasta com uma foto."""
    gravar_png(tmp_path / "raw" / "rgb" / "a.png", foto_sintetica())
    return CacheMapasFrangi(
        tmp_path / "raw", tmp_path / "cache", REGISTRO, ESCALAS, beta=0.5
    )


def direto(sigma: float, sigma_fundo: float) -> np.ndarray:
    """O mapa calculado direto pelo Frangi, arredondado para float32."""
    c = REGISTRO.c_do_fundo(sigma_fundo)
    parametros = ParametrosFrangi((sigma,), sigma_fundo, c, 0.5)
    return SegmentadorFrangi(parametros).mapear(foto_sintetica()).astype(np.float32)


def test_cumpre_o_port(cache: CacheMapasFrangi) -> None:
    assert isinstance(cache, MapasPorEscala)


def test_mapa_e_o_do_frangi_em_float32(cache: CacheMapasFrangi) -> None:
    mapa = cache.mapa("rgb/a.png", 2.0, 0.0)
    assert mapa.dtype == np.float32
    assert np.array_equal(mapa, direto(2.0, 0.0))


def test_primeiro_pedido_grava_todas_as_escalas_sem_temporarios(
    cache: CacheMapasFrangi,
) -> None:
    cache.mapa("rgb/a.png", 1.0, 8.0)
    gravados = sorted(
        p.relative_to(cache.pasta_cache).as_posix()
        for p in cache.pasta_cache.rglob("*")
        if p.is_file()
    )
    assert gravados == ["fundo_8/sigma_1/a.npy", "fundo_8/sigma_2/a.npy"]


def test_segundo_pedido_le_do_disco_sem_a_foto(cache: CacheMapasFrangi) -> None:
    primeiro = cache.mapa("rgb/a.png", 1.0, 0.0)
    (cache.pasta_fotos / "rgb" / "a.png").unlink()
    assert np.array_equal(cache.mapa("rgb/a.png", 1.0, 0.0), primeiro)
    assert np.array_equal(cache.mapa("rgb/a.png", 2.0, 0.0), direto(2.0, 0.0))


def test_fundos_diferentes_nao_se_misturam(cache: CacheMapasFrangi) -> None:
    sem_fundo = cache.mapa("rgb/a.png", 2.0, 0.0)
    com_fundo = cache.mapa("rgb/a.png", 2.0, 8.0)
    assert np.array_equal(com_fundo, direto(2.0, 8.0))
    assert not np.array_equal(com_fundo, sem_fundo)


@pytest.mark.parametrize(
    ("sigma", "sigma_fundo", "trecho"),
    [(4.0, 0.0, "escala"), (1.0, 64.0, "não tem c")],
)
def test_escala_ou_fundo_fora_do_cache_sao_recusados(
    cache: CacheMapasFrangi, sigma: float, sigma_fundo: float, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        cache.mapa("rgb/a.png", sigma, sigma_fundo)
