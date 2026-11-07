"""Testes do comando de download e conferência dos pesos.

O download usa um Hub falso injetado: nada é baixado. A conferência, que
precisa de torch e timm, fica sob o marcador torch.
"""

import json
from pathlib import Path

import pytest

from concrete_crack.config.caminhos import caminho_manifesto_pesos, pasta_modelos
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.presentation.pesos import (
    ARQUIVO,
    REPOSITORIO,
    baixar_pesos,
    conferir_pesos,
    main,
)

REVISAO = "f" * 40
CONTEUDO = b"pesos falsos"


class HubFalso:
    """Substituto do Hub que registra as chamadas e grava um arquivo pequeno."""

    def __init__(self) -> None:
        self.chamadas: list[tuple[str, str, str, Path]] = []

    def revisao_de(self, repositorio: str) -> str:
        assert repositorio == REPOSITORIO
        return REVISAO

    def baixar(self, repositorio: str, arquivo: str, revisao: str, pasta: Path) -> Path:
        self.chamadas.append((repositorio, arquivo, revisao, pasta))
        destino = pasta / arquivo
        destino.write_bytes(CONTEUDO)
        return destino


def raiz_vazia(tmp_path: Path) -> Path:
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    return raiz


def test_repositorio_e_o_do_timm_para_o_modelo_pre_registrado() -> None:
    assert REPOSITORIO == "timm/vit_small_patch14_dinov2.lvd142m"
    assert ARQUIVO == "model.safetensors"


def test_baixar_usa_a_revisao_consultada_e_grava_o_manifesto(tmp_path: Path) -> None:
    raiz = raiz_vazia(tmp_path)
    hub = HubFalso()
    registro = baixar_pesos(raiz, "2026-11-07", hub.revisao_de, hub.baixar)
    assert hub.chamadas == [(REPOSITORIO, ARQUIVO, REVISAO, pasta_modelos(raiz))]
    arquivo = pasta_modelos(raiz) / ARQUIVO
    assert registro.revisao == REVISAO
    assert registro.tamanho_bytes == len(CONTEUDO)
    assert registro.sha256 == sha256_do_arquivo(arquivo)
    assert registro.data_download == "2026-11-07"
    gravado = json.loads(caminho_manifesto_pesos(raiz).read_text(encoding="utf-8"))
    assert gravado["sha256"] == registro.sha256
    assert gravado["revisao"] == REVISAO


def test_baixar_recusa_se_o_manifesto_ja_existe_e_nao_baixa(tmp_path: Path) -> None:
    raiz = raiz_vazia(tmp_path)
    baixar_pesos(raiz, "2026-11-07", HubFalso().revisao_de, HubFalso().baixar)
    antes = caminho_manifesto_pesos(raiz).read_bytes()
    hub = HubFalso()
    with pytest.raises(FileExistsError, match="não se refaz"):
        baixar_pesos(raiz, "2026-11-08", hub.revisao_de, hub.baixar)
    assert hub.chamadas == []
    assert caminho_manifesto_pesos(raiz).read_bytes() == antes


def test_main_baixar_devolve_2_quando_o_manifesto_ja_existe(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = raiz_vazia(tmp_path)
    baixar_pesos(raiz, "2026-11-07", HubFalso().revisao_de, HubFalso().baixar)
    assert main(["--raiz", str(raiz), "baixar"]) == 2
    assert "não se refaz" in capsys.readouterr().err


def test_main_conferir_sem_manifesto_devolve_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--raiz", str(raiz_vazia(tmp_path)), "conferir"]) == 2
    assert "Erro:" in capsys.readouterr().err


@pytest.fixture
def raiz_com_pesos(tmp_path: Path) -> Path:
    """Raiz com um arquivo de pesos de rede sem pré-treino e o manifesto dele."""
    import timm
    import torch
    from safetensors.torch import save_file

    from concrete_crack.config.regras import REGRAS

    raiz = raiz_vazia(tmp_path)
    torch.manual_seed(0)
    rede = timm.create_model(
        REGRAS.modelo_embeddings,
        pretrained=False,
        num_classes=0,
        img_size=REGRAS.lado_entrada_embeddings,
    )
    estado = {nome: valor.contiguous() for nome, valor in rede.state_dict().items()}

    def baixar(repositorio: str, arquivo: str, revisao: str, pasta: Path) -> Path:
        save_file(estado, pasta / arquivo)
        return pasta / arquivo

    baixar_pesos(raiz, "2026-11-07", lambda _: REVISAO, baixar)
    return raiz


@pytest.mark.torch
def test_conferir_carrega_e_devolve_384_numeros(raiz_com_pesos: Path) -> None:
    assert conferir_pesos(raiz_com_pesos).shape == (384,)


@pytest.mark.torch
def test_conferir_recusa_arquivo_alterado_depois_do_download(
    raiz_com_pesos: Path,
) -> None:
    arquivo = pasta_modelos(raiz_com_pesos) / ARQUIVO
    with arquivo.open("ab") as saida:
        saida.write(b"\0")
    with pytest.raises(ValueError, match="hash dos pesos não confere"):
        conferir_pesos(raiz_com_pesos)


@pytest.mark.torch
def test_repositorio_bate_com_a_configuracao_do_timm() -> None:
    import timm

    from concrete_crack.config.regras import REGRAS

    configuracao = timm.models.get_pretrained_cfg(REGRAS.modelo_embeddings)
    assert configuracao.hf_hub_id == REPOSITORIO
