"""Testes do bootstrap pareado e da regra do critério 1 (A62, itens 6 e 7)."""

import numpy as np
import pytest

from concrete_crack.domain.bootstrap import (
    INCONCLUSIVO,
    INFERIOR,
    SUPERIOR,
    Intervalo,
    bootstrap_pareado,
    decidir,
)

B, NIVEL, SEED = 10_000, 0.95, 20261117


def test_diferencas_iguais_dao_intervalo_de_largura_zero() -> None:
    intervalo = bootstrap_pareado([0.25] * 8, list("aabbccdd"), B, NIVEL, SEED)
    assert intervalo == Intervalo(0.25, 0.25, 0.25)


def test_um_grupo_so_nao_tem_variacao_para_reamostrar() -> None:
    intervalo = bootstrap_pareado([0.1, 0.3, 0.5], ["g"] * 3, B, NIVEL, SEED)
    assert intervalo.inferior == intervalo.superior == pytest.approx(0.3)


def test_estimativa_e_media_por_imagem_e_nao_por_grupo() -> None:
    # grupo a: 1, 1, 1; grupo b: 0. Por imagem: 3/4; por grupo seria 1/2
    intervalo = bootstrap_pareado([1.0, 1.0, 1.0, 0.0], list("aaab"), B, NIVEL, SEED)
    assert intervalo.estimativa == 0.75


def test_mesma_seed_repete_o_intervalo() -> None:
    gerador = np.random.default_rng(1)
    diferencas = list(gerador.normal(0.05, 0.2, 60))
    grupos = [str(i) for i in range(60)]
    primeiro = bootstrap_pareado(diferencas, grupos, B, NIVEL, SEED)
    assert bootstrap_pareado(diferencas, grupos, B, NIVEL, SEED) == primeiro
    assert bootstrap_pareado(diferencas, grupos, B, NIVEL, SEED + 1) != primeiro


def test_largura_bate_com_a_teoria_para_imagens_independentes() -> None:
    # 400 imagens com desvio 1: erro padrão 1/20; largura ≈ 2 x 1,96 / 20 = 0,196
    gerador = np.random.default_rng(2)
    diferencas = list(gerador.normal(0.0, 1.0, 400))
    intervalo = bootstrap_pareado(
        diferencas, [str(i) for i in range(400)], B, NIVEL, SEED
    )
    assert intervalo.superior - intervalo.inferior == pytest.approx(0.196, rel=0.1)


def test_sortear_por_grupo_alarga_o_intervalo_de_fotos_parecidas() -> None:
    # 10 grupos de 10 fotos idênticas, metade +1 e metade -1 (ρ = 1):
    # efeito de desenho 1 + (10 - 1) x 1 = 10, largura cerca de √10 ≈ 3,2 vezes
    diferencas = [1.0 if g % 2 else -1.0 for g in range(10) for _ in range(10)]
    por_grupo = [str(g) for g in range(10) for _ in range(10)]
    por_imagem = [str(i) for i in range(100)]
    grupo = bootstrap_pareado(diferencas, por_grupo, B, NIVEL, SEED)
    imagem = bootstrap_pareado(diferencas, por_imagem, B, NIVEL, SEED)
    razao = (grupo.superior - grupo.inferior) / (imagem.superior - imagem.inferior)
    assert razao > 2.5


@pytest.mark.parametrize(
    ("inferior", "superior", "esperado"),
    [
        (0.01, 0.20, SUPERIOR),
        (-0.20, -0.01, INFERIOR),
        (-0.10, 0.10, INCONCLUSIVO),
        (0.0, 0.20, INCONCLUSIVO),
        (-0.20, 0.0, INCONCLUSIVO),
    ],
)
def test_regra_do_criterio_1(inferior: float, superior: float, esperado: str) -> None:
    assert decidir(Intervalo(0.0, inferior, superior)) == esperado


@pytest.mark.parametrize(
    ("diferencas", "grupos", "n", "nivel", "trecho"),
    [
        ([], [], B, NIVEL, "não vazios"),
        ([0.1, 0.2], ["a"], B, NIVEL, "mesmo tamanho"),
        ([0.1, float("nan")], ["a", "b"], B, NIVEL, "finitas"),
        ([0.1], ["a"], 0, NIVEL, "reamostragem"),
        ([0.1], ["a"], B, 1.0, "nível"),
    ],
)
def test_entradas_invalidas_sao_recusadas(
    diferencas: list[float], grupos: list[str], n: int, nivel: float, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        bootstrap_pareado(diferencas, grupos, n, nivel, SEED)
