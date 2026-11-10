"""Índice de tiles do CCSD, conforme a A52 (item 6).

Para cada foto, o índice guarda o conjunto herdado da divisão, o tamanho de
exibição (com a orientação EXIF aplicada) e, por escala, as posições de início
das colunas e das linhas. Os tiles de uma escala são todas as combinações
(x, y) dessas posições, em ordem de leitura. Funções puras, sem disco.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .divisao import TESTE, TREINO, VALIDACAO, Divisao
from .pesos import PADRAO_SHA256
from .tiles import inicios, tamanho_na_escala

CONJUNTOS = (TREINO, VALIDACAO, TESTE)


@dataclass(frozen=True, slots=True)
class GradeFoto:
    """A grade de uma foto numa escala.

    Attributes:
        fator: Fator de redução da escala (1 é a nativa).
        xs: Posições de início das colunas, na escala.
        ys: Posições de início das linhas, na escala.
    """

    fator: int
    xs: tuple[int, ...]
    ys: tuple[int, ...]

    @property
    def n_tiles(self) -> int:
        """Quantidade de tiles da grade."""
        return len(self.xs) * len(self.ys)


@dataclass(frozen=True, slots=True)
class FotoIndexada:
    """Uma foto do índice.

    Attributes:
        foto: Caminho da foto no manifesto.
        conjunto: ``"treino"``, ``"validacao"`` ou ``"teste"``.
        largura: Largura de exibição na escala nativa.
        altura: Altura de exibição na escala nativa.
        grades: Uma grade por escala, na ordem das escalas do índice.
    """

    foto: str
    conjunto: str
    largura: int
    altura: int
    grades: tuple[GradeFoto, ...]


def indexar_foto(
    foto: str,
    conjunto: str,
    tamanho: tuple[int, int],
    escalas: Sequence[tuple[int, int]],
) -> FotoIndexada:
    """Monta a grade de uma foto em cada escala.

    Args:
        foto: Caminho da foto.
        conjunto: Conjunto da foto na divisão.
        tamanho: (largura, altura) de exibição na escala nativa.
        escalas: Pares (fator, lado do tile).

    Returns:
        A foto indexada.

    Raises:
        ValueError: Se algum fator não dividir o tamanho ou a imagem reduzida
            for menor que o tile.
    """
    largura, altura = tamanho
    grades = []
    for fator, lado in escalas:
        largura_escala, altura_escala = tamanho_na_escala(largura, altura, fator)
        grades.append(
            GradeFoto(
                fator, inicios(largura_escala, lado), inicios(altura_escala, lado)
            )
        )
    return FotoIndexada(foto, conjunto, largura, altura, tuple(grades))


def indexar(
    tamanhos: Mapping[str, tuple[int, int]],
    divisao: Divisao,
    escalas: Sequence[tuple[int, int]],
) -> tuple[FotoIndexada, ...]:
    """Indexa todas as fotos da divisão, em ordem alfabética de caminho.

    Args:
        tamanhos: Tamanho de exibição na escala nativa, por foto.
        divisao: A divisão gravada, que dá o conjunto de cada foto.
        escalas: Pares (fator, lado do tile).

    Returns:
        As fotos indexadas.

    Raises:
        ValueError: Se as fotos com tamanho não forem exatamente as da divisão.
    """
    fotos = {*divisao.treino, *divisao.validacao, *divisao.teste}
    if set(tamanhos) != fotos:
        raise ValueError("As fotos com tamanho não são exatamente as da divisão.")
    return tuple(
        indexar_foto(foto, divisao.conjunto_de(foto), tamanhos[foto], escalas)
        for foto in sorted(fotos)
    )


@dataclass(frozen=True, slots=True)
class IndiceTiles:
    """O índice de tiles de uma fonte e a procedência dele.

    Attributes:
        fonte_id: Identificador da fonte.
        sha256_split: Hash do registro da divisão usado.
        sha256_manifesto: Hash do manifesto de arquivos da fonte.
        escalas: Pares (fator, lado do tile), com fatores distintos.
        fotos: As fotos indexadas, em ordem alfabética de caminho.
    """

    fonte_id: str
    sha256_split: str
    sha256_manifesto: str
    escalas: tuple[tuple[int, int], ...]
    fotos: tuple[FotoIndexada, ...]

    def __post_init__(self) -> None:
        """Recusa índices mal formados."""
        if not self.fonte_id:
            raise ValueError("A fonte não pode ser vazia.")
        for valor in (self.sha256_split, self.sha256_manifesto):
            if not PADRAO_SHA256.fullmatch(valor):
                raise ValueError("Os hashes devem ter 64 hexadecimais minúsculos.")
        fatores = [fator for fator, _ in self.escalas]
        if not fatores or len(set(fatores)) != len(fatores):
            raise ValueError("As escalas devem ter fatores distintos.")
        nomes = [foto.foto for foto in self.fotos]
        if nomes != sorted(set(nomes)):
            raise ValueError("As fotos devem ser únicas e em ordem alfabética.")
        for foto in self.fotos:
            if foto.conjunto not in CONJUNTOS:
                raise ValueError(f"Conjunto desconhecido: {foto.conjunto!r}.")
            if [grade.fator for grade in foto.grades] != fatores:
                raise ValueError(f"As grades de {foto.foto} não seguem as escalas.")

    @property
    def n_tiles(self) -> int:
        """Quantidade total de tiles, somando as escalas."""
        return sum(grade.n_tiles for foto in self.fotos for grade in foto.grades)
