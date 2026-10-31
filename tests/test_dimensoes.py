"""Testes da conferência de dimensões entre máscaras e fotos."""

import pytest

from concrete_crack.domain.dimensoes import Cabecalho, conferir_dimensoes

PAISAGEM = Cabecalho(4032, 3024, 1)
PAISAGEM_GIRADA = Cabecalho(4032, 3024, 6)
RETRATO = Cabecalho(3024, 4032, 6)


def test_dimensoes_iguais_nao_geram_divergencia() -> None:
    cabecalhos = {"BW/1.jpg": Cabecalho(4032, 3024), "rgb/1.JPG": PAISAGEM}
    resultado = conferir_dimensoes([("BW/1.jpg", "rgb/1.JPG")], cabecalhos)
    assert resultado.diferentes == ()
    assert resultado.eixos_trocados == ()
    assert resultado.tamanhos_mascaras == (((4032, 3024), 1),)
    assert resultado.tamanhos_fotos == (((4032, 3024), 1),)


def test_tamanho_diferente_e_detectado_sem_ser_eixo_trocado() -> None:
    cabecalhos = {"BW/1.jpg": Cabecalho(1000, 800), "rgb/1.JPG": Cabecalho(2000, 1600)}
    resultado = conferir_dimensoes([("BW/1.jpg", "rgb/1.JPG")], cabecalhos)
    assert resultado.diferentes == (("BW/1.jpg", "rgb/1.JPG"),)
    assert resultado.eixos_trocados == ()


def test_eixos_trocados_sao_detectados() -> None:
    cabecalhos = {"BW/1.jpg": Cabecalho(3024, 4032), "rgb/1.JPG": PAISAGEM}
    resultado = conferir_dimensoes([("BW/1.jpg", "rgb/1.JPG")], cabecalhos)
    assert resultado.diferentes == (("BW/1.jpg", "rgb/1.JPG"),)
    assert resultado.eixos_trocados == (("BW/1.jpg", "rgb/1.JPG"),)


def test_tamanhos_vem_do_mais_frequente_ao_menos_frequente() -> None:
    cabecalhos = {
        "BW/1.jpg": Cabecalho(3024, 4032),
        "rgb/1.JPG": RETRATO,
        "BW/2.jpg": Cabecalho(4032, 3024),
        "rgb/2.JPG": PAISAGEM,
        "BW/3.jpg": Cabecalho(4032, 3024),
        "rgb/3.JPG": PAISAGEM,
    }
    pares = [
        ("BW/1.jpg", "rgb/1.JPG"),
        ("BW/2.jpg", "rgb/2.JPG"),
        ("BW/3.jpg", "rgb/3.JPG"),
    ]
    resultado = conferir_dimensoes(pares, cabecalhos)
    esperado = (((4032, 3024), 2), ((3024, 4032), 1))
    assert resultado.tamanhos_mascaras == esperado
    assert resultado.tamanhos_fotos == esperado


def test_orientacoes_sao_contadas_inclusive_a_ausente() -> None:
    quadrada = Cabecalho(100, 100)
    cabecalhos = {f"BW/{i}.jpg": quadrada for i in range(4)}
    orientacoes = [1, 1, 6, None]
    for i, orientacao in enumerate(orientacoes):
        cabecalhos[f"rgb/{i}.JPG"] = Cabecalho(100, 100, orientacao)
    pares = [(f"BW/{i}.jpg", f"rgb/{i}.JPG") for i in range(4)]
    resultado = conferir_dimensoes(pares, cabecalhos)
    assert resultado.orientacoes_fotos == ((1, 2), (None, 1), (6, 1))
    assert resultado.orientacoes_mascaras == ((None, 4),)


def test_cabecalho_ausente_e_recusado() -> None:
    cabecalhos = {"BW/1.jpg": PAISAGEM}
    with pytest.raises(ValueError, match="Falta o cabeçalho"):
        conferir_dimensoes([("BW/1.jpg", "rgb/1.JPG")], cabecalhos)


