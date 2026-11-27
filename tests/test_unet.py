"""Testes da U-Net em CPU (rodam só na job dl do CI, marcador torch).

A rede é criada sem pesos pré-treinados: os testes conferem a arquitetura da
A68 (formatos, atalhos, normalização, saída em logits, número de parâmetros)
e que um passo de otimização reduz a perda, não a qualidade da segmentação.
O torch é importado dentro das funções, para que a job core, sem torch,
consiga coletar este arquivo e apenas deixá-lo de fora pelo marcador.
"""

import pytest

from concrete_crack.config.regras import REGRAS

pytestmark = pytest.mark.torch


@pytest.fixture(scope="module")
def rede():
    """A U-Net da A68, com pesos aleatórios e semente fixa, em avaliação."""
    import torch

    from concrete_crack.infrastructure.unet import UNetResNet18

    torch.manual_seed(0)
    modelo = UNetResNet18(
        REGRAS.canais_decoder_unet,
        REGRAS.modo_subida_unet,
        REGRAS.media_normalizacao,
        REGRAS.desvio_normalizacao,
    )
    return modelo.eval()


def entrada(lado: int, n: int = 1):
    """Lote de imagens aleatórias em [0, 1], com semente fixa."""
    import torch

    gerador = torch.Generator().manual_seed(1)
    return torch.rand(n, 3, lado, lado, generator=gerador)


@pytest.mark.parametrize("lado", [512, 256])
def test_saida_tem_um_canal_e_o_tamanho_da_entrada(rede, lado: int) -> None:
    import torch

    with torch.no_grad():
        saida = rede(entrada(lado))
    assert saida.shape == (1, 1, lado, lado)
    assert torch.isfinite(saida).all()


def test_atalhos_e_fundo_tem_os_formatos_da_a68(rede) -> None:
    import torch

    with torch.no_grad():
        formatos = [tuple(t.shape) for t in rede.caracteristicas(entrada(512))]
    assert formatos == [
        (1, 64, 256, 256),
        (1, 64, 128, 128),
        (1, 128, 64, 64),
        (1, 256, 32, 32),
        (1, 512, 16, 16),
    ]


@pytest.mark.parametrize("formato", [(1, 3, 500, 512), (1, 3, 512, 500)])
def test_lado_que_nao_e_multiplo_de_32_e_recusado(rede, formato) -> None:
    import torch

    with pytest.raises(ValueError, match="múltiplas de 32"):
        rede(torch.zeros(formato))


def test_entrada_sem_tres_canais_e_recusada(rede) -> None:
    import torch

    with pytest.raises(ValueError, match="N, 3, H, W"):
        rede(torch.zeros(1, 1, 64, 64))


def test_normalizacao_zera_uma_entrada_igual_a_media(rede) -> None:
    import torch

    media = torch.tensor(REGRAS.media_normalizacao).view(1, 3, 1, 1)
    x = media.expand(1, 3, 64, 64)
    assert torch.allclose(rede.normalizar(x), torch.zeros(1, 3, 64, 64), atol=1e-7)


def test_normalizacao_vai_no_checkpoint_mas_nao_e_treinavel(rede) -> None:
    nomes_parametros = {nome for nome, _ in rede.named_parameters()}
    assert {"media", "desvio"} <= set(rede.state_dict())
    assert not {"media", "desvio"} & nomes_parametros


def test_saida_e_logit_sem_sigmoide(rede) -> None:
    import copy

    import torch

    modelo = copy.deepcopy(rede)
    with torch.no_grad():
        modelo.cabeca.weight.zero_()
        for vies in (5.0, -5.0):
            modelo.cabeca.bias.fill_(vies)
            saida = modelo(entrada(64))
            assert torch.equal(saida, torch.full_like(saida, vies))


def test_convolucoes_antes_do_batchnorm_nao_tem_vies(rede) -> None:
    import torch

    convolucoes = [m for m in rede.decoder.modules() if isinstance(m, torch.nn.Conv2d)]
    assert len(convolucoes) == 10
    assert all(c.bias is None for c in convolucoes)
    assert rede.cabeca.bias is not None


def test_numero_de_parametros_e_o_da_conta_da_licao(rede) -> None:
    def contar(modulo) -> int:
        return sum(p.numel() for p in modulo.parameters())

    assert contar(rede.encoder) == 11_176_512
    assert contar(rede.decoder) + contar(rede.cabeca) == 3_151_569
    assert contar(rede) == 14_328_081


def test_fator_de_reducao_do_encoder_e_o_das_regras() -> None:
    from concrete_crack.infrastructure.unet import FATOR_REDUCAO

    assert FATOR_REDUCAO == REGRAS.fator_reducao_unet


def test_decoder_sem_um_bloco_por_reducao_e_recusado() -> None:
    from concrete_crack.infrastructure.unet import UNetResNet18

    with pytest.raises(ValueError, match="um bloco por redução"):
        UNetResNet18(
            (256, 128, 64, 32),
            REGRAS.modo_subida_unet,
            REGRAS.media_normalizacao,
            REGRAS.desvio_normalizacao,
        )


def test_um_passo_de_otimizacao_reduz_a_perda(rede) -> None:
    import copy

    import torch

    torch.manual_seed(0)
    modelo = copy.deepcopy(rede).train()
    x = entrada(64, n=2)
    alvo = torch.rand(2, 1, 64, 64, generator=torch.Generator().manual_seed(2)) > 0.9
    perda = torch.nn.BCEWithLogitsLoss()
    otimizador = torch.optim.Adam(modelo.parameters(), lr=1e-3)
    antes = perda(modelo(x), alvo.float())
    otimizador.zero_grad()
    antes.backward()
    otimizador.step()
    with torch.no_grad():
        depois = perda(modelo(x), alvo.float())
    assert depois.item() < antes.item()
