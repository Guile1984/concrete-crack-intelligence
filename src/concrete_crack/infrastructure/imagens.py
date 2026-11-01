"""Leitura de imagens: o cabeçalho, sem decodificar, e os pixels em cinza."""

from pathlib import Path

import numpy as np
from PIL import Image

from ..domain.dimensoes import Cabecalho

ETIQUETA_ORIENTACAO = 0x0112


def ler_cabecalho(caminho: Path) -> Cabecalho:
    """Lê a largura, a altura e a orientação EXIF de uma imagem.

    O tamanho é o gravado no arquivo: a rotação indicada pela etiqueta EXIF
    não é aplicada. Os pixels não são decodificados.

    Args:
        caminho: Arquivo de imagem.

    Returns:
        O cabeçalho da imagem; a orientação é None quando a etiqueta não existe.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        OSError: Se o arquivo não for uma imagem reconhecida.
        ValueError: Se as dimensões ou a orientação forem inválidas; a
            mensagem cita o caminho.
    """
    with Image.open(caminho) as imagem:
        largura, altura = imagem.size
        orientacao = imagem.getexif().get(ETIQUETA_ORIENTACAO)
    try:
        return Cabecalho(largura, altura, orientacao)
    except ValueError as erro:
        raise ValueError(f"{caminho}: {erro}") from erro


def ler_cinza(caminho: Path, fator: int) -> np.ndarray:
    """Lê uma imagem em tons de cinza, reduzida por um fator inteiro.

    A matriz fica como armazenada no arquivo: a orientação EXIF não é aplicada.
    Em JPEG, a redução usa a decodificação parcial do Pillow (``draft``), que
    evita decodificar os 12 megapixels inteiros; nos demais formatos, e quando
    o tamanho obtido difere do alvo, a redução é por média de blocos.

    Args:
        caminho: Arquivo de imagem.
        fator: Divisor inteiro das dimensões (1 mantém o tamanho original).

    Returns:
        Matriz uint8 de forma (altura // fator, largura // fator).

    Raises:
        ValueError: Se ``fator`` for menor que 1.
        FileNotFoundError: Se o arquivo não existir.
        OSError: Se o arquivo não for uma imagem reconhecida.
    """
    if fator < 1:
        raise ValueError(f"fator deve ser um inteiro positivo, não {fator}.")
    with Image.open(caminho) as imagem:
        largura, altura = imagem.size
        alvo = (max(1, largura // fator), max(1, altura // fator))
        imagem.draft("L", alvo)
        cinza = imagem.convert("L")
        if cinza.size != alvo:
            cinza = cinza.resize(alvo, Image.Resampling.BOX)
        return np.array(cinza)
