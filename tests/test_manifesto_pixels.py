"""Testes do manifesto de hashes dos pixels (A54, escolha A)."""

from dataclasses import replace
from pathlib import Path

import PIL
import pytest

from concrete_crack.domain.manifesto_pixels import (
    HashesEscala,
    HashesFoto,
    diferencas,
    montar_manifesto,
)
from concrete_crack.infrastructure.imagens import versao_pillow
from concrete_crack.infrastructure.manifesto_pixels_json import (
    carregar_manifesto_pixels,
    gravar_manifesto_pixels,
)

A, B, C, D = "a" * 64, "b" * 64, "c" * 64, "d" * 64
FOTO = HashesFoto("rgb/001.jpg", (HashesEscala(1, A, B), HashesEscala(2, C, D)))


def test_hashes_iguais_nao_tem_diferencas() -> None:
    assert diferencas(FOTO, FOTO) == []


def test_aponta_a_escala_e_a_imagem_que_mudaram() -> None:
    obtido = HashesFoto("rgb/001.jpg", (HashesEscala(1, A, B), HashesEscala(2, C, A)))
    assert diferencas(FOTO, obtido) == ["escala 2: máscara"]


def test_aponta_foto_e_mascara_da_mesma_escala() -> None:
    obtido = HashesFoto("rgb/001.jpg", (HashesEscala(1, D, C), HashesEscala(2, C, D)))
    assert diferencas(FOTO, obtido) == ["escala 1: foto", "escala 1: máscara"]


def test_escalas_ou_foto_diferentes_sao_apontadas() -> None:
    so_nativa = HashesFoto("rgb/001.jpg", (HashesEscala(1, A, B),))
    outra = replace(FOTO, foto="rgb/002.jpg")
    assert diferencas(FOTO, so_nativa) == ["escalas diferentes"]
    assert diferencas(FOTO, outra) == ["foto 'rgb/002.jpg' no lugar de 'rgb/001.jpg'"]


def test_hash_mal_formado_e_recusado() -> None:
    with pytest.raises(ValueError, match="hexadecimais"):
        HashesEscala(1, "x" * 64, A)


SEGUNDA = HashesFoto("rgb/002.jpg", (HashesEscala(1, B, A), HashesEscala(2, D, C)))


def test_montar_ordena_as_fotos_e_acha_cada_uma() -> None:
    manifesto = montar_manifesto("ccsd", A, "12.0.0", [SEGUNDA, FOTO])
    assert [f.foto for f in manifesto.fotos] == ["rgb/001.jpg", "rgb/002.jpg"]
    assert manifesto.da_foto("rgb/002.jpg") == SEGUNDA
    with pytest.raises(KeyError):
        manifesto.da_foto("rgb/999.jpg")


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("versao_pillow", "", "versão do Pillow"),
        ("sha256_indice", "x", "hexadecimais"),
        ("fotos", (FOTO, FOTO), "únicas"),
    ],
)
def test_manifestos_invalidos_sao_recusados(
    campo: str, valor: object, trecho: str
) -> None:
    manifesto = montar_manifesto("ccsd", A, "12.0.0", [FOTO])
    with pytest.raises(ValueError, match=trecho):
        replace(manifesto, **{campo: valor})


def test_json_com_uma_linha_por_foto_e_ida_e_volta(tmp_path: Path) -> None:
    manifesto = montar_manifesto("ccsd", A, "12.0.0", [SEGUNDA, FOTO])
    destino = tmp_path / "pixels.json"
    gravar_manifesto_pixels(manifesto, destino)
    linhas = destino.read_text(encoding="utf-8").splitlines()
    # "{", 4 linhas de cabeçalho, 2 fotos, "  ]" e "}"
    assert len(linhas) == 9
    assert linhas[5].startswith('    {"foto": "rgb/001.jpg", "escalas": [')
    assert carregar_manifesto_pixels(destino) == manifesto


def test_versao_pillow_e_a_do_pacote_instalado() -> None:
    assert versao_pillow() == PIL.__version__
