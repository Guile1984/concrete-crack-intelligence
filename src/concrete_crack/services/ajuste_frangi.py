"""Busca em grade do Frangi na validação (A66, itens 4 a 6).

Avalia as configurações da grade em cada foto, com os mapas por escala vindos
do port ``MapasPorEscala``; agrega no recorte da A63; escolhe a maior média
por imagem do clDice, com o desempate pela ordem da grade; e avalia o
preditor trivial nas mesmas fotos, como linha de base (A62, item 8).

O esqueleto do gabarito não depende da configuração: é calculado uma vez por
foto, e não uma vez por configuração.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from ..domain.agregacao import ImagemAvaliada, Resumo, resumir
from ..domain.avaliacao import acuracia_global, avaliar_imagem, tudo_e_fundo
from ..domain.bootstrap import Intervalo, bootstrap_pareado
from ..domain.grade import ConfiguracaoFrangi, combinar_faixa, segmentar
from ..domain.metricas import (
    cldice_de_contagens,
    contar,
    contar_esqueletos,
    esqueleto,
)
from ..domain.posprocessamento import conferir_mapa
from ..ports.mapas_por_escala import MapasPorEscala


@dataclass(frozen=True, slots=True)
class AvaliacaoGrade:
    """As imagens avaliadas de cada configuração e do preditor trivial.

    Attributes:
        por_configuracao: Para cada configuração, na ordem da grade, as fotos
            avaliadas, na ordem das fotos.
        trivial: As mesmas fotos avaliadas pelo preditor "tudo é fundo".
    """

    por_configuracao: tuple[tuple[ConfiguracaoFrangi, tuple[ImagemAvaliada, ...]], ...]
    trivial: tuple[ImagemAvaliada, ...]


def avaliar_grade(
    fotos: Sequence[str],
    ler_gabarito: Callable[[str], np.ndarray],
    mapas: MapasPorEscala,
    configuracoes: Sequence[ConfiguracaoFrangi],
    conectividade: int,
    metodo_esqueleto: str,
    progresso: Callable[[int, int], None] | None = None,
) -> AvaliacaoGrade:
    """Avalia todas as configurações em todas as fotos.

    Args:
        fotos: As fotos da validação.
        ler_gabarito: Devolve a máscara booleana do gabarito de uma foto.
        mapas: A fonte dos mapas por escala.
        configuracoes: A grade, na ordem do desempate.
        conectividade: ``REGRAS.conectividade_componentes``.
        metodo_esqueleto: ``REGRAS.metodo_esqueleto``.
        progresso: Função chamada com (fotos feitas, total) após cada foto.

    Returns:
        As imagens avaliadas de cada configuração e do trivial.

    Raises:
        ValueError: Se alguma foto se repetir ou algum mapa sair do contrato.
    """
    if len(set(fotos)) != len(fotos):
        raise ValueError("Cada foto deve aparecer uma única vez.")
    avaliadas: dict[ConfiguracaoFrangi, list[ImagemAvaliada]] = {
        configuracao: [] for configuracao in configuracoes
    }
    trivial = []
    for feitas, foto in enumerate(fotos, start=1):
        gabarito = ler_gabarito(foto)
        esqueleto_gabarito = esqueleto(gabarito, metodo_esqueleto)
        por_escala: dict[tuple[float, float], np.ndarray] = {}
        for configuracao in configuracoes:
            for sigma in configuracao.faixa:
                chave = (sigma, configuracao.sigma_fundo)
                if chave not in por_escala:
                    por_escala[chave] = mapas.mapa(foto, *chave)
                    conferir_mapa(por_escala[chave], gabarito.shape)
            mapa = combinar_faixa(
                [por_escala[(s, configuracao.sigma_fundo)] for s in configuracao.faixa]
            )
            previsao = segmentar(
                mapa, configuracao.limiar, configuracao.tamanho_minimo, conectividade
            )
            avaliadas[configuracao].append(
                ImagemAvaliada(
                    foto,
                    contar(previsao, gabarito),
                    contar_esqueletos(
                        previsao,
                        gabarito,
                        esqueleto(previsao, metodo_esqueleto),
                        esqueleto_gabarito,
                    ),
                )
            )
        trivial.append(
            avaliar_imagem(foto, tudo_e_fundo(gabarito), gabarito, metodo_esqueleto)
        )
        if progresso is not None:
            progresso(feitas, len(fotos))
    return AvaliacaoGrade(
        tuple((c, tuple(avaliadas[c])) for c in configuracoes), tuple(trivial)
    )


@dataclass(frozen=True, slots=True)
class ResultadoGrade:
    """O resumo de cada configuração, a escolhida e a linha de base.

    Attributes:
        resumos: Configuração e resumo, na ordem da grade.
        indice_escolhida: Posição da escolhida em ``resumos``.
        trivial: Resumo do preditor trivial.
        acuracia_trivial: Acurácia global do trivial, com e sem fissura.
    """

    resumos: tuple[tuple[ConfiguracaoFrangi, Resumo], ...]
    indice_escolhida: int
    trivial: Resumo
    acuracia_trivial: float | None

    @property
    def escolhida(self) -> tuple[ConfiguracaoFrangi, Resumo]:
        """A configuração escolhida e o seu resumo."""
        return self.resumos[self.indice_escolhida]


def escolher(resumos: Sequence[tuple[ConfiguracaoFrangi, Resumo]]) -> int:
    """Escolhe a maior média por imagem do clDice; no empate, a primeira.

    Args:
        resumos: Configuração e resumo, na ordem da grade.

    Returns:
        A posição da escolhida.

    Raises:
        ValueError: Se não houver resumos ou nenhum tiver clDice definido.
    """
    melhor: int | None = None
    melhor_valor = 0.0
    for indice, (_, resumo) in enumerate(resumos):
        valor = resumo.cldice.valor
        if valor is not None and (melhor is None or valor > melhor_valor):
            melhor, melhor_valor = indice, valor
    if melhor is None:
        raise ValueError("Nenhuma configuração tem clDice definido.")
    return melhor


def resumir_grade(avaliacao: AvaliacaoGrade) -> ResultadoGrade:
    """Resume cada configuração no recorte da A63 e escolhe a melhor.

    Args:
        avaliacao: O resultado de ``avaliar_grade``.

    Returns:
        Os resumos, a escolhida e a linha de base.
    """
    resumos = tuple(
        (configuracao, resumir(imagens))
        for configuracao, imagens in avaliacao.por_configuracao
    )
    return ResultadoGrade(
        resumos,
        escolher(resumos),
        resumir(avaliacao.trivial),
        acuracia_global(avaliacao.trivial),
    )


def intervalo_cldice(
    imagens: Sequence[ImagemAvaliada],
    grupo_de: Mapping[str, str],
    n_reamostragens: int,
    nivel: float,
    seed: int,
) -> Intervalo:
    """Intervalo da média por imagem do clDice, sorteando grupos inteiros.

    Usa o bootstrap pareado da A62 com a diferença contra zero, ou seja, o
    intervalo do próprio clDice; só as imagens do recorte da A63 entram.

    Args:
        imagens: As imagens avaliadas de uma configuração.
        grupo_de: O grupo da A49 de cada foto.
        n_reamostragens: ``REGRAS.n_reamostragens_bootstrap``.
        nivel: ``REGRAS.nivel_confianca_bootstrap``.
        seed: ``REGRAS.seed_bootstrap``.

    Returns:
        A estimativa e o intervalo.

    Raises:
        KeyError: Se alguma foto não tiver grupo.
    """
    valores = []
    grupos = []
    for imagem in imagens:
        valor = cldice_de_contagens(imagem.esqueletos)
        if imagem.tem_fissura and valor is not None:
            valores.append(valor)
            grupos.append(grupo_de[imagem.imagem])
    return bootstrap_pareado(valores, grupos, n_reamostragens, nivel, seed)
