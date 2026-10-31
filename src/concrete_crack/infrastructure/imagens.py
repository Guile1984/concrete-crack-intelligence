"""Leitura do cabeçalho de imagens, sem decodificar os pixels."""

from pathlib import Path

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
