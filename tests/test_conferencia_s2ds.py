"""Testes da conferência dos rótulos do S2DS (A58), com dados sintéticos."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.config.caminhos import (
    caminho_manifesto_arquivos,
    pasta_dados_brutos,
)
from concrete_crack.domain.conferencia_s2ds import (
    ContagemClasse,
    divergencias_da_tabela,
)
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.presentation.rotulos_s2ds import (
    conferir_rotulos,
    formatar_conferencia,
    main,
)

PRETO, BRANCO, VERMELHO = (0, 0, 0), (255, 255, 255), (255, 0, 0)


def test_divergencias_da_tabela_imagens_exatas_e_pixels_com_tolerancia() -> None:
    medido = {"a": ContagemClasse(3, 120_000), "b": ContagemClasse(2, 40_000)}
    # a: 0,12 M contra 0,1 M (dentro de 0,05); b: 2 contra 3 imagens
    publicado = {"a": (3, 0.1), "b": (3, 0.0)}
    assert divergencias_da_tabela(medido, publicado, 0.05) == [
        "b: 2 imagens, publicado 3"
    ]
    assert divergencias_da_tabela(medido, {"a": (3, 0.2)}, 0.05) == [
        "a: 0.12 M pixels, publicado 0.2 M",
        "b: classe ausente de um dos lados",
    ]


def rotulo(cor_metade: tuple[int, int, int]) -> np.ndarray:
    """Rótulo RGBA 4 x 4: metade de cima preta e metade de baixo na cor dada."""
    rgba = np.zeros((4, 4, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    rgba[2:, :, :3] = cor_metade
    return rgba


def montar_raiz(tmp_path: Path, cor_val: tuple[int, int, int] = VERMELHO) -> Path:
    """Dois rótulos no treino (fissura e só fundo) e um na validação."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    pasta = pasta_dados_brutos(raiz, "s2ds")
    rotulos = {
        "train/1_lab.png": rotulo(BRANCO),
        "train/2_lab.png": rotulo(PRETO),
        "val/3_lab.png": rotulo(cor_val),
    }
    for caminho, matriz in rotulos.items():
        destino = pasta / caminho
        destino.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(matriz).save(destino)
    nomes = ["s2ds.zip", "train/1.png", *rotulos]
    arquivos = tuple(ArquivoRegistrado(n, 1, "a" * 64) for n in sorted(nomes))
    gravar_manifesto(
        ManifestoArquivos("s2ds", "2026-11-16", arquivos),
        caminho_manifesto_arquivos(raiz, "s2ds"),
    )
    return raiz


TABELA = {
    "train": {
        "fundo": (2, 0.0),
        "fissura": (1, 0.0),
        "desplacamento": (0, 0.0),
        "corrosao": (0, 0.0),
        "eflorescencia": (0, 0.0),
        "vegetacao": (0, 0.0),
        "ponto_de_controle": (0, 0.0),
    },
    "val": {
        "fundo": (1, 0.0),
        "fissura": (0, 0.0),
        "desplacamento": (1, 0.0),
        "corrosao": (0, 0.0),
        "eflorescencia": (0, 0.0),
        "vegetacao": (0, 0.0),
        "ponto_de_controle": (0, 0.0),
    },
}


def test_conta_imagens_e_pixels_por_conjunto_e_classe(tmp_path: Path) -> None:
    conferencia = conferir_rotulos(montar_raiz(tmp_path), TABELA)
    treino = conferencia.contagens["train"]
    # treino: 8 pixels de fissura na 1; 8 + 16 de fundo nas duas
    assert conferencia.imagens == {"train": 2, "val": 1, "test": 0}
    assert treino["fissura"] == ContagemClasse(1, 8)
    assert treino["fundo"] == ContagemClasse(2, 24)
    assert conferencia.contagens["val"]["desplacamento"] == ContagemClasse(1, 8)
    assert conferencia.divergencias == {"train": [], "val": []}


def test_divergencia_aparece_no_relatorio(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, cor_val=(0, 255, 0))
    texto = formatar_conferencia(conferir_rotulos(raiz, TABELA))
    assert "val: desplacamento: 0 imagens, publicado 1" in texto
    assert "val: vegetacao: 1 imagens, publicado 0" in texto


def test_rotulo_com_cor_fora_do_mapa_e_recusado_com_o_nome(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, cor_val=(128, 128, 128))
    with pytest.raises(ValueError, match="val/3_lab.png: 8 pixel"):
        conferir_rotulos(raiz, TABELA)


def test_main_sem_tabela_real_devolve_1_e_sem_manifesto_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # com a tabela do README, os rótulos sintéticos divergem: código 1
    assert main(["--raiz", str(montar_raiz(tmp_path))]) == 1
    assert "divergência(s)" in capsys.readouterr().out
    assert main(["--raiz", str(tmp_path)]) == 2
    assert "Erro:" in capsys.readouterr().err
