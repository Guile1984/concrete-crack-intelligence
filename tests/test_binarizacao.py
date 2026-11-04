"""Testes da medição de área de fissura em função do limiar de binarização."""

import numpy as np
import pytest

from concrete_crack.domain.binarizacao import (
    N_NIVEIS,
    avaliar_patamar,
    contagem_por_desvio,
    contar_acima,
    e_anomala,
    fracao_de_fissura,
)

GRADE = tuple(range(16, 256, 16))


def contagem_de(**por_desvio: int) -> np.ndarray:
    """Monta uma contagem a partir de pares como d64=100 (desvio 64)."""
    contagem = np.zeros(N_NIVEIS, dtype=np.int64)
    for nome, quantidade in por_desvio.items():
        contagem[int(nome[1:])] = quantidade
    return contagem


def test_contagem_soma_o_numero_de_pixels() -> None:
    cinza = np.random.default_rng(0).integers(0, 256, (30, 40), dtype=np.uint8)
    contagem = contagem_por_desvio(cinza)
    assert contagem.shape == (256,)
    assert contagem.sum() == 30 * 40


def test_fissura_clara_sobre_fundo_escuro() -> None:
    cinza = np.zeros((10, 10), dtype=np.uint8)
    cinza[0, :] = 255
    contagem = contagem_por_desvio(cinza)
    assert contagem[0] == 90
    assert contagem[255] == 10


def test_polaridade_invertida_da_a_mesma_contagem() -> None:
    cinza = np.zeros((10, 10), dtype=np.uint8)
    cinza[0, :] = 255
    assert np.array_equal(contagem_por_desvio(cinza), contagem_por_desvio(255 - cinza))


def test_fissura_acinzentada_cai_num_desvio_intermediario() -> None:
    cinza = np.full((10, 10), 10, dtype=np.uint8)
    cinza[0, :] = 138
    contagem = contagem_por_desvio(cinza)
    assert contagem[128] == 10


def test_mediana_entre_dois_niveis_arredonda_o_desvio_para_cima() -> None:
    cinza = np.array([[0, 0], [1, 1]], dtype=np.uint8)
    contagem = contagem_por_desvio(cinza)
    assert contagem[1] == 4


def test_imagem_vazia_e_recusada() -> None:
    with pytest.raises(ValueError, match="vazia"):
        contagem_por_desvio(np.zeros((0, 5), dtype=np.uint8))


def test_imagem_nao_uint8_e_recusada() -> None:
    with pytest.raises(ValueError, match="uint8"):
        contagem_por_desvio(np.zeros((4, 4), dtype=np.float64))


def test_contar_acima_inclui_o_proprio_limiar() -> None:
    contagem = contagem_de(d0=80, d64=15, d128=5)
    assert contar_acima(contagem, 64) == 20
    assert contar_acima(contagem, 65) == 5
    assert contar_acima(contagem, 128) == 5
    assert contar_acima(contagem, 129) == 0


@pytest.mark.parametrize("limiar", [0, 256, -1])
def test_contar_acima_recusa_limiar_fora_de_1_a_255(limiar: int) -> None:
    with pytest.raises(ValueError, match="entre 1 e 255"):
        contar_acima(contagem_de(d0=10), limiar)


def test_contar_acima_recusa_contagem_de_tamanho_errado() -> None:
    with pytest.raises(ValueError, match="256"):
        contar_acima(np.zeros(10, dtype=np.int64), 5)


def test_fracao_de_fissura() -> None:
    contagem = contagem_de(d0=900, d128=100)
    assert fracao_de_fissura(contagem, 128) == pytest.approx(0.10)
    assert fracao_de_fissura(contagem, 129) == 0.0


def test_fracao_recusa_contagem_sem_pixels() -> None:
    with pytest.raises(ValueError, match="não tem pixels"):
        fracao_de_fissura(np.zeros(256, dtype=np.int64), 128)


def test_exatamente_no_maximo_nao_e_anomala_e_acima_e() -> None:
    no_limite = contagem_de(d0=90, d128=10)
    acima = contagem_de(d0=89, d128=11)
    assert not e_anomala(no_limite, 128, 0.10)
    assert e_anomala(acima, 128, 0.10)


def test_patamar_robusto_quando_a_area_quase_nao_cai() -> None:
    contagem = contagem_de(d0=900, d64=5, d128=5, d192=90)
    resumo = avaliar_patamar(contagem, GRADE, 64, 192, 0.80)
    assert resumo.razao == pytest.approx(0.90)
    assert resumo.robusta


def test_patamar_sensivel_quando_a_area_cai_muito() -> None:
    contagem = contagem_de(d0=900, d64=10, d128=80, d192=10)
    resumo = avaliar_patamar(contagem, GRADE, 64, 192, 0.80)
    assert resumo.razao == pytest.approx(0.10)
    assert not resumo.robusta


def test_patamar_na_fronteira_de_80_por_cento_e_robusto() -> None:
    contagem = contagem_de(d0=900, d64=20, d192=80)
    resumo = avaliar_patamar(contagem, GRADE, 64, 192, 0.80)
    assert resumo.razao == 0.80
    assert resumo.robusta


def test_patamar_logo_abaixo_de_80_por_cento_e_sensivel() -> None:
    contagem = contagem_de(d0=900, d64=21, d192=79)
    resumo = avaliar_patamar(contagem, GRADE, 64, 192, 0.80)
    assert resumo.razao == pytest.approx(0.79)
    assert not resumo.robusta


def test_curva_acompanha_a_grade_e_nunca_cresce() -> None:
    contagem = contagem_de(d0=800, d32=50, d96=50, d160=50, d224=50)
    resumo = avaliar_patamar(contagem, GRADE, 64, 192, 0.80)
    assert resumo.limiares == GRADE
    assert len(resumo.areas) == len(GRADE)
    assert all(a >= b for a, b in zip(resumo.areas, resumo.areas[1:], strict=False))
    assert resumo.areas[0] == pytest.approx(0.20)


def test_patamar_recusa_limiar_fora_da_grade() -> None:
    contagem = contagem_de(d0=900, d128=100)
    with pytest.raises(ValueError, match="grade"):
        avaliar_patamar(contagem, GRADE, 60, 192, 0.80)


def test_patamar_recusa_baixo_maior_ou_igual_ao_alto() -> None:
    contagem = contagem_de(d0=900, d128=100)
    with pytest.raises(ValueError, match="menor"):
        avaliar_patamar(contagem, GRADE, 192, 64, 0.80)


def test_patamar_recusa_area_nula_no_limiar_baixo() -> None:
    contagem = contagem_de(d0=1000)
    with pytest.raises(ValueError, match="Não há pixels"):
        avaliar_patamar(contagem, GRADE, 64, 192, 0.80)
