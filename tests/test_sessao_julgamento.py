"""Testes da sessão de julgamento, simulada sem console."""

from pathlib import Path

import pytest

from concrete_crack.domain.registro_vereditos import RegistroVereditos
from concrete_crack.domain.veredito import Veredito
from concrete_crack.presentation.sessao_julgamento import (
    Ambiente,
    rodar_sessao,
)

ADEQ = Veredito.ADEQUADA
INAD = Veredito.INADEQUADA
DUV = Veredito.DUVIDOSA

SHA = "c" * 64
MARCA_RUBRICA = "Critério (A31)"


def amostra_de(n: int) -> tuple[str, ...]:
    return tuple(f"BW/{i:03d}.jpg" for i in range(1, n + 1))


def novo(n: int = 3) -> RegistroVereditos:
    return RegistroVereditos("ccsd", SHA, amostra_de(n))


def imagem_de(posicao: int, mascara: str) -> Path:
    return Path("imagens") / f"{posicao:02d}_{Path(mascara).stem}.png"


class Roteiro:
    """Simula teclado, tela, visualizador, relógio e disco."""

    def __init__(self, respostas: list[str | type[EOFError]]) -> None:
        self.respostas = list(respostas)
        self.saida: list[str] = []
        self.perguntas: list[str] = []
        self.abertas: list[Path] = []
        self.gravados: list[RegistroVereditos] = []
        self.abrir_falha = False
        self.chamadas_agora = 0

    def ler(self, pergunta: str) -> str:
        self.perguntas.append(pergunta)
        resposta = self.respostas.pop(0)
        if resposta is EOFError:
            raise EOFError
        assert isinstance(resposta, str)
        return resposta

    def abrir(self, caminho: Path) -> None:
        if self.abrir_falha:
            raise OSError("sem visualizador")
        self.abertas.append(caminho)

    def agora(self) -> str:
        self.chamadas_agora += 1
        return f"2026-11-02T15:{self.chamadas_agora:02d}:00+00:00"

    def ambiente(self) -> Ambiente:
        return Ambiente(
            ler=self.ler,
            escrever=self.saida.append,
            abrir=self.abrir,
            agora=self.agora,
            gravar=self.gravados.append,
        )

    @property
    def texto(self) -> str:
        return "\n".join(self.saida)


def rodar(roteiro: Roteiro, registro: RegistroVereditos) -> RegistroVereditos:
    return rodar_sessao(registro, imagem_de, roteiro.ambiente())


def test_julga_todas_na_ordem_do_sorteio() -> None:
    roteiro = Roteiro(["a", "", "i", "", "d", ""])
    final = rodar(roteiro, novo())
    assert final.completo
    assert final.vereditos == (ADEQ, INAD, DUV)
    assert [j.mascara for j in final.julgamentos] == list(amostra_de(3))


def test_grava_depois_de_cada_veredito() -> None:
    roteiro = Roteiro(["a", "", "i", "", "d", ""])
    rodar(roteiro, novo())
    assert [len(r.julgamentos) for r in roteiro.gravados] == [1, 2, 3]


def test_observacao_e_guardada_e_enter_deixa_vazia() -> None:
    roteiro = Roteiro(["i", "  excesso na borda ", "a", ""])
    final = rodar(roteiro, novo(2))
    assert final.julgamentos[0].observacao == "excesso na borda"
    assert final.julgamentos[1].observacao == ""


def test_aceita_maiuscula_e_espacos() -> None:
    roteiro = Roteiro([" A ", "", "I", ""])
    final = rodar(roteiro, novo(2))
    assert final.vereditos == (ADEQ, INAD)


def test_entrada_invalida_pergunta_de_novo_sem_registrar() -> None:
    roteiro = Roteiro(["x", "", "a", ""])
    final = rodar(roteiro, novo(1))
    assert "Entrada inválida" in roteiro.texto
    assert final.vereditos == (ADEQ,)
    assert len(roteiro.gravados) == 1


