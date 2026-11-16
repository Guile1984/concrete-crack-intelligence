"""Conferência dos rótulos do S2DS e da binarização (A58).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.rotulos_s2ds

Lê os 743 rótulos listados no manifesto de arquivos do S2DS, converte cada um
no mapa de classes (recusando alfa ou cor fora do padrão), confere que a
máscara binária tem exatamente os pixels brancos do rótulo e compara as
contagens por conjunto e classe com a tabela publicada no README. Só relata:
não grava nada e não mostra imagens (A57).
"""

import argparse
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import numpy as np

from ..config.caminhos import caminho_manifesto_arquivos, pasta_dados_brutos
from ..config.regras import REGRAS
from ..domain.conferencia_s2ds import ContagemClasse, divergencias_da_tabela
from ..domain.rotulos_s2ds import contar_classes, mapa_de_classes, mascara_binaria
from ..infrastructure.imagens import ler_rgba
from ..infrastructure.manifesto_arquivos import carregar_manifesto

FONTE = "s2ds"
SUFIXO_ROTULO = "_lab.png"
CONJUNTOS = ("train", "val", "test")
# Metade do arredondamento de 0,1 M da tabela publicada (A58).
TOLERANCIA_MILHOES = 0.05
# Tabela do README do S2DS (pacote baixado em 2026-11-16): por conjunto e
# classe, (imagens em que a classe aparece, pixels em milhões).
TABELA_README: dict[str, dict[str, tuple[int, float]]] = {
    "train": {
        "fundo": (556, 519.9),
        "fissura": (180, 0.6),
        "desplacamento": (151, 39.2),
        "corrosao": (209, 8.8),
        "eflorescencia": (96, 4.6),
        "vegetacao": (97, 15.7),
        "ponto_de_controle": (70, 1.5),
    },
    "val": {
        "fundo": (87, 83.8),
        "fissura": (25, 0.1),
        "desplacamento": (23, 3.3),
        "corrosao": (36, 0.5),
        "eflorescencia": (13, 0.6),
        "vegetacao": (16, 2.7),
        "ponto_de_controle": (9, 0.2),
    },
    "test": {
        "fundo": (93, 87.7),
        "fissura": (27, 0.1),
        "desplacamento": (20, 4.2),
        "corrosao": (38, 0.9),
        "eflorescencia": (17, 1.5),
        "vegetacao": (18, 2.9),
        "ponto_de_controle": (10, 0.2),
    },
}


@dataclass(frozen=True, slots=True)
class ConferenciaS2DS:
    """O resultado da conferência dos rótulos.

    Attributes:
        imagens: Rótulos lidos em cada conjunto.
        contagens: Por conjunto, a contagem de cada classe.
        divergencias: Por conjunto, as divergências com a tabela publicada.
    """

    imagens: dict[str, int]
    contagens: dict[str, dict[str, ContagemClasse]]
    divergencias: dict[str, list[str]]


def conferir_rotulos(
    raiz: Path,
    tabela: Mapping[str, Mapping[str, tuple[int, float]]] = TABELA_README,
    progresso: Callable[[int, int], None] | None = None,
) -> ConferenciaS2DS:
    """Converte e conta os rótulos do S2DS e compara com a tabela publicada.

    Args:
        raiz: Raiz do projeto.
        tabela: Tabela publicada, por conjunto e classe.
        progresso: Função chamada com (rótulos lidos, total) após cada um.

    Returns:
        A conferência.

    Raises:
        FileNotFoundError: Se faltar o manifesto ou algum rótulo.
        OSError: Se algum rótulo não for uma imagem reconhecida.
        ValueError: Se algum rótulo tiver modo, alfa ou cor fora do padrão, ou
            se a máscara binária não tiver exatamente os pixels brancos.
    """
    manifesto = carregar_manifesto(caminho_manifesto_arquivos(raiz, FONTE))
    rotulos = [
        a.caminho for a in manifesto.arquivos if a.caminho.endswith(SUFIXO_ROTULO)
    ]
    nomes = [nome for nome, _ in REGRAS.cores_classes_s2ds]
    indice_fissura = nomes.index(REGRAS.classe_fissura_s2ds)
    pasta = pasta_dados_brutos(raiz, FONTE)
    pixels = {c: np.zeros(len(nomes), dtype=np.int64) for c in CONJUNTOS}
    presencas = {c: np.zeros(len(nomes), dtype=np.int64) for c in CONJUNTOS}
    imagens = dict.fromkeys(CONJUNTOS, 0)
    for numero, caminho in enumerate(rotulos, start=1):
        conjunto = PurePosixPath(caminho).parts[0]
        rotulo = ler_rgba(pasta / caminho)
        try:
            classes = mapa_de_classes(
                rotulo, REGRAS.cores_classes_s2ds, REGRAS.alfa_rotulos_s2ds
            )
        except ValueError as erro:
            raise ValueError(f"{caminho}: {erro}") from erro
        brancos = int((rotulo[..., :3] == 255).all(axis=2).sum())
        if int(mascara_binaria(classes, indice_fissura).sum()) != brancos:
            raise ValueError(
                f"{caminho}: a máscara binária não tem os pixels brancos do rótulo."
            )
        contagem = np.array(contar_classes(classes, len(nomes)))
        pixels[conjunto] += contagem
        presencas[conjunto] += contagem > 0
        imagens[conjunto] += 1
        if progresso is not None:
            progresso(numero, len(rotulos))
    contagens = {
        c: {
            nome: ContagemClasse(int(presencas[c][i]), int(pixels[c][i]))
            for i, nome in enumerate(nomes)
        }
        for c in CONJUNTOS
        if c in tabela
    }
    divergencias = {
        c: divergencias_da_tabela(contagens[c], tabela[c], TOLERANCIA_MILHOES)
        for c in contagens
    }
    return ConferenciaS2DS(imagens, contagens, divergencias)


def formatar_conferencia(conferencia: ConferenciaS2DS) -> str:
    """Monta o relatório, só com números agregados.

    Args:
        conferencia: A conferência a relatar.

    Returns:
        O texto do relatório.
    """
    linhas = ["Rótulos do S2DS conferidos com o README (A58)"]
    for conjunto, por_classe in conferencia.contagens.items():
        linhas.append(f"{conjunto}: {conferencia.imagens[conjunto]} rótulos")
        for nome, contagem in por_classe.items():
            linhas.append(
                f"  {nome:<18} {contagem.imagens:4d} imagens  "
                f"{contagem.pixels / 1e6:8.2f} M pixels"
            )
    total = sum(len(d) for d in conferencia.divergencias.values())
    if total == 0:
        linhas.append("Conferência com o README: nenhuma divergência.")
    else:
        linhas.append(f"Conferência com o README: {total} divergência(s):")
        for conjunto, problemas in conferencia.divergencias.items():
            linhas.extend(f"  {conjunto}: {problema}" for problema in problemas)
    return "\n".join(linhas)


def _mostrar_progresso(lidos: int, total: int) -> None:
    """Escreve o andamento em stderr a cada 100 rótulos e ao final."""
    if lidos % 100 == 0 or lidos == total:
        print(f"  {lidos}/{total} rótulos", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a conferência dos rótulos do S2DS.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 sem divergências; 1 com divergências; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.rotulos_s2ds",
        description="Confere os rótulos do S2DS e a binarização (A58).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    args = parser.parse_args(argv)
    try:
        conferencia = conferir_rotulos(
            args.raiz.resolve(), progresso=_mostrar_progresso
        )
    except (ValueError, OSError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    print(formatar_conferencia(conferencia))
    return 1 if any(conferencia.divergencias.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
