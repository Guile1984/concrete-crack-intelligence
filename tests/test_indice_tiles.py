"""Testes do índice de tiles (A52, item 6), com grades conferidas à mão."""

from dataclasses import replace

import pytest

from concrete_crack.domain.divisao import Divisao
from concrete_crack.domain.indice_tiles import (
    GradeFoto,
    IndiceTiles,
    indexar,
    indexar_foto,
)

ESCALAS = ((1, 512), (2, 256))


def test_foto_de_4032_por_3024_nas_duas_escalas() -> None:
    indexada = indexar_foto("rgb/001.jpg", "treino", (4032, 3024), ESCALAS)
    nativa, reduzida = indexada.grades
    assert nativa == GradeFoto(
        1,
        (0, 512, 1024, 1536, 2048, 2560, 3072, 3520),
        (0, 512, 1024, 1536, 2048, 2512),
    )
    # 2016 x 1512: últimos encostados em 2016 - 256 = 1760 e 1512 - 256 = 1256
    assert reduzida == GradeFoto(
        2, (0, 256, 512, 768, 1024, 1280, 1536, 1760), (0, 256, 512, 768, 1024, 1256)
    )
    assert (nativa.n_tiles, reduzida.n_tiles) == (48, 48)


@pytest.mark.parametrize(
    "tamanho", [(4032, 3024), (3024, 4032), (3264, 2448), (2448, 3264)]
)
def test_tiles_das_duas_escalas_cobrem_as_mesmas_regioes_da_foto(
    tamanho: tuple[int, int],
) -> None:
    nativa, reduzida = indexar_foto("rgb/x.jpg", "teste", tamanho, ESCALAS).grades
    assert tuple(2 * x for x in reduzida.xs) == nativa.xs
    assert tuple(2 * y for y in reduzida.ys) == nativa.ys


def test_retrato_troca_colunas_e_linhas() -> None:
    paisagem = indexar_foto("a", "treino", (4032, 3024), ESCALAS).grades[0]
    retrato = indexar_foto("b", "treino", (3024, 4032), ESCALAS).grades[0]
    assert (retrato.xs, retrato.ys) == (paisagem.ys, paisagem.xs)


DIVISAO = Divisao(("rgb/b.jpg",), ("rgb/c.jpg",), ("rgb/a.jpg",))
TAMANHOS = {
    "rgb/a.jpg": (4032, 3024),
    "rgb/b.jpg": (3024, 4032),
    "rgb/c.jpg": (3264, 2448),
}


def test_indexa_em_ordem_alfabetica_com_o_conjunto_da_divisao() -> None:
    fotos = indexar(TAMANHOS, DIVISAO, ESCALAS)
    assert [(f.foto, f.conjunto) for f in fotos] == [
        ("rgb/a.jpg", "teste"),
        ("rgb/b.jpg", "treino"),
        ("rgb/c.jpg", "validacao"),
    ]
    assert (fotos[1].largura, fotos[1].altura) == (3024, 4032)


def test_fotos_diferentes_das_da_divisao_sao_recusadas() -> None:
    incompleto = {k: v for k, v in TAMANHOS.items() if k != "rgb/c.jpg"}
    with pytest.raises(ValueError, match="exatamente as da divisão"):
        indexar(incompleto, DIVISAO, ESCALAS)


INDICE = IndiceTiles(
    fonte_id="ccsd",
    sha256_split="a" * 64,
    sha256_manifesto="b" * 64,
    escalas=ESCALAS,
    fotos=indexar(TAMANHOS, DIVISAO, ESCALAS),
)


def test_total_de_tiles_soma_fotos_e_escalas() -> None:
    # (48 + 48) + (48 + 48) + (35 + 35)
    assert INDICE.n_tiles == 262


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("fonte_id", "", "vazia"),
        ("sha256_split", "x" * 64, "hashes"),
        ("escalas", ((1, 512), (1, 256)), "fatores distintos"),
        ("fotos", tuple(reversed(INDICE.fotos)), "ordem alfabética"),
        ("fotos", (replace(INDICE.fotos[0], conjunto="outro"),), "desconhecido"),
        ("escalas", ((1, 512),), "não seguem as escalas"),
    ],
)
def test_indices_invalidos_sao_recusados(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(INDICE, **{campo: valor})
