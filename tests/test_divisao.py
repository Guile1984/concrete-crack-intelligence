"""Testes de vazamento da divisão por grupos, em mini-datasets sintéticos (A49)."""

import hashlib

import pytest

from concrete_crack.domain.divisao import (
    Divisao,
    chave_do_grupo,
    dividir_por_grupos,
    tamanhos_alvo,
)

# Mini-dataset conferido à mão (seed 7). Chaves sha256("7:<nome>"), 8 primeiros
# caracteres: e 18fdd435 < g 4bfe3339 < b 5836b79b < c 66c3f8b0 < f dfbb6254
# < a f18f4f9d. Percorrendo nessa ordem com teste = 2 e validação = 2:
# e e g enchem o teste; b vai para a validação; o par (c, d) não cabe nela
# (1 + 2 > 2) e vai para o treino; f completa a validação; a vai para o treino.
MINI = [("a.jpg",), ("b.jpg",), ("c.jpg", "d.jpg"), ("e.jpg",), ("f.jpg",), ("g.jpg",)]


def grupos_sinteticos(n_isoladas: int = 40, n_pares: int = 5) -> list[tuple[str, ...]]:
    isoladas = [(f"foto_{i:03d}.jpg",) for i in range(n_isoladas)]
    pares = [(f"par_{i:02d}_a.jpg", f"par_{i:02d}_b.jpg") for i in range(n_pares)]
    return isoladas + pares


def test_tamanhos_do_ccsd_sao_320_69_69() -> None:
    assert tamanhos_alvo(458, 0.15, 0.15) == (320, 69, 69)


def test_tamanhos_somam_o_total() -> None:
    for n in (10, 99, 458, 1001):
        assert sum(tamanhos_alvo(n, 0.15, 0.15)) == n


def test_tamanhos_recusam_proporcoes_sem_treino() -> None:
    with pytest.raises(ValueError, match="treino"):
        tamanhos_alvo(10, 0.5, 0.5)


def test_chave_e_o_hash_do_menor_nome_com_a_seed() -> None:
    esperado = hashlib.sha256(b"7:c.jpg").hexdigest()
    assert chave_do_grupo(7, ("d.jpg", "c.jpg")) == esperado


def test_divisao_do_mini_dataset_conferida_a_mao() -> None:
    divisao = dividir_por_grupos(MINI, seed=7, n_validacao=2, n_teste=2)
    assert divisao == Divisao(
        treino=("a.jpg", "c.jpg", "d.jpg"),
        validacao=("b.jpg", "f.jpg"),
        teste=("e.jpg", "g.jpg"),
    )


def test_nenhum_grupo_em_dois_conjuntos_e_par_nunca_partido() -> None:
    grupos = grupos_sinteticos()
    divisao = dividir_por_grupos(grupos, seed=20261022, n_validacao=8, n_teste=8)
    for grupo in grupos:
        assert len({divisao.conjunto_de(foto) for foto in grupo}) == 1


def test_todas_as_fotos_aparecem_exatamente_uma_vez() -> None:
    grupos = grupos_sinteticos()
    divisao = dividir_por_grupos(grupos, seed=20261022, n_validacao=8, n_teste=8)
    todas = divisao.treino + divisao.validacao + divisao.teste
    assert sorted(todas) == sorted(foto for grupo in grupos for foto in grupo)


def test_totais_saem_exatos() -> None:
    divisao = dividir_por_grupos(grupos_sinteticos(), 20261022, 8, 8)
    assert (len(divisao.treino), len(divisao.validacao), len(divisao.teste)) == (
        34,
        8,
        8,
    )


def test_mesma_seed_gera_a_mesma_divisao() -> None:
    grupos = grupos_sinteticos()
    assert dividir_por_grupos(grupos, 20261022, 8, 8) == dividir_por_grupos(
        grupos, 20261022, 8, 8
    )


def test_seeds_diferentes_geram_divisoes_diferentes() -> None:
    grupos = grupos_sinteticos()
    assert dividir_por_grupos(grupos, 1, 8, 8) != dividir_por_grupos(grupos, 2, 8, 8)


def test_ordem_de_entrada_dos_grupos_nao_muda_o_resultado() -> None:
    grupos = grupos_sinteticos()
    invertidos = [tuple(reversed(grupo)) for grupo in reversed(grupos)]
    assert dividir_por_grupos(grupos, 20261022, 8, 8) == dividir_por_grupos(
        invertidos, 20261022, 8, 8
    )


def test_conjunto_de_foto_desconhecida_levanta_erro() -> None:
    divisao = dividir_por_grupos(MINI, 7, 2, 2)
    with pytest.raises(KeyError):
        divisao.conjunto_de("z.jpg")


@pytest.mark.parametrize(
    ("grupos", "n_validacao", "n_teste", "trecho"),
    [
        ([("a.jpg",), ()], 0, 0, "vazio"),
        ([("a.jpg",), ("a.jpg",)], 0, 0, "mais de um grupo"),
        ([("a.jpg",), ("b.jpg",)], -1, 0, "inválidos"),
        ([("a.jpg",), ("b.jpg",)], 1, 2, "inválidos"),
        ([("a.jpg", "b.jpg"), ("c.jpg", "d.jpg")], 1, 1, "exatamente"),
    ],
)
def test_entradas_invalidas_sao_recusadas(
    grupos: list[tuple[str, ...]], n_validacao: int, n_teste: int, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        dividir_por_grupos(grupos, 7, n_validacao, n_teste)
