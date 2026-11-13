"""Manifesto de hashes dos pixels preparados de cada foto (A54, escolha A).

Para cada foto e cada escala, o manifesto guarda o hash da foto inteira e o
da máscara inteira, já preparadas. Uma geração em outra máquina é aceita só se
todos os hashes coincidirem. Funções puras, sem disco.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from .pesos import PADRAO_SHA256


@dataclass(frozen=True, slots=True)
class HashesEscala:
    """Os hashes da foto e da máscara de uma escala.

    Attributes:
        fator: Fator de redução da escala.
        foto: SHA-256 dos pixels da foto preparada.
        mascara: SHA-256 dos pixels da máscara preparada.
    """

    fator: int
    foto: str
    mascara: str

    def __post_init__(self) -> None:
        """Recusa hashes mal formados."""
        for valor in (self.foto, self.mascara):
            if not PADRAO_SHA256.fullmatch(valor):
                raise ValueError("Os hashes devem ter 64 hexadecimais minúsculos.")


@dataclass(frozen=True, slots=True)
class HashesFoto:
    """Os hashes de uma foto em todas as escalas.

    Attributes:
        foto: Caminho da foto no manifesto de arquivos.
        escalas: Um ``HashesEscala`` por escala, na ordem do índice de tiles.
    """

    foto: str
    escalas: tuple[HashesEscala, ...]


def diferencas(esperado: HashesFoto, obtido: HashesFoto) -> list[str]:
    """Lista o que difere entre os hashes registrados e os obtidos.

    Args:
        esperado: Hashes registrados no manifesto.
        obtido: Hashes da geração atual.

    Returns:
        Descrições curtas de cada diferença, como ``"escala 2: máscara"``;
        lista vazia se tudo coincidir.
    """
    if esperado.foto != obtido.foto:
        return [f"foto {obtido.foto!r} no lugar de {esperado.foto!r}"]
    fatores_esperados = [e.fator for e in esperado.escalas]
    if fatores_esperados != [e.fator for e in obtido.escalas]:
        return ["escalas diferentes"]
    problemas = []
    for antes, agora in zip(esperado.escalas, obtido.escalas, strict=True):
        if antes.foto != agora.foto:
            problemas.append(f"escala {antes.fator}: foto")
        if antes.mascara != agora.mascara:
            problemas.append(f"escala {antes.fator}: máscara")
    return problemas


@dataclass(frozen=True, slots=True)
class ManifestoPixels:
    """O manifesto de hashes dos pixels de uma fonte.

    Attributes:
        fonte_id: Identificador da fonte.
        sha256_indice: Hash do índice de tiles usado na geração.
        versao_pillow: Versão do Pillow que decodificou as imagens (A54, C).
        fotos: Os hashes de cada foto, em ordem alfabética de caminho.
    """

    fonte_id: str
    sha256_indice: str
    versao_pillow: str
    fotos: tuple[HashesFoto, ...]

    def __post_init__(self) -> None:
        """Recusa manifestos mal formados."""
        if not self.fonte_id or not self.versao_pillow:
            raise ValueError("A fonte e a versão do Pillow não podem ser vazias.")
        if not PADRAO_SHA256.fullmatch(self.sha256_indice):
            raise ValueError("Os hashes devem ter 64 hexadecimais minúsculos.")
        nomes = [foto.foto for foto in self.fotos]
        if nomes != sorted(set(nomes)):
            raise ValueError("As fotos devem ser únicas e em ordem alfabética.")

    def da_foto(self, foto: str) -> HashesFoto:
        """Devolve os hashes registrados de uma foto.

        Args:
            foto: Caminho da foto.

        Returns:
            Os hashes registrados.

        Raises:
            KeyError: Se a foto não estiver no manifesto.
        """
        for registrada in self.fotos:
            if registrada.foto == foto:
                return registrada
        raise KeyError(foto)


def montar_manifesto(
    fonte_id: str,
    sha256_indice: str,
    versao_pillow: str,
    fotos: Sequence[HashesFoto],
) -> ManifestoPixels:
    """Monta o manifesto com as fotos em ordem alfabética.

    Args:
        fonte_id: Identificador da fonte.
        sha256_indice: Hash do índice de tiles.
        versao_pillow: Versão do Pillow.
        fotos: Os hashes de cada foto, em qualquer ordem.

    Returns:
        O manifesto validado.
    """
    ordenadas = tuple(sorted(fotos, key=lambda foto: foto.foto))
    return ManifestoPixels(fonte_id, sha256_indice, versao_pillow, ordenadas)
