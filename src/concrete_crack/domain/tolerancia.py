"""F1 com tolerância k, conforme a A64.

Funções puras sobre máscaras booleanas, sem disco. Um pixel previsto conta
como acerto se estiver a distância euclidiana até k de algum pixel do
gabarito, e vice-versa. Sem pareamento um a um: uma faixa larga em volta de
uma fissura fina é toda perdoada, por isso o F1 com tolerância é lido junto
com o Dice e nunca decide nada (A64, item 4). Com k = 0, é exatamente o Dice.
"""

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt


@dataclass(frozen=True, slots=True)
class ContagensTolerancia:
    """As quatro contagens do F1 com tolerância de uma imagem.

    Attributes:
        n_p: Pixels previstos a até k de algum pixel do gabarito.
        d_p: Pixels previstos.
        n_s: Pixels do gabarito a até k de algum pixel previsto.
        d_s: Pixels do gabarito.
    """

    n_p: int
    d_p: int
    n_s: int
    d_s: int

    def __post_init__(self) -> None:
        """Recusa contagens que nenhum par de máscaras produziria."""
        if not (0 <= self.n_p <= self.d_p and 0 <= self.n_s <= self.d_s):
            raise ValueError("Cada parte deve estar entre 0 e a sua máscara.")
        if (self.d_p == 0 and self.n_s > 0) or (self.d_s == 0 and self.n_p > 0):
            raise ValueError("Uma máscara vazia não pode ter vizinhos.")


def vizinhanca(mascara: np.ndarray, k: int) -> np.ndarray:
    """Pixels a distância euclidiana até k de algum pixel da máscara.

    Args:
        mascara: Máscara booleana.
        k: Tolerância, em pixels, inteira e maior ou igual a 0.

    Returns:
        A máscara "engordada" por um disco de raio k, ou uma máscara vazia se
        a máscara de entrada for vazia.

    Raises:
        ValueError: Se a máscara não for booleana ou k for negativo.
    """
    if mascara.dtype != np.bool_:
        raise ValueError("A máscara deve ser booleana.")
    if k < 0:
        raise ValueError("A tolerância k deve ser maior ou igual a 0.")
    if not mascara.any():
        return np.zeros(mascara.shape, dtype=bool)
    return distance_transform_edt(~mascara) <= k


def contar_tolerancia(
    previsao: np.ndarray, gabarito: np.ndarray, k: int
) -> ContagensTolerancia:
    """Conta as partes do F1 com tolerância de uma previsão.

    Args:
        previsao: Máscara booleana prevista (P).
        gabarito: Máscara booleana do gabarito (L), do mesmo formato.
        k: Tolerância, em pixels; o valor do projeto é pré-registrado antes da
            Sprint 4, sem padrão aqui.

    Returns:
        As quatro contagens.

    Raises:
        ValueError: Se as máscaras não forem booleanas, tiverem formatos
            diferentes, ou se k for negativo.
    """
    if previsao.shape != gabarito.shape:
        raise ValueError(
            f"Formatos diferentes: previsão {previsao.shape}, "
            f"gabarito {gabarito.shape}."
        )
    perto_do_gabarito = vizinhanca(gabarito, k)
    perto_da_previsao = vizinhanca(previsao, k)
    return ContagensTolerancia(
        n_p=int(np.count_nonzero(previsao & perto_do_gabarito)),
        d_p=int(np.count_nonzero(previsao)),
        n_s=int(np.count_nonzero(gabarito & perto_da_previsao)),
        d_s=int(np.count_nonzero(gabarito)),
    )


def precisao_tolerante(contagens: ContagensTolerancia) -> float | None:
    """Fração dos pixels previstos que ficam perto do gabarito.

    Returns:
        n_p / d_p, ou ``None`` se nada foi previsto como fissura.
    """
    return contagens.n_p / contagens.d_p if contagens.d_p else None


def recall_tolerante(contagens: ContagensTolerancia) -> float | None:
    """Fração dos pixels do gabarito que ficam perto da previsão.

    Returns:
        n_s / d_s, ou ``None`` se o gabarito não tem fissura.
    """
    return contagens.n_s / contagens.d_s if contagens.d_s else None


def f1_tolerante(contagens: ContagensTolerancia) -> float | None:
    """F1 com tolerância: média harmônica de Ptol e Rtol.

    Calculado numa única divisão de inteiros: 2 n_p n_s / (n_p d_s + n_s d_p).

    Returns:
        O F1; ``None`` se o gabarito não tem fissura, e 0 se nada fica perto,
        o que inclui a previsão vazia (A64, item 5).
    """
    c = contagens
    if c.d_s == 0:
        return None
    if c.n_p == 0 and c.n_s == 0:
        return 0.0
    return 2 * c.n_p * c.n_s / (c.n_p * c.d_s + c.n_s * c.d_p)
