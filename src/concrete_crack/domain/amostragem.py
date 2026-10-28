"""Amostragem determinística por hash, sem depender de bibliotecas de sorteio."""

import hashlib
from collections.abc import Sequence


def _chave(seed: int, nome: str) -> str:
    """Calcula a chave de ordenação de um nome para uma seed.

    Args:
        seed: Semente do sorteio.
        nome: Nome do item.

    Returns:
        SHA-256 hexadecimal de ``"{seed}:{nome}"``.
    """
    return hashlib.sha256(f"{seed}:{nome}".encode()).hexdigest()


def amostrar_por_hash(nomes: Sequence[str], n: int, seed: int) -> tuple[str, ...]:
    """Sorteia ``n`` nomes ordenando-os pelo hash de ``seed:nome``.

    O resultado depende só do conjunto de nomes, de ``n`` e da seed: não depende
    da ordem de entrada nem da versão de nenhuma biblioteca.

    Args:
        nomes: Nomes distintos dos itens disponíveis.
        n: Quantos nomes sortear.
        seed: Semente do sorteio.

    Returns:
        Os ``n`` nomes sorteados, em ordem alfabética.

    Raises:
        ValueError: Se ``n`` for negativo ou maior que o total, ou se houver
            nomes repetidos.
    """
    if len(set(nomes)) != len(nomes):
        raise ValueError("Há nomes repetidos na lista a sortear.")
    if not 0 <= n <= len(nomes):
        raise ValueError(f"n={n} fora do intervalo de 0 a {len(nomes)}.")
    ordenados = sorted(nomes, key=lambda nome: _chave(seed, nome))
    return tuple(sorted(ordenados[:n]))
