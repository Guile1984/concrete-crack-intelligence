"""Distribuição das fotos e da fissura por conjunto da divisão (A49).

Só relata: resume, para cada conjunto, quantas fotos recebeu, de que resoluções
armazenadas, e quanta fissura as máscaras têm no limiar de binarização. Funções
puras, sem acesso a disco; quem mede as fotos é a camada de apresentação.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from .divisao import TESTE, TREINO, VALIDACAO, Divisao


@dataclass(frozen=True, slots=True)
class MedidaFoto:
    """O que se mede de uma foto e da sua máscara.

    Attributes:
        resolucao: (largura, altura) da foto como gravada no arquivo, sem a
            rotação EXIF.
        pixels_fissura: Pixels de fissura da máscara no limiar de binarização.
        pixels_total: Total de pixels da máscara.
    """

    resolucao: tuple[int, int]
    pixels_fissura: int
    pixels_total: int

    def __post_init__(self) -> None:
        """Recusa contagens impossíveis."""
        if self.pixels_total <= 0:
            raise ValueError("O total de pixels deve ser positivo.")
        if not 0 <= self.pixels_fissura <= self.pixels_total:
            raise ValueError("Os pixels de fissura devem estar entre 0 e o total.")

    @property
    def fracao(self) -> float:
        """Fração de 0 a 1 dos pixels da máscara que são fissura."""
        return self.pixels_fissura / self.pixels_total


@dataclass(frozen=True, slots=True)
class ResumoConjunto:
    """O resumo de um conjunto da divisão.

    Attributes:
        nome: ``"treino"``, ``"validacao"`` ou ``"teste"``.
        n_fotos: Quantidade de fotos.
        resolucoes: Pares ((largura, altura), quantidade), da resolução mais
            frequente para a menos frequente.
        quartis: (1º quartil, mediana, 3º quartil) da fração de fissura por
            máscara, com interpolação linear (o padrão do numpy).
        fracao_total: Pixels de fissura do conjunto sobre os pixels do conjunto.
    """

    nome: str
    n_fotos: int
    resolucoes: tuple[tuple[tuple[int, int], int], ...]
    quartis: tuple[float, float, float]
    fracao_total: float


def resumir_conjunto(nome: str, medidas: Sequence[MedidaFoto]) -> ResumoConjunto:
    """Resume as medidas das fotos de um conjunto.

    A fração total pondera cada máscara pelo seu número de pixels; os quartis
    tratam cada máscara como um caso, qualquer que seja o tamanho.

    Args:
        nome: Nome do conjunto.
        medidas: As medidas das fotos do conjunto.

    Returns:
        O resumo do conjunto.

    Raises:
        ValueError: Se o conjunto não tiver fotos.
    """
    if not medidas:
        raise ValueError(f"O conjunto {nome} não tem fotos.")
    contagem = Counter(medida.resolucao for medida in medidas)
    resolucoes = tuple(sorted(contagem.items(), key=lambda item: (-item[1], item[0])))
    fracoes = np.array([medida.fracao for medida in medidas])
    q1, mediana, q3 = (float(q) for q in np.quantile(fracoes, (0.25, 0.5, 0.75)))
    fissura = sum(medida.pixels_fissura for medida in medidas)
    total = sum(medida.pixels_total for medida in medidas)
    return ResumoConjunto(
        nome=nome,
        n_fotos=len(medidas),
        resolucoes=resolucoes,
        quartis=(q1, mediana, q3),
        fracao_total=fissura / total,
    )


def distribuir(
    divisao: Divisao, medidas: Mapping[str, MedidaFoto]
) -> tuple[ResumoConjunto, ResumoConjunto, ResumoConjunto]:
    """Resume treino, validação e teste, nessa ordem.

    Args:
        divisao: A divisão gravada.
        medidas: A medida de cada foto da divisão, pelo caminho da foto.

    Returns:
        Os resumos do treino, da validação e do teste.

    Raises:
        ValueError: Se faltar medida para alguma foto da divisão, se houver
            medida de foto fora dela, ou se algum conjunto estiver vazio.
    """
    fotos = {*divisao.treino, *divisao.validacao, *divisao.teste}
    faltando = fotos - medidas.keys()
    sobrando = medidas.keys() - fotos
    if faltando or sobrando:
        raise ValueError(
            f"As medidas não correspondem à divisão: {len(faltando)} foto(s) sem "
            f"medida e {len(sobrando)} medida(s) de foto fora da divisão."
        )
    treino, validacao, teste = (
        resumir_conjunto(nome, [medidas[foto] for foto in conjunto])
        for nome, conjunto in (
            (TREINO, divisao.treino),
            (VALIDACAO, divisao.validacao),
            (TESTE, divisao.teste),
        )
    )
    return treino, validacao, teste
