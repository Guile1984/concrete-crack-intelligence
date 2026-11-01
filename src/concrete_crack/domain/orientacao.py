"""Orientação EXIF aplicada a matrizes e estatística de contraste da máscara.

Serve ao teste de alinhamento entre foto e máscara: a foto é lida como está
armazenada, a orientação EXIF é aplicada aqui, e o contraste sob a máscara diz
qual orientação concorda com o desenho da fissura.
"""

from collections.abc import Callable

import numpy as np

_TRANSFORMACOES: dict[int, Callable[[np.ndarray], np.ndarray]] = {
    1: lambda m: m,
    2: np.fliplr,
    3: lambda m: np.rot90(m, 2),
    4: np.flipud,
    5: lambda m: m.T,
    6: lambda m: np.rot90(m, -1),
    7: lambda m: np.rot90(m, 2).T,
    8: lambda m: np.rot90(m, 1),
}

# Girar 180 graus depois de aplicar a orientação o equivale a aplicar a oposta.
_OPOSTAS: dict[int, int] = {1: 3, 2: 4, 3: 1, 4: 2, 5: 7, 6: 8, 7: 5, 8: 6}


def _normalizar(orientacao: int | None) -> int:
    """Troca a ausência de orientação por 1 e recusa valores fora de 1 a 8."""
    if orientacao is None:
        return 1
    if orientacao not in _TRANSFORMACOES:
        raise ValueError(f"Orientação EXIF inválida: {orientacao!r}. Use 1 a 8.")
    return orientacao


def aplicar_orientacao(matriz: np.ndarray, orientacao: int | None) -> np.ndarray:
    """Aplica a uma matriz 2D a orientação EXIF, como um visualizador faria.

    Args:
        matriz: Pixels como armazenados no arquivo (linhas x colunas).
        orientacao: Valor da etiqueta EXIF 0x0112 (1 a 8) ou None se ausente.

    Returns:
        A matriz na orientação de exibição. Não altera a entrada.

    Raises:
        ValueError: Se a orientação não for None nem um inteiro de 1 a 8.
    """
    transformacao = _TRANSFORMACOES[_normalizar(orientacao)]
    return np.ascontiguousarray(transformacao(matriz))


def orientacao_oposta(orientacao: int | None) -> int:
    """Devolve a orientação que difere da dada por uma rotação de 180 graus.

    Args:
        orientacao: Valor da etiqueta EXIF (1 a 8) ou None se ausente.

    Returns:
        A orientação oposta (1 e 3, 2 e 4, 5 e 7, 6 e 8). Ausente conta como 1.

    Raises:
        ValueError: Se a orientação não for None nem um inteiro de 1 a 8.
    """
    return _OPOSTAS[_normalizar(orientacao)]


def contraste(cinza: np.ndarray, mascara: np.ndarray) -> float:
    """Mede quanto os pixels sob a máscara são mais escuros que os de fora.

    A estatística é (média_fora - média_dentro) / desvio_fora. Fissuras são
    escuras, então um valor positivo e alto indica máscara sobre a fissura.

    Args:
        cinza: Imagem em tons de cinza (linhas x colunas).
        mascara: Máscara booleana de mesma forma; True marca a fissura.

    Returns:
        O contraste, em desvios-padrão do fundo.

    Raises:
        ValueError: Se a máscara não for booleana, se as formas diferirem, se
            faltarem pixels dentro ou fora da máscara ou se o fundo for constante.
    """
    if mascara.dtype != np.bool_:
        raise ValueError("A máscara precisa ser booleana.")
    if cinza.shape != mascara.shape:
        raise ValueError(
            f"Formas diferentes: imagem {cinza.shape}, máscara {mascara.shape}."
        )
    valores = cinza.astype(np.float64)
    dentro = valores[mascara]
    fora = valores[~mascara]
    if dentro.size == 0 or fora.size == 0:
        raise ValueError("A máscara precisa ter pixels dentro e fora.")
    desvio = float(fora.std())
    if desvio == 0.0:
        raise ValueError("O fundo é constante; o contraste não é definido.")
    return float((fora.mean() - dentro.mean()) / desvio)


def vantagem_da_orientacao_exif(
    cinza_armazenada: np.ndarray, mascara: np.ndarray, orientacao: int | None
) -> float:
    """Compara o contraste na orientação EXIF com o da orientação oposta.

    Args:
        cinza_armazenada: Foto em cinza, como armazenada no arquivo.
        mascara: Máscara booleana, na orientação de exibição.
        orientacao: Etiqueta EXIF da foto (1 a 8) ou None se ausente.

    Returns:
        contraste(EXIF) - contraste(oposta). Positivo favorece a orientação EXIF.

    Raises:
        ValueError: Nas mesmas condições de ``contraste`` e ``aplicar_orientacao``.
    """
    pela_exif = aplicar_orientacao(cinza_armazenada, orientacao)
    pela_oposta = aplicar_orientacao(cinza_armazenada, orientacao_oposta(orientacao))
    return contraste(pela_exif, mascara) - contraste(pela_oposta, mascara)
