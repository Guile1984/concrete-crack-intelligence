"""Testes dos vereditos, da regra de reprovação e do intervalo de Wilson."""

import pytest

from concrete_crack.domain.veredito import Veredito, avaliar, intervalo_wilson

ADEQ = Veredito.ADEQUADA
INAD = Veredito.INADEQUADA
DUV = Veredito.DUVIDOSA


def amostra(inadequadas: int, duvidosas: int = 0, n: int = 40) -> list[Veredito]:
    adequadas = n - inadequadas - duvidosas
    return [INAD] * inadequadas + [DUV] * duvidosas + [ADEQ] * adequadas


def test_wilson_de_zero_em_40_vai_de_zero_a_cerca_de_9_por_cento() -> None:
    inferior, superior = intervalo_wilson(0, 40)
    assert inferior == 0.0
    assert superior == pytest.approx(0.0876, abs=1e-4)


def test_wilson_de_8_em_40_vai_de_10_a_35_por_cento() -> None:
    inferior, superior = intervalo_wilson(8, 40)
    assert inferior == pytest.approx(0.1050, abs=1e-4)
    assert superior == pytest.approx(0.3476, abs=1e-4)


def test_wilson_de_40_em_40_termina_em_um() -> None:
    inferior, superior = intervalo_wilson(40, 40)
    assert inferior == pytest.approx(0.9124, abs=1e-4)
    assert superior == 1.0


@pytest.mark.parametrize(("sucessos", "n"), [(3, 40), (8, 40), (1, 10)])
def test_wilson_e_simetrico_entre_sucessos_e_falhas(sucessos: int, n: int) -> None:
    inferior, superior = intervalo_wilson(sucessos, n)
    inferior_oposto, superior_oposto = intervalo_wilson(n - sucessos, n)
    assert inferior == pytest.approx(1 - superior_oposto)
    assert superior == pytest.approx(1 - inferior_oposto)


def test_wilson_sempre_contem_a_proporcao_observada() -> None:
    for sucessos in range(41):
        inferior, superior = intervalo_wilson(sucessos, 40)
        assert inferior <= sucessos / 40 <= superior


@pytest.mark.parametrize(("sucessos", "n"), [(0, 0), (-1, 10), (11, 10)])
def test_wilson_recusa_argumentos_invalidos(sucessos: int, n: int) -> None:
    with pytest.raises(ValueError):
        intervalo_wilson(sucessos, n)


def test_7_inadequadas_em_40_nao_reprovam() -> None:
    resultado = avaliar(amostra(7), 8)
    assert (resultado.n, resultado.inadequadas, resultado.adequadas) == (40, 7, 33)
    assert not resultado.reprovada


def test_8_inadequadas_em_40_reprovam() -> None:
    assert avaliar(amostra(8), 8).reprovada


def test_duvidosas_nao_entram_na_regra_mas_entram_na_sensibilidade() -> None:
    resultado = avaliar(amostra(6, duvidosas=2), 8)
    assert resultado.duvidosas == 2
    assert not resultado.reprovada
    assert resultado.reprovada_se_duvidosas_forem_inadequadas
    assert resultado.conclusao_depende_das_duvidosas


def test_sem_duvidosas_a_sensibilidade_nao_muda_a_decisao() -> None:
    resultado = avaliar(amostra(8), 8)
    assert resultado.reprovada_se_duvidosas_forem_inadequadas
    assert not resultado.conclusao_depende_das_duvidosas


def test_intervalos_do_resultado_sao_os_de_wilson() -> None:
    resultado = avaliar(amostra(5, duvidosas=3), 8)
    assert resultado.intervalo_inadequadas == intervalo_wilson(5, 40)
    assert resultado.intervalo_sensibilidade == intervalo_wilson(8, 40)


def test_avaliar_sem_vereditos_e_recusado() -> None:
    with pytest.raises(ValueError, match="Não há vereditos"):
        avaliar([], 8)


@pytest.mark.parametrize("limiar", [0, 41])
def test_limiar_fora_de_1_ao_tamanho_da_amostra_e_recusado(limiar: int) -> None:
    with pytest.raises(ValueError, match="limiar"):
        avaliar(amostra(0), limiar)


@pytest.mark.parametrize(
    ("texto", "veredito"),
    [("adequada", ADEQ), ("inadequada", INAD), ("duvidosa", DUV)],
)
def test_veredito_e_lido_pelo_texto(texto: str, veredito: Veredito) -> None:
    assert Veredito(texto) is veredito


def test_texto_desconhecido_nao_e_veredito() -> None:
    with pytest.raises(ValueError):
        Veredito("talvez")
