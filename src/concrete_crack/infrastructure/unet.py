"""U-Net com encoder ResNet-18 do torchvision e decoder próprio (A4, A68).

O encoder é a ResNet-18 sem a cabeça de classificação; os atalhos saem de
quatro pontos dela, e o fundo, do último estágio. O decoder tem um bloco por
redução do encoder: sobe 2× por vizinho mais próximo, concatena o atalho do
mesmo nível e aplica duas vezes conv 3×3 sem viés, BatchNorm e ReLU. A
normalização do ImageNet é feita dentro do modelo, e a saída é um logit por
pixel; a sigmoide fica fora, no adaptador que cumpre o port ``Segmentador``.

A rede nasce sem pesos pré-treinados; o carregamento dos pesos do ImageNet,
conferidos por hash, é outro passo.
"""

from collections.abc import Sequence

import torch
from torch import nn
from torch.nn import functional
from torchvision.models import resnet18

FATOR_REDUCAO = 32
CANAIS_FUNDO = 512
CANAIS_ATALHOS = (256, 128, 64, 64)
CANAIS_RGB = 3


class BlocoDecoder(nn.Module):
    """Um bloco do decoder: sobe 2×, junta o atalho e aplica duas convoluções.

    As convoluções não têm viés porque o BatchNorm logo depois subtrai a média
    do canal, o que cancela qualquer viés somado antes dele.
    """

    def __init__(
        self, canais_baixo: int, canais_atalho: int, canais_saida: int, modo: str
    ) -> None:
        """Monta o bloco.

        Args:
            canais_baixo: Canais que chegam do nível de baixo.
            canais_atalho: Canais do atalho concatenado; 0 se não houver.
            canais_saida: Canais de saída das duas convoluções.
            modo: Modo do ``interpolate`` que sobe a resolução.
        """
        super().__init__()
        self.modo = modo
        self.convolucoes = nn.Sequential(
            nn.Conv2d(
                canais_baixo + canais_atalho,
                canais_saida,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(canais_saida),
            nn.ReLU(inplace=True),
            nn.Conv2d(canais_saida, canais_saida, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(canais_saida),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor, atalho: torch.Tensor | None) -> torch.Tensor:
        """Sobe a resolução, concatena o atalho (se houver) e convolui."""
        x = functional.interpolate(x, scale_factor=2, mode=self.modo)
        if atalho is not None:
            x = torch.cat([x, atalho], dim=1)
        return self.convolucoes(x)


class UNetResNet18(nn.Module):
    """U-Net de saída única (logit de fissura por pixel).

    Attributes:
        encoder: A ResNet-18 sem ``avgpool`` e ``fc``.
        decoder: Os blocos do decoder, de baixo para cima.
        cabeca: Conv 1×1 que leva os canais do último bloco a um logit.
        media: Média por canal da normalização (buffer, não treinável).
        desvio: Desvio por canal da normalização (buffer, não treinável).
    """

    def __init__(
        self,
        canais_decoder: Sequence[int],
        modo_subida: str,
        media: tuple[float, float, float],
        desvio: tuple[float, float, float],
    ) -> None:
        """Monta a rede com pesos aleatórios.

        Args:
            canais_decoder: Canais de saída de cada bloco, de baixo para cima;
                um bloco por redução do encoder.
            modo_subida: Modo do ``interpolate`` nos blocos.
            media: Média por canal (RGB em [0, 1]) subtraída da entrada.
            desvio: Desvio por canal que divide a entrada.

        Raises:
            ValueError: Se o número de blocos não for o de reduções do encoder.
        """
        super().__init__()
        if 2 ** len(canais_decoder) != FATOR_REDUCAO:
            raise ValueError(
                "O decoder precisa de um bloco por redução do encoder "
                f"({FATOR_REDUCAO} = 2 elevado ao número de blocos)."
            )
        encoder = resnet18(weights=None)
        del encoder.avgpool, encoder.fc
        self.encoder = encoder
        canais_baixo = (CANAIS_FUNDO, *canais_decoder[:-1])
        canais_atalho = (*CANAIS_ATALHOS, 0)
        self.decoder = nn.ModuleList(
            BlocoDecoder(baixo, atalho, saida, modo_subida)
            for baixo, atalho, saida in zip(
                canais_baixo, canais_atalho, canais_decoder, strict=True
            )
        )
        self.cabeca = nn.Conv2d(canais_decoder[-1], 1, kernel_size=1)
        self.register_buffer("media", torch.tensor(media).view(1, CANAIS_RGB, 1, 1))
        self.register_buffer("desvio", torch.tensor(desvio).view(1, CANAIS_RGB, 1, 1))

    def normalizar(self, x: torch.Tensor) -> torch.Tensor:
        """Aplica (x − média) / desvio, canal a canal.

        Raises:
            ValueError: Se a entrada não for (N, 3, H, W) com H e W múltiplos
                do fator de redução.
        """
        if x.ndim != 4 or x.shape[1] != CANAIS_RGB:
            raise ValueError(f"A entrada deve ser (N, 3, H, W); veio {tuple(x.shape)}.")
        altura, largura = x.shape[-2:]
        if altura % FATOR_REDUCAO or largura % FATOR_REDUCAO:
            raise ValueError(
                f"Altura e largura devem ser múltiplas de {FATOR_REDUCAO}; "
                f"vieram {altura} e {largura}."
            )
        return (x - self.media) / self.desvio

    def caracteristicas(self, x: torch.Tensor) -> tuple[torch.Tensor, ...]:
        """Passa a entrada pelo encoder e devolve os atalhos e o fundo.

        Returns:
            (a1, a2, a3, a4, fundo), nas escalas 1/2, 1/4, 1/8, 1/16 e 1/32.
        """
        e = self.encoder
        a1 = e.relu(e.bn1(e.conv1(self.normalizar(x))))
        a2 = e.layer1(e.maxpool(a1))
        a3 = e.layer2(a2)
        a4 = e.layer3(a3)
        return a1, a2, a3, a4, e.layer4(a4)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Calcula o logit de fissura de cada pixel.

        Args:
            x: Imagens RGB em [0, 1], formato (N, 3, H, W).

        Returns:
            Logits no formato (N, 1, H, W), sem sigmoide.
        """
        a1, a2, a3, a4, x = self.caracteristicas(x)
        for bloco, atalho in zip(self.decoder, (a4, a3, a2, a1, None), strict=True):
            x = bloco(x, atalho)
        return self.cabeca(x)
