"""Testes do pareamento de máscaras e fotos."""

import pytest

from concrete_crack.domain.pareamento import parear


def test_pareia_ignorando_pasta_extensao_e_maiusculas() -> None:
    resultado = parear(["BW/001.jpg", "BW/Abc.jpg"], ["rgb/001.JPG", "rgb/abc.JPG"])
    assert resultado.pares == (
        ("BW/001.jpg", "rgb/001.JPG"),
        ("BW/Abc.jpg", "rgb/abc.JPG"),
    )
    assert resultado.completo


def test_detecta_mascara_sem_foto_e_foto_sem_mascara() -> None:
    resultado = parear(["BW/001.jpg", "BW/002.jpg"], ["rgb/001.JPG", "rgb/003.JPG"])
    assert resultado.pares == (("BW/001.jpg", "rgb/001.JPG"),)
    assert resultado.mascaras_sem_foto == ("BW/002.jpg",)
    assert resultado.fotos_sem_mascara == ("rgb/003.JPG",)
    assert not resultado.completo


def test_resultado_independe_da_ordem_da_entrada() -> None:
    mascaras = ["BW/001.jpg", "BW/002.jpg", "BW/009.jpg"]
    fotos = ["rgb/002.JPG", "rgb/001.JPG", "rgb/010.JPG"]
    assert parear(mascaras, fotos) == parear(mascaras[::-1], fotos[::-1])


def test_nomes_que_colidem_sao_recusados() -> None:
    with pytest.raises(ValueError, match="mesmo nome"):
        parear(["BW/Abc.jpg", "BW/abc.JPG"], ["rgb/abc.JPG"])
    with pytest.raises(ValueError, match="fotos"):
        parear(["BW/abc.jpg"], ["rgb/abc.JPG", "rgb/ABC.jpg"])


def test_numeracao_com_lacunas_nao_e_problema() -> None:
    resultado = parear(["BW/001.jpg", "BW/005.jpg"], ["rgb/001.JPG", "rgb/005.JPG"])
    assert resultado.completo
    assert len(resultado.pares) == 2


def test_ponto_no_meio_do_nome_so_perde_a_ultima_extensao() -> None:
    resultado = parear(["BW/a.b.jpg"], ["rgb/a.b.JPG"])
    assert resultado.pares == (("BW/a.b.jpg", "rgb/a.b.JPG"),)


def test_listas_vazias_dao_pareamento_vazio_e_completo() -> None:
    resultado = parear([], [])
    assert resultado.pares == ()
    assert resultado.completo
