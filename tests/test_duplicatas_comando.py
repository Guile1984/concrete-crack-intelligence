"""Testes do comando de detecção de quase-duplicatas."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.config.caminhos import (
    caminho_manifesto_arquivos,
    pasta_dados_brutos,
)
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.domain.orientacao import aplicar_orientacao
from concrete_crack.domain.variacoes import LADOS
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.presentation.duplicatas import (
    detectar_duplicatas,
    formatar_duplicatas,
    lado_do_recorte,
    main,
)

HASH = "a" * 64
N_FOTOS = 45


def cena(semente: int) -> np.ndarray:
    """Foto 180 x 240 em blocos de brilho aleatório, sem ruído fino."""
    blocos = np.random.default_rng(semente).uniform(20, 235, (6, 8))
    return np.kron(blocos, np.ones((30, 30))).astype(np.uint8)


def montar_raiz(
    tmp_path: Path,
    fotos: list[tuple[np.ndarray, int | None]],
    manifesto_da_fonte: str = "ccsd",
) -> Path:
    """Grava cada (pixels armazenados, orientação EXIF) como rgb/NNN.JPG."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    nomes = [f"rgb/{i:03d}.JPG" for i in range(1, len(fotos) + 1)]
    caminhos = ["pacote.rar", "BW/001.jpg", *nomes]
    arquivos = tuple(ArquivoRegistrado(c, 1, HASH) for c in caminhos)
    manifesto = ManifestoArquivos(manifesto_da_fonte, "2026-11-06", arquivos)
    gravar_manifesto(manifesto, caminho_manifesto_arquivos(raiz, "ccsd"))
    pasta = pasta_dados_brutos(raiz, "ccsd")
    (pasta / "rgb").mkdir(parents=True)
    for nome, (pixels, orientacao) in zip(nomes, fotos, strict=True):
        imagem = Image.fromarray(pixels)
        if orientacao is None:
            imagem.save(pasta / nome, quality=95)
        else:
            exif = Image.Exif()
            exif[0x0112] = orientacao
            imagem.save(pasta / nome, quality=95, exif=exif)
    return raiz


def fotos_distintas(n: int = N_FOTOS) -> list[tuple[np.ndarray, int | None]]:
    return [(cena(s), None) for s in range(n)]


def test_controle_positivo_tem_40_bases_e_5_variacoes(tmp_path: Path) -> None:
    resultado = detectar_duplicatas(montar_raiz(tmp_path, fotos_distintas()), "ccsd")
    assert len(resultado.fotos) == N_FOTOS
    assert list(resultado.distancias_controle) == [
        "jpeg 70",
        "brilho x0.85",
        "brilho x1.15",
        "recorte 5%",
        "recorte 10%",
    ]
    assert all(len(v) == 40 for v in resultado.distancias_controle.values())


def test_fotos_distintas_ficam_sozinhas_e_o_hash_e_aprovado(tmp_path: Path) -> None:
    resultado = detectar_duplicatas(montar_raiz(tmp_path, fotos_distintas()), "ccsd")
    assert resultado.agrupamento.maior_grupo == 1
    assert not resultado.avaliacao.reprovado


def test_copia_de_uma_foto_entra_no_mesmo_grupo(tmp_path: Path) -> None:
    fotos = fotos_distintas()
    fotos.append((cena(3), None))
    resultado = detectar_duplicatas(montar_raiz(tmp_path, fotos), "ccsd")
    assert (3, N_FOTOS) in resultado.agrupamento.grupos
    assert resultado.agrupamento.maior_grupo == 2


def test_orientacao_exif_e_aplicada_antes_do_hash(tmp_path: Path) -> None:
    exibida = cena(7)
    armazenada = np.ascontiguousarray(np.rot90(exibida, 1))
    assert np.array_equal(aplicar_orientacao(armazenada, 6), exibida)
    fotos = fotos_distintas()
    fotos.append((armazenada, 6))
    resultado = detectar_duplicatas(montar_raiz(tmp_path, fotos), "ccsd")
    assert (7, N_FOTOS) in resultado.agrupamento.grupos


def test_fotos_quase_iguais_formam_grupo_gigante_e_reprovam(tmp_path: Path) -> None:
    base = cena(0).astype(np.int16)
    rng = np.random.default_rng(99)
    fotos = [
        (np.clip(base + rng.integers(-3, 4, base.shape), 0, 255).astype(np.uint8), None)
        for _ in range(N_FOTOS)
    ]
    resultado = detectar_duplicatas(montar_raiz(tmp_path, fotos), "ccsd")
    assert resultado.agrupamento.maior_grupo == N_FOTOS
    assert resultado.avaliacao.grupo_grande_demais
    assert resultado.avaliacao.pares_demais
    assert resultado.avaliacao.reprovado


def test_lado_do_recorte_e_deterministico_e_valido() -> None:
    lado = lado_do_recorte(20261106, "rgb/001.JPG", 0.10)
    assert lado in LADOS
    assert lado == lado_do_recorte(20261106, "rgb/001.JPG", 0.10)
    sorteados = {lado_do_recorte(20261106, f"rgb/{i:03d}.JPG", 0.10) for i in range(40)}
    assert sorteados == set(LADOS)


def test_resultado_e_reprodutivel(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, fotos_distintas())
    primeiro = detectar_duplicatas(raiz, "ccsd")
    segundo = detectar_duplicatas(raiz, "ccsd")
    assert primeiro.distancias_controle == segundo.distancias_controle
    assert primeiro.limiar == segundo.limiar


def test_manifesto_de_outra_fonte_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, fotos_distintas(), manifesto_da_fonte="s2ds")
    with pytest.raises(ValueError, match="declara a fonte"):
        detectar_duplicatas(raiz, "ccsd")


def test_menos_fotos_que_o_controle_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, fotos_distintas(39))
    with pytest.raises(ValueError, match="pelo menos 40"):
        detectar_duplicatas(raiz, "ccsd")


def test_relatorio_tem_numeros_e_nenhum_nome_de_foto(tmp_path: Path) -> None:
    resultado = detectar_duplicatas(montar_raiz(tmp_path, fotos_distintas()), "ccsd")
    texto = formatar_duplicatas(resultado)
    assert "Fotos: 45; bits por hash: 128" in texto
    assert "Controle positivo: 200 variações fabricadas" in texto
    assert f"Limiar T (menor inteiro que reconhece 95,00%): {resultado.limiar}" in texto
    assert "de 990 (" in texto
    assert "dHash APROVADO" in texto
    assert "rgb/" not in texto
    assert ".JPG" not in texto


def test_relatorio_explica_a_reprovacao(tmp_path: Path) -> None:
    base = cena(0)
    fotos = [(base, None)] * N_FOTOS
    texto = formatar_duplicatas(
        detectar_duplicatas(montar_raiz(tmp_path, fotos), "ccsd")
    )
    assert "dHash REPROVADO (maior grupo acima do máximo; pares ligados" in texto
    assert "escalar para embeddings" in texto


def test_main_devolve_0_e_imprime(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path, fotos_distintas())
    codigo = main(["--raiz", str(raiz), "ccsd"])
    saida = capsys.readouterr()
    assert codigo == 0
    assert "dHash APROVADO" in saida.out
    assert "45/45 fotos lidas" in saida.err


def test_main_devolve_2_sem_manifesto(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--raiz", str(tmp_path), "ccsd"]) == 2
    assert "Erro:" in capsys.readouterr().err
