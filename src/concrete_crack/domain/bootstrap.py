"""Bootstrap pareado e a regra de decisão do critério 1 (A62, itens 6 e 7).

Funções puras, sem disco. A entrada é a diferença da métrica entre dois
métodos em cada imagem (o pareamento: as duas notas são da mesma imagem) e o
grupo de cada imagem. Cada reamostragem sorteia grupos inteiros, com
reposição, e calcula a média por imagem das diferenças das imagens sorteadas.
No CCSD o grupo é o da A49; no S2DS, cada imagem é o seu próprio grupo (A61).
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

SUPERIOR = "superior"
INFERIOR = "inferior"
INCONCLUSIVO = "inconclusivo"


@dataclass(frozen=True, slots=True)
class Intervalo:
    """Diferença média observada e o seu intervalo percentil.

    Attributes:
        estimativa: Média por imagem das diferenças observadas.
        inferior: Limite inferior do intervalo.
        superior: Limite superior do intervalo.
    """

    estimativa: float
    inferior: float
    superior: float


def bootstrap_pareado(
    diferencas: Sequence[float],
    grupos: Sequence[str],
    n_reamostragens: int,
    nivel: float,
    seed: int,
) -> Intervalo:
    """Intervalo percentil da diferença média, sorteando grupos inteiros.

    Args:
        diferencas: Diferença da métrica (primeiro método menos o segundo),
            uma por imagem.
        grupos: Grupo de cada imagem, na mesma ordem.
        n_reamostragens: Quantidade de reamostragens (B).
        nivel: Nível do intervalo, em (0, 1).
        seed: Semente do sorteio.

    Returns:
        A estimativa e os quantis (1 - nível) / 2 e (1 + nível) / 2 das médias
        reamostradas, pelo quantil linear do numpy.

    Raises:
        ValueError: Se as entradas forem vazias, de tamanhos diferentes, não
            finitas, ou se B ou o nível forem inválidos.
    """
    valores = np.asarray(diferencas, dtype=np.float64)
    if valores.size == 0 or valores.size != len(grupos):
        raise ValueError("Diferenças e grupos devem ser não vazios e do mesmo tamanho.")
    if not np.all(np.isfinite(valores)):
        raise ValueError("As diferenças devem ser finitas.")
    if n_reamostragens < 1:
        raise ValueError("O bootstrap precisa de pelo menos 1 reamostragem.")
    if not 0 < nivel < 1:
        raise ValueError("O nível deve estar em (0, 1).")
    _, indice = np.unique(np.asarray(grupos), return_inverse=True)
    somas = np.bincount(indice, weights=valores)
    tamanhos = np.bincount(indice)
    gerador = np.random.default_rng(seed)
    sorteios = gerador.integers(0, somas.size, size=(n_reamostragens, somas.size))
    medias = somas[sorteios].sum(axis=1) / tamanhos[sorteios].sum(axis=1)
    inferior, superior = np.quantile(medias, [(1 - nivel) / 2, (1 + nivel) / 2])
    return Intervalo(float(valores.mean()), float(inferior), float(superior))


def decidir(intervalo: Intervalo) -> str:
    """Regra do critério 1 sobre o intervalo da diferença.

    Returns:
        ``"superior"`` se o intervalo estiver inteiro acima de zero (o
        primeiro método supera o segundo), ``"inferior"`` se estiver inteiro
        abaixo, e ``"inconclusivo"`` se tocar ou cruzar o zero.
    """
    if intervalo.inferior > 0:
        return SUPERIOR
    if intervalo.superior < 0:
        return INFERIOR
    return INCONCLUSIVO
