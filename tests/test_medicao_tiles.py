"""Testes da medição descritiva dos tiles do treino (A52, item 8)."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.config.caminhos import (
    caminho_manifesto_arquivos,
    caminho_split,
    pasta_dados_brutos,
)
from concrete_crack.domain.divisao import Divisao, RegistroDivisao
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.infrastructure.registro_divisao_json import (
    gravar_registro_divisao,
)
from concrete_crack.presentation.indice_tiles import gravar_indice
from concrete_crack.presentation.medicao_tiles import (
    formatar_medicao_tiles,
    main,
    medir_tiles,
)

# 001 e 002 no treino; 003 no teste, que não pode entrar na medição.
DIVISAO = Divisao(("rgb/001.JPG", "rgb/002.JPG"), (), ("rgb/003.JPG",))
LADO = 512 * 512


def mascara(numero: str) -> np.ndarray:
    """Máscaras 768 x 1024 conferidas à mão."""
    cinza = np.zeros((768, 1024), dtype=np.uint8)
    if numero == "001":
        cinza[:, 1] = 255  # fissura vertical de 1 px, 768 pixels
        cinza[10, 700] = 255  # ponto isolado, no tile (x=512, y=0)
    if numero == "003":
        cinza[:, :300] = 255  # muita fissura, mas no teste
    return cinza


def montar_raiz(tmp_path: Path) -> Path:
    """Fotos 1024 x 768, máscaras, manifesto, divisão e índice de tiles."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    pasta = pasta_dados_brutos(raiz, "ccsd")
    (pasta / "rgb").mkdir(parents=True)
    (pasta / "BW").mkdir()
    for numero in ("001", "002", "003"):
        foto = np.full((768, 1024, 3), 128, dtype=np.uint8)
        Image.fromarray(foto).save(pasta / f"rgb/{numero}.JPG", "PNG")
        Image.fromarray(mascara(numero)).save(pasta / f"BW/{numero}.jpg", "PNG")
    nomes = [f"BW/{n}.jpg" for n in ("001", "002", "003")]
    nomes += [f"rgb/{n}.JPG" for n in ("001", "002", "003")]
    arquivos = tuple(ArquivoRegistrado(n, 1, "a" * 64) for n in nomes)
    manifesto = caminho_manifesto_arquivos(raiz, "ccsd")
    gravar_manifesto(ManifestoArquivos("ccsd", "2026-11-14", arquivos), manifesto)
    registro = RegistroDivisao(
        "ccsd", 7, (0.70, 0.15, 0.15), "b" * 64, sha256_do_arquivo(manifesto), DIVISAO
    )
    gravar_registro_divisao(registro, caminho_split(raiz))
    gravar_indice(raiz, "ccsd")
    return raiz


def test_mede_so_o_treino_e_conta_os_tiles_sem_fissura(tmp_path: Path) -> None:
    medicao = medir_tiles(montar_raiz(tmp_path), "ccsd")
    assert (medicao.n_fotos, medicao.n_mascaras_sem_fissura) == (2, 1)
    # 2 fotos x 4 tiles; sem fissura: 1 na 001 (x=512, y=256) e os 4 da 002
    assert (medicao.n_tiles, medicao.n_tiles_sem_fissura) == (8, 5)


def test_fracao_de_fissura_nos_tiles_com_fissura(tmp_path: Path) -> None:
    medicao = medir_tiles(montar_raiz(tmp_path), "ccsd")
    # tiles com fissura da 001: 512, 1 e 512 pixels de 262.144
    menor, maior = 1 / LADO, 512 / LADO
    assert medicao.fracao_quartis == pytest.approx(((menor + maior) / 2, maior, maior))


def test_ida_e_volta_das_duas_regras(tmp_path: Path) -> None:
    maioria, qualquer = medir_tiles(montar_raiz(tmp_path), "ccsd").regras
    # fissura original: 768 + 1 = 769 pixels
    assert maioria.regra == "maioria"
    assert maioria.preservados_total == pytest.approx(768 / 769)
    assert maioria.a_mais_total == pytest.approx(768 / 769)
    assert qualquer.regra == "qualquer"
    assert qualquer.preservados_total == 1.0
    # a coluna dobra (+768) e o ponto vira bloco (+3)
    assert qualquer.a_mais_total == pytest.approx(771 / 769)


def test_relatorio_e_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    raiz = montar_raiz(tmp_path)
    texto = formatar_medicao_tiles(medir_tiles(raiz, "ccsd"))
    assert "Máscaras do treino: 2 (1 sem fissura); tiles por escala: 8" in texto
    assert "(a) Tiles sem fissura: 5 de 8 (62,50%)" in texto
    assert "  qualquer  preservados 100,00%" in texto
    assert main(["--raiz", str(raiz), "ccsd"]) == 0
    saida = capsys.readouterr()
    assert "2/2 máscaras" in saida.err
    assert main(["--raiz", str(tmp_path), "ccsd"]) == 2
    assert "Erro:" in capsys.readouterr().err


def test_divisao_alterada_depois_do_indice_e_recusada(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with caminho_split(raiz).open("a", encoding="utf-8") as f:
        f.write(" ")
    with pytest.raises(ValueError, match="divisão mudou"):
        medir_tiles(raiz, "ccsd")
