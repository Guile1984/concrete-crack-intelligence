"""Testes do comando de medição da binarização das máscaras."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.config.caminhos import (
    caminho_manifesto_arquivos,
    pasta_dados_brutos,
)
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.presentation.medicao import (
    formatar_medicao,
    main,
    medir_binarizacao,
)

HASH = "a" * 64
ALTURA = 40
LARGURA = 50


def mascara_com(valor: int, linhas: int) -> np.ndarray:
    """Máscara preta ALTURA x LARGURA com ``linhas`` linhas inteiras no valor."""
    cinza = np.zeros((ALTURA, LARGURA), dtype=np.uint8)
    cinza[:linhas, :] = valor
    return cinza


def montar_raiz(
    tmp_path: Path,
    mascaras: list[np.ndarray],
    fonte_id: str = "ccsd",
    manifesto_da_fonte: str = "ccsd",
) -> Path:
    """Cria a raiz com um manifesto e uma máscara PNG por matriz (BW/001.jpg...)."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    nomes = [f"BW/{i:03d}.jpg" for i in range(1, len(mascaras) + 1)]
    arquivos = tuple(ArquivoRegistrado(c, 1, HASH) for c in ["pacote.rar", *nomes])
    manifesto = ManifestoArquivos(manifesto_da_fonte, "2026-11-04", arquivos)
    gravar_manifesto(manifesto, caminho_manifesto_arquivos(raiz, fonte_id))
    pasta = pasta_dados_brutos(raiz, fonte_id)
    for nome, cinza in zip(nomes, mascaras, strict=True):
        destino = pasta / nome
        destino.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(cinza).save(destino, format="PNG")
    return raiz


def area_em(medicao_patamar_limiares: tuple[int, ...], areas: tuple[float, ...]):
    """Devolve a função que dá a área num limiar da grade."""

    def area(limiar: int) -> float:
        return areas[medicao_patamar_limiares.index(limiar)]

    return area


def test_mede_em_resolucao_cheia(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2), mascara_com(255, 2)])
    medicao = medir_binarizacao(raiz, "ccsd")
    assert medicao.n_mascaras == 2
    assert medicao.n_pixels == 2 * ALTURA * LARGURA


def test_area_no_limiar_de_treino_e_a_fracao_da_fissura(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2)])
    medicao = medir_binarizacao(raiz, "ccsd")
    area = area_em(medicao.patamar.limiares, medicao.patamar.areas)
    assert area(medicao.limiar) == pytest.approx(2 / ALTURA)


def test_fissura_nitida_da_binarizacao_robusta(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2)])
    medicao = medir_binarizacao(raiz, "ccsd")
    assert medicao.patamar.razao == 1.0
    assert medicao.patamar.robusta


def test_fissura_acinzentada_da_binarizacao_sensivel(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(100, 2)])
    medicao = medir_binarizacao(raiz, "ccsd")
    assert medicao.patamar.razao == 0.0
    assert not medicao.patamar.robusta


def test_sem_anomalias_quando_a_fissura_e_fina(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2), mascara_com(255, 3)])
    assert medir_binarizacao(raiz, "ccsd").anomalas == ()


def test_lista_a_mascara_anomala_com_a_fracao(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2), mascara_com(255, 15)])
    anomalas = medir_binarizacao(raiz, "ccsd").anomalas
    assert [a.mascara for a in anomalas] == ["BW/002.jpg"]
    assert anomalas[0].fracao == pytest.approx(0.375)


def test_anomalas_vem_da_maior_fracao_para_a_menor(tmp_path: Path) -> None:
    raiz = montar_raiz(
        tmp_path, [mascara_com(255, 8), mascara_com(255, 2), mascara_com(255, 15)]
    )
    anomalas = medir_binarizacao(raiz, "ccsd").anomalas
    assert [a.mascara for a in anomalas] == ["BW/003.jpg", "BW/001.jpg"]


def test_progresso_e_chamado_a_cada_mascara(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2)] * 3)
    chamadas: list[tuple[int, int]] = []
    medir_binarizacao(
        raiz, "ccsd", lambda feitas, total: chamadas.append((feitas, total))
    )
    assert chamadas == [(1, 3), (2, 3), (3, 3)]


def test_manifesto_de_outra_fonte_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2)], manifesto_da_fonte="s2ds")
    with pytest.raises(ValueError, match="declara a fonte"):
        medir_binarizacao(raiz, "ccsd")


def test_manifesto_sem_mascaras_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [])
    with pytest.raises(ValueError, match="não tem máscaras"):
        medir_binarizacao(raiz, "ccsd")


def test_mascara_ausente_no_disco_e_recusada(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2)])
    (pasta_dados_brutos(raiz, "ccsd") / "BW" / "001.jpg").unlink()
    with pytest.raises(FileNotFoundError):
        medir_binarizacao(raiz, "ccsd")


def test_sem_nenhuma_fissura_no_limiar_baixo_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [np.full((ALTURA, LARGURA), 90, dtype=np.uint8)])
    with pytest.raises(ValueError, match="Não há pixels"):
        medir_binarizacao(raiz, "ccsd")


def test_relatorio_traz_numeros_curva_classificacao_e_nomes(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2), mascara_com(255, 15)])
    texto = formatar_medicao(medir_binarizacao(raiz, "ccsd"))
    assert "Binarização das máscaras de ccsd" in texto
    assert "Máscaras medidas: 2 (4000 pixels)" in texto
    assert "Limiar de treino pré-registrado: 128" in texto
    assert "  limiar  16:" in texto
    assert "  limiar 240:" in texto
    assert "Patamar 64-192: razão 1,000 (mínimo 0,80) -> binarização ROBUSTA." in texto
    assert "Máscaras anômalas (fissura acima de 10,000% no limiar 128): 1" in texto
    assert "  BW/002.jpg  37,500%" in texto


def test_relatorio_marca_sensivel(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(100, 2)])
    texto = formatar_medicao(medir_binarizacao(raiz, "ccsd"))
    assert "binarização SENSÍVEL." in texto


def test_main_devolve_0_e_imprime_o_relatorio(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path, [mascara_com(255, 2)])
    codigo = main(["--raiz", str(raiz), "ccsd"])
    saida = capsys.readouterr()
    assert codigo == 0
    assert "binarização ROBUSTA." in saida.out
    assert "1/1 máscaras medidas" in saida.err


def test_main_devolve_2_sem_manifesto(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    codigo = main(["--raiz", str(tmp_path), "ccsd"])
    assert codigo == 2
    assert "Erro:" in capsys.readouterr().err
