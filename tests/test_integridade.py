"""Testes do registro de arquivos e da comparação de integridade."""

import pytest

from concrete_crack.domain.integridade import (
    ArquivoRegistrado,
    Divergencias,
    ManifestoArquivos,
    comparar,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def arq(
    caminho: str = "img/a.jpg", tamanho: int = 10, sha256: str = HASH_A
) -> ArquivoRegistrado:
    return ArquivoRegistrado(caminho, tamanho, sha256)


def manifesto(*arquivos: ArquivoRegistrado) -> ManifestoArquivos:
    return ManifestoArquivos("ccsd", "2026-10-27", tuple(arquivos))


def test_registro_valido_e_aceito() -> None:
    assert arq().caminho == "img/a.jpg"


@pytest.mark.parametrize(
    "caminho",
    [
        "",
        "/abs/a.jpg",
        "C:/a.jpg",
        "a\\b.jpg",
        "../a.jpg",
        "a/../b.jpg",
        "a//b.jpg",
        "a/",
        "./a.jpg",
    ],
)
def test_caminho_invalido_e_recusado(caminho: str) -> None:
    with pytest.raises(ValueError, match="Caminho"):
        arq(caminho=caminho)


def test_tamanho_negativo_e_recusado() -> None:
    with pytest.raises(ValueError, match="negativo"):
        arq(tamanho=-1)


@pytest.mark.parametrize("sha256", ["abc", "A" * 64, "g" * 64, "a" * 63])
def test_hash_mal_formado_e_recusado(sha256: str) -> None:
    with pytest.raises(ValueError, match="sha256"):
        arq(sha256=sha256)


def test_manifesto_valido_e_aceito() -> None:
    assert len(manifesto(arq("a.jpg"), arq("b.jpg")).arquivos) == 2


def test_manifesto_sem_arquivos_e_recusado() -> None:
    with pytest.raises(ValueError, match="ao menos um arquivo"):
        manifesto()


def test_manifesto_com_caminhos_repetidos_e_recusado() -> None:
    with pytest.raises(ValueError, match="repetidos"):
        manifesto(arq("a.jpg"), arq("a.jpg", sha256=HASH_B))


def test_manifesto_com_data_invalida_e_recusado() -> None:
    with pytest.raises(ValueError, match="AAAA-MM-DD"):
        ManifestoArquivos("ccsd", "27/10/2026", (arq(),))


def test_manifesto_com_fonte_vazia_e_recusado() -> None:
    with pytest.raises(ValueError, match="fonte_id"):
        ManifestoArquivos("  ", "2026-10-27", (arq(),))


def test_arquivos_identicos_nao_divergem() -> None:
    esperado = manifesto(arq("a.jpg"), arq("b.jpg"))
    assert comparar(esperado, (arq("b.jpg"), arq("a.jpg"))).vazio


def test_arquivo_ausente_e_detectado() -> None:
    esperado = manifesto(arq("a.jpg"), arq("b.jpg"))
    assert comparar(esperado, (arq("a.jpg"),)).ausentes == ("b.jpg",)


def test_arquivo_inesperado_e_detectado() -> None:
    esperado = manifesto(arq("a.jpg"))
    assert comparar(esperado, (arq("a.jpg"), arq("x.jpg"))).inesperados == ("x.jpg",)


def test_arquivo_alterado_por_hash_e_detectado() -> None:
    esperado = manifesto(arq("a.jpg"))
    assert comparar(esperado, (arq("a.jpg", sha256=HASH_B),)).alterados == ("a.jpg",)


def test_arquivo_alterado_por_tamanho_e_detectado() -> None:
    esperado = manifesto(arq("a.jpg"))
    assert comparar(esperado, (arq("a.jpg", tamanho=11),)).alterados == ("a.jpg",)


def test_caminhos_repetidos_entre_observados_sao_recusados() -> None:
    esperado = manifesto(arq("a.jpg"))
    with pytest.raises(ValueError, match="repetidos"):
        comparar(esperado, (arq("a.jpg"), arq("a.jpg")))


def test_divergencias_mistas_saem_ordenadas() -> None:
    esperado = manifesto(arq("b.jpg"), arq("a.jpg"), arq("c.jpg"))
    observado = (arq("c.jpg", sha256=HASH_B), arq("d.jpg"), arq("a.jpg"))
    assert comparar(esperado, observado) == Divergencias(
        ausentes=("b.jpg",),
        inesperados=("d.jpg",),
        alterados=("c.jpg",),
    )
