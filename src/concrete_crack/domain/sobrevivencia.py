"""Medição descritiva dos tiles e da sobrevivência das fissuras (A52, item 8).

Funções puras sobre máscaras booleanas, sem disco. A fissura de cada tile é
contada na escala nativa; a sobrevivência é medida pela ida e volta: reduzir a
máscara, aplicar uma regra de volta ao binário e ampliar de novo, repetindo
cada pixel reduzido num bloco de fator x fator, para comparar com o original
na resolução nativa (A52, item 5).
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .pixels import recortar, somar_blocos

MAIORIA = "maioria"
QUALQUER = "qualquer"


def fissura_por_tile(
    mascara: np.ndarray, xs: Sequence[int], ys: Sequence[int], lado: int
) -> list[int]:
    """Conta os pixels de fissura de cada tile da grade, em ordem de leitura.

    Args:
        mascara: Máscara booleana na escala nativa.
        xs: Posições das colunas da grade.
        ys: Posições das linhas da grade.
        lado: Lado do tile.

    Returns:
        A contagem de cada tile, linha a linha.
    """
    return [int(recortar(mascara, x, y, lado).sum()) for y in ys for x in xs]


def ida_e_volta(mascara: np.ndarray, fator: int, regra: str) -> np.ndarray:
    """Reduz a máscara, aplica a regra e amplia de volta à escala nativa.

    Args:
        mascara: Máscara booleana na escala nativa.
        fator: Fator de redução.
        regra: ``"maioria"`` (pelo menos metade do bloco é fissura) ou
            ``"qualquer"`` (pelo menos um pixel do bloco é fissura).

    Returns:
        Máscara booleana do mesmo tamanho da original.

    Raises:
        ValueError: Se a regra for desconhecida, a máscara não for booleana ou
            o fator for inválido.
    """
    if mascara.dtype != np.bool_:
        raise ValueError("A máscara deve ser booleana.")
    contagem = somar_blocos(mascara, fator)
    if regra == MAIORIA:
        reduzida = 2 * contagem >= fator * fator
    elif regra == QUALQUER:
        reduzida = contagem >= 1
    else:
        raise ValueError(f"Regra desconhecida: {regra!r}.")
    return np.repeat(np.repeat(reduzida, fator, axis=0), fator, axis=1)


@dataclass(frozen=True, slots=True)
class Sobrevivencia:
    """A comparação de uma máscara com a sua ida e volta.

    Attributes:
        fissura: Pixels de fissura da máscara original.
        preservados: Pixels de fissura que continuam marcados na volta.
        a_mais: Pixels de fundo que passaram a ser marcados na volta.
    """

    fissura: int
    preservados: int
    a_mais: int


def comparar(original: np.ndarray, volta: np.ndarray) -> Sobrevivencia:
    """Compara a máscara original com a máscara depois da ida e volta.

    Args:
        original: Máscara booleana original.
        volta: Máscara booleana depois da ida e volta, do mesmo tamanho.

    Returns:
        As contagens de fissura, preservados e pixels a mais.

    Raises:
        ValueError: Se as duas máscaras tiverem tamanhos diferentes.
    """
    if original.shape != volta.shape:
        raise ValueError("As máscaras têm tamanhos diferentes.")
    return Sobrevivencia(
        fissura=int(original.sum()),
        preservados=int((original & volta).sum()),
        a_mais=int((volta & ~original).sum()),
    )


def quartis(valores: Sequence[float]) -> tuple[float, float, float]:
    """Calcula 1º quartil, mediana e 3º quartil, com interpolação linear.

    Args:
        valores: Os valores, não vazios.

    Returns:
        (1º quartil, mediana, 3º quartil).

    Raises:
        ValueError: Se não houver valores.
    """
    if not valores:
        raise ValueError("Não há valores para os quartis.")
    q1, mediana, q3 = np.quantile(np.asarray(valores, dtype=float), (0.25, 0.5, 0.75))
    return float(q1), float(mediana), float(q3)
