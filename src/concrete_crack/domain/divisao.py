"""Divisão das imagens-mãe em treino, validação e teste por grupos (A49).

Função pura e determinística: cada grupo recebe a chave
``sha256("<seed>:<primeiro nome do grupo em ordem alfabética>")`` e os grupos
são percorridos em ordem crescente de chave. Cada grupo vai para o teste se
couber, senão para a validação se couber, senão para o treino. Um grupo nunca
é partido, e o resultado não depende da ordem em que os grupos chegam nem de
nenhuma biblioteca de números aleatórios.
"""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass

from .pesos import PADRAO_SHA256

TREINO = "treino"
VALIDACAO = "validacao"
TESTE = "teste"


def tamanhos_alvo(
    n_fotos: int, proporcao_validacao: float, proporcao_teste: float
) -> tuple[int, int, int]:
    """Calcula quantas fotos vão para treino, validação e teste.

    Validação e teste são arredondados com ``round`` (a metade vai para o par);
    o treino fica com o restante, para que a soma seja exatamente ``n_fotos``.

    Args:
        n_fotos: Total de fotos.
        proporcao_validacao: Fração da validação, em (0, 1).
        proporcao_teste: Fração do teste, em (0, 1).

    Returns:
        (treino, validação, teste).

    Raises:
        ValueError: Se as proporções não deixarem fotos para o treino.
    """
    validacao = round(proporcao_validacao * n_fotos)
    teste = round(proporcao_teste * n_fotos)
    treino = n_fotos - validacao - teste
    if treino <= 0 or validacao < 0 or teste < 0:
        raise ValueError("As proporções não deixam fotos para o treino.")
    return treino, validacao, teste


def chave_do_grupo(seed: int, grupo: Sequence[str]) -> str:
    """Devolve a chave de sorteio de um grupo: o hash do seu primeiro nome.

    Args:
        seed: Semente da divisão.
        grupo: Nomes das fotos do grupo, não vazio.

    Returns:
        O SHA-256 hexadecimal de ``"<seed>:<menor nome>"``.
    """
    return hashlib.sha256(f"{seed}:{min(grupo)}".encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Divisao:
    """As fotos de cada conjunto, em ordem alfabética.

    Attributes:
        treino: Fotos do treino.
        validacao: Fotos da validação.
        teste: Fotos do teste.
    """

    treino: tuple[str, ...]
    validacao: tuple[str, ...]
    teste: tuple[str, ...]

    def conjunto_de(self, foto: str) -> str:
        """Diz em que conjunto está uma foto.

        Args:
            foto: Nome da foto.

        Returns:
            ``"treino"``, ``"validacao"`` ou ``"teste"``.

        Raises:
            KeyError: Se a foto não estiver em nenhum conjunto.
        """
        for nome, fotos in (
            (TREINO, self.treino),
            (VALIDACAO, self.validacao),
            (TESTE, self.teste),
        ):
            if foto in fotos:
                return nome
        raise KeyError(foto)


def dividir_por_grupos(
    grupos: Sequence[Sequence[str]], seed: int, n_validacao: int, n_teste: int
) -> Divisao:
    """Divide os grupos conforme a A49.

    Args:
        grupos: Os grupos de fotos; cada foto aparece em um só grupo.
        seed: Semente da divisão.
        n_validacao: Quantidade exata de fotos da validação.
        n_teste: Quantidade exata de fotos do teste.

    Returns:
        A divisão, com cada conjunto em ordem alfabética.

    Raises:
        ValueError: Se houver grupo vazio, foto repetida, alvo negativo ou
            maior que o total, ou se teste e validação não puderem ser
            preenchidos exatamente.
    """
    if any(not grupo for grupo in grupos):
        raise ValueError("Há um grupo vazio.")
    fotos = [foto for grupo in grupos for foto in grupo]
    if len(fotos) != len(set(fotos)):
        raise ValueError("Uma foto aparece em mais de um grupo.")
    if n_validacao < 0 or n_teste < 0 or n_validacao + n_teste > len(fotos):
        raise ValueError("Os tamanhos de validação e teste são inválidos.")
    ordem = sorted(grupos, key=lambda grupo: chave_do_grupo(seed, grupo))
    teste: list[str] = []
    validacao: list[str] = []
    treino: list[str] = []
    for grupo in ordem:
        if len(teste) + len(grupo) <= n_teste:
            teste.extend(grupo)
        elif len(validacao) + len(grupo) <= n_validacao:
            validacao.extend(grupo)
        else:
            treino.extend(grupo)
    if len(teste) != n_teste or len(validacao) != n_validacao:
        raise ValueError(
            f"Não foi possível preencher exatamente o teste ({len(teste)} de "
            f"{n_teste}) e a validação ({len(validacao)} de {n_validacao})."
        )
    return Divisao(
        tuple(sorted(treino)), tuple(sorted(validacao)), tuple(sorted(teste))
    )


@dataclass(frozen=True, slots=True)
class RegistroDivisao:
    """A divisão gravada e a procedência dela.

    Attributes:
        fonte_id: Identificador da fonte.
        seed: Semente do sorteio.
        proporcoes: (treino, validação, teste) pré-registradas.
        sha256_grupos: Hash do registro de grupos sorteado.
        sha256_manifesto: Hash do manifesto de arquivos da fonte.
        divisao: As fotos de cada conjunto.
    """

    fonte_id: str
    seed: int
    proporcoes: tuple[float, float, float]
    sha256_grupos: str
    sha256_manifesto: str
    divisao: Divisao

    def __post_init__(self) -> None:
        """Recusa registros mal formados ou com uma foto em dois conjuntos."""
        if not self.fonte_id:
            raise ValueError("A fonte não pode ser vazia.")
        for valor in (self.sha256_grupos, self.sha256_manifesto):
            if not PADRAO_SHA256.fullmatch(valor):
                raise ValueError("Os hashes devem ter 64 hexadecimais minúsculos.")
        if abs(sum(self.proporcoes) - 1.0) > 1e-9:
            raise ValueError("As proporções devem somar 1.")
        conjuntos = (self.divisao.treino, self.divisao.validacao, self.divisao.teste)
        fotos = [foto for conjunto in conjuntos for foto in conjunto]
        if len(fotos) != len(set(fotos)):
            raise ValueError("Uma foto aparece em mais de um conjunto.")
