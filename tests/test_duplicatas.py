"""Testes da detecção de quase-duplicatas por dHash duplo."""

import numpy as np
import pytest

from concrete_crack.domain.duplicatas import (
    Agrupamento,
    agrupar,
    avaliar_hash,
    densidade_do_grupo,
    dhash_duplo,
    distancia_hamming,
    e_serie_real,
    limiar_por_cobertura,
    matriz_de_distancias,
    matriz_de_distancias_cosseno,
    reduzir_por_blocos,
)


def imagem_aleatoria(semente: int, forma: tuple[int, int] = (60, 80)) -> np.ndarray:
    return np.random.default_rng(semente).integers(0, 256, forma, dtype=np.uint8)


def test_reducao_divisivel_e_a_media_de_cada_bloco() -> None:
    cinza = np.array([[0, 2, 10, 12], [4, 6, 14, 16]], dtype=np.uint8)
    reduzida = reduzir_por_blocos(cinza, 1, 2)
    assert reduzida.tolist() == [[3.0, 13.0]]


def test_reducao_nao_divisivel_cobre_todos_os_pixels() -> None:
    cinza = np.arange(7 * 5, dtype=np.float64).reshape(7, 5)
    reduzida = reduzir_por_blocos(cinza, 3, 2)
    assert reduzida.shape == (3, 2)
    # bordas das linhas: 0, 2, 4 (alturas 2, 2, 3); colunas: 0, 2 (larguras 2, 3)
    assert reduzida[2, 1] == pytest.approx(cinza[4:7, 2:5].mean())


def test_reducao_nao_estoura_com_uint8() -> None:
    cinza = np.full((10, 10), 255, dtype=np.uint8)
    assert reduzir_por_blocos(cinza, 2, 2).tolist() == [[255.0, 255.0]] * 2


def test_reducao_recusa_imagem_menor_que_o_alvo_ou_nao_2d() -> None:
    with pytest.raises(ValueError, match="reduzir"):
        reduzir_por_blocos(np.zeros((5, 5)), 6, 2)
    with pytest.raises(ValueError, match="2D"):
        reduzir_por_blocos(np.zeros((5, 5, 3)), 2, 2)


def test_dhash_tem_2_x_lado_x_lado_bits() -> None:
    assert dhash_duplo(imagem_aleatoria(0), 8).shape == (128,)
    assert dhash_duplo(imagem_aleatoria(0), 4).shape == (32,)


def test_dhash_de_gradiente_horizontal() -> None:
    gradiente = np.tile(np.arange(90, dtype=np.uint8), (80, 1))
    bits = dhash_duplo(gradiente, 8)
    assert not bits[:64].any()  # cada célula é mais escura que a da direita
    assert not bits[64:].any()  # as linhas são iguais: nenhuma mais clara


def test_dhash_de_gradiente_vertical_decrescente() -> None:
    gradiente = np.tile(np.arange(90, 0, -1, dtype=np.uint8)[:, None], (1, 80))
    bits = dhash_duplo(gradiente, 8)
    assert not bits[:64].any()
    assert bits[64:].all()  # cada célula é mais clara que a de baixo


def test_dhash_ignora_brilho_multiplicativo() -> None:
    cinza = imagem_aleatoria(1).astype(np.float64)
    assert np.array_equal(dhash_duplo(cinza, 8), dhash_duplo(cinza * 0.85, 8))


def test_dhash_recusa_lado_menor_que_2() -> None:
    with pytest.raises(ValueError, match="lado"):
        dhash_duplo(imagem_aleatoria(0), 1)


def test_hamming_conta_bits_diferentes() -> None:
    a = np.array([True, False, True, False])
    b = np.array([True, True, False, False])
    assert distancia_hamming(a, b) == 2
    assert distancia_hamming(a, a) == 0


def test_hamming_recusa_formas_diferentes() -> None:
    with pytest.raises(ValueError, match="forma"):
        distancia_hamming(np.zeros(4, dtype=bool), np.zeros(5, dtype=bool))


def test_limiar_cobre_95_por_cento_de_200_distancias() -> None:
    assert limiar_por_cobertura(list(range(200)), 0.95) == 189


def test_limiar_com_cobertura_total_e_a_maior_distancia() -> None:
    assert limiar_por_cobertura([3, 9, 1, 4], 1.0) == 9


