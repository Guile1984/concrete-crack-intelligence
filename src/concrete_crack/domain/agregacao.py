"""Agregação das métricas de um conjunto de imagens (A62, item 5, e A63).

Funções puras, sem disco. Pelo recorte único da A63, as quatro métricas de
segmentação só usam as imagens com fissura no gabarito; as imagens sem
fissura ficam para a taxa de alarme falso. A agregação principal é a média
por imagem, que ignora os valores indefinidos e conta quantos foram; o
complemento é a soma global, com as métricas calculadas sobre as contagens
somadas.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .metricas import (
    Contagens,
    ContagensEsqueleto,
    cldice_de_contagens,
    dice,
    precisao,
    recall,
)


@dataclass(frozen=True, slots=True)
class ImagemAvaliada:
    """As contagens de uma imagem avaliada.

    Attributes:
        imagem: Identificador da imagem.
        pixels: Contagens de pixels (VP, FP, FN, VN).
        esqueletos: Contagens dos esqueletos, para o clDice.
    """

    imagem: str
    pixels: Contagens
    esqueletos: ContagensEsqueleto

    def __post_init__(self) -> None:
        """Recusa contagens de pixels e de esqueletos que se contradizem."""
        if self.tem_fissura != (self.esqueletos.d_s > 0):
            raise ValueError(
                f"{self.imagem}: o gabarito tem fissura só num dos dois tipos "
                "de contagem."
            )

    @property
    def tem_fissura(self) -> bool:
        """Se o gabarito tem fissura (VP + FN > 0)."""
        return self.pixels.vp + self.pixels.fn > 0


@dataclass(frozen=True, slots=True)
class Media:
    """Média por imagem de uma métrica.

    Attributes:
        valor: A média dos valores definidos, ou ``None`` se não houver nenhum.
        n_definidas: Imagens que entraram na média.
        n_indefinidas: Imagens em que a métrica era 0/0 e ficaram de fora.
    """

    valor: float | None
    n_definidas: int
    n_indefinidas: int


def media(valores: Sequence[float | None]) -> Media:
    """Média dos valores definidos, com a contagem dos indefinidos.

    Args:
        valores: Um valor por imagem; ``None`` é indefinido.

    Returns:
        A média e as duas contagens.
    """
    definidos = [valor for valor in valores if valor is not None]
    valor = math.fsum(definidos) / len(definidos) if definidos else None
    return Media(valor, len(definidos), len(valores) - len(definidos))


@dataclass(frozen=True, slots=True)
class Resumo:
    """As métricas de segmentação de um conjunto de imagens.

    Attributes:
        n_imagens: Imagens avaliadas, com e sem fissura.
        n_com_fissura: Imagens do recorte da A63 (gabarito com fissura).
        precisao: Média por imagem da precisão.
        recall: Média por imagem do recall.
        dice: Média por imagem do Dice.
        cldice: Média por imagem do clDice.
        precisao_global: Precisão das contagens somadas.
        recall_global: Recall das contagens somadas.
        dice_global: Dice das contagens somadas.
        cldice_global: clDice das contagens de esqueleto somadas.
    """

    n_imagens: int
    n_com_fissura: int
    precisao: Media
    recall: Media
    dice: Media
    cldice: Media
    precisao_global: float | None
    recall_global: float | None
    dice_global: float | None
    cldice_global: float | None


def resumir(imagens: Sequence[ImagemAvaliada]) -> Resumo:
    """Agrega as métricas de segmentação no recorte da A63.

    Args:
        imagens: As imagens avaliadas, com e sem fissura no gabarito.

    Returns:
        As médias por imagem e as métricas globais.

    Raises:
        ValueError: Se alguma imagem aparecer mais de uma vez.
    """
    nomes = [imagem.imagem for imagem in imagens]
    if len(set(nomes)) != len(nomes):
        raise ValueError("Cada imagem deve aparecer uma única vez.")
    recorte = [imagem for imagem in imagens if imagem.tem_fissura]
    pixels = Contagens(
        vp=sum(i.pixels.vp for i in recorte),
        fp=sum(i.pixels.fp for i in recorte),
        fn=sum(i.pixels.fn for i in recorte),
        vn=sum(i.pixels.vn for i in recorte),
    )
    esqueletos = ContagensEsqueleto(
        n_p=sum(i.esqueletos.n_p for i in recorte),
        d_p=sum(i.esqueletos.d_p for i in recorte),
        n_s=sum(i.esqueletos.n_s for i in recorte),
        d_s=sum(i.esqueletos.d_s for i in recorte),
    )
    return Resumo(
        n_imagens=len(imagens),
        n_com_fissura=len(recorte),
        precisao=media([precisao(i.pixels) for i in recorte]),
        recall=media([recall(i.pixels) for i in recorte]),
        dice=media([dice(i.pixels) for i in recorte]),
        cldice=media([cldice_de_contagens(i.esqueletos) for i in recorte]),
        precisao_global=precisao(pixels),
        recall_global=recall(pixels),
        dice_global=dice(pixels),
        cldice_global=cldice_de_contagens(esqueletos),
    )
