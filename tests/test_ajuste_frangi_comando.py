"""Testes do comando de ajuste do Frangi, com a grade pré-registrada inteira."""

import json
from pathlib import Path

import numpy as np
import pytest

from concrete_crack.config.caminhos import caminho_ajuste_frangi
from concrete_crack.domain.bootstrap import Intervalo
from concrete_crack.domain.grade import ConfiguracaoFrangi
from concrete_crack.presentation.ajuste_frangi import ajustar, main, montar_registros
from concrete_crack.services.ajuste_frangi import ResultadoGrade

FORMATO = (30, 50)


def gabarito(foto: str) -> np.ndarray:
    """Barra de 3 x 40 px (120 px) nas fotos "a" e "b"; "c" não tem fissura."""
    mascara = np.zeros(FORMATO, dtype=bool)
    linha = {"a": 10, "b": 18}.get(foto)
    if linha is not None:
        mascara[linha : linha + 3, 5:45] = True
    return mascara


class MapasFalsos:
    """Barra 0,6 (fundo 0) ou 0,9 (fundo 64), mancha 0,95, fundo 0,2.

    Valores da escala 1; nas outras escalas, tudo vale a metade.
    """

    def mapa(self, foto: str, sigma: float, sigma_fundo: float) -> np.ndarray:
        """Devolve o mapa sintético."""
        mapa = np.full(FORMATO, 0.2)
        mapa[gabarito(foto)] = 0.6 if sigma_fundo == 0 else 0.9
        mapa[25, 5:7] = 0.95
        return mapa if sigma == 1.0 else mapa / 2


@pytest.fixture(scope="module")
def ajuste() -> tuple[ResultadoGrade, Intervalo]:
    """A grade pré-registrada inteira, nas três fotos sintéticas."""
    grupos = {"a": "g1", "b": "g2", "c": "g3"}
    return ajustar(["a", "b", "c"], grupos, gabarito, MapasFalsos())


def test_escolhe_a_primeira_que_isola_a_barra(
    ajuste: tuple[ResultadoGrade, Intervalo],
) -> None:
    # limiar 0,25 (o primeiro acima do fundo 0,2) com tamanho 100 (a mancha some,
    # a barra de 120 px fica): posição 2 x 3 + 1 = 7 na grade
    resultado, intervalo = ajuste
    assert resultado.indice_escolhida == 7
    assert resultado.escolhida[0] == ConfiguracaoFrangi((1.0, 2.0, 4.0), 0.0, 0.25, 100)
    assert intervalo == Intervalo(1.0, 1.0, 1.0)


def test_registros_tem_o_resumo_e_as_240_linhas(
    ajuste: tuple[ResultadoGrade, Intervalo],
) -> None:
    resultado, intervalo = ajuste
    resumo, linhas = montar_registros(resultado, intervalo, {"fonte_id": "x"})
    assert len(linhas) == 240
    assert resumo["fonte_id"] == "x"
    escolhida = json.loads(json.dumps(resumo))["escolhida"]
    assert escolhida["indice"] == 7
    assert escolhida["configuracao"]["faixa"] == [1.0, 2.0, 4.0]
    assert escolhida["intervalo"]["superior"] == 1.0
    assert json.loads(json.dumps(linhas[7])) == {
        "configuracao": escolhida["configuracao"],
        "resumo": escolhida["resumo"],
    }


def test_comando_se_recusa_a_refazer_a_escolha(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    destino = caminho_ajuste_frangi(tmp_path)
    destino.parent.mkdir(parents=True)
    destino.write_text("{}\n", encoding="utf-8")
    assert main(["--raiz", str(tmp_path), "ccsd"]) == 2
    assert "uma única vez" in capsys.readouterr().err
