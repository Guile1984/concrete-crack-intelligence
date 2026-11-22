"""A grade de ajuste do Frangi e as operações de cada configuração (A66).

Funções puras, sem disco. A grade é o produto das faixas de escalas, dos σ do
fundo, dos limiares e dos tamanhos mínimos, nesta ordem, que é também a
ordem do desempate (A66, item 4). O mapa de uma faixa é o máximo dos mapas
das suas escalas (A66, item 1).
"""

import itertools
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .posprocessamento import binarizar, remover_componentes_pequenos


@dataclass(frozen=True, slots=True)
class ConfiguracaoFrangi:
    """Uma configuração da grade.

    Attributes:
        faixa: As escalas σ cujo máximo forma o mapa.
        sigma_fundo: σ do borrão do fundo.
        limiar: Limiar aplicado ao mapa.
        tamanho_minimo: Tamanho mínimo de componente, em pixels.
    """

    faixa: tuple[float, ...]
    sigma_fundo: float
    limiar: float
    tamanho_minimo: int


def configuracoes_da_grade(
    faixas: Sequence[tuple[float, ...]],
    fundos: Sequence[float],
    limiares: Sequence[float],
    tamanhos: Sequence[int],
) -> tuple[ConfiguracaoFrangi, ...]:
    """Monta todas as configurações, na ordem da grade.

    A faixa varia mais devagar e o tamanho mínimo mais depressa, como num
    hodômetro: a ordem dos parâmetros é a da A66, item 2.

    Args:
        faixas: Faixas de escalas.
        fundos: σ do fundo.
        limiares: Limiares.
        tamanhos: Tamanhos mínimos de componente.

    Returns:
        As configurações, na ordem do desempate.
    """
    return tuple(
        ConfiguracaoFrangi(faixa, fundo, limiar, tamanho)
        for faixa, fundo, limiar, tamanho in itertools.product(
            faixas, fundos, limiares, tamanhos
        )
    )


def combinar_faixa(mapas: Sequence[np.ndarray]) -> np.ndarray:
    """Combina os mapas das escalas de uma faixa pelo máximo, pixel a pixel.

    Args:
        mapas: Um mapa por escala da faixa, todos do mesmo formato.

    Returns:
        O mapa da faixa.

    Raises:
        ValueError: Se não houver mapas ou os formatos forem diferentes.
    """
    if not mapas:
        raise ValueError("Uma faixa precisa de pelo menos um mapa.")
    if len({mapa.shape for mapa in mapas}) != 1:
        raise ValueError("Os mapas de uma faixa devem ter o mesmo formato.")
    return np.maximum.reduce(list(mapas))


def segmentar(
    mapa: np.ndarray, limiar: float, tamanho_minimo: int, conectividade: int
) -> np.ndarray:
    """Aplica o limiar e a limpeza de componentes, como em todo segmentador.

    Args:
        mapa: Mapa de score em [0, 1].
        limiar: Limiar da configuração.
        tamanho_minimo: Tamanho mínimo de componente da configuração.
        conectividade: ``REGRAS.conectividade_componentes``.

    Returns:
        A máscara prevista.
    """
    return remover_componentes_pequenos(
        binarizar(mapa, limiar), tamanho_minimo, conectividade
    )
