"""Testes do comando de quase-duplicatas por embeddings (A45).

Um extrator falso substitui a rede: o vetor é a cor média de cada célula de uma
grade 4 x 4, o que basta para que fotos iguais tenham o mesmo vetor e fotos
diferentes, vetores diferentes. Nenhum teste aqui precisa de torch.
"""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from concrete_crack.config.caminhos import (
    caminho_manifesto_arquivos,
    pasta_dados_brutos,
)
from concrete_crack.domain.duplicatas import reduzir_por_blocos
from concrete_crack.domain.escalada import Desfecho
from concrete_crack.domain.integridade import ArquivoRegistrado, ManifestoArquivos
from concrete_crack.domain.orientacao import aplicar_orientacao
from concrete_crack.infrastructure.manifesto_arquivos import gravar_manifesto
from concrete_crack.presentation.duplicatas_embeddings import (
    detectar_por_embeddings,
    formatar_embeddings,
    main,
)

HASH = "a" * 64
N_FOTOS = 45


class ExtratorFalso:
    """Vetor = cor média de cada célula de uma grade 4 x 4 (48 números)."""

    def __init__(self) -> None:
        self.chamadas = 0

    def extrair(self, rgb: np.ndarray) -> np.ndarray:
        self.chamadas += 1
        canais = [reduzir_por_blocos(rgb[:, :, c], 4, 4) for c in range(3)]
        return np.concatenate([canal.ravel() for canal in canais])


def cena(semente: int) -> np.ndarray:
    """Foto colorida 240 x 320 em blocos de cor aleatória."""
    blocos = np.random.default_rng(semente).uniform(20, 235, (6, 8, 3))
    return np.kron(blocos, np.ones((40, 40, 1))).astype(np.uint8)


def montar_raiz(
    tmp_path: Path, fotos: list[tuple[np.ndarray, int | None]], fonte: str = "ccsd"
) -> Path:
    """Grava cada (pixels armazenados, orientação EXIF) como rgb/NNN.JPG."""
    raiz = tmp_path / "projeto"
    (raiz / "manifests").mkdir(parents=True)
    nomes = [f"rgb/{i:03d}.JPG" for i in range(1, len(fotos) + 1)]
    arquivos = tuple(
        ArquivoRegistrado(c, 1, HASH) for c in ["pacote.rar", "BW/001.jpg", *nomes]
    )
    gravar_manifesto(
        ManifestoArquivos(fonte, "2026-11-07", arquivos),
        caminho_manifesto_arquivos(raiz, "ccsd"),
    )
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


def distintas(n: int = N_FOTOS) -> list[tuple[np.ndarray, int | None]]:
    return [(cena(s), None) for s in range(n)]


def detectar(raiz: Path):
    return detectar_por_embeddings(raiz, "ccsd", extrator=ExtratorFalso())


def test_controle_positivo_tem_40_bases_e_5_variacoes(tmp_path: Path) -> None:
    resultado = detectar(montar_raiz(tmp_path, distintas()))
    assert list(resultado.distancias_controle) == [
        "jpeg 70",
        "brilho x0.85",
        "brilho x1.15",
        "recorte 5%",
        "recorte 10%",
    ]
    assert all(len(v) == 40 for v in resultado.distancias_controle.values())
    assert all(
        0.0 <= d <= 2.0 for v in resultado.distancias_controle.values() for d in v
    )


def test_cada_foto_e_cada_variacao_passam_pelo_extrator(tmp_path: Path) -> None:
    extrator = ExtratorFalso()
    detectar_por_embeddings(montar_raiz(tmp_path, distintas()), "ccsd", extrator)
    assert extrator.chamadas == N_FOTOS + 40 * 5


def test_fotos_distintas_ficam_sozinhas_e_os_embeddings_sao_aprovados(
    tmp_path: Path,
) -> None:
    resultado = detectar(montar_raiz(tmp_path, distintas()))
    assert resultado.agrupamento.maior_grupo == 1
    assert resultado.densidade_maior_grupo == 0.0
    assert resultado.decisao.desfecho is Desfecho.APROVADO


def test_foto_deitada_com_exif_6_se_junta_a_copia_em_pe(tmp_path: Path) -> None:
    exibida = cena(7)
    armazenada = np.ascontiguousarray(np.rot90(exibida, 1))
    assert np.array_equal(aplicar_orientacao(armazenada, 6), exibida)
    fotos = distintas()
    fotos.append((armazenada, 6))
    resultado = detectar(montar_raiz(tmp_path, fotos))
    assert (7, N_FOTOS) in resultado.agrupamento.grupos


def test_fotos_todas_iguais_voltam_ao_dhash(tmp_path: Path) -> None:
    fotos = [(cena(0), None)] * N_FOTOS
    resultado = detectar(montar_raiz(tmp_path, fotos))
    assert resultado.avaliacao.pares_demais
    assert resultado.densidade_maior_grupo == 1.0
    assert resultado.decisao.desfecho is Desfecho.VOLTAR_AO_DHASH


def test_relatorio_tem_numeros_decisao_e_nenhum_nome(tmp_path: Path) -> None:
    texto = formatar_embeddings(detectar(montar_raiz(tmp_path, distintas())))
    assert "Fotos: 45; distância de cosseno (0 a 2)" in texto
    assert "Controle positivo: 200 variações fabricadas" in texto
    assert "Limiar T (menor valor que reconhece 95,00%):" in texto
    assert "Densidade do maior grupo: 0,0000 (série real a partir de 0,50)" in texto
    assert "Decisão (A45): embeddings APROVADOS" in texto
    assert "rgb/" not in texto
    assert ".JPG" not in texto


def test_relatorio_da_volta_ao_dhash(tmp_path: Path) -> None:
    fotos = [(cena(0), None)] * N_FOTOS
    texto = formatar_embeddings(detectar(montar_raiz(tmp_path, fotos)))
    assert "REPROVADOS por pares demais" in texto
    assert "Maior grupo declarado" not in texto


def test_manifesto_de_outra_fonte_e_recusado(tmp_path: Path) -> None:
    raiz = montar_raiz(tmp_path, distintas(), fonte="s2ds")
    with pytest.raises(ValueError, match="declara a fonte"):
        detectar(raiz)


def test_menos_fotos_que_o_controle_e_recusado(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pelo menos 40"):
        detectar(montar_raiz(tmp_path, distintas(39)))


def test_main_sem_manifesto_dos_pesos_devolve_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = montar_raiz(tmp_path, distintas())
    assert main(["--raiz", str(raiz), "ccsd"]) == 2
    assert "pesos_embeddings.json" in capsys.readouterr().err


def test_main_sem_manifesto_de_arquivos_devolve_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--raiz", str(tmp_path), "ccsd"]) == 2
    assert "Erro:" in capsys.readouterr().err
