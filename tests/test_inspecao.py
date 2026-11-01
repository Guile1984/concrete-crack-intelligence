"""Testes do sorteio da amostra e da preparação das imagens de inspeção."""

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.config.caminhos import (
    caminho_amostra_inspecao,
    caminho_manifesto_arquivos,
    pasta_dados_brutos,
    pasta_imagens_inspecao,
)
from concrete_crack.config.regras import REGRAS
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.infrastructure.arquivos import sha256_do_arquivo
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.presentation.inspecao import (
    LARGURA_SEPARADOR,
    main,
    preparar_imagens,
    sortear_amostra,
)

HASH = "a" * 64


def montar_raiz(tmp_path: Path, n_mascaras: int = 100, nome: str = "projeto") -> Path:
    raiz = tmp_path / nome
    (raiz / "manifests").mkdir(parents=True)
    arquivos = [ArquivoRegistrado("pacote.rar", 10, HASH)]
    for i in range(1, n_mascaras + 1):
        arquivos.append(ArquivoRegistrado(f"BW/{i:03d}.jpg", 1, HASH))
        arquivos.append(ArquivoRegistrado(f"rgb/{i:03d}.JPG", 1, HASH))
    manifesto = ManifestoArquivos("ccsd", "2026-10-28", tuple(arquivos))
    gravar_manifesto(manifesto, caminho_manifesto_arquivos(raiz, "ccsd"))
    return raiz


def salvar_png(
    caminho: Path, matriz: np.ndarray, orientacao: int | None = None
) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    imagem = Image.fromarray(matriz)
    if orientacao is None:
        imagem.save(caminho, format="PNG")
    else:
        exif = Image.Exif()
        exif[0x0112] = orientacao
        imagem.save(caminho, format="PNG", exif=exif)


def foto_gradiente(altura: int = 40, largura: int = 80) -> np.ndarray:
    """Foto RGB assimétrica, para que qualquer giro errado apareça."""
    linhas = np.arange(altura, dtype=np.uint8)[:, np.newaxis, np.newaxis]
    colunas = np.arange(largura, dtype=np.uint8)[np.newaxis, :, np.newaxis]
    return np.broadcast_to(linhas + colunas, (altura, largura, 3)).astype(np.uint8)