@pytest.mark.parametrize(
    ("largura", "altura", "orientacao"),
    [(0, 10, None), (10, -1, None), (10, 10, 9)],
)
def test_cabecalho_invalido_e_recusado(
    largura: int, altura: int, orientacao: int | None
) -> None:
    with pytest.raises(ValueError, match="positivas|orientacao_exif"):
        Cabecalho(largura, altura, orientacao)


def test_sem_pares_o_resultado_e_vazio() -> None:
    resultado = conferir_dimensoes([], {})
    assert resultado.tamanhos_mascaras == ()
    assert resultado.orientacoes_fotos == ()
    assert resultado.diferentes == ()
    assert resultado.eixos_trocados == ()
    assert resultado.orientacoes_fotos_dos_trocados == ()
    assert resultado.diferentes_apos_orientacao == ()


@pytest.mark.parametrize(
    ("orientacao", "esperado"),
    [
        (None, (4, 3)),
        (1, (4, 3)),
        (2, (4, 3)),
        (3, (4, 3)),
        (4, (4, 3)),
        (5, (3, 4)),
        (6, (3, 4)),
        (7, (3, 4)),
        (8, (3, 4)),
    ],
)
def test_tamanho_exibido_troca_os_eixos_so_nas_orientacoes_5_a_8(
    orientacao: int | None, esperado: tuple[int, int]
) -> None:
    assert Cabecalho(4, 3, orientacao).tamanho_exibido == esperado


def test_a_rotacao_exif_resolve_o_par_de_eixos_trocados() -> None:
    cabecalhos = {"BW/1.jpg": Cabecalho(3024, 4032, 1), "rgb/1.JPG": PAISAGEM_GIRADA}
    resultado = conferir_dimensoes([("BW/1.jpg", "rgb/1.JPG")], cabecalhos)
    assert resultado.eixos_trocados == (("BW/1.jpg", "rgb/1.JPG"),)
    assert resultado.diferentes_apos_orientacao == ()


def test_a_rotacao_de_180_graus_nao_altera_o_tamanho() -> None:
    cabecalhos = {"BW/1.jpg": PAISAGEM, "rgb/1.JPG": Cabecalho(4032, 3024, 3)}
    resultado = conferir_dimensoes([("BW/1.jpg", "rgb/1.JPG")], cabecalhos)
    assert resultado.diferentes == ()
    assert resultado.diferentes_apos_orientacao == ()


def test_par_que_continua_divergente_apos_a_orientacao() -> None:
    cabecalhos = {
        "BW/1.jpg": Cabecalho(1000, 800, 1),
        "rgb/1.JPG": Cabecalho(2000, 1600, 6),
    }
    resultado = conferir_dimensoes([("BW/1.jpg", "rgb/1.JPG")], cabecalhos)
    assert resultado.diferentes_apos_orientacao == (("BW/1.jpg", "rgb/1.JPG"),)


def test_orientacoes_das_fotos_dos_pares_trocados() -> None:
    cabecalhos = {
        "BW/1.jpg": Cabecalho(3024, 4032, 1),
        "rgb/1.JPG": Cabecalho(4032, 3024, 6),
        "BW/2.jpg": Cabecalho(3024, 4032, 1),
        "rgb/2.JPG": Cabecalho(4032, 3024, 6),
        "BW/3.jpg": Cabecalho(3024, 4032, 1),
        "rgb/3.JPG": Cabecalho(4032, 3024, 8),
        "BW/4.jpg": Cabecalho(4032, 3024, 1),
        "rgb/4.JPG": Cabecalho(4032, 3024, 3),
    }
    pares = [(f"BW/{i}.jpg", f"rgb/{i}.JPG") for i in range(1, 5)]
    resultado = conferir_dimensoes(pares, cabecalhos)
    assert len(resultado.eixos_trocados) == 3
    assert resultado.orientacoes_fotos_dos_trocados == ((6, 2), (8, 1))
