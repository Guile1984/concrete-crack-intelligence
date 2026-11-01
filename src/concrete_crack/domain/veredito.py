"""Vereditos da inspeção das máscaras, regra de reprovação e intervalo de Wilson.

Funções puras, sem acesso a disco. O tamanho da amostra e o limiar de reprovação
vêm de fora (``config/regras.py``), pois o domínio não importa a configuração.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from statistics import NormalDist

Z_95 = NormalDist().inv_cdf(0.975)


class Veredito(Enum):
    """Veredito do Gui sobre uma máscara.

    Attributes:
        ADEQUADA: A máscara descreve a fissura de forma aceitável.
        INADEQUADA: Omite fissura visível, marca o que não é fissura ou tem
            espessura visivelmente incompatível.
        DUVIDOSA: Não foi possível decidir; é registrada e não entra na regra.
    """

    ADEQUADA = "adequada"
    INADEQUADA = "inadequada"
    DUVIDOSA = "duvidosa"


def intervalo_wilson(sucessos: int, n: int) -> tuple[float, float]:
    """Calcula o intervalo de Wilson de 95% para uma proporção.

    Args:
        sucessos: Quantidade de casos observados (0 a n).
        n: Tamanho da amostra, positivo.

    Returns:
        Os limites inferior e superior da proporção, entre 0 e 1.

    Raises:
        ValueError: Se ``n`` não for positivo ou ``sucessos`` estiver fora de 0 a n.
    """
    if n <= 0:
        raise ValueError("n deve ser positivo.")
    if not 0 <= sucessos <= n:
        raise ValueError("sucessos deve estar entre 0 e n.")
    proporcao = sucessos / n
    z2 = Z_95**2
    denominador = 1 + z2 / n
    centro = (proporcao + z2 / (2 * n)) / denominador
    margem = (
        Z_95
        * math.sqrt(proporcao * (1 - proporcao) / n + z2 / (4 * n**2))
        / denominador
    )
    inferior = 0.0 if sucessos == 0 else centro - margem
    superior = 1.0 if sucessos == n else centro + margem
    return inferior, superior


@dataclass(frozen=True, slots=True)
class ResultadoInspecao:
    """Resultado da inspeção de uma amostra de máscaras.

    Attributes:
        n: Quantidade de máscaras julgadas.
        adequadas: Quantas foram julgadas adequadas.
        inadequadas: Quantas foram julgadas inadequadas.
        duvidosas: Quantas ficaram duvidosas.
        limiar_reprovacao: Quantidade de inadequadas que reprova a fonte.
        reprovada: Verdadeiro se as inadequadas atingem o limiar (regra A31).
        reprovada_se_duvidosas_forem_inadequadas: A mesma regra, contando as
            duvidosas como inadequadas (sensibilidade).
        intervalo_inadequadas: Intervalo de Wilson de 95% da proporção de
            inadequadas.
        intervalo_sensibilidade: Intervalo de Wilson de 95% da proporção de
            inadequadas mais duvidosas.
    """

    n: int
    adequadas: int
    inadequadas: int
    duvidosas: int
    limiar_reprovacao: int
    reprovada: bool
    reprovada_se_duvidosas_forem_inadequadas: bool
    intervalo_inadequadas: tuple[float, float]
    intervalo_sensibilidade: tuple[float, float]

    @property
    def conclusao_depende_das_duvidosas(self) -> bool:
        """Verdadeiro se contar as duvidosas como inadequadas muda a decisão."""
        return self.reprovada != self.reprovada_se_duvidosas_forem_inadequadas


def avaliar(vereditos: Sequence[Veredito], limiar_reprovacao: int) -> ResultadoInspecao:
    """Aplica a regra de reprovação aos vereditos de uma amostra.

    A fonte é reprovada quando as inadequadas atingem o limiar. As duvidosas não
    entram na regra, mas a sensibilidade (contá-las como inadequadas) é
    calculada junto, para ser reportada.

    Args:
        vereditos: Um veredito por máscara julgada; não pode ser vazio.
        limiar_reprovacao: Quantidade de inadequadas que reprova; de 1 ao
            tamanho da amostra.

    Returns:
        O resultado, com contagens, decisão, sensibilidade e intervalos.

    Raises:
        ValueError: Se não houver vereditos ou o limiar estiver fora de 1 a n.
    """
    n = len(vereditos)
    if n == 0:
        raise ValueError("Não há vereditos para avaliar.")
    if not 1 <= limiar_reprovacao <= n:
        raise ValueError(
            "O limiar de reprovação deve estar entre 1 e o tamanho da amostra."
        )
    inadequadas = sum(1 for v in vereditos if v is Veredito.INADEQUADA)
    duvidosas = sum(1 for v in vereditos if v is Veredito.DUVIDOSA)
    return ResultadoInspecao(
        n=n,
        adequadas=n - inadequadas - duvidosas,
        inadequadas=inadequadas,
        duvidosas=duvidosas,
        limiar_reprovacao=limiar_reprovacao,
        reprovada=inadequadas >= limiar_reprovacao,
        reprovada_se_duvidosas_forem_inadequadas=(
            inadequadas + duvidosas >= limiar_reprovacao
        ),
        intervalo_inadequadas=intervalo_wilson(inadequadas, n),
        intervalo_sensibilidade=intervalo_wilson(inadequadas + duvidosas, n),
    )
