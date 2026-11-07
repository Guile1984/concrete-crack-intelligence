"""Testes do extrator de embeddings (rodam só na job dl do CI, marcador torch).

A rede é criada sem pesos pré-treinados: os testes conferem formato,
pré-processamento e determinismo, não a qualidade dos vetores. O torch e o
timm são importados dentro da fixture, para que a job core, sem torch, consiga
coletar este arquivo e apenas deixá-lo de fora pelo marcador.
"""

import numpy as np
import pytest

from concrete_crack.config.regras import REGRAS

pytestmark = pytest.mark.torch

MEDIA_IMAGENET = (0.485, 0.456, 0.406)
DESVIO_IMAGENET = (0.229, 0.224, 0.225)


@pytest.fixture(scope="module")
def extrator():
    from concrete_crack.infrastructure.embeddings import criar_extrator

    return criar_extrator(REGRAS.modelo_embeddings, REGRAS.lado_entrada_embeddings)


def foto(altura: int = 75, largura: int = 100, semente: int = 0) -> np.ndarray:
    rng = np.random.default_rng(semente)
    return rng.integers(0, 256, (altura, largura, 3), dtype=np.uint8)


def test_dinov2_vit_s14_devolve_384_numeros(extrator) -> None:
    vetor = extrator.extrair(foto())
    assert extrator.dimensao == 384
    assert vetor.shape == (384,)
    assert vetor.dtype == np.float64
    assert np.isfinite(vetor).all()


def test_grade_de_patches_de_37_por_37_em_518(extrator) -> None:
    assert extrator.modelo.patch_embed.grid_size == (37, 37)


def test_normalizacao_e_a_do_imagenet(extrator) -> None:
    assert extrator.media == pytest.approx(MEDIA_IMAGENET)
    assert extrator.desvio == pytest.approx(DESVIO_IMAGENET)


def test_preparo_redimensiona_sem_cortar(extrator) -> None:
    tensor = extrator.preparar(foto(75, 100))
    assert tuple(tensor.shape) == (1, 3, 518, 518)


def test_preparo_de_imagem_uniforme_e_constante_por_canal(extrator) -> None:
    cinza = np.full((40, 60, 3), 128, dtype=np.uint8)
    tensor = extrator.preparar(cinza)
    pares = zip(MEDIA_IMAGENET, DESVIO_IMAGENET, strict=True)
    for canal, (media, desvio) in enumerate(pares):
        esperado = (128 / 255 - media) / desvio
        assert tensor[0, canal].numpy() == pytest.approx(esperado, abs=1e-5)


def test_mesma_imagem_da_o_mesmo_vetor(extrator) -> None:
    imagem = foto(semente=3)
    assert np.array_equal(extrator.extrair(imagem), extrator.extrair(imagem))


def test_imagens_diferentes_dao_vetores_diferentes(extrator) -> None:
    a = extrator.extrair(foto(semente=1))
    b = extrator.extrair(foto(semente=2))
    assert not np.allclose(a, b)


@pytest.mark.parametrize(
    "imagem",
    [
        np.zeros((10, 10), dtype=np.uint8),
        np.zeros((10, 10, 4), dtype=np.uint8),
        np.zeros((10, 10, 3), dtype=np.float32),
    ],
)
def test_entrada_que_nao_e_rgb_uint8_e_recusada(extrator, imagem) -> None:
    with pytest.raises(ValueError, match="uint8"):
        extrator.preparar(imagem)
