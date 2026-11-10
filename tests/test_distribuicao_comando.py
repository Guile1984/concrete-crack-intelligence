"""Testes do comando que resume fotos e fissura por conjunto da divisão."""

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
from concrete_crack.presentation.distribuicao import (
    formatar_distribuicao,
    main,
    medir_distribuicao,
)

ALTURA = 40
LARGURA = 50
# Linhas de fissura de cada máscara (de 40): frações 5%, 10%, 2,5% e 7,5%.
LINHAS = {"001": 2, "002": 4, "003": 1, "004": 3}
DIVISAO = Divisao(("rgb/001.JPG", "rgb/002.JPG"), ("rgb/003.JPG",), ("rgb/004.JPG",))


def mascara(linhas: int) -> np.ndarray:
    """Máscara preta com ``linhas`` linhas inteiras brancas."""
    cinza = np.zeros((ALTURA, LARGURA), dtype=np.uint8)
    cinza[:linhas, :] = 255
    return cinza


def montar_raiz(tmp_path: Path, foto_extra: bool = False) -> Path:
    """Fotos cinza uniformes (a 004 em retrato), máscaras, manifesto e divisão."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    pasta = pasta_dados_brutos(raiz, "ccsd")
    (pasta / "BW").mkdir(parents=True)
    (pasta / "rgb").mkdir()
    for numero, linhas in LINHAS.items():
        Image.fromarray(mascara(linhas)).save(pasta / f"BW/{numero}.jpg", "PNG")
        forma = (LARGURA, ALTURA) if numero == "004" else (ALTURA, LARGURA)
        foto = np.full(forma, 128, dtype=np.uint8)
        Image.fromarray(foto).save(pasta / f"rgb/{numero}.JPG", "PNG")
    nomes = [f"BW/{n}.jpg" for n in LINHAS] + [f"rgb/{n}.JPG" for n in LINHAS]
    if foto_extra:
        nomes.append("rgb/999.JPG")
    arquivos = tuple(ArquivoRegistrado(c, 1, "a" * 64) for c in nomes)
    manifesto = caminho_manifesto_arquivos(raiz, "ccsd")
    gravar_manifesto(ManifestoArquivos("ccsd", "2026-11-10", arquivos), manifesto)
    registro = RegistroDivisao(
        "ccsd", 7, (0.70, 0.15, 0.15), "b" * 64, sha256_do_arquivo(manifesto), DIVISAO
    )
    gravar_registro_divisao(registro, caminho_split(raiz))
    return raiz


def test_resume_cada_conjunto_pela_mascara_em_resolucao_cheia(tmp_path: Path) -> None:
    treino, validacao, teste = medir_distribuicao(
        montar_raiz(tmp_path), "ccsd"
    ).conjuntos
    assert (treino.n_fotos, validacao.n_fotos, teste.n_fotos) == (2, 1, 1)
    # treino: (2 + 4) linhas x 50 pixels sobre 2 x 2000 pixels
    assert treino.fracao_total == pytest.approx(300 / 4000)
    assert treino.quartis == pytest.approx((0.0625, 0.075, 0.0875))
    assert validacao.fracao_total == pytest.approx(0.025)
    assert teste.fracao_total == pytest.approx(0.075)


def test_resolucao_vem_do_cabecalho_da_foto(tmp_path: Path) -> None:
    treino, _, teste = medir_distribuicao(montar_raiz(tmp_path), "ccsd").conjuntos
    assert treino.resolucoes == (((LARGURA, ALTURA), 2),)
    assert teste.resolucoes == (((ALTURA, LARGURA), 1),)


def test_usa_o_limiar_pre_registrado(tmp_path: Path) -> None:
    assert medir_distribuicao(montar_raiz(tmp_path), "ccsd").limiar == 128


def test_manifesto_alterado_depois_da_divisao_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with caminho_manifesto_arquivos(raiz, "ccsd").open("a", encoding="utf-8") as f:
        f.write(" ")
    with pytest.raises(ValueError, match="manifesto de arquivos mudou"):
        medir_distribuicao(raiz, "ccsd")


def test_pareamento_incompleto_e_recusado(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="sem máscara"):
        medir_distribuicao(montar_raiz(tmp_path, foto_extra=True), "ccsd")


def test_progresso_e_chamado_a_cada_foto(tmp_path: Path) -> None:
    chamadas: list[tuple[int, int]] = []
    medir_distribuicao(
        montar_raiz(tmp_path),
        "ccsd",
        lambda feitas, total: chamadas.append((feitas, total)),
    )
    assert chamadas == [(1, 4), (2, 4), (3, 4), (4, 4)]


def test_relatorio_traz_a_tabela_e_as_resolucoes(tmp_path: Path) -> None:
    texto = formatar_distribuicao(medir_distribuicao(montar_raiz(tmp_path), "ccsd"))
    assert "Distribuição da divisão v1 de ccsd (fissura no limiar 128)" in texto
    assert "treino         2         7,500%      6,250%     7,500%      8,750%" in texto
    assert "teste          1         7,500%" in texto
    assert "  treino: 50x40: 2" in texto
    assert "  teste: 40x50: 1" in texto
    assert "rgb/" not in texto


def test_main_devolve_0_e_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    raiz = montar_raiz(tmp_path)
    assert main(["--raiz", str(raiz), "ccsd"]) == 0
    saida = capsys.readouterr()
    assert "validacao      1" in saida.out
    assert "4/4 fotos medidas" in saida.err
    assert main(["--raiz", str(tmp_path), "ccsd"]) == 2
    assert "Erro:" in capsys.readouterr().err
