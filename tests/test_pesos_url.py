"""Testes do registro de pesos baixados de uma URL fixa (sem torch, sem rede)."""

from dataclasses import replace

import pytest

from concrete_crack.domain.pesos_url import RegistroPesosUrl, prefixo_sha256

REGISTRO = RegistroPesosUrl(
    url="https://download.pytorch.org/models/resnet18-f37072fd.pth",
    arquivo="resnet18-f37072fd.pth",
    tamanho_bytes=123_456,
    sha256="f37072fd" + "0" * 56,
    data_download="2026-11-27",
)


def test_registro_valido_e_aceito() -> None:
    assert REGISTRO.arquivo == "resnet18-f37072fd.pth"


@pytest.mark.parametrize(
    ("arquivo", "prefixo"),
    [
        ("resnet18-f37072fd.pth", "f37072fd"),
        ("efficientnet_b0_rwightman-7f5810bc.pth", "7f5810bc"),
        ("vit-b-16-c867db91.pth", "c867db91"),
    ],
)
def test_prefixo_sai_do_fim_do_nome(arquivo: str, prefixo: str) -> None:
    assert prefixo_sha256(arquivo) == prefixo


@pytest.mark.parametrize(
    "arquivo", ["model.safetensors", "resnet18-f3707.pth", "resnet18-F37072FD.pth"]
)
def test_nome_sem_prefixo_e_recusado(arquivo: str) -> None:
    with pytest.raises(ValueError, match="prefixo"):
        prefixo_sha256(arquivo)


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("url", "http://download.pytorch.org/models/resnet18-f37072fd.pth", "https"),
        ("arquivo", "", "nome simples"),
        ("arquivo", "models/resnet18-f37072fd.pth", "nome simples"),
        ("arquivo", "resnet34-b627a593.pth", "terminar"),
        ("tamanho_bytes", 0, "positivo"),
        ("sha256", "F37072FD" + "0" * 56, "SHA-256"),
        ("sha256", "f37072fd" + "0" * 55, "SHA-256"),
        ("sha256", "0" * 64, "prefixo publicado"),
        ("data_download", "27/11/2026", "AAAA-MM-DD"),
    ],
)
def test_campos_invalidos_sao_recusados(campo: str, valor: object, trecho: str) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGISTRO, **{campo: valor})


def test_url_e_arquivo_sem_prefixo_sao_recusados() -> None:
    with pytest.raises(ValueError, match="prefixo"):
        replace(
            REGISTRO,
            url="https://exemplo.org/model.safetensors",
            arquivo="model.safetensors",
        )
