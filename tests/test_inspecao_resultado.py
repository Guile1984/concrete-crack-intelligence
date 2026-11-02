"""Testes do comando resultado: aplicação da regra pré-registrada."""

import json
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_amostra_inspecao,
    caminho_vereditos_inspecao,
)
from concrete_crack.domain.registro_vereditos import RegistroVereditos
from concrete_crack.domain.veredito import Veredito
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.registro_vereditos_json import gravar_registro
from concrete_crack.presentation.inspecao import (
    calcular_resultado,
    formatar_resultado,
    main,
)

ADEQ = Veredito.ADEQUADA
INAD = Veredito.INADEQUADA
DUV = Veredito.DUVIDOSA

AMOSTRA = tuple(f"BW/{i:03d}.jpg" for i in range(1, 41))


def vereditos_com(inadequadas: int, duvidosas: int = 0) -> list[Veredito]:
    adequadas = 40 - inadequadas - duvidosas
    return [INAD] * inadequadas + [DUV] * duvidosas + [ADEQ] * adequadas


def montar_raiz(
    tmp_path: Path,
    vereditos: list[Veredito],
    correcao: bool = False,
) -> Path:
    """Cria a amostra de 40 e grava um registro com os vereditos dados."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    texto = json.dumps({"fonte_id": "ccsd", "amostra": list(AMOSTRA)}, indent=2)
    arquivo = caminho_amostra_inspecao(raiz, "ccsd")
    arquivo.write_text(texto + "\n", encoding="utf-8")
    registro = RegistroVereditos("ccsd", sha256_do_arquivo(arquivo), AMOSTRA)
    for i, (mascara, veredito) in enumerate(zip(AMOSTRA, vereditos, strict=False)):
        hora = f"2026-11-02T15:{i:02d}:00+00:00"
        registro = registro.julgar(mascara, veredito, hora)
    if correcao:
        registro = registro.corrigir(
            "BW/001.jpg", ADEQ, "tecla errada", "2026-11-02T16:00:00+00:00"
        )
    gravar_registro(registro, caminho_vereditos_inspecao(raiz, "ccsd"))
    return raiz


def relatorio(raiz: Path) -> str:
    registro, resultado = calcular_resultado(raiz, "ccsd")
    return formatar_resultado("ccsd", registro, resultado)


def test_oito_inadequadas_reprovam_a_fonte(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, vereditos_com(8))
    _, resultado = calcular_resultado(raiz, "ccsd")
    assert resultado.reprovada
    assert resultado.inadequadas == 8
    assert "Decisão: fonte REPROVADA." in relatorio(raiz)


def test_sete_inadequadas_aprovam_a_fonte(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, vereditos_com(7))
    _, resultado = calcular_resultado(raiz, "ccsd")
    assert not resultado.reprovada
    assert "Decisão: fonte APROVADA." in relatorio(raiz)


def test_duvidosas_nao_entram_na_regra_mas_aparecem_na_sensibilidade(
    tmp_path: Path,
) -> None:
    raiz = montar_raiz(tmp_path, vereditos_com(7, duvidosas=1))
    texto = relatorio(raiz)
    assert "Decisão: fonte APROVADA." in texto
    assert "(duvidosas contadas como inadequadas): fonte REPROVADA" in texto
    assert "A conclusão depende das duvidosas: sim." in texto


def test_sem_duvidosas_a_conclusao_nao_depende_delas(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, vereditos_com(3))
    assert "A conclusão depende das duvidosas: não." in relatorio(raiz)


def test_relatorio_traz_proporcoes_e_wilson_de_oito_em_quarenta(
    tmp_path: Path,
) -> None:
    texto = relatorio(montar_raiz(tmp_path, vereditos_com(8)))
    assert "Inadequadas: 8 (20.0%); Wilson 95%: 10.5% a 34.8%" in texto
    assert "Adequadas:   32 (80.0%)" in texto
    assert "Máscaras julgadas: 40" in texto


def test_relatorio_informa_correcoes_e_duracao(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, vereditos_com(2), correcao=True)
    texto = relatorio(raiz)
    assert "Correções registradas: 1." in texto
    assert "Duração do julgamento: 39 min" in texto


def test_recusa_julgamento_incompleto(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, vereditos_com(2)[:30])
    with pytest.raises(ValueError, match="faltam 10"):
        calcular_resultado(raiz, "ccsd")


def test_recusa_quando_nao_ha_vereditos(tmp_path: Path) -> None:
    raiz = tmp_path / "vazio"
    (raiz / "manifests").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="Ainda não há vereditos"):
        calcular_resultado(raiz, "ccsd")


def test_recusa_amostra_de_tamanho_diferente_do_pre_registro(
    tmp_path: Path,
) -> None:
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    pequena = AMOSTRA[:3]
    texto = json.dumps({"fonte_id": "ccsd", "amostra": list(pequena)}, indent=2)
    arquivo = caminho_amostra_inspecao(raiz, "ccsd")
    arquivo.write_text(texto + "\n", encoding="utf-8")
    registro = RegistroVereditos("ccsd", sha256_do_arquivo(arquivo), pequena)
    for mascara in pequena:
        registro = registro.julgar(mascara, ADEQ, "2026-11-02T15:00:00+00:00")
    gravar_registro(registro, caminho_vereditos_inspecao(raiz, "ccsd"))
    with pytest.raises(ValueError, match="pré-registro"):
        calcular_resultado(raiz, "ccsd")


def test_recusa_registro_de_outra_amostra(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, vereditos_com(2))
    arquivo = caminho_amostra_inspecao(raiz, "ccsd")
    arquivo.write_text(arquivo.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="outra amostra"):
        calcular_resultado(raiz, "ccsd")


def test_main_resultado_imprime_o_relatorio(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path, vereditos_com(8))
    assert main(["--raiz", str(raiz), "resultado", "ccsd"]) == 0
    saida = capsys.readouterr().out
    assert "Inspeção das máscaras de ccsd" in saida
    assert "Decisão: fonte REPROVADA." in saida


def test_main_resultado_incompleto_sai_com_erro(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path, vereditos_com(2)[:30])
    assert main(["--raiz", str(raiz), "resultado", "ccsd"]) == 2
    assert "incompleto" in capsys.readouterr().err
