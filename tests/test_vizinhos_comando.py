"""Testes do comando de análise dos vizinhos mais próximos (sem torch).

Usa o extrator falso e as fotos sintéticas dos testes anteriores: os grupos são
gravados primeiro, como no fluxo real, e a análise roda sobre eles.
"""

import json
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import caminho_grupos, caminho_manifesto_pesos
from concrete_crack.presentation.grupos import gravar_grupos
from concrete_crack.presentation.vizinhos import (
    analisar_vizinhos,
    formatar_vizinhos,
    main,
)
from test_duplicatas_embeddings import ExtratorFalso
from test_grupos import raiz_com_par_e_pesos, referencia_da_execucao


def raiz_com_grupos(tmp_path: Path) -> Path:
    raiz = raiz_com_par_e_pesos(tmp_path)
    gravar_grupos(raiz, "ccsd", referencia_da_execucao(raiz), ExtratorFalso())
    return raiz


def analisar(raiz: Path):
    return analisar_vizinhos(raiz, "ccsd", ExtratorFalso())


def test_mede_as_46_fotos_e_conta_o_par_ate_t(tmp_path: Path) -> None:
    resultado = analisar(raiz_com_grupos(tmp_path))
    assert resultado.n_fotos == 46
    assert sum(resultado.contagens_faixas) == 46
    assert resultado.contagens_faixas[0] == 2
    assert len(resultado.quantis) == 7
    assert resultado.quantis[0] == pytest.approx(0.0)


def test_sensibilidade_em_2t_e_5t(tmp_path: Path) -> None:
    resultado = analisar(raiz_com_grupos(tmp_path))
    assert [item.multiplo for item in resultado.sensibilidade] == [2.0, 5.0]
    pares = [item.pares_ligados for item in resultado.sensibilidade]
    assert pares == sorted(pares)
    assert all(item.pares_ligados >= 1 for item in resultado.sensibilidade)


def test_relatorio_tem_faixas_classificacao_e_nenhum_nome(tmp_path: Path) -> None:
    texto = formatar_vizinhos(analisar(raiz_com_grupos(tmp_path)))
    assert "O agrupamento em T reproduziu os grupos gravados." in texto
    assert "  até T" in texto
    assert "  de T a 2T" in texto
    assert "  de 10T a 20T" in texto
    assert "  acima de 20T" in texto
    assert "com 2T:" in texto and "com 5T:" in texto
    assert "(relevante com mais de 5%)" in texto
    assert "A decisão da A46 não muda." in texto
    assert "rgb/" not in texto
    assert ".JPG" not in texto


def test_grupos_gravados_diferentes_sao_recusados(tmp_path: Path) -> None:
    raiz = raiz_com_grupos(tmp_path)
    arquivo = caminho_grupos(raiz, "ccsd")
    conteudo = json.loads(arquivo.read_text(encoding="utf-8"))
    conteudo["grupos"] = [[foto] for grupo in conteudo["grupos"] for foto in grupo]
    arquivo.write_text(json.dumps(conteudo), encoding="utf-8")
    with pytest.raises(ValueError, match="não reproduz os grupos gravados"):
        analisar(raiz)


def test_pesos_diferentes_dos_da_gravacao_sao_recusados(tmp_path: Path) -> None:
    raiz = raiz_com_grupos(tmp_path)
    manifesto = caminho_manifesto_pesos(raiz)
    conteudo = json.loads(manifesto.read_text(encoding="utf-8"))
    conteudo["sha256"] = "d" * 64
    manifesto.write_text(json.dumps(conteudo), encoding="utf-8")
    extrator = ExtratorFalso()
    with pytest.raises(ValueError, match="pesos não são os mesmos"):
        analisar_vizinhos(raiz, "ccsd", extrator)
    assert extrator.chamadas == 0


def test_main_sem_grupos_gravados_devolve_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = raiz_com_par_e_pesos(tmp_path)
    assert main(["--raiz", str(raiz), "ccsd"]) == 2
    assert "grupos_ccsd.json" in capsys.readouterr().err
