"""Testes do registro imutável de vereditos da inspeção."""

import dataclasses

import pytest

from concrete_crack.domain.registro_vereditos import (
    Correcao,
    Julgamento,
    RegistroVereditos,
)
from concrete_crack.domain.veredito import Veredito

ADEQ = Veredito.ADEQUADA
INAD = Veredito.INADEQUADA
DUV = Veredito.DUVIDOSA

SHA = "a" * 64
H1 = "2026-11-02T15:00:00+00:00"
H2 = "2026-11-02T15:05:00+00:00"
AMOSTRA = ("BW/001.jpg", "BW/002.jpg", "BW/003.jpg")


def novo() -> RegistroVereditos:
    return RegistroVereditos("ccsd", SHA, AMOSTRA)


def test_registro_novo_tem_tudo_pendente_na_ordem_do_sorteio() -> None:
    registro = novo()
    assert registro.pendentes == AMOSTRA
    assert registro.proxima == "BW/001.jpg"
    assert not registro.completo
    assert registro.vereditos == ()


def test_julgar_devolve_registro_novo_e_nao_altera_o_original() -> None:
    original = novo()
    depois = original.julgar("BW/001.jpg", ADEQ, H1, "limpa")
    assert original.julgamentos == ()
    assert depois.julgamentos == (Julgamento("BW/001.jpg", ADEQ, H1, "limpa"),)
    assert depois.proxima == "BW/002.jpg"


def test_registro_e_imutavel() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        novo().fonte_id = "outra"  # type: ignore[misc]


def test_julgar_recusa_mascara_fora_da_amostra() -> None:
    with pytest.raises(ValueError, match="não está na amostra"):
        novo().julgar("BW/999.jpg", ADEQ, H1)


def test_julgar_recusa_mascara_ja_julgada() -> None:
    registro = novo().julgar("BW/001.jpg", ADEQ, H1)
    with pytest.raises(ValueError, match="já foi julgada"):
        registro.julgar("BW/001.jpg", INAD, H2)


@pytest.mark.parametrize("hora", ["ontem", "2026-11-02T15:00:00"])
def test_julgar_recusa_hora_invalida_ou_sem_fuso(hora: str) -> None:
    with pytest.raises(ValueError, match="[Hh]ora"):
        novo().julgar("BW/001.jpg", ADEQ, hora)


def test_completo_quando_todas_foram_julgadas() -> None:
    registro = novo()
    for mascara in AMOSTRA:
        registro = registro.julgar(mascara, ADEQ, H1)
    assert registro.completo
    assert registro.proxima is None
    assert registro.pendentes == ()


def test_vereditos_saem_na_ordem_do_sorteio() -> None:
    registro = novo().julgar("BW/002.jpg", INAD, H1).julgar("BW/001.jpg", DUV, H2)
    assert registro.vereditos == (DUV, INAD)


def test_corrigir_troca_o_veredito_e_guarda_o_historico() -> None:
    registro = novo().julgar("BW/001.jpg", ADEQ, H1, "ok")
    corrigido = registro.corrigir("BW/001.jpg", INAD, "vi falha ao ampliar", H2)
    assert corrigido.vereditos == (INAD,)
    assert corrigido.julgamentos[0].registrado_em == H1
    assert corrigido.julgamentos[0].observacao == "ok"
    assert corrigido.correcoes == (
        Correcao("BW/001.jpg", ADEQ, INAD, "vi falha ao ampliar", H2),
    )
    assert registro.vereditos == (ADEQ,)


def test_corrigir_recusa_mascara_nao_julgada() -> None:
    with pytest.raises(ValueError, match="ainda não foi julgada"):
        novo().corrigir("BW/001.jpg", INAD, "motivo", H1)


@pytest.mark.parametrize("motivo", ["", "   "])
def test_corrigir_recusa_motivo_vazio(motivo: str) -> None:
    registro = novo().julgar("BW/001.jpg", ADEQ, H1)
    with pytest.raises(ValueError, match="motivo"):
        registro.corrigir("BW/001.jpg", INAD, motivo, H2)


def test_corrigir_recusa_veredito_igual() -> None:
    registro = novo().julgar("BW/001.jpg", ADEQ, H1)
    with pytest.raises(ValueError, match="mudar o veredito"):
        registro.corrigir("BW/001.jpg", ADEQ, "motivo", H2)


@pytest.mark.parametrize("amostra", [(), ("BW/001.jpg", "BW/001.jpg")])
def test_amostra_vazia_ou_repetida_e_recusada(amostra: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="amostra"):
        RegistroVereditos("ccsd", SHA, amostra)


@pytest.mark.parametrize("sha", ["", "abc", "A" * 64, "g" * 64])
def test_sha256_invalido_e_recusado(sha: str) -> None:
    with pytest.raises(ValueError, match="sha256"):
        RegistroVereditos("ccsd", sha, AMOSTRA)


def test_fonte_vazia_e_recusada() -> None:
    with pytest.raises(ValueError, match="fonte_id"):
        RegistroVereditos("  ", SHA, AMOSTRA)


def test_construtor_recusa_julgamento_fora_da_amostra() -> None:
    julgamento = Julgamento("BW/999.jpg", ADEQ, H1)
    with pytest.raises(ValueError, match="não está na amostra"):
        RegistroVereditos("ccsd", SHA, AMOSTRA, (julgamento,))


def test_construtor_recusa_julgamento_duplicado() -> None:
    julgamento = Julgamento("BW/001.jpg", ADEQ, H1)
    with pytest.raises(ValueError, match="mais de uma vez"):
        RegistroVereditos("ccsd", SHA, AMOSTRA, (julgamento, julgamento))


def test_construtor_recusa_correcao_de_mascara_nao_julgada() -> None:
    correcao = Correcao("BW/001.jpg", ADEQ, INAD, "motivo", H1)
    with pytest.raises(ValueError, match="não foi julgada"):
        RegistroVereditos("ccsd", SHA, AMOSTRA, (), (correcao,))
