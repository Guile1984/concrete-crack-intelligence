"""Leitura de imagens (cabeçalho e pixels reduzidos) e gravação de PNG."""

from pathlib import Path

import numpy as np
import PIL
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


def _decodificar(caminho: Path, fator: int, modo: str) -> np.ndarray:
    """Decodifica uma imagem reduzida por um fator inteiro, no modo pedido."""
    if fator < 1:
        raise ValueError(f"fator deve ser um inteiro positivo, não {fator}.")
    with Image.open(caminho) as imagem:
        largura, altura = imagem.size
        alvo = (max(1, largura // fator), max(1, altura // fator))
        imagem.draft(modo, alvo)
        convertida = imagem.convert(modo)
        if convertida.size != alvo:
            convertida = convertida.resize(alvo, Image.Resampling.BOX)
        return np.array(convertida)


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
    return _decodificar(caminho, fator, "L")


def ler_rgb(caminho: Path, fator: int) -> np.ndarray:
    """Lê uma imagem colorida, reduzida por um fator inteiro.

    Como em ``ler_cinza``, a matriz fica como armazenada no arquivo, sem aplicar
    a orientação EXIF. Imagens em tons de cinza são convertidas para RGB.

    Args:
        caminho: Arquivo de imagem.
        fator: Divisor inteiro das dimensões (1 mantém o tamanho original).

    Returns:
        Matriz uint8 de forma (altura // fator, largura // fator, 3).

    Raises:
        ValueError: Se ``fator`` for menor que 1.
        FileNotFoundError: Se o arquivo não existir.
        OSError: Se o arquivo não for uma imagem reconhecida.
    """
    return _decodificar(caminho, fator, "RGB")


def gravar_png(caminho: Path, imagem: np.ndarray) -> None:
    """Grava uma matriz uint8 como PNG, criando as pastas que faltarem.

    Args:
        caminho: Arquivo de destino; um arquivo existente é substituído.
        imagem: Matriz uint8, em tons de cinza (2D) ou RGB (3D).

    Raises:
        ValueError: Se a matriz não for uint8.
    """
    if imagem.dtype != np.uint8:
        raise ValueError("A imagem precisa ser uint8.")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(imagem).save(caminho, format="PNG")


def versao_pillow() -> str:
    """Devolve a versão do Pillow que decodifica as imagens (A54, escolha C).

    Returns:
        A versão, por exemplo ``"12.0.0"``.
    """
    return PIL.__version__