def test_limiar_com_produto_inexato_nao_exige_distancia_a_mais() -> None:
    # 0,07 x 100 = 7,000000000000001 em ponto flutuante: bastam 7 distâncias
    assert limiar_por_cobertura(list(range(100)), 0.07) == 6


def test_limiar_com_cobertura_pequena_usa_a_menor_distancia() -> None:
    assert limiar_por_cobertura([7, 5, 6], 0.01) == 5


@pytest.mark.parametrize(
    ("distancias", "cobertura", "trecho"),
    [([], 0.95, "Não há"), ([1, -1], 0.95, "negativas"), ([1], 0.0, "cobertura")],
)
def test_limiar_recusa_entradas_invalidas(
    distancias: list[int], cobertura: float, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        limiar_por_cobertura(distancias, cobertura)


def test_matriz_de_distancias_e_simetrica_com_diagonal_zero() -> None:
    hashes = [dhash_duplo(imagem_aleatoria(s), 8) for s in range(4)]
    matriz = matriz_de_distancias(hashes)
    assert matriz.shape == (4, 4)
    assert np.array_equal(matriz, matriz.T)
    assert not np.diag(matriz).any()
    assert matriz[1, 2] == distancia_hamming(hashes[1], hashes[2])


def test_matriz_recusa_um_hash_so_ou_formas_diferentes() -> None:
    with pytest.raises(ValueError, match="pelo menos 2"):
        matriz_de_distancias([np.zeros(4, dtype=bool)])
    with pytest.raises(ValueError, match="forma"):
        matriz_de_distancias([np.zeros(4, dtype=bool), np.zeros(5, dtype=bool)])


def matriz(*linhas: list[int]) -> np.ndarray:
    return np.array(linhas, dtype=np.int64)


def test_agrupa_por_ligacao_indireta() -> None:
    # 0-1 a 5 e 1-2 a 5 (ligados); 0-2 a 10 (distantes); 3 isolado
    distancias = matriz(
        [0, 5, 10, 50],
        [5, 0, 5, 50],
        [10, 5, 0, 50],
        [50, 50, 50, 0],
    )
    agrupamento = agrupar(distancias, 5)
    assert agrupamento.grupos == ((0, 1, 2), (3,))
    assert agrupamento.pares_ligados == 2
    assert agrupamento.total_pares == 6
    assert agrupamento.maior_grupo == 3
    assert agrupamento.n_imagens == 4


def test_limiar_inclui_a_distancia_igual() -> None:
    distancias = matriz([0, 5], [5, 0])
    assert agrupar(distancias, 5).grupos == ((0, 1),)
    assert agrupar(distancias, 4).grupos == ((0,), (1,))


def test_agrupar_recusa_matriz_invalida() -> None:
    with pytest.raises(ValueError, match="quadrada"):
        agrupar(np.zeros((2, 3), dtype=np.int64), 1)
    with pytest.raises(ValueError, match="pelo menos 2"):
        agrupar(np.zeros((1, 1), dtype=np.int64), 1)
    with pytest.raises(ValueError, match="simétrica"):
        agrupar(matriz([0, 1], [2, 0]), 1)
    with pytest.raises(ValueError, match="negativo"):
        agrupar(matriz([0, 1], [1, 0]), -1)


def agrupamento_com(maior: int, n: int, pares: int, total: int) -> Agrupamento:
    grupos = (tuple(range(maior)), *((i,) for i in range(maior, n)))
    return Agrupamento(grupos, pares, total)


def test_hash_aprovado_dentro_dos_dois_limites() -> None:
    avaliacao = avaliar_hash(agrupamento_com(45, 458, 2000, 104653), 0.10, 0.02)
    assert not avaliacao.reprovado


def test_grupo_de_46_em_458_reprova_e_de_45_nao() -> None:
    reprova = avaliar_hash(agrupamento_com(46, 458, 0, 104653), 0.10, 0.02)
    passa = avaliar_hash(agrupamento_com(45, 458, 0, 104653), 0.10, 0.02)
    assert reprova.grupo_grande_demais and reprova.reprovado
    assert not passa.grupo_grande_demais


def test_pares_exatamente_no_limite_nao_reprovam_e_acima_reprovam() -> None:
    no_limite = avaliar_hash(agrupamento_com(2, 10, 2, 100), 0.5, 0.02)
    acima = avaliar_hash(agrupamento_com(2, 10, 3, 100), 0.5, 0.02)
    assert not no_limite.pares_demais
    assert acima.pares_demais and acima.reprovado


def test_cosseno_de_direcoes_iguais_perpendiculares_e_opostas() -> None:
    vetores = [np.array([1.0, 0.0]), np.array([3.0, 0.0]), np.array([0.0, 2.0])]
    vetores.append(np.array([-1.0, 0.0]))
    distancias = matriz_de_distancias_cosseno(vetores)
    assert distancias[0, 1] == pytest.approx(0.0)
    assert distancias[0, 2] == pytest.approx(1.0)
    assert distancias[0, 3] == pytest.approx(2.0)


def test_cosseno_e_simetrico_com_diagonal_zero_e_dentro_de_0_a_2() -> None:
    rng = np.random.default_rng(0)
    distancias = matriz_de_distancias_cosseno(list(rng.normal(size=(6, 384))))
    assert np.array_equal(distancias, distancias.T)
    assert not np.diag(distancias).any()
    assert distancias.min() >= 0.0 and distancias.max() <= 2.0


def test_cosseno_ignora_o_tamanho_do_vetor() -> None:
    v = np.random.default_rng(1).normal(size=384)
    assert matriz_de_distancias_cosseno([v, 5 * v])[0, 1] == pytest.approx(0.0)


def test_cosseno_recusa_vetor_nulo_poucos_vetores_ou_formas_diferentes() -> None:
    with pytest.raises(ValueError, match="nulo"):
        matriz_de_distancias_cosseno([np.ones(3), np.zeros(3)])
    with pytest.raises(ValueError, match="pelo menos 2"):
        matriz_de_distancias_cosseno([np.ones(3)])
    with pytest.raises(ValueError, match="forma"):
        matriz_de_distancias_cosseno([np.ones(3), np.ones(4)])


def test_limiar_por_cobertura_com_distancias_continuas() -> None:
    distancias = [0.01 * i for i in range(1, 101)]
    assert limiar_por_cobertura(distancias, 0.95) == pytest.approx(0.95)


def test_agrupa_com_distancias_de_cosseno() -> None:
    vetores = [np.array([1.0, 0.0]), np.array([0.99, 0.14]), np.array([0.0, 1.0])]
    distancias = matriz_de_distancias_cosseno(vetores)
    assert agrupar(distancias, 0.05).grupos == ((0, 1), (2,))


def corrente(n: int) -> np.ndarray:
    """Matriz em que cada imagem só é próxima (1) das vizinhas imediatas."""
    indices = np.arange(n)
    return np.where(np.abs(indices[:, None] - indices[None, :]) == 1, 1, 10)


def test_densidade_de_uma_corrente_e_baixa() -> None:
    distancias = corrente(10)
    np.fill_diagonal(distancias, 0)
    # 9 ligações entre vizinhos em 45 pares possíveis
    assert densidade_do_grupo(distancias, range(10), 1) == pytest.approx(0.2)


def test_densidade_de_uma_serie_e_total() -> None:
    distancias = np.ones((5, 5))
    np.fill_diagonal(distancias, 0)
    assert densidade_do_grupo(distancias, [0, 1, 2, 3, 4], 1) == 1.0


def test_densidade_conta_so_os_pares_dentro_do_grupo() -> None:
    distancias = corrente(6)
    np.fill_diagonal(distancias, 0)
    # grupo {0, 1, 3}: só o par 0-1 é vizinho; 3 pares possíveis
    assert densidade_do_grupo(distancias, [0, 1, 3], 1) == pytest.approx(1 / 3)


def test_densidade_recusa_grupo_de_uma_imagem() -> None:
    with pytest.raises(ValueError, match="pelo menos 2"):
        densidade_do_grupo(np.zeros((3, 3)), [1], 1)


def test_serie_real_a_partir_do_corte_inclusive() -> None:
    assert e_serie_real(0.5, 0.5)
    assert e_serie_real(0.9, 0.5)
    assert not e_serie_real(0.49, 0.5)
