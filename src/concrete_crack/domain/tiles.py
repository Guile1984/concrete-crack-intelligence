"""Grade de tiles de uma foto, conforme a A52.

Funções puras, sem acesso a disco. O passo é igual ao lado do tile (sem
sobreposição); o último tile de cada eixo é encostado na borda, para cobrir a
foto inteira sem padding e sem descartar pixels. Os tiles saem em ordem de
leitura: linha a linha, de cima para baixo, e da esquerda para a direita.
"""

from dataclasses import dataclass


def inicios(comprimento: int, lado: int) -> tuple[int, ...]:
    """Calcula as posições de início dos tiles ao longo de um eixo.

    Args:
        comprimento: Tamanho do eixo da imagem, em pixels.
        lado: Lado do tile, em pixels.

    Returns:
        As posições, em ordem crescente: 0, lado, 2 x lado, ... e, se a última
        não terminar exatamente na borda, mais uma em ``comprimento - lado``.

    Raises:
        ValueError: Se o lado não for positivo ou a imagem for menor que o tile.
    """
    if lado <= 0:
        raise ValueError("O lado do tile deve ser positivo.")
    if comprimento < lado:
        raise ValueError(f"A imagem ({comprimento} px) é menor que o tile ({lado} px).")
    posicoes = list(range(0, comprimento - lado + 1, lado))
    ultima = comprimento - lado
    if posicoes[-1] != ultima:
        posicoes.append(ultima)
    return tuple(posicoes)


@dataclass(frozen=True, slots=True)
class Tile:
    """Um tile quadrado, pelo canto superior esquerdo.

    Attributes:
        x: Coluna do canto superior esquerdo.
        y: Linha do canto superior esquerdo.
        lado: Lado do tile, em pixels.
    """

    x: int
    y: int
    lado: int


def grade(largura: int, altura: int, lado: int) -> tuple[Tile, ...]:
    """Monta a grade de tiles de uma imagem.

    Args:
        largura: Largura da imagem, em pixels.
        altura: Altura da imagem, em pixels.
        lado: Lado do tile, em pixels.

    Returns:
        Os tiles, linha a linha, cobrindo a imagem inteira.

    Raises:
        ValueError: Se o lado não for positivo ou a imagem for menor que o tile.
    """
    colunas = inicios(largura, lado)
    return tuple(Tile(x, y, lado) for y in inicios(altura, lado) for x in colunas)


def tamanho_na_escala(largura: int, altura: int, fator: int) -> tuple[int, int]:
    """Calcula o tamanho de uma imagem reduzida por um fator inteiro.

    Args:
        largura: Largura na escala nativa.
        altura: Altura na escala nativa.
        fator: Fator de redução (1 mantém a escala nativa).

    Returns:
        (largura, altura) na escala reduzida.

    Raises:
        ValueError: Se o fator não for positivo ou não dividir os dois lados.
    """
    if fator < 1:
        raise ValueError("O fator deve ser >= 1.")
    if largura % fator or altura % fator:
        raise ValueError(
            f"O fator {fator} não divide o tamanho {largura}x{altura} exatamente."
        )
    return largura // fator, altura // fator
