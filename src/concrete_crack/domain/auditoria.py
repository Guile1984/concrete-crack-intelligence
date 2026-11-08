"""Auditoria descritiva de pares de fotos diante de uma divisão (A49).

Conta quantos pares ficaram com uma foto no teste e a outra fora, e quantos
ficaram em conjuntos diferentes quaisquer, e compara com o esperado se as fotos
fossem distribuídas ao acaso com os mesmos tamanhos de conjunto. Só relata: não
altera a divisão.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from .divisao import TESTE, Divisao


@dataclass(frozen=True, slots=True)
class AuditoriaPares:
    """O resultado da auditoria de pares.

    Attributes:
        pares: Os pares auditados, na ordem recebida.
        conjuntos: O conjunto de cada foto de cada par, na mesma ordem.
        cruzam_teste: Pares com exatamente uma foto no teste.
        em_conjuntos_diferentes: Pares com as fotos em conjuntos diferentes.
        esperado_cruzam_teste: Pares esperados com uma foto no teste, ao acaso.
        esperado_diferentes: Pares esperados em conjuntos diferentes, ao acaso.
    """

    pares: tuple[tuple[str, str], ...]
    conjuntos: tuple[tuple[str, str], ...]
    cruzam_teste: int
    em_conjuntos_diferentes: int
    esperado_cruzam_teste: float
    esperado_diferentes: float


def probabilidades_ao_acaso(divisao: Divisao) -> tuple[float, float]:
    """Probabilidades de um par de fotos distintas, sorteado ao acaso, cruzar.

    Sorteia-se a primeira foto entre as N e a segunda entre as N - 1 restantes.

    Args:
        divisao: A divisão, que fornece os tamanhos dos conjuntos.

    Returns:
        (probabilidade de exatamente uma foto no teste, probabilidade de as
        duas fotos ficarem em conjuntos diferentes).

    Raises:
        ValueError: Se a divisão tiver menos de 2 fotos.
    """
    tamanhos = (len(divisao.treino), len(divisao.validacao), len(divisao.teste))
    n = sum(tamanhos)
    if n < 2:
        raise ValueError("A divisão precisa de pelo menos 2 fotos.")
    ordenados = n * (n - 1)
    n_teste = len(divisao.teste)
    cruzar_teste = 2 * n_teste * (n - n_teste) / ordenados
    mesmo_conjunto = sum(k * (k - 1) for k in tamanhos) / ordenados
    return cruzar_teste, 1.0 - mesmo_conjunto


def auditar_pares(pares: Sequence[tuple[str, str]], divisao: Divisao) -> AuditoriaPares:
    """Conta os pares que cruzam a fronteira do teste e os de conjuntos diferentes.

    Args:
        pares: Os pares de fotos a auditar.
        divisao: A divisão gravada.

    Returns:
        A auditoria, com as contagens observadas e as esperadas ao acaso.

    Raises:
        KeyError: Se alguma foto de um par não estiver na divisão.
        ValueError: Se a divisão tiver menos de 2 fotos.
    """
    conjuntos = tuple(
        (divisao.conjunto_de(a), divisao.conjunto_de(b)) for a, b in pares
    )
    cruzam = sum((x == TESTE) != (y == TESTE) for x, y in conjuntos)
    diferentes = sum(x != y for x, y in conjuntos)
    p_teste, p_diferentes = probabilidades_ao_acaso(divisao)
    return AuditoriaPares(
        pares=tuple(pares),
        conjuntos=conjuntos,
        cruzam_teste=cruzam,
        em_conjuntos_diferentes=diferentes,
        esperado_cruzam_teste=len(pares) * p_teste,
        esperado_diferentes=len(pares) * p_diferentes,
    )