def mascara_com_faixa(altura: int = 40, largura: int = 80) -> np.ndarray:
    matriz = np.zeros((altura, largura), dtype=np.uint8)
    matriz[altura // 2 : altura // 2 + 10, :] = 255
    return matriz


def montar_com_imagens(
    tmp_path: Path,
    foto: np.ndarray | None = None,
    mascara: np.ndarray | None = None,
    orientacao: int | None = None,
) -> Path:
    """Monta 45 pares iguais em disco e sorteia a amostra."""
    raiz = montar_raiz(tmp_path, n_mascaras=45)
    pasta = pasta_dados_brutos(raiz, "ccsd")
    foto = foto_gradiente() if foto is None else foto
    mascara = mascara_com_faixa() if mascara is None else mascara
    for i in range(1, 46):
        salvar_png(pasta / f"rgb/{i:03d}.JPG", foto, orientacao)
        salvar_png(pasta / f"BW/{i:03d}.jpg", mascara)
    sortear_amostra(raiz, "ccsd")
    return raiz


def test_amostra_so_tem_mascaras_e_o_tamanho_registrado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    amostra = sortear_amostra(raiz, "ccsd")["amostra"]
    assert len(amostra) == REGRAS.n_inspecao_mascaras
    assert all(caminho.startswith("BW/") for caminho in amostra)


def test_arquivo_gravado_tem_o_registro_completo(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    sortear_amostra(raiz, "ccsd")
    destino = caminho_amostra_inspecao(raiz, "ccsd")
    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["fonte_id"] == "ccsd"
    assert dados["seed"] == REGRAS.seed_inspecao_mascaras
    assert dados["n"] == REGRAS.n_inspecao_mascaras
    assert dados["limiar_reprovacao"] == REGRAS.limiar_reprovacao_mascaras
    assert dados["total_mascaras"] == 100
    assert dados["sha256_manifesto_de_arquivos"] == sha256_do_arquivo(
        caminho_manifesto_arquivos(raiz, "ccsd")
    )
    assert dados["amostra"] == sorted(dados["amostra"])
    conteudo = destino.read_bytes()
    assert conteudo.endswith(b"\n")
    assert b"\r" not in conteudo


def test_mesmo_manifesto_gera_a_mesma_amostra(tmp_path: Path) -> None:
    raiz_a = montar_raiz(tmp_path, nome="a")
    raiz_b = montar_raiz(tmp_path, nome="b")
    assert sortear_amostra(raiz_a, "ccsd") == sortear_amostra(raiz_b, "ccsd")


def test_nao_sobrescreve_a_amostra(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    sortear_amostra(raiz, "ccsd")
    destino = caminho_amostra_inspecao(raiz, "ccsd")
    antes = destino.read_bytes()
    with pytest.raises(FileExistsError):
        sortear_amostra(raiz, "ccsd")
    assert destino.read_bytes() == antes


def test_manifesto_com_poucas_mascaras_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, n_mascaras=30)
    with pytest.raises(ValueError, match="fora do intervalo"):
        sortear_amostra(raiz, "ccsd")
    assert not caminho_amostra_inspecao(raiz, "ccsd").exists()


def test_manifesto_de_outra_fonte_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    outro = ManifestoArquivos(
        "s2ds", "2026-10-28", (ArquivoRegistrado("BW/001.jpg", 1, HASH),)
    )
    gravar_manifesto(outro, caminho_manifesto_arquivos(raiz, "ccsd"))
    with pytest.raises(ValueError, match="declara"):
        sortear_amostra(raiz, "ccsd")


def test_main_sorteia_e_recusa_repetir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    base = ["--raiz", str(raiz)]
    assert main([*base, "sortear", "ccsd"]) == 0
    assert "Sorteadas 40 de 100" in capsys.readouterr().out
    assert main([*base, "sortear", "ccsd"]) == 2
    assert "já existe" in capsys.readouterr().err


def test_main_devolve_2_sem_manifesto(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = tmp_path / "vazio"
    (raiz / "manifests").mkdir(parents=True)
    assert main(["--raiz", str(raiz), "sortear", "ccsd"]) == 2
    assert "Erro" in capsys.readouterr().err


def test_convencao_do_caminho_da_amostra() -> None:
    raiz = Path("projeto")
    assert caminho_amostra_inspecao(raiz, "ccsd") == (
        raiz / "manifests" / "inspecao_ccsd.json"
    )


def test_convencao_da_pasta_das_imagens_de_inspecao() -> None:
    raiz = Path("projeto")
    assert pasta_imagens_inspecao(raiz, "ccsd") == (
        raiz / "data" / "interim" / "inspecao_ccsd"
    )


def test_preparar_grava_uma_imagem_por_mascara_da_amostra(tmp_path: Path) -> None:
    raiz = montar_com_imagens(tmp_path)
    gravadas = preparar_imagens(raiz, "ccsd")
    amostra = json.loads(
        caminho_amostra_inspecao(raiz, "ccsd").read_text(encoding="utf-8")
    )["amostra"]
    assert len(gravadas) == REGRAS.n_inspecao_mascaras
    assert [p.name for p in gravadas] == [
        f"{i:02d}_{Path(m).stem}.png" for i, m in enumerate(amostra, start=1)
    ]
    assert all(p.is_file() for p in gravadas)


def test_painel_tem_foto_limpa_a_esquerda_e_vermelho_so_sob_a_mascara(
    tmp_path: Path,
) -> None:
    foto = foto_gradiente()
    raiz = montar_com_imagens(tmp_path, foto=foto)
    primeira = preparar_imagens(raiz, "ccsd")[0]
    painel = np.asarray(Image.open(primeira))
    # foto 80x40 reduzida 5x: 16x8; painel = 16 + faixa + 16 colunas.
    assert painel.shape == (8, 16 + LARGURA_SEPARADOR + 16, 3)
    esquerda = painel[:, :16]
    direita = painel[:, 16 + LARGURA_SEPARADOR :]
    faixa_mascara = slice(4, 6)  # linhas 20..29 da máscara, reduzidas 5x
    fora = np.ones(8, dtype=bool)
    fora[faixa_mascara] = False
    assert np.array_equal(direita[fora], esquerda[fora])
    assert np.all(direita[faixa_mascara][..., 0] > esquerda[faixa_mascara][..., 0])
    assert np.all(direita[faixa_mascara][..., 1] < esquerda[faixa_mascara][..., 1])
    assert np.all(painel[:, 16 : 16 + LARGURA_SEPARADOR] == (0, 0, 255))


def test_foto_com_exif_6_aparece_girada_no_painel(tmp_path: Path) -> None:
    armazenada = foto_gradiente(altura=40, largura=80)
    mascara_retrato = mascara_com_faixa(altura=80, largura=40)
    raiz = montar_com_imagens(
        tmp_path, foto=armazenada, mascara=mascara_retrato, orientacao=6
    )
    primeira = preparar_imagens(raiz, "ccsd")[0]
    painel = np.asarray(Image.open(primeira))
    esperado = np.rot90(armazenada[::5, ::5], -1)
    assert painel.shape == (16, 8 + LARGURA_SEPARADOR + 8, 3)
    assert np.abs(painel[:, :8].astype(int) - esperado.astype(int)).max() <= 5


def test_preparar_pode_ser_repetido(tmp_path: Path) -> None:
    raiz = montar_com_imagens(tmp_path)
    primeira = preparar_imagens(raiz, "ccsd")
    antes = primeira[0].read_bytes()
    segunda = preparar_imagens(raiz, "ccsd")
    assert segunda == primeira
    assert segunda[0].read_bytes() == antes


def test_preparar_exige_a_amostra_sorteada(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path)
    with pytest.raises(FileNotFoundError):
        preparar_imagens(raiz, "ccsd")


def test_preparar_recusa_manifesto_alterado_depois_do_sorteio(
    tmp_path: Path,
) -> None:
    raiz = montar_com_imagens(tmp_path)
    caminho = caminho_manifesto_arquivos(raiz, "ccsd")
    alterado = ManifestoArquivos(
        "ccsd", "2026-10-29", (ArquivoRegistrado("BW/001.jpg", 1, HASH),)
    )
    gravar_manifesto(alterado, caminho)
    with pytest.raises(ValueError, match="mudou"):
        preparar_imagens(raiz, "ccsd")


def test_preparar_recusa_mascara_da_amostra_sem_foto(tmp_path: Path) -> None:
    raiz = montar_com_imagens(tmp_path)
    destino = caminho_amostra_inspecao(raiz, "ccsd")
    registro = json.loads(destino.read_text(encoding="utf-8"))
    registro["amostra"] = ["BW/999.jpg"]
    destino.write_text(json.dumps(registro), encoding="utf-8")
    with pytest.raises(ValueError, match="não tem foto"):
        preparar_imagens(raiz, "ccsd")


def test_preparar_recusa_foto_e_mascara_de_formas_diferentes(tmp_path: Path) -> None:
    raiz = montar_com_imagens(tmp_path, mascara=mascara_com_faixa(80, 40))
    with pytest.raises(ValueError, match="formas diferentes"):
        preparar_imagens(raiz, "ccsd")


def test_main_prepara_e_informa(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_com_imagens(tmp_path)
    assert main(["--raiz", str(raiz), "preparar", "ccsd"]) == 0
    saida = capsys.readouterr().out
    assert "Gravadas 40 imagens" in saida
    assert "foto à esquerda" in saida


def test_main_preparar_devolve_2_sem_amostra(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path)
    assert main(["--raiz", str(raiz), "preparar", "ccsd"]) == 2
    assert "Erro" in capsys.readouterr().err
