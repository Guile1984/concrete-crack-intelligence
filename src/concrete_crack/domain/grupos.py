"""Registro dos grupos de quase-duplicatas que a divisão vai respeitar.

Cada grupo reúne fotos que precisam ficar no mesmo conjunto (treino, validação
ou teste). O registro guarda também de onde os grupos vieram: o método, o hash
do manifesto de arquivos, o hash dos pesos da rede e o limiar usado.
"""

from dataclasses import dataclass

from .pesos import PADRAO_SHA256


@dataclass(frozen=True, slots=True)
class RegistroGrupos:
    """Os grupos de fotos de uma fonte e a procedência deles.

    Attributes:
        fonte_id: Identificador da fonte.
        metodo: Descrição curta do método e da decisão que o aprovou.
        sha256_manifesto: Hash do manifesto de arquivos usado.
        sha256_pesos: Hash dos pesos da rede que gerou os vetores.
        limiar: Limiar de distância que ligou as fotos.
        grupos: Os grupos, cada um com os caminhos das fotos.
    """

    fonte_id: str
    metodo: str
    sha256_manifesto: str
    sha256_pesos: str
    limiar: float
    grupos: tuple[tuple[str, ...], ...]

    def __post_init__(self) -> None:
        """Recusa registros mal formados ou com uma foto em dois grupos."""
        if not self.fonte_id or not self.metodo:
            raise ValueError("A fonte e o método não podem ser vazios.")
        for valor in (self.sha256_manifesto, self.sha256_pesos):
            if not PADRAO_SHA256.fullmatch(valor):
                raise ValueError("Os hashes devem ter 64 hexadecimais minúsculos.")
        if self.limiar < 0:
            raise ValueError("O limiar não pode ser negativo.")
        if not self.grupos or any(not grupo for grupo in self.grupos):
            raise ValueError("Os grupos não podem ser vazios.")
        fotos = [foto for grupo in self.grupos for foto in grupo]
        if len(fotos) != len(set(fotos)):
            raise ValueError("Uma foto aparece em mais de um grupo.")

    @property
    def n_fotos(self) -> int:
        """Quantidade de fotos registradas."""
        return sum(len(grupo) for grupo in self.grupos)
