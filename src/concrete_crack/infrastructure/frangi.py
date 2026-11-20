"""Adaptador Frangi do port Segmentador, conforme a A65 (itens 3 a 5).

Tons de cinza, subtração do fundo, Frangi multiescala com a constante c
absoluta (nunca calculada por imagem) e normalização por σ², feita chamando o
filtro uma escala por vez com γ = c / σ². O máximo entre as escalas já fica em
[0, 1] pela própria fórmula do filtro.
"""

from dataclasses import dataclass

import numpy as np
from skimage.color import rgb2gray
from skimage.filters import frangi, gaussian


@dataclass(frozen=True, slots=True)
class ParametrosFrangi:
    """Parâmetros de uma execução do Frangi.

    Attributes:
        sigmas: Escalas do filtro, em pixels, crescentes e sem repetição.
        sigma_fundo: σ do borrão gaussiano que estima o fundo; 0 desliga a
            correção de iluminação.
        c: Constante da "estrutura forte", já normalizada por σ² (A65, item
            4); vem da regra do treino, nunca da imagem.
        beta: Penalidade das formas arredondadas (``REGRAS.beta_frangi``).
    """

    sigmas: tuple[float, ...]
    sigma_fundo: float
    c: float
    beta: float

    def __post_init__(self) -> None:
        """Recusa parâmetros fora dos valores válidos."""
        if not self.sigmas or any(sigma <= 0 for sigma in self.sigmas):
            raise ValueError("As escalas devem ser positivas e não vazias.")
        if list(self.sigmas) != sorted(set(self.sigmas)):
            raise ValueError("As escalas devem ser crescentes e sem repetição.")
        if self.sigma_fundo < 0:
            raise ValueError("O σ do fundo não pode ser negativo.")
        if self.c <= 0 or self.beta <= 0:
            raise ValueError("O c e o β devem ser positivos.")


def cinza_corrigido(imagem: np.ndarray, sigma_fundo: float) -> np.ndarray:
    """Converte para cinza em [0, 1] e subtrai o fundo estimado.

    Args:
        imagem: Imagem RGB ``uint8`` de formato (altura, largura, 3).
        sigma_fundo: σ do borrão que estima o fundo; 0 não subtrai nada.

    Returns:
        A imagem em cinza, ``float64``, com o fundo subtraído.

    Raises:
        ValueError: Se a imagem não for RGB ``uint8``.
    """
    if imagem.dtype != np.uint8 or imagem.ndim != 3 or imagem.shape[2] != 3:
        raise ValueError("A imagem deve ser RGB uint8 (altura, largura, 3).")
    cinza = rgb2gray(imagem)
    if sigma_fundo == 0:
        return cinza
    return cinza - gaussian(cinza, sigma=sigma_fundo)


class SegmentadorFrangi:
    """O baseline clássico atrás do port ``Segmentador``."""

    def __init__(self, parametros: ParametrosFrangi) -> None:
        """Guarda os parâmetros congelados.

        Args:
            parametros: Os parâmetros da execução.
        """
        self.parametros = parametros

    def mapear(self, imagem: np.ndarray) -> np.ndarray:
        """Calcula o mapa de resposta do Frangi.

        Args:
            imagem: Imagem RGB ``uint8`` inteira, de formato (altura, largura,
                3).

        Returns:
            Mapa ``float64`` (altura, largura) em [0, 1]: o máximo, entre as
            escalas, da resposta com a Hessiana normalizada por σ².
        """
        p = self.parametros
        corrigida = cinza_corrigido(imagem, p.sigma_fundo)
        mapa = np.zeros(corrigida.shape)
        for sigma in p.sigmas:
            resposta = frangi(
                corrigida,
                sigmas=[sigma],
                beta=p.beta,
                gamma=p.c / sigma**2,
                black_ridges=True,
            )
            mapa = np.maximum(mapa, resposta)
        return mapa
