"""Medição da área de fissura das máscaras em função do limiar de binarização.

Funções puras sobre matrizes numpy e contagens, sem acesso a disco. Os limiares
e as regras de decisão vêm de fora (``config/regras.py``), pois o domínio não
importa a configuração.

O desvio de um pixel é a distância dele ao fundo da máscara, o valor mediano da
imagem (como em ``marcar_fissura`` e ``intensidade_da_mascara``), o que dispensa
saber se a fissura é clara sobre escuro ou o inverso. Como a mediana pode cair
entre dois níveis (por exemplo 3,5), o desvio é arredondado para cima: assim,
para um limiar inteiro T, "desvio >= T" e "desvio arredondado >= T" coincidem.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

N_NIVEIS = 256


def contagem_por_desvio(cinza: np.ndarray) -> np.ndarray:
    """Conta os pixels de uma máscara por desvio do fundo (0 a 255).

    Args:
        cinza: Máscara em tons de cinza uint8 (linhas x colunas), não vazia.

    Returns:
        Vetor int64 de 256 posições; a posição k conta os pixels cujo desvio
        do fundo, arredondado para cima, é k. A soma é o número de pixels.

    Raises:
        ValueError: Se a imagem for vazia ou não for uint8.
    """
    if cinza.dtype != np.uint8:
        raise ValueError("A máscara deve ser uint8.")
    if cinza.size == 0:
        raise ValueError("A imagem está vazia.")
    fundo = np.median(cinza)
    desvios = np.ceil(np.abs(cinza.astype(np.float64) - fundo)).astype(np.int64)
    return np.bincount(desvios.ravel(), minlength=N_NIVEIS)


def contar_acima(contagem: np.ndarray, limiar: int) -> int:
    """Conta os pixels com desvio do fundo maior ou igual ao limiar.

    Args:
        contagem: Contagem por desvio, de 256 posições.
        limiar: Limiar inteiro de 1 a 255.

    Returns:
        A quantidade de pixels com desvio >= limiar.

    Raises:
        ValueError: Se a contagem não tiver 256 posições ou o limiar estiver
            fora de 1 a 255.
    """
    if contagem.shape != (N_NIVEIS,):
        raise ValueError("A contagem deve ter 256 posições.")
    if not 1 <= limiar <= N_NIVEIS - 1:
        raise ValueError("O limiar deve estar entre 1 e 255.")
    return int(contagem[limiar:].sum())


def fracao_de_fissura(contagem: np.ndarray, limiar: int) -> float:
    """Calcula a fração de pixels de fissura (desvio >= limiar) numa contagem.

    Args:
        contagem: Contagem por desvio de uma máscara, ou a soma de várias.
        limiar: Limiar inteiro de 1 a 255.

    Returns:
        A fração de 0 a 1 dos pixels que viram fissura.

    Raises:
        ValueError: Se a contagem for inválida, vazia ou o limiar for inválido.
    """
    total = int(contagem.sum())
    if total == 0:
        raise ValueError("A contagem não tem pixels.")
    return contar_acima(contagem, limiar) / total


def e_anomala(contagem: np.ndarray, limiar: int, fracao_maxima: float) -> bool:
    """Diz se uma máscara tem fissura demais no limiar (suspeita de inversão).

    Args:
        contagem: Contagem por desvio de uma máscara.
        limiar: Limiar de binarização.
        fracao_maxima: Fração acima da qual a máscara é anômala.

    Returns:
        Verdadeiro se a fração de fissura for estritamente maior que o máximo.
    """
    return fracao_de_fissura(contagem, limiar) > fracao_maxima


@dataclass(frozen=True, slots=True)
class ResumoPatamar:
    """A curva de área de fissura e a classificação da robustez.

    Attributes:
        limiares: A grade de limiares usada.
        areas: Fração de pixels de fissura em cada limiar da grade.
        razao: Área no limiar alto dividida pela área no limiar baixo.
        robusta: Verdadeiro se a razão atinge o mínimo pré-registrado.
    """

    limiares: tuple[int, ...]
    areas: tuple[float, ...]
    razao: float
    robusta: bool


def avaliar_patamar(
    contagem: np.ndarray,
    limiares: Sequence[int],
    baixo: int,
    alto: int,
    razao_minima: float,
) -> ResumoPatamar:
    """Mede a curva de área e classifica a binarização como robusta ou sensível.

    A binarização é robusta quando a área no limiar alto é pelo menos
    ``razao_minima`` vezes a área no limiar baixo.

    Args:
        contagem: Contagem agregada por desvio (soma das máscaras).
        limiares: Grade de limiares inteiros de 1 a 255.
        baixo: Limiar baixo do patamar, presente na grade.
        alto: Limiar alto do patamar, presente na grade e maior que o baixo.
        razao_minima: Razão mínima para ser robusta, em (0, 1].

    Returns:
        O resumo com a curva, a razão e a classificação.

    Raises:
        ValueError: Se baixo ou alto não estiverem na grade, ``baixo`` não for
            menor que ``alto`` ou não houver pixel de fissura no limiar baixo.
    """
    grade = tuple(limiares)
    if baixo not in grade or alto not in grade:
        raise ValueError("Os limiares do patamar precisam estar na grade.")
    if baixo >= alto:
        raise ValueError("O limiar baixo do patamar deve ser menor que o alto.")
    area_baixa = contar_acima(contagem, baixo)
    if area_baixa == 0:
        raise ValueError("Não há pixels de fissura no limiar baixo do patamar.")
    razao = contar_acima(contagem, alto) / area_baixa
    areas = tuple(fracao_de_fissura(contagem, limiar) for limiar in grade)
    return ResumoPatamar(grade, areas, razao, razao >= razao_minima)
