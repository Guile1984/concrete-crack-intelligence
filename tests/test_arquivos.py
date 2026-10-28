"""Testes do registro de pastas e do manifesto de arquivos em JSON."""

import hashlib
import json
from pathlib import Path

import pytest

from concrete_crack.domain.integridade import ManifestoArquivos, comparar
from concrete_crack.infrastructure.arquivos import registrar_pasta, sha256_do_arquivo
from concrete_crack.infrastructure.manifesto_arquivos import (
    carregar_manifesto,
    gravar_manifesto,
)

# Vetores de teste padrão do SHA-256 (respostas conhecidas de antemão).
VETOR_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
VETOR_VAZIO = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@pytest.mark.parametrize(
    ("conteudo", "esperado"), [(b"abc", VETOR_ABC), (b"", VETOR_VAZIO)]
)
def test_sha256_de_vetores_conhecidos(
    tmp_path: Path, conteudo: bytes, esperado: str
) -> None:
    arquivo = tmp_path / "x.bin"
    arquivo.write_bytes(conteudo)
    assert sha256_do_arquivo(arquivo) == esperado


def test_sha256_em_arquivo_maior_que_um_bloco(tmp_path: Path) -> None:
    conteudo = bytes(range(256)) * (10 * 1024)  # 2,5 MiB: três leituras
    arquivo = tmp_path / "grande.bin"
    arquivo.write_bytes(conteudo)
    assert sha256_do_arquivo(arquivo) == hashlib.sha256(conteudo).hexdigest()


def test_registrar_pasta_ordena_e_usa_barra(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_bytes(b"abc")
    (tmp_path / "B.txt").write_bytes(b"")
    (tmp_path / "sub" / "c.txt").write_bytes(b"abc")
    registros = registrar_pasta(tmp_path)
    assert [r.caminho for r in registros] == ["B.txt", "a.txt", "sub/c.txt"]
    assert [r.tamanho_bytes for r in registros] == [0, 3, 3]
    assert [r.sha256 for r in registros] == [VETOR_VAZIO, VETOR_ABC, VETOR_ABC]


def test_pasta_vazia_nao_tem_arquivos(tmp_path: Path) -> None:
    assert registrar_pasta(tmp_path) == ()


def test_caminho_que_nao_e_pasta_e_recusado(tmp_path: Path) -> None:
    arquivo = tmp_path / "a.txt"
    arquivo.write_bytes(b"abc")
    with pytest.raises(NotADirectoryError):
        registrar_pasta(tmp_path / "nao_existe")
    with pytest.raises(NotADirectoryError):
        registrar_pasta(arquivo)


def test_manifesto_ida_e_volta(tmp_path: Path) -> None:
    pasta = tmp_path / "dados"
    pasta.mkdir()
    (pasta / "a.txt").write_bytes(b"abc")
    manifesto = ManifestoArquivos("ccsd", "2026-10-28", registrar_pasta(pasta))
    destino = tmp_path / "manifesto.json"  # fora da pasta descrita
    gravar_manifesto(manifesto, destino)
    assert carregar_manifesto(destino) == manifesto


def test_gravacao_independe_da_ordem(tmp_path: Path) -> None:
    pasta = tmp_path / "dados"
    pasta.mkdir()
    (pasta / "a.txt").write_bytes(b"abc")
    (pasta / "b.txt").write_bytes(b"xyz")
    registros = registrar_pasta(pasta)
    um = ManifestoArquivos("ccsd", "2026-10-28", registros)
    outro = ManifestoArquivos("ccsd", "2026-10-28", tuple(reversed(registros)))
    gravar_manifesto(um, tmp_path / "1.json")
    gravar_manifesto(outro, tmp_path / "2.json")
    assert (tmp_path / "1.json").read_bytes() == (tmp_path / "2.json").read_bytes()


def test_gravacao_usa_lf_e_termina_com_quebra_de_linha(tmp_path: Path) -> None:
    pasta = tmp_path / "dados"
    pasta.mkdir()
    (pasta / "a.txt").write_bytes(b"abc")
    manifesto = ManifestoArquivos("ccsd", "2026-10-28", registrar_pasta(pasta))
    destino = tmp_path / "manifesto.json"
    gravar_manifesto(manifesto, destino)
    conteudo = destino.read_bytes()
    assert b"\r" not in conteudo
    assert conteudo.endswith(b"\n")


def test_comparacao_detecta_mudanca_remocao_e_adicao(tmp_path: Path) -> None:
    pasta = tmp_path / "dados"
    pasta.mkdir()
    (pasta / "a.txt").write_bytes(b"abc")
    (pasta / "b.txt").write_bytes(b"xyz")
    manifesto = ManifestoArquivos("ccsd", "2026-10-28", registrar_pasta(pasta))
    assert comparar(manifesto, registrar_pasta(pasta)).vazio

    # Mesmo tamanho (3 bytes), conteúdo diferente: só o hash percebe.
    (pasta / "a.txt").write_bytes(b"abd")
    assert comparar(manifesto, registrar_pasta(pasta)).alterados == ("a.txt",)

    (pasta / "a.txt").write_bytes(b"abc")
    (pasta / "b.txt").unlink()
    (pasta / "c.txt").write_bytes(b"novo")
    divergencias = comparar(manifesto, registrar_pasta(pasta))
    assert divergencias.ausentes == ("b.txt",)
    assert divergencias.inesperados == ("c.txt",)


def test_hash_invalido_no_json_e_recusado(tmp_path: Path) -> None:
    destino = tmp_path / "ruim.json"
    ruim = {
        "fonte_id": "ccsd",
        "data_download": "2026-10-28",
        "arquivos": [{"caminho": "a.txt", "tamanho_bytes": 3, "sha256": "xyz"}],
    }
    destino.write_text(json.dumps(ruim), encoding="utf-8")
    with pytest.raises(ValueError, match="sha256"):
        carregar_manifesto(destino)
