"""Pareamento de máscaras e fotos pelo nome, sem acesso a disco."""

from collections.abc import Sequence
from dataclasses import dataclass


def _chave(caminho: str) -> str:
    """Devolve o nome do arquivo sem pasta nem extensão, em minúsculas."""
    nome = caminho.rsplit("/", 1)[-1]
    if "." in nome:
        nome = nome.rsplit(".", 1)[0]
    return nome.lower()


def _indexar(caminhos: Sequence[str], rotulo: str) -> dict[str, str]:
    """Indexa os caminhos pela chave de pareamento, recusando colisões."""
    indice: dict[str, str] = {}
    for caminho in caminhos:
        chave = _chave(caminho)
        if chave in indice:
            raise ValueError(
                f"Há {rotulo} com o mesmo nome (sem extensão e ignorando "
                f"maiúsculas): {indice[chave]!r} e {caminho!r}."
            )
        indice[chave] = caminho
    return indice


@dataclass(frozen=True, slots=True)
class Pareamento:
    """Resultado do pareamento entre máscaras e fotos.

    Attributes:
        pares: Pares (máscara, foto), ordenados pelo caminho da máscara.
        mascaras_sem_foto: Máscaras sem foto de mesmo nome.
        fotos_sem_mascara: Fotos sem máscara de mesmo nome.
    """

    pares: tuple[tuple[str, str], ...]
    mascaras_sem_foto: tuple[str, ...]
    fotos_sem_mascara: tuple[str, ...]

    @property
    def completo(self) -> bool:
        """Verdadeiro quando toda máscara tem foto e toda foto tem máscara."""
        return not (self.mascaras_sem_foto or self.fotos_sem_mascara)


def parear(mascaras: Sequence[str], fotos: Sequence[str]) -> Pareamento:
    """Pareia máscaras e fotos pelo nome, ignorando pasta, extensão e maiúsculas.

    Args:
        mascaras: Caminhos das máscaras.
        fotos: Caminhos das fotos.

    Returns:
        O pareamento, com cada grupo em ordem alfabética de caminho.

    Raises:
        ValueError: Se duas máscaras (ou duas fotos) tiverem o mesmo nome.
    """
    por_mascara = _indexar(mascaras, "máscaras")
    por_foto = _indexar(fotos, "fotos")
    comuns = por_mascara.keys() & por_foto.keys()
    pares = tuple(sorted((por_mascara[chave], por_foto[chave]) for chave in comuns))
    mascaras_sem_foto = tuple(
        sorted(por_mascara[chave] for chave in por_mascara.keys() - por_foto.keys())
    )
    fotos_sem_mascara = tuple(
        sorted(por_foto[chave] for chave in por_foto.keys() - por_mascara.keys())
    )
    return Pareamento(pares, mascaras_sem_foto, fotos_sem_mascara)
