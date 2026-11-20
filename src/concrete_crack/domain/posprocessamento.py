"""Pós-processamento comum a todo segmentador, conforme a A65 (item 2).

Funções puras, sem disco. O mapa de score de qualquer segmentador passa pela
conferência do contrato, pelo limiar e pela remoção de componentes pequenos;
a rede e o Frangi usam as mesmas funções, cada um com os seus parâmetros.
"""

import numpy as np
from skimage.measure import label


def conferir_mapa(mapa: np.ndarray, formato: tuple[int, int]) -> None:
    """Recusa um mapa que não cumpre o contrato do ``Segmentador``.

    Args:
        mapa: O mapa devolvido pelo segmentador.
        formato: (altura, largura) da imagem de entrada.

    Raises:
        ValueError: Se o mapa não for ``float``, tiver outro formato, valores
            não finitos ou fora de [0, 1].
    """
    if mapa.dtype.kind != "f":
        raise ValueError(f"O mapa deve ser float, não {mapa.dtype}.")
    if mapa.shape != formato:
        raise ValueError(f"O mapa tem formato {mapa.shape}, e não {formato}.")
    if not np.all(np.isfinite(mapa)):
        raise ValueError("O mapa tem valores não finitos.")
    if mapa.size and (mapa.min() < 0 or mapa.max() > 1):
        raise ValueError("Os valores do mapa devem estar em [0, 1].")


def binarizar(mapa: np.ndarray, limiar: float) -> np.ndarray:
    """Marca como fissura os pixels com score maior ou igual ao limiar.

    Args:
        mapa: Mapa de score em [0, 1].
        limiar: Limiar em [0, 1].

    Returns:
        Máscara booleana do formato do mapa.

    Raises:
        ValueError: Se o limiar estiver fora de [0, 1].
    """
    if not 0 <= limiar <= 1:
        raise ValueError("O limiar deve estar em [0, 1].")
    return mapa >= limiar


def remover_componentes_pequenos(
    mascara: np.ndarray, tamanho_minimo: int, conectividade: int
) -> np.ndarray:
    """Remove os componentes conexos com menos pixels que o tamanho mínimo.

    Args:
        mascara: Máscara booleana.
        tamanho_minimo: Componentes com menos pixels que isso viram fundo;
            0 desliga a limpeza.
        conectividade: 4 (só lados) ou 8 (lados e diagonais), em
            ``REGRAS.conectividade_componentes``.

    Returns:
        Uma nova máscara booleana; a de entrada não é alterada.

    Raises:
        ValueError: Se a máscara não for booleana, o tamanho for negativo ou
            a conectividade não for 4 nem 8.
    """
    if mascara.dtype != np.bool_:
        raise ValueError("A máscara deve ser booleana.")
    if tamanho_minimo < 0:
        raise ValueError("O tamanho mínimo não pode ser negativo.")
    if conectividade not in {4, 8}:
        raise ValueError("A conectividade deve ser 4 ou 8.")
    if tamanho_minimo <= 1 or not mascara.any():
        return mascara.copy()
    rotulos = label(mascara, connectivity=1 if conectividade == 4 else 2)
    tamanhos = np.bincount(rotulos.ravel())
    manter = tamanhos >= tamanho_minimo
    manter[0] = False
    return manter[rotulos]
