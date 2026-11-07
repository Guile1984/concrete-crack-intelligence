"""Extração de embeddings de imagens com uma rede do timm (DINOv2 ViT-S/14).

Único módulo do projeto que usa o timm. A rede recebe a imagem inteira,
redimensionada para um quadrado sem corte e normalizada com a média e o desvio
declarados pelo próprio modelo. O carregamento dos pesos pré-treinados, com
conferência do hash, fica em outro passo; aqui a rede pode ser criada sem
pesos, o que permite testar o formato sem baixar nada.
"""

import numpy as np
import timm
import torch
from torch.nn import functional

CANAIS_RGB = 3


class ExtratorEmbeddings:
    """Transforma uma imagem RGB num vetor de características.

    Attributes:
        modelo: A rede, em modo de avaliação.
        lado: Lado da imagem quadrada na entrada da rede.
        media: Média por canal (R, G, B) da normalização, na escala 0 a 1.
        desvio: Desvio por canal da normalização, na escala 0 a 1.
        dimensao: Quantidade de números do vetor de saída.
    """

    def __init__(
        self,
        modelo: torch.nn.Module,
        lado: int,
        media: tuple[float, float, float],
        desvio: tuple[float, float, float],
        dimensao: int,
    ) -> None:
        """Guarda a rede e os parâmetros do pré-processamento.

        Args:
            modelo: Rede que devolve um vetor por imagem (sem cabeça de classes).
            lado: Lado da imagem quadrada na entrada.
            media: Média por canal (R, G, B) da normalização, na escala 0 a 1.
            desvio: Desvio por canal da normalização, na escala 0 a 1.
            dimensao: Tamanho do vetor que a rede devolve.
        """
        self.modelo = modelo.eval()
        self.lado = lado
        self.media = media
        self.desvio = desvio
        self.dimensao = dimensao
        self._media = torch.tensor(media).view(1, CANAIS_RGB, 1, 1)
        self._desvio = torch.tensor(desvio).view(1, CANAIS_RGB, 1, 1)

    def preparar(self, rgb: np.ndarray) -> torch.Tensor:
        """Converte a imagem no tensor de entrada da rede.

        A imagem inteira é redimensionada para lado x lado (bicúbica, com
        antisserrilhamento), sem corte, e normalizada por canal.

        Args:
            rgb: Imagem uint8 de forma (altura, largura, 3).

        Returns:
            Tensor float32 de forma (1, 3, lado, lado).

        Raises:
            ValueError: Se a imagem não for uint8 com 3 canais.
        """
        if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != CANAIS_RGB:
            raise ValueError("A imagem deve ser uint8 de forma (altura, largura, 3).")
        tensor = torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1)
        tensor = tensor.unsqueeze(0).float() / 255.0
        tensor = functional.interpolate(
            tensor,
            size=(self.lado, self.lado),
            mode="bicubic",
            align_corners=False,
            antialias=True,
        )
        return (tensor - self._media) / self._desvio

    def extrair(self, rgb: np.ndarray) -> np.ndarray:
        """Calcula o embedding de uma imagem.

        Args:
            rgb: Imagem uint8 de forma (altura, largura, 3).

        Returns:
            Vetor float64 de ``dimensao`` números.
        """
        with torch.no_grad():
            saida = self.modelo(self.preparar(rgb))
        return saida[0].double().numpy()


def criar_extrator(nome_modelo: str, lado: int) -> ExtratorEmbeddings:
    """Cria o extrator com a arquitetura do timm, ainda sem pesos pré-treinados.

    Args:
        nome_modelo: Nome do modelo no timm, como em ``REGRAS.modelo_embeddings``.
        lado: Lado da imagem quadrada na entrada.

    Returns:
        O extrator, com pesos aleatórios e a normalização declarada pelo modelo.
    """
    modelo = timm.create_model(
        nome_modelo, pretrained=False, num_classes=0, img_size=lado
    )
    configuracao = modelo.pretrained_cfg
    return ExtratorEmbeddings(
        modelo,
        lado,
        tuple(configuracao["mean"]),
        tuple(configuracao["std"]),
        modelo.num_features,
    )
