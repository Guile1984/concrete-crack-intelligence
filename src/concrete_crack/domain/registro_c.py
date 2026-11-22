"""Registro da constante c do Frangi e da amostra que a produziu (A66, item 3).

O c é calculado uma única vez, antes de qualquer validação; o registro guarda
o valor de cada fundo e tudo o que é preciso para refazer a conta.
"""

from dataclasses import dataclass

from .pesos import PADRAO_SHA256


@dataclass(frozen=True, slots=True)
class ConstanteC:
    """O c de um valor de σ do fundo.

    Attributes:
        sigma_fundo: σ do borrão do fundo (0 é sem correção).
        percentil_s: O percentil de S* nos pixels sorteados.
        c: A constante: fração x ``percentil_s``.
    """

    sigma_fundo: float
    percentil_s: float
    c: float


@dataclass(frozen=True, slots=True)
class RegistroC:
    """A constante c, por fundo, e a procedência dela.

    Attributes:
        fonte_id: Identificador da fonte.
        sha256_split: Hash do registro da divisão de onde saiu o treino.
        seed: Semente do sorteio das fotos e dos pixels.
        n_pixels_por_foto: Pixels sorteados em cada foto.
        escalas: As oitavas σ usadas em S*.
        percentil: O percentil pré-registrado.
        fracao: A fração pré-registrada.
        fotos: As fotos sorteadas do treino, em ordem alfabética.
        constantes: Um c por σ do fundo, em ordem crescente de σ.
        versoes: Pares (biblioteca, versão) do ambiente que calculou.
    """

    fonte_id: str
    sha256_split: str
    seed: int
    n_pixels_por_foto: int
    escalas: tuple[float, ...]
    percentil: float
    fracao: float
    fotos: tuple[str, ...]
    constantes: tuple[ConstanteC, ...]
    versoes: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        """Recusa registros mal formados ou com um c que não bate com a regra."""
        if not self.fonte_id:
            raise ValueError("A fonte não pode ser vazia.")
        if not PADRAO_SHA256.fullmatch(self.sha256_split):
            raise ValueError("O hash da divisão deve ter 64 hexadecimais minúsculos.")
        if not self.fotos or list(self.fotos) != sorted(set(self.fotos)):
            raise ValueError("As fotos devem ser únicas e em ordem alfabética.")
        fundos = [constante.sigma_fundo for constante in self.constantes]
        if not fundos or fundos != sorted(set(fundos)):
            raise ValueError("Os σ do fundo devem ser distintos e crescentes.")
        for constante in self.constantes:
            if constante.c <= 0 or constante.c != self.fracao * constante.percentil_s:
                raise ValueError(
                    f"O c do fundo {constante.sigma_fundo} não é fração x percentil."
                )

    def c_do_fundo(self, sigma_fundo: float) -> float:
        """Devolve o c de um σ do fundo.

        Raises:
            KeyError: Se o registro não tiver esse σ do fundo.
        """
        for constante in self.constantes:
            if constante.sigma_fundo == sigma_fundo:
                return constante.c
        raise KeyError(f"Não há c para o σ do fundo {sigma_fundo}.")
