"""Redução, recorte e hash dos pixels dos tiles (A52, itens 3, 4 e 7).

Funções puras sobre matrizes numpy, sem disco. A redução por média de área usa
só aritmética inteira, que dá o mesmo resultado em qualquer máquina e em
qualquer versão de biblioteca de imagens; o hash é calculado sobre os bytes
dos pixels, junto com o tipo e a forma da matriz, e não sobre um arquivo.
"""

import hashlib

import numpy as np


def somar_blocos(imagem: np.ndarray, fator: int) -> np.ndarray:
    """Soma os pixels de cada bloco de fator x fator.

    Args:
        imagem: Matriz (altura, largura) ou (altura, largura, canais).
        fator: Lado do bloco.

    Returns:
        Matriz int64 com altura e largura divididas pelo fator; os canais,
        se houver, são somados separadamente.

    Raises:
        ValueError: Se o fator for menor que 1 ou não dividir a altura e a
            largura.
    """
    if fator < 1:
        raise ValueError("O fator deve ser >= 1.")
    altura, largura = imagem.shape[:2]
    if altura % fator or largura % fator:
        raise ValueError(
            f"O fator {fator} não divide o tamanho {largura}x{altura} exatamente."
        )
    blocos = imagem.astype(np.int64).reshape(
        altura // fator, fator, largura // fator, fator, *imagem.shape[2:]
    )
    return blocos.sum(axis=(1, 3))


def reduzir_foto(imagem: np.ndarray, fator: int) -> np.ndarray:
    """Reduz uma foto uint8 pela média de cada bloco, arredondando meio para cima.

    Args:
        imagem: Foto uint8, (altura, largura) ou (altura, largura, canais).
        fator: Fator de redução.

    Returns:
        A foto reduzida, uint8.

    Raises:
        ValueError: Se a foto não for uint8 ou o fator for inválido.
    """
    if imagem.dtype != np.uint8:
        raise ValueError("A foto deve ser uint8.")
    n = fator * fator
    return ((somar_blocos(imagem, fator) + n // 2) // n).astype(np.uint8)


def reduzir_mascara(mascara: np.ndarray, fator: int) -> np.ndarray:
    """Reduz uma máscara binária à fração de fissura de cada bloco.

    Args:
        mascara: Máscara booleana (altura, largura), verdadeira na fissura.
        fator: Fator de redução.

    Returns:
        Matriz float64 com valores de 0 a 1.

    Raises:
        ValueError: Se a máscara não for booleana ou o fator for inválido.
    """
    if mascara.dtype != np.bool_:
        raise ValueError("A máscara deve ser booleana.")
    return somar_blocos(mascara, fator) / (fator * fator)


def recortar(imagem: np.ndarray, x: int, y: int, lado: int) -> np.ndarray:
    """Recorta o tile quadrado de canto superior esquerdo (x, y).

    Args:
        imagem: Matriz (altura, largura) ou (altura, largura, canais).
        x: Coluna do canto.
        y: Linha do canto.
        lado: Lado do tile.

    Returns:
        O tile, como vista da imagem (sem cópia).

    Raises:
        ValueError: Se o tile sair da imagem.
    """
    altura, largura = imagem.shape[:2]
    if x < 0 or y < 0 or lado <= 0 or x + lado > largura or y + lado > altura:
        raise ValueError(f"O tile ({x}, {y}, {lado}) sai da imagem {largura}x{altura}.")
    return imagem[y : y + lado, x : x + lado]


def hash_pixels(imagem: np.ndarray) -> str:
    """Calcula o SHA-256 dos pixels, com o tipo e a forma da matriz.

    Args:
        imagem: Qualquer matriz numpy.

    Returns:
        O hash hexadecimal de ``"<tipo>|<forma>|"`` seguido dos bytes da matriz
        em ordem C.
    """
    contigua = np.ascontiguousarray(imagem)
    cabecalho = f"{contigua.dtype.str}|{contigua.shape}|".encode()
    return hashlib.sha256(cabecalho + contigua.tobytes()).hexdigest()
