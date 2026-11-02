"""Testes dos comandos julgar e corrigir da inspeção das máscaras."""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_amostra_inspecao,
    caminho_vereditos_inspecao,
    pasta_imagens_inspecao,
)
from concrete_crack.domain.registro_vereditos import RegistroVereditos
from concrete_crack.domain.veredito import Veredito
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.registro_vereditos_json import (
    carregar_registro,
    gravar_registro,
)
from concrete_crack.presentation import inspecao
from concrete_crack.presentation.inspecao import (
    abrir_imagem,
    agora_utc,
    corrigir_veredito,
    julgar_amostra,
    main,
    nome_da_imagem,
)

ADEQ = Veredito.ADEQUADA
INAD = Veredito.INADEQUADA
DUV = Veredito.DUVIDOSA

AMOSTRA = ("BW/010.jpg", "BW/020.jpg", "BW/030.jpg")


def hora_fixa() -> str:
    return "2026-11-02T15:00:00+00:00"


def montar_raiz(tmp_path: Path, com_imagens: bool = True) -> Path:
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    registro = {"fonte_id": "ccsd", "amostra": list(AMOSTRA)}
    texto = json.dumps(registro, ensure_ascii=False, indent=2) + "\n"
    caminho_amostra_inspecao(raiz, "ccsd").write_text(texto, encoding="utf-8")
    if com_imagens:
        pasta = pasta_imagens_inspecao(raiz, "ccsd")
        pasta.mkdir(parents=True)
        for posicao, mascara in enumerate(AMOSTRA, start=1):
            (pasta / nome_da_imagem(posicao, mascara)).write_bytes(b"")
    return raiz


class Teclado:
    """Entrega respostas prontas e guarda a saída e as imagens abertas."""

    def __init__(self, respostas: list[str]) -> None:
        self.respostas = list(respostas)
        self.saida: list[str] = []
        self.abertas: list[Path] = []

    def ler(self, _pergunta: str) -> str:
        if not self.respostas:
            raise EOFError
        return self.respostas.pop(0)

    def julgar(self, raiz: Path) -> RegistroVereditos:
        return julgar_amostra(
            raiz, "ccsd", self.ler, self.saida.append, self.abertas.append, hora_fixa
        )


def test_nome_da_imagem_tem_posicao_com_dois_digitos_e_numero_da_mascara() -> None:
    assert nome_da_imagem(2, "BW/064.jpg") == "02_064.png"
    assert nome_da_imagem(12, "BW/586.jpg") == "12_586.png"


