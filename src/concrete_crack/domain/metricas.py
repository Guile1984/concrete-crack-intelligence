"""Métricas de segmentação de uma imagem, conforme a A62.

Funções puras sobre máscaras booleanas, sem disco. As métricas saem das
quatro contagens de pixels; quando a divisão seria 0/0, o resultado é
``None`` (indefinido), e a imagem sai da média daquela métrica (A62, item 4).
O clDice sai dos esqueletos, em duas camadas: a fórmula recebe esqueletos
prontos, e o esqueleto real vem do ``skeletonize`` do scikit-image (A62,
itens 3 e 9).
"""

from dataclasses import dataclass

import numpy as np
from skimage.morphology import skeletonize


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


def _conferir_mascaras(previsao: np.ndarray, gabarito: np.ndarray) -> None:
    """Recusa máscaras que não sejam booleanas ou que tenham formatos diferentes."""
    if previsao.dtype != np.bool_ or gabarito.dtype != np.bool_:
        raise ValueError("As máscaras devem ser booleanas.")
    if previsao.shape != gabarito.shape:
        raise ValueError(
            f"Formatos diferentes: previsão {previsao.shape}, "
            f"gabarito {gabarito.shape}."
        )


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
    _conferir_mascaras(previsao, gabarito)
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


def _conferir_esqueleto(mascara: np.ndarray, esqueleto: np.ndarray, de: str) -> None:
    """Recusa um esqueleto incompatível com a máscara de que ele foi tirado."""
    if esqueleto.dtype != np.bool_ or esqueleto.shape != mascara.shape:
        raise ValueError(f"O esqueleto {de} deve ser booleano e do formato da máscara.")
    if np.any(esqueleto & ~mascara):
        raise ValueError(f"O esqueleto {de} sai da máscara.")
    if esqueleto.any() != mascara.any():
        raise ValueError(f"O esqueleto {de} só pode ser vazio se a máscara for.")


def cldice_de_esqueletos(
    previsao: np.ndarray,
    gabarito: np.ndarray,
    esqueleto_previsao: np.ndarray,
    esqueleto_gabarito: np.ndarray,
) -> float | None:
    """Calcula o clDice a partir de esqueletos prontos (a fórmula, sem algoritmo).

    Tprec = |S_P ∩ V_L| / |S_P| e Tsens = |S_L ∩ V_P| / |S_L|; o clDice é a
    média harmônica das duas, calculada com uma única divisão de inteiros:
    2 n_p n_s / (n_p d_s + n_s d_p).

    Args:
        previsao: Máscara booleana prevista (V_P).
        gabarito: Máscara booleana do gabarito (V_L).
        esqueleto_previsao: Esqueleto da previsão (S_P), dentro dela.
        esqueleto_gabarito: Esqueleto do gabarito (S_L), dentro dele.

    Returns:
        O clDice; ``None`` se o gabarito não tem fissura, e 0 se a previsão é
        vazia (A62, item 4).

    Raises:
        ValueError: Se as máscaras ou os esqueletos forem incompatíveis.
    """
    _conferir_mascaras(previsao, gabarito)
    _conferir_esqueleto(previsao, esqueleto_previsao, "da previsão")
    _conferir_esqueleto(gabarito, esqueleto_gabarito, "do gabarito")
    if not gabarito.any():
        return None
    if not previsao.any():
        return 0.0
    n_p = int(np.count_nonzero(esqueleto_previsao & gabarito))
    d_p = int(np.count_nonzero(esqueleto_previsao))
    n_s = int(np.count_nonzero(esqueleto_gabarito & previsao))
    d_s = int(np.count_nonzero(esqueleto_gabarito))
    if n_p == 0 and n_s == 0:
        return 0.0
    return 2 * n_p * n_s / (n_p * d_s + n_s * d_p)


def esqueleto(mascara: np.ndarray, metodo: str) -> np.ndarray:
    """Esqueleto de uma máscara pelo ``skeletonize`` do scikit-image.

    Args:
        mascara: Máscara booleana.
        metodo: ``"zhang"`` ou ``"lee"``; o projeto usa o da A62, em
            ``REGRAS.metodo_esqueleto``, sem valor padrão aqui.

    Returns:
        O esqueleto, booleano e do formato da máscara.

    Raises:
        ValueError: Se a máscara não for booleana.
    """
    if mascara.dtype != np.bool_:
        raise ValueError("A máscara deve ser booleana.")
    return skeletonize(mascara, method=metodo)


def cldice(previsao: np.ndarray, gabarito: np.ndarray, metodo: str) -> float | None:
    """Calcula o clDice com os esqueletos reais das duas máscaras.

    Args:
        previsao: Máscara booleana prevista.
        gabarito: Máscara booleana do gabarito.
        metodo: Método do esqueleto (``REGRAS.metodo_esqueleto``).

    Returns:
        O clDice, com as mesmas regras de :func:`cldice_de_esqueletos`.
    """
    _conferir_mascaras(previsao, gabarito)
    return cldice_de_esqueletos(
        previsao, gabarito, esqueleto(previsao, metodo), esqueleto(gabarito, metodo)
    )