def test_sair_interrompe_e_mantem_o_que_ja_foi_julgado() -> None:
    roteiro = Roteiro(["a", "", "s"])
    final = rodar(roteiro, novo())
    assert final.vereditos == (ADEQ,)
    assert not final.completo
    assert "Rode de novo" in roteiro.texto
    assert len(roteiro.gravados) == 1


def test_fim_da_entrada_equivale_a_sair() -> None:
    roteiro = Roteiro(["a", "", EOFError])
    final = rodar(roteiro, novo())
    assert final.vereditos == (ADEQ,)


def test_retoma_da_primeira_pendente() -> None:
    parcial = novo().julgar("BW/001.jpg", ADEQ, "2026-11-02T14:00:00+00:00")
    roteiro = Roteiro(["i", "", "d", ""])
    final = rodar(roteiro, parcial)
    assert final.vereditos == (ADEQ, INAD, DUV)
    assert "Máscara 1 de 3" not in roteiro.texto
    assert "Máscara 2 de 3" in roteiro.texto


def test_mostra_so_a_posicao_e_nunca_contagens_de_vereditos() -> None:
    roteiro = Roteiro(["i", "", "a", "", "d", ""])
    rodar(roteiro, novo())
    assert "Máscara 2 de 3" in roteiro.texto
    for palavra in ("inadequadas", "adequadas", "duvidosas", "reprov"):
        assert palavra not in roteiro.texto


def test_rubrica_no_inicio_e_a_cada_dez_mascaras() -> None:
    roteiro = Roteiro(["a", ""] * 25)
    rodar(roteiro, novo(25))
    assert roteiro.texto.count(MARCA_RUBRICA) == 3


def test_retomando_na_posicao_onze_a_rubrica_sai_so_uma_vez() -> None:
    registro = novo(12)
    for mascara in amostra_de(12)[:10]:
        registro = registro.julgar(mascara, ADEQ, "2026-11-02T14:00:00+00:00")
    roteiro = Roteiro(["a", "", "a", ""])
    rodar(roteiro, registro)
    assert roteiro.texto.count(MARCA_RUBRICA) == 1


def test_abre_cada_imagem_na_ordem() -> None:
    roteiro = Roteiro(["a", "", "a", ""])
    rodar(roteiro, novo(2))
    assert roteiro.abertas == [imagem_de(1, "BW/001.jpg"), imagem_de(2, "BW/002.jpg")]
    assert str(imagem_de(1, "BW/001.jpg")) in roteiro.texto


def test_falha_ao_abrir_nao_interrompe_a_sessao() -> None:
    roteiro = Roteiro(["a", ""])
    roteiro.abrir_falha = True
    final = rodar(roteiro, novo(1))
    assert final.vereditos == (ADEQ,)
    assert "abra-a pelo caminho" in roteiro.texto


def test_registro_completo_nao_pergunta_nem_grava() -> None:
    registro = novo(1).julgar("BW/001.jpg", ADEQ, "2026-11-02T14:00:00+00:00")
    roteiro = Roteiro([])
    final = rodar(roteiro, registro)
    assert final == registro
    assert roteiro.gravados == []
    assert "já foram julgadas" in roteiro.texto


def test_hora_vem_do_relogio_no_momento_do_veredito() -> None:
    roteiro = Roteiro(["a", "", "i", ""])
    final = rodar(roteiro, novo(2))
    assert [j.registrado_em for j in final.julgamentos] == [
        "2026-11-02T15:01:00+00:00",
        "2026-11-02T15:02:00+00:00",
    ]


def test_falha_na_gravacao_interrompe_com_o_erro() -> None:
    roteiro = Roteiro(["a", ""])

    def falhar(_registro: RegistroVereditos) -> None:
        raise OSError("disco cheio")

    ambiente = Ambiente(
        ler=roteiro.ler,
        escrever=roteiro.saida.append,
        abrir=roteiro.abrir,
        agora=roteiro.agora,
        gravar=falhar,
    )
    with pytest.raises(OSError, match="disco cheio"):
        rodar_sessao(novo(1), imagem_de, ambiente)