def test_sessao_completa_grava_o_registro_preso_a_amostra(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    final = Teclado(["a", "", "i", "ficou largo", "d", ""]).julgar(raiz)
    gravado = carregar_registro(caminho_vereditos_inspecao(raiz, "ccsd"))
    assert gravado == final
    assert gravado.completo
    assert gravado.vereditos == (ADEQ, INAD, DUV)
    assert gravado.sha256_amostra == sha256_do_arquivo(
        caminho_amostra_inspecao(raiz, "ccsd")
    )


def test_abre_as_imagens_da_pasta_de_inspecao(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    teclado = Teclado(["a", "", "s"])
    teclado.julgar(raiz)
    pasta = pasta_imagens_inspecao(raiz, "ccsd")
    assert teclado.abertas == [pasta / "01_010.png", pasta / "02_020.png"]


def test_sessao_interrompida_continua_de_onde_parou(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    Teclado(["a", "", "i", "", "s"]).julgar(raiz)
    parcial = carregar_registro(caminho_vereditos_inspecao(raiz, "ccsd"))
    assert parcial.vereditos == (ADEQ, INAD)
    teclado = Teclado(["d", ""])
    teclado.julgar(raiz)
    final = carregar_registro(caminho_vereditos_inspecao(raiz, "ccsd"))
    assert final.vereditos == (ADEQ, INAD, DUV)
    assert [p.name for p in teclado.abertas] == ["03_030.png"]


def test_recusa_registro_de_outra_amostra(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    alheio = RegistroVereditos("ccsd", "f" * 64, AMOSTRA)
    gravar_registro(alheio, caminho_vereditos_inspecao(raiz, "ccsd"))
    with pytest.raises(ValueError, match="outra amostra"):
        Teclado(["a", ""]).julgar(raiz)


def test_recusa_registro_de_outra_fonte(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    sha = sha256_do_arquivo(caminho_amostra_inspecao(raiz, "ccsd"))
    alheio = RegistroVereditos("outra", sha, AMOSTRA)
    gravar_registro(alheio, caminho_vereditos_inspecao(raiz, "ccsd"))
    with pytest.raises(ValueError, match="fonte"):
        Teclado(["a", ""]).julgar(raiz)


def test_recusa_quando_faltam_imagens(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, com_imagens=False)
    with pytest.raises(FileNotFoundError, match="preparar"):
        Teclado(["a", ""]).julgar(raiz)


def test_recusa_quando_nao_ha_amostra(tmp_path: Path) -> None:
    raiz = tmp_path / "vazio"
    (raiz / "manifests").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="sortear"):
        Teclado([]).julgar(raiz)


def test_corrigir_muda_o_veredito_e_guarda_o_historico(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    Teclado(["a", "", "a", "", "a", ""]).julgar(raiz)
    corrigido = corrigir_veredito(
        raiz, "ccsd", "BW/020.jpg", INAD, "vi falha ao ampliar", hora_fixa
    )
    gravado = carregar_registro(caminho_vereditos_inspecao(raiz, "ccsd"))
    assert gravado == corrigido
    assert gravado.vereditos == (ADEQ, INAD, ADEQ)
    assert gravado.correcoes[0].de is ADEQ
    assert gravado.correcoes[0].motivo == "vi falha ao ampliar"


def test_corrigir_sem_nenhum_veredito_registrado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with pytest.raises(FileNotFoundError, match="Ainda não há vereditos"):
        corrigir_veredito(raiz, "ccsd", "BW/010.jpg", INAD, "motivo", hora_fixa)


def test_corrigir_mascara_nao_julgada(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    Teclado(["a", "", "s"]).julgar(raiz)
    with pytest.raises(ValueError, match="ainda não foi julgada"):
        corrigir_veredito(raiz, "ccsd", "BW/030.jpg", INAD, "motivo", hora_fixa)


def test_agora_utc_tem_fuso_utc_e_chega_ao_segundo() -> None:
    hora = agora_utc()
    instante = datetime.fromisoformat(hora)
    assert instante.utcoffset() is not None
    assert instante.utcoffset().total_seconds() == 0
    assert instante.microsecond == 0


def test_abrir_imagem_chama_o_startfile_do_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas: list[Path] = []
    monkeypatch.setattr(os, "startfile", chamadas.append, raising=False)
    abrir_imagem(Path("x.png"))
    assert chamadas == [Path("x.png")]


def test_abrir_imagem_sem_startfile_levanta_oserror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delattr(os, "startfile", raising=False)
    with pytest.raises(OSError, match="automaticamente"):
        abrir_imagem(Path("x.png"))


def test_main_julgar_de_ponta_a_ponta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raiz = montar_raiz(tmp_path)
    respostas = iter(["a", "", "i", "", "d", ""])
    monkeypatch.setattr("builtins.input", lambda _pergunta="": next(respostas))
    monkeypatch.setattr(inspecao, "abrir_imagem", lambda _caminho: None)
    assert main(["--raiz", str(raiz), "julgar", "ccsd"]) == 0
    gravado = carregar_registro(caminho_vereditos_inspecao(raiz, "ccsd"))
    assert gravado.vereditos == (ADEQ, INAD, DUV)
    assert datetime.fromisoformat(gravado.julgamentos[0].registrado_em).tzinfo


def test_main_corrigir_de_ponta_a_ponta(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    Teclado(["a", "", "a", "", "a", ""]).julgar(raiz)
    argv = ["--raiz", str(raiz), "corrigir", "ccsd", "BW/010.jpg", "duvidosa", "x"]
    assert main(argv) == 0
    assert "Correção registrada para BW/010.jpg" in capsys.readouterr().out
    gravado = carregar_registro(caminho_vereditos_inspecao(raiz, "ccsd"))
    assert gravado.vereditos == (DUV, ADEQ, ADEQ)


def test_main_corrigir_recusa_veredito_inexistente(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    argv = ["--raiz", str(raiz), "corrigir", "ccsd", "BW/010.jpg", "otima", "x"]
    with pytest.raises(SystemExit) as saida:
        main(argv)
    assert saida.value.code == 2


def test_main_julgar_sem_amostra_sai_com_erro(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = tmp_path / "vazio"
    (raiz / "manifests").mkdir(parents=True)
    assert main(["--raiz", str(raiz), "julgar", "ccsd"]) == 2
    assert "Erro:" in capsys.readouterr().err


def test_main_ctrl_c_sai_com_130_e_mensagem(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def interromper(*_args: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(inspecao, "julgar_amostra", interromper)
    assert main(["--raiz", str(tmp_path), "julgar", "ccsd"]) == 130
    assert "está gravado" in capsys.readouterr().out
