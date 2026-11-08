"""Testes da auditoria de pares diante da divisão (sem torch, sem imagens)."""

from pathlib import Path

import pytest

from concrete_crack.config.caminhos import (
    caminho_grupos,
    caminho_quase_ligadas,
    caminho_split,
)
from concrete_crack.domain.auditoria import auditar_pares, probabilidades_ao_acaso
from concrete_crack.domain.divisao import Divisao, RegistroDivisao
from concrete_crack.domain.grupos import RegistroGrupos
from concrete_crack.domain.vizinhos import RegistroQuaseLigadas
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.registro_divisao_json import (
    gravar_registro_divisao,
)
from concrete_crack.infrastructure.registro_grupos_json import gravar_registro_grupos
from concrete_crack.infrastructure.registro_quase_ligadas_json import (
    gravar_registro_quase_ligadas,
)
from concrete_crack.presentation.auditoria import (
    auditar_divisao,
    formatar_auditoria,
    main,
)

# Seis fotos conferidas à mão: 4 no treino, 1 na validação, 1 no teste.
DIVISAO = Divisao(("a", "b", "c", "d"), ("e",), ("f",))
# (a, b) mesmo conjunto; (a, f) cruza o teste; (e, f) cruza o teste e
# (b, e) está em conjuntos diferentes sem tocar o teste.
PARES = (("a", "b"), ("a", "f"), ("e", "f"), ("b", "e"))


def test_probabilidades_conferidas_a_mao() -> None:
    # 6 x 5 = 30 pares ordenados; teste: 2 x 1 x 5 = 10; mesmo conjunto: 4 x 3 = 12
    p_teste, p_diferentes = probabilidades_ao_acaso(DIVISAO)
    assert p_teste == pytest.approx(10 / 30)
    assert p_diferentes == pytest.approx(1 - 12 / 30)


def test_probabilidades_com_os_tamanhos_da_divisao_v1() -> None:
    divisao = Divisao(
        tuple(f"t{i}" for i in range(320)),
        tuple(f"v{i}" for i in range(69)),
        tuple(f"x{i}" for i in range(69)),
    )
    p_teste, p_diferentes = probabilidades_ao_acaso(divisao)
    assert 7 * p_teste == pytest.approx(7 * 2 * 69 * 389 / (458 * 457))
    assert 7 * p_diferentes == pytest.approx(7 * 97842 / (458 * 457))


def test_divisao_com_menos_de_2_fotos_e_recusada() -> None:
    with pytest.raises(ValueError, match="pelo menos 2"):
        probabilidades_ao_acaso(Divisao(("a",), (), ()))


def test_conta_quem_cruza_o_teste_e_quem_esta_em_conjuntos_diferentes() -> None:
    auditoria = auditar_pares(PARES, DIVISAO)
    assert auditoria.cruzam_teste == 2
    assert auditoria.em_conjuntos_diferentes == 3
    assert auditoria.esperado_cruzam_teste == pytest.approx(4 * 10 / 30)
    assert auditoria.esperado_diferentes == pytest.approx(4 * 18 / 30)


def test_par_com_as_duas_fotos_no_teste_nao_cruza() -> None:
    divisao = Divisao(("a", "b"), (), ("c", "d"))
    auditoria = auditar_pares((("c", "d"),), divisao)
    assert auditoria.cruzam_teste == 0
    assert auditoria.em_conjuntos_diferentes == 0


def test_guarda_o_conjunto_de_cada_foto_na_ordem_dos_pares() -> None:
    auditoria = auditar_pares(PARES, DIVISAO)
    assert auditoria.pares == PARES
    assert auditoria.conjuntos == (
        ("treino", "treino"),
        ("treino", "teste"),
        ("validacao", "teste"),
        ("treino", "validacao"),
    )


def test_foto_fora_da_divisao_e_recusada() -> None:
    with pytest.raises(KeyError):
        auditar_pares((("a", "z"),), DIVISAO)


def montar_raiz(tmp_path: Path, sha_dos_pares: str | None = None) -> Path:
    """Grupos, divisão e pares quase ligados coerentes entre si."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    grupos = tuple((foto,) for foto in sorted("abcdef"))
    gravar_registro_grupos(
        RegistroGrupos("ccsd", "teste", "c" * 64, "d" * 64, 0.005, grupos),
        caminho_grupos(raiz, "ccsd"),
    )
    sha_grupos = sha256_do_arquivo(caminho_grupos(raiz, "ccsd"))
    registro = RegistroDivisao(
        "ccsd", 7, (0.70, 0.15, 0.15), sha_grupos, "e" * 64, DIVISAO
    )
    gravar_registro_divisao(registro, caminho_split(raiz))
    quase = RegistroQuaseLigadas("ccsd", sha_dos_pares or sha_grupos, 0.005, 2.0, PARES)
    gravar_registro_quase_ligadas(quase, caminho_quase_ligadas(raiz, "ccsd"))
    return raiz


def test_comando_audita_os_pares_gravados(tmp_path: Path) -> None:
    auditoria = auditar_divisao(montar_raiz(tmp_path), "ccsd")
    assert (auditoria.cruzam_teste, auditoria.em_conjuntos_diferentes) == (2, 3)


def test_pares_de_outro_registro_de_grupos_sao_recusados(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, sha_dos_pares="f" * 64)
    with pytest.raises(ValueError, match="outro registro de grupos"):
        auditar_divisao(raiz, "ccsd")


def test_grupos_alterados_depois_da_divisao_sao_recusados(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with caminho_grupos(raiz, "ccsd").open("a", encoding="utf-8") as f:
        f.write(" ")
    with pytest.raises(ValueError, match="mudou desde a gravação da divisão"):
        auditar_divisao(raiz, "ccsd")


def test_relatorio_marca_os_pares_que_cruzam_o_teste(tmp_path: Path) -> None:
    texto = formatar_auditoria(auditar_divisao(montar_raiz(tmp_path), "ccsd"), "ccsd")
    assert "Pares: 4 (8 fotos)" in texto
    assert "Uma foto no teste e a outra fora: 2 (esperado ao acaso: 1,33)" in texto
    assert "Em conjuntos diferentes quaisquer: 3 (esperado ao acaso: 2,40)" in texto
    assert "  a (treino)  f (teste)  <- cruza o teste" in texto
    assert "  b (treino)  e (validacao)\n" in texto + "\n"


def test_main_devolve_0_e_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    raiz = montar_raiz(tmp_path)
    assert main(["--raiz", str(raiz), "ccsd"]) == 0
    assert "Pares: 4 (8 fotos)" in capsys.readouterr().out
    assert main(["--raiz", str(tmp_path), "ccsd"]) == 2
    assert "Erro:" in capsys.readouterr().err
