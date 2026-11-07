"""Árvore de decisão da escalada para embeddings, pré-registrada na A45.

Função pura: recebe a avaliação dos critérios (a) e (b), o agrupamento e a
densidade do maior grupo, e devolve o desfecho. A ordem das perguntas é a da
A45: pares demais (b) decidem primeiro, com ou sem (a); depois o maior grupo
(a); sem nenhum dos dois, os embeddings são aprovados.
"""

from dataclasses import dataclass
from enum import StrEnum

from .duplicatas import Agrupamento, AvaliacaoHash, e_serie_real


class Desfecho(StrEnum):
    """O que fazer com os grupos, conforme a A45."""

    APROVADO = "aprovado"
    GRUPO_NO_TREINO = "grupo_no_treino"
    VOLTAR_AO_DHASH = "voltar_ao_dhash"
    TESTE_EXTERNO = "teste_externo"


@dataclass(frozen=True, slots=True)
class DecisaoEscalada:
    """O desfecho e a classificação do maior grupo.

    Attributes:
        desfecho: O que fazer com os grupos.
        serie_real: Verdadeiro se o maior grupo foi declarado série real, falso
            se corrente; None quando a classificação não se aplica (aprovado ou
            volta ao dHash).
    """

    desfecho: Desfecho
    serie_real: bool | None


def decidir_escalada(
    avaliacao: AvaliacaoHash,
    agrupamento: Agrupamento,
    densidade_maior_grupo: float,
    proporcao_treino: float,
    densidade_minima: float,
) -> DecisaoEscalada:
    """Aplica a árvore de decisão da A45.

    Args:
        avaliacao: Resultado dos critérios (a) e (b) para os embeddings.
        agrupamento: Grupos das fotos reais pelos embeddings.
        densidade_maior_grupo: Densidade do maior grupo, de 0 a 1.
        proporcao_treino: Fração das fotos que cabe no treino.
        densidade_minima: Corte de série real.

    Returns:
        A decisão.
    """
    if avaliacao.pares_demais:
        return DecisaoEscalada(Desfecho.VOLTAR_AO_DHASH, None)
    if avaliacao.grupo_grande_demais:
        serie = e_serie_real(densidade_maior_grupo, densidade_minima)
        cabe = agrupamento.maior_grupo <= proporcao_treino * agrupamento.n_imagens
        desfecho = Desfecho.GRUPO_NO_TREINO if cabe else Desfecho.TESTE_EXTERNO
        return DecisaoEscalada(desfecho, serie)
    return DecisaoEscalada(Desfecho.APROVADO, None)
