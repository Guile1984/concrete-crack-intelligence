"""Extração de embeddings de imagens com uma rede do timm (DINOv2 ViT-S/14).

Único módulo do projeto que usa o timm. A rede recebe a imagem inteira,
redimensionada para um quadrado sem corte e normalizada com a média e o desvio
declarados pelo próprio modelo. A rede pode ser criada sem pesos (para testar o
formato sem baixar nada) ou com os pesos de um arquivo local, cujo SHA-256 é
conferido antes do carregamento.
"""

from pathlib import Path

import numpy as np
import timm
import torch
from torch.nn import functional

from .arquivos import sha256_do_arquivo

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


def _montar(modelo: torch.nn.Module, lado: int) -> ExtratorEmbeddings:
    """Envolve a rede do timm no extrator, com a normalização declarada por ela."""
    configuracao = modelo.pretrained_cfg
    return ExtratorEmbeddings(
        modelo,
        lado,
        tuple(configuracao["mean"]),
        tuple(configuracao["std"]),
        modelo.num_features,
    )


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
    return _montar(modelo, lado)


def criar_extrator_com_pesos(
    nome_modelo: str, lado: int, caminho_pesos: Path, sha256_esperado: str
) -> ExtratorEmbeddings:
    """Cria o extrator com os pesos de um arquivo local, conferindo o hash antes.

    O carregamento é estrito: se faltar ou sobrar qualquer parâmetro em relação
    à arquitetura, ele falha, em vez de seguir com uma rede em parte aleatória.
    Nada é baixado: o arquivo precisa já estar em disco.

    Args:
        nome_modelo: Nome do modelo no timm.
        lado: Lado da imagem quadrada na entrada.
        caminho_pesos: Arquivo de pesos (safetensors) em disco.
        sha256_esperado: Hash registrado no manifesto dos pesos.

    Returns:
        O extrator com os pesos carregados.

    Raises:
        FileNotFoundError: Se o arquivo de pesos não existir.
        ValueError: Se o hash do arquivo for diferente do esperado.
        RuntimeError: Se os parâmetros do arquivo não corresponderem à rede.
    """
    obtido = sha256_do_arquivo(caminho_pesos)
    if obtido != sha256_esperado:
        raise ValueError(
            f"O hash dos pesos não confere: esperado {sha256_esperado[:12]}, "
            f"obtido {obtido[:12]}."
        )
    modelo = timm.create_model(
        nome_modelo,
        pretrained=True,
        num_classes=0,
        img_size=lado,
        pretrained_cfg_overlay={"file": str(caminho_pesos)},
    )
    return _montar(modelo, lado)
