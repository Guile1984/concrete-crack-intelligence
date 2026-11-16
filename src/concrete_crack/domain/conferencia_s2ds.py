"""Conferência das contagens dos rótulos do S2DS com a tabela publicada (A58).

Funções puras, sem disco. Por conjunto e por classe, compara a quantidade de
imagens em que a classe aparece (que deve ser exata) e a quantidade de pixels
(que deve ficar dentro do arredondamento da tabela publicada).
"""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContagemClasse:
    """Quanto de uma classe há num conjunto.

    Attributes:
        imagens: Imagens em que a classe tem pelo menos um pixel.
        pixels: Total de pixels da classe.
    """

    imagens: int
    pixels: int


def divergencias_da_tabela(
    medido: Mapping[str, ContagemClasse],
    publicado: Mapping[str, tuple[int, float]],
    tolerancia_milhoes: float,
) -> list[str]:
    """Lista as classes cujas contagens não batem com a tabela publicada.

    Args:
        medido: Contagem medida de cada classe.
        publicado: Para cada classe, (imagens, pixels em milhões) publicados.
        tolerancia_milhoes: Diferença máxima aceita nos pixels, em milhões.

    Returns:
        Uma descrição por divergência; lista vazia se tudo bater.
    """
    problemas = []
    for classe in sorted(set(medido) | set(publicado)):
        if classe not in medido or classe not in publicado:
            problemas.append(f"{classe}: classe ausente de um dos lados")
            continue
        imagens, milhoes = publicado[classe]
        contagem = medido[classe]
        if contagem.imagens != imagens:
            problemas.append(
                f"{classe}: {contagem.imagens} imagens, publicado {imagens}"
            )
        if abs(contagem.pixels / 1e6 - milhoes) > tolerancia_milhoes:
            problemas.append(
                f"{classe}: {contagem.pixels / 1e6:.2f} M pixels, publicado {milhoes} M"
            )
    return problemas
