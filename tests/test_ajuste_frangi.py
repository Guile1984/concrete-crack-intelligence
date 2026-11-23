"""Testes da busca em grade do Frangi (A66), com mapas e gabaritos sintéticos."""

import numpy as np
import pytest

from concrete_crack.domain.agregacao import Media
from concrete_crack.domain.avaliacao import avaliar_imagem
from concrete_crack.domain.bootstrap import Intervalo
from concrete_crack.domain.grade import (
    ConfiguracaoFrangi,
    combinar_faixa,
    configuracoes_da_grade,
    segmentar,
)
from concrete_crack.services.ajuste_frangi import (
    AvaliacaoGrade,
    avaliar_grade,
    escolher,
    intervalo_cldice,
    resumir_grade,
)

ZHANG = "zhang"
FORMATO = (30, 40)
GRADE = configuracoes_da_grade(((1.0,), (1.0, 2.0)), (0.0, 8.0), (0.5, 0.95), (0, 3))


def gabarito(foto: str) -> np.ndarray:
    """Barra de 3 x 31 px nas fotos "a" e "b"; a foto "c" não tem fissura."""
    mascara = np.zeros(FORMATO, dtype=bool)
    linha = {"a": 10, "b": 18}.get(foto)
    if linha is not None:
        mascara[linha : linha + 3, 5:36] = True
    return mascara


class MapasFalsos:
    """Mapas por escala montados à mão, que anotam cada pedido.

    Na escala 1, a barra vale 0,6 (fundo 0) ou 0,9 (fundo 8), uma mancha de
    2 px vale 0,95 e o resto 0,2; na escala 2, tudo é menor que na escala 1.
    """

    def __init__(self) -> None:
        """Começa sem pedidos."""
        self.pedidos: list[tuple[str, float, float]] = []

    def mapa(self, foto: str, sigma: float, sigma_fundo: float) -> np.ndarray:
        """Devolve o mapa sintético e anota o pedido."""
        self.pedidos.append((foto, sigma, sigma_fundo))
        mapa = np.full(FORMATO, 0.2)
        mapa[gabarito(foto)] = 0.6 if sigma_fundo == 0 else 0.9
        mapa[25, 5:7] = 0.95
        return mapa if sigma == 1.0 else mapa / 2


def rodar() -> tuple[MapasFalsos, AvaliacaoGrade]:
    """Roda a grade nas três fotos e devolve os mapas e a avaliação."""
    mapas = MapasFalsos()
    avaliacao = avaliar_grade(["a", "b", "c"], gabarito, mapas, GRADE, 8, ZHANG)
    return mapas, avaliacao


def test_escolhe_a_primeira_das_empatadas() -> None:
    # limiar 0,5 com tamanho 3 pega só a barra (clDice 1) em 4 configurações
    # (2 faixas x 2 fundos); a primeira na ordem da grade é a de índice 1
    resultado = resumir_grade(rodar()[1])
    assert resultado.indice_escolhida == 1
    configuracao, resumo = resultado.escolhida
    assert configuracao == ConfiguracaoFrangi((1.0,), 0.0, 0.5, 3)
    assert resumo.cldice == Media(1.0, 2, 0)
    assert (resumo.n_imagens, resumo.n_com_fissura) == (3, 2)


def test_resultados_iguais_aos_da_avaliacao_direta() -> None:
    # calcular o esqueleto do gabarito uma vez por foto não muda nada
    mapas = MapasFalsos()
    avaliacao = rodar()[1]
    for configuracao, imagens in avaliacao.por_configuracao:
        for imagem in imagens:
            mapa = combinar_faixa(
                [
                    mapas.mapa(imagem.imagem, s, configuracao.sigma_fundo)
                    for s in configuracao.faixa
                ]
            )
            previsao = segmentar(
                mapa, configuracao.limiar, configuracao.tamanho_minimo, 8
            )
            direta = avaliar_imagem(
                imagem.imagem, previsao, gabarito(imagem.imagem), ZHANG
            )
            assert imagem == direta


def test_cada_mapa_por_escala_e_pedido_uma_vez() -> None:
    # 3 fotos x 2 escalas x 2 fundos, embora 16 configurações os usem
    mapas = rodar()[0]
    assert len(mapas.pedidos) == 12 and len(set(mapas.pedidos)) == 12


def test_trivial_ao_lado() -> None:
    resultado = resumir_grade(rodar()[1])
    assert resultado.trivial.dice == Media(0.0, 2, 0)
    # 3 fotos de 1.200 px; 2 barras de 93 px: (3.600 - 186) / 3.600
    assert resultado.acuracia_trivial == pytest.approx(3414 / 3600)


def test_intervalo_so_com_as_fotos_com_fissura() -> None:
    avaliacao = rodar()[1]
    imagens = dict(avaliacao.por_configuracao)[GRADE[1]]
    intervalo = intervalo_cldice(imagens, {"a": "g1", "b": "g2"}, 1000, 0.95, 1)
    assert intervalo == Intervalo(1.0, 1.0, 1.0)
    with pytest.raises(KeyError):
        intervalo_cldice(imagens, {"a": "g1"}, 1000, 0.95, 1)


def test_mapa_fora_do_contrato_e_recusado() -> None:
    class Errado(MapasFalsos):
        """Devolve mapas com o formato errado."""

        def mapa(self, foto: str, sigma: float, sigma_fundo: float) -> np.ndarray:
            """Devolve um mapa menor que a foto."""
            return np.zeros((10, 10))

    with pytest.raises(ValueError, match="formato"):
        avaliar_grade(["a"], gabarito, Errado(), GRADE, 8, ZHANG)


def test_foto_repetida_e_recusada() -> None:
    with pytest.raises(ValueError, match="única vez"):
        avaliar_grade(["a", "a"], gabarito, MapasFalsos(), GRADE, 8, ZHANG)


def test_sem_cldice_definido_nao_ha_escolha() -> None:
    avaliacao = avaliar_grade(["c"], gabarito, MapasFalsos(), GRADE, 8, ZHANG)
    with pytest.raises(ValueError, match="Nenhuma"):
        resumir_grade(avaliacao)
    with pytest.raises(ValueError, match="Nenhuma"):
        escolher([])
