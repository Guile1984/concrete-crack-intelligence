"""Métricas de segmentação de uma imagem, conforme a A62.

Funções puras sobre máscaras booleanas, sem disco. As métricas saem das
quatro contagens de pixels; quando a divisão seria 0/0, o resultado é
``None`` (indefinido), e a imagem sai da média daquela métrica (A62, item 4).
O clDice sai de quatro contagens dos esqueletos, em duas camadas: a fórmula
recebe esqueletos prontos, e o esqueleto real vem do ``skeletonize`` do
scikit-image (A62, itens 3 e 9). As contagens, e não só o valor, são o que a
soma global do clDice precisa (A62, item 5).
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


@dataclass(frozen=True, slots=True)
class ContagensEsqueleto:
    """As quatro contagens de que o clDice de uma imagem é feito.

    Attributes:
        n_p: Pixels do esqueleto da previsão dentro do gabarito (S_P ∩ V_L).
        d_p: Pixels do esqueleto da previsão (S_P).
        n_s: Pixels do esqueleto do gabarito dentro da previsão (S_L ∩ V_P).
        d_s: Pixels do esqueleto do gabarito (S_L).
    """

    n_p: int
    d_p: int
    n_s: int
    d_s: int

    def __post_init__(self) -> None:
        """Recusa contagens que nenhum par de esqueletos produziria."""
        if not (0 <= self.n_p <= self.d_p and 0 <= self.n_s <= self.d_s):
            raise ValueError("Cada parte deve estar entre 0 e o seu esqueleto.")
        if (self.d_p == 0 and self.n_s > 0) or (self.d_s == 0 and self.n_p > 0):
            raise ValueError("Um esqueleto vazio não pode ter sobreposição.")


def contar_esqueletos(
    previsao: np.ndarray,
    gabarito: np.ndarray,
    esqueleto_previsao: np.ndarray,
    esqueleto_gabarito: np.ndarray,
) -> ContagensEsqueleto:
    """Conta as partes do clDice a partir de esqueletos prontos.

    Args:
        previsao: Máscara booleana prevista (V_P).
        gabarito: Máscara booleana do gabarito (V_L).
        esqueleto_previsao: Esqueleto da previsão (S_P), dentro dela.
        esqueleto_gabarito: Esqueleto do gabarito (S_L), dentro dele.

    Returns:
        As quatro contagens.

    Raises:
        ValueError: Se as máscaras ou os esqueletos forem incompatíveis.
    """
    _conferir_mascaras(previsao, gabarito)
    _conferir_esqueleto(previsao, esqueleto_previsao, "da previsão")
    _conferir_esqueleto(gabarito, esqueleto_gabarito, "do gabarito")
    return ContagensEsqueleto(
        n_p=int(np.count_nonzero(esqueleto_previsao & gabarito)),
        d_p=int(np.count_nonzero(esqueleto_previsao)),
        n_s=int(np.count_nonzero(esqueleto_gabarito & previsao)),
        d_s=int(np.count_nonzero(esqueleto_gabarito)),
    )


def cldice_de_contagens(contagens: ContagensEsqueleto) -> float | None:
    """Calcula o clDice a partir das quatro contagens dos esqueletos.

    Tprec = n_p / d_p e Tsens = n_s / d_s; o clDice é a média harmônica das
    duas, calculada com uma única divisão de inteiros:
    2 n_p n_s / (n_p d_s + n_s d_p).

    Returns:
        O clDice; ``None`` se o gabarito não tem fissura (d_s = 0), e 0 se
        nada se sobrepõe, o que inclui a previsão vazia (A62, item 4).
    """
    c = contagens
    if c.d_s == 0:
        return None
    if c.n_p == 0 and c.n_s == 0:
        return 0.0
    return 2 * c.n_p * c.n_s / (c.n_p * c.d_s + c.n_s * c.d_p)


def cldice_de_esqueletos(
    previsao: np.ndarray,
    gabarito: np.ndarray,
    esqueleto_previsao: np.ndarray,
    esqueleto_gabarito: np.ndarray,
) -> float | None:
    """Calcula o clDice a partir de esqueletos prontos (a fórmula, sem algoritmo).

    Returns:
        O clDice, com as regras de :func:`cldice_de_contagens`.

    Raises:
        ValueError: Se as máscaras ou os esqueletos forem incompatíveis.
    """
    return cldice_de_contagens(
        contar_esqueletos(previsao, gabarito, esqueleto_previsao, esqueleto_gabarito)
    )


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


def contar_esqueletos_reais(
    previsao: np.ndarray, gabarito: np.ndarray, metodo: str
) -> ContagensEsqueleto:
    """Conta as partes do clDice com os esqueletos reais das duas máscaras.

    Args:
        previsao: Máscara booleana prevista.
        gabarito: Máscara booleana do gabarito.
        metodo: Método do esqueleto (``REGRAS.metodo_esqueleto``).

    Returns:
        As quatro contagens.
    """
    _conferir_mascaras(previsao, gabarito)
    return contar_esqueletos(
        previsao, gabarito, esqueleto(previsao, metodo), esqueleto(gabarito, metodo)
    )


def cldice(previsao: np.ndarray, gabarito: np.ndarray, metodo: str) -> float | None:
    """Calcula o clDice com os esqueletos reais das duas máscaras.

    Args:
        previsao: Máscara booleana prevista.
        gabarito: Máscara booleana do gabarito.
        metodo: Método do esqueleto (``REGRAS.metodo_esqueleto``).

    Returns:
        O clDice, com as regras de :func:`cldice_de_contagens`.
    """
    return cldice_de_contagens(contar_esqueletos_reais(previsao, gabarito, metodo))
