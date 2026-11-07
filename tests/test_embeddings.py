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


@pytest.fixture(scope="module")
def pesos_salvos(tmp_path_factory):
    """Grava os pesos de uma rede sem pré-treino e devolve (rede, arquivo)."""
    import timm
    import torch
    from safetensors.torch import save_file

    torch.manual_seed(0)
    rede = timm.create_model(
        REGRAS.modelo_embeddings,
        pretrained=False,
        num_classes=0,
        img_size=REGRAS.lado_entrada_embeddings,
    )
    pasta = tmp_path_factory.mktemp("pesos")
    estado = {nome: valor.contiguous() for nome, valor in rede.state_dict().items()}
    save_file(estado, pasta / "model.safetensors")
    return rede, pasta / "model.safetensors"


def carregar(caminho, sha256):
    from concrete_crack.infrastructure.embeddings import criar_extrator_com_pesos

    return criar_extrator_com_pesos(
        REGRAS.modelo_embeddings, REGRAS.lado_entrada_embeddings, caminho, sha256
    )


def test_pesos_do_arquivo_sao_carregados_inteiros(pesos_salvos) -> None:
    import torch

    from concrete_crack.infrastructure.arquivos import sha256_do_arquivo

    rede, caminho = pesos_salvos
    extrator = carregar(caminho, sha256_do_arquivo(caminho))
    originais = rede.state_dict()
    carregados = extrator.modelo.state_dict()
    assert originais.keys() == carregados.keys()
    assert all(torch.equal(originais[nome], carregados[nome]) for nome in originais)


def test_hash_divergente_e_recusado_antes_de_carregar(pesos_salvos) -> None:
    _, caminho = pesos_salvos
    with pytest.raises(ValueError, match="hash dos pesos não confere"):
        carregar(caminho, "0" * 64)


def test_arquivo_com_parametro_faltando_e_recusado(pesos_salvos, tmp_path) -> None:
    from safetensors.torch import load_file, save_file

    from concrete_crack.infrastructure.arquivos import sha256_do_arquivo

    _, caminho = pesos_salvos
    estado = load_file(caminho)
    del estado["norm.weight"]
    incompleto = tmp_path / "incompleto.safetensors"
    save_file(estado, incompleto)
    with pytest.raises(RuntimeError, match="norm.weight"):
        carregar(incompleto, sha256_do_arquivo(incompleto))
