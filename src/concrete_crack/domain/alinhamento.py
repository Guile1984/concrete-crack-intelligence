"""Marcação da fissura numa máscara e resumo do teste de alinhamento.

Funções puras: recebem matrizes e números, sem acesso a disco.
"""

import statistics
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


def marcar_fissura(cinza: np.ndarray, desvio_minimo: int) -> np.ndarray:
    """Marca como fissura os pixels que diferem do fundo da máscara.

    O fundo é o valor mediano da imagem (a maior parte da máscara é fundo), o
    que dispensa saber se a fissura é branca sobre preto ou o inverso. Pixels
    de fissura fina, que a redução deixou acinzentados, ainda diferem do fundo.

    Args:
        cinza: Máscara em tons de cinza (linhas x colunas), não vazia.
        desvio_minimo: Diferença mínima, em níveis de cinza, para contar como
            fissura; deve ser positiva.

    Returns:
        Matriz booleana de mesma forma; True marca a fissura.

    Raises:
        ValueError: Se ``desvio_minimo`` não for positivo ou a imagem for vazia.
    """
    if desvio_minimo <= 0:
        raise ValueError("desvio_minimo deve ser positivo.")
    if cinza.size == 0:
        raise ValueError("A imagem está vazia.")
    fundo = np.median(cinza)
    return np.abs(cinza.astype(np.float64) - fundo) >= desvio_minimo


@dataclass(frozen=True, slots=True)
class ResumoVantagens:
    """Resumo das vantagens da orientação EXIF num grupo de pares.

    Attributes:
        n: Quantidade de pares avaliados.
        positivas: Quantos têm vantagem estritamente positiva.
        mediana: Mediana das vantagens.
        minimo: Menor vantagem.
        maximo: Maior vantagem.
    """

    n: int
    positivas: int
    mediana: float
    minimo: float
    maximo: float

    @property
    def fracao_positiva(self) -> float:
        """Proporção de pares com vantagem positiva."""
        return self.positivas / self.n


def resumir_vantagens(vantagens: Sequence[float]) -> ResumoVantagens:
    """Resume uma lista de vantagens.

    Args:
        vantagens: Uma vantagem por par; não pode ser vazia.

    Returns:
        O resumo. Vantagem zero não conta como positiva.

    Raises:
        ValueError: Se a lista for vazia.
    """
    if not vantagens:
        raise ValueError("Não há vantagens para resumir.")
    return ResumoVantagens(
        n=len(vantagens),
        positivas=sum(1 for v in vantagens if v > 0),
        mediana=float(statistics.median(vantagens)),
        minimo=float(min(vantagens)),
        maximo=float(max(vantagens)),
    )
