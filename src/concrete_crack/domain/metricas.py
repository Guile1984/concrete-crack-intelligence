"""Métricas de segmentação de uma imagem, conforme a A62.

Funções puras sobre máscaras booleanas, sem disco. As métricas saem das
quatro contagens de pixels; quando a divisão seria 0/0, o resultado é
``None`` (indefinido), e a imagem sai da média daquela métrica (A62, item 4).
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class Contagens:
    """As quatro contagens de pixels de uma imagem.

    Attributes:
        vp: Verdadeiros positivos (fissura prevista onde há fissura).
        fp: Falsos positivos (fissura prevista onde é fundo).
        fn: Falsos negativos (fundo previsto onde há fissura).
        vn: Verdadeiros negativos (fundo previsto onde é fundo).
    """

    vp: int
    fp: int
    fn: int
    vn: int

    def __post_init__(self) -> None:
        """Recusa contagens negativas."""
        if min(self.vp, self.fp, self.fn, self.vn) < 0:
            raise ValueError("As contagens não podem ser negativas.")

    @property
    def total(self) -> int:
        """Quantidade de pixels da imagem."""
        return self.vp + self.fp + self.fn + self.vn


def contar(previsao: np.ndarray, gabarito: np.ndarray) -> Contagens:
    """Conta VP, FP, FN e VN de uma previsão contra o gabarito.

    Args:
        previsao: Máscara booleana prevista.
        gabarito: Máscara booleana do gabarito, do mesmo formato.

    Returns:
        As quatro contagens.

    Raises:
        ValueError: Se alguma máscara não for booleana ou os formatos forem
            diferentes.
    """
    if previsao.dtype != np.bool_ or gabarito.dtype != np.bool_:
        raise ValueError("As máscaras devem ser booleanas.")
    if previsao.shape != gabarito.shape:
        raise ValueError(
            f"Formatos diferentes: previsão {previsao.shape}, "
            f"gabarito {gabarito.shape}."
        )
    vp = int(np.count_nonzero(previsao & gabarito))
    fp = int(np.count_nonzero(previsao & ~gabarito))
    fn = int(np.count_nonzero(~previsao & gabarito))
    return Contagens(vp, fp, fn, previsao.size - vp - fp - fn)


def precisao(contagens: Contagens) -> float | None:
    """Fração da fissura prevista que é fissura de verdade.

    Returns:
        VP / (VP + FP), ou ``None`` se nada foi previsto como fissura.
    """
    previstos = contagens.vp + contagens.fp
    return contagens.vp / previstos if previstos else None


def recall(contagens: Contagens) -> float | None:
    """Fração da fissura do gabarito que a previsão encontrou.

    Returns:
        VP / (VP + FN), ou ``None`` se o gabarito não tem fissura.
    """
    reais = contagens.vp + contagens.fn
    return contagens.vp / reais if reais else None


def dice(contagens: Contagens) -> float | None:
    """Sobreposição entre previsão e gabarito (média harmônica de P e R).

    Returns:
        2 VP / (2 VP + FP + FN), ou ``None`` se o gabarito não tem fissura:
        essa imagem fica fora do Dice e conta na taxa de alarme falso (A62).
    """
    if contagens.vp + contagens.fn == 0:
        return None
    return 2 * contagens.vp / (2 * contagens.vp + contagens.fp + contagens.fn)


def acuracia(contagens: Contagens) -> float:
    """Fração de pixels classificados corretamente.

    Só aparece no relatório do preditor trivial, como exemplo de métrica
    enganosa quando a fissura é rara (A62, item 2).

    Returns:
        (VP + VN) / total.
    """
    return (contagens.vp + contagens.vn) / contagens.total
