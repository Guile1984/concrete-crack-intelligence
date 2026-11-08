"""Análise descritiva da distância de cada foto ao vizinho mais próximo (A47).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.vizinhos ccsd

Usa o limiar T e os grupos gravados em ``manifests/grupos_ccsd.json`` e recusa
se o manifesto de arquivos ou os pesos forem outros. Extrai só os vetores das
fotos (sem as variações do controle positivo) e confere que o agrupamento em T
reproduz exatamente os grupos gravados. Imprime só números. Nada aqui muda a
decisão da A46: o resultado serve para descrever a limitação de T.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config.caminhos import (
    caminho_grupos,
    caminho_manifesto_arquivos,
    caminho_manifesto_pesos,
    pasta_dados_brutos,
)
from ..config.regras import REGRAS
from ..domain.duplicatas import agrupar, matriz_de_distancias_cosseno
from ..domain.grupos import RegistroGrupos
from ..domain.orientacao import aplicar_orientacao
from ..domain.vizinhos import (
    contar_por_faixas,
    distancias_ao_vizinho_mais_proximo,
    limitacao_relevante,
    quantis,
    quase_ligadas,
)
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import ler_cabecalho, ler_rgb
from ..infrastructure.manifesto_arquivos import carregar_manifesto
from ..infrastructure.registro_grupos_json import carregar_registro_grupos
from ..infrastructure.registro_pesos_json import carregar_registro_pesos
from .duplicatas_embeddings import Extrator, extrator_com_pesos_conferidos
from .estrutura import PREFIXO_FOTOS

INTERVALO_PROGRESSO = 50
ROTULOS_QUANTIS = ("mínimo", "5%", "25%", "mediana", "75%", "95%", "máximo")


@dataclass(frozen=True, slots=True)
class Sensibilidade:
    """Como ficaria o agrupamento com um múltiplo de T (só descritivo).

    Attributes:
        multiplo: O múltiplo de T.
        pares_ligados: Pares com distância <= multiplo x T.
        n_grupos: Quantidade de grupos.
        maior_grupo: Tamanho do maior grupo.
    """

    multiplo: float
    pares_ligados: int
    n_grupos: int
    maior_grupo: int


@dataclass(frozen=True, slots=True)
class ResultadoVizinhos:
    """Resultado da análise descritiva dos vizinhos mais próximos.

    Attributes:
        fonte_id: Identificador da fonte.
        n_fotos: Quantidade de fotos.
        limiar: O T gravado com os grupos.
        quantis: Mínimo, 5%, 25%, mediana, 75%, 95% e máximo das distâncias.
        contagens_faixas: Fotos por faixa de múltiplos de T.
        n_quase_ligadas: Fotos com vizinho acima de T e até o múltiplo da A47.
        relevante: Se a limitação de T é declarada relevante.
        sensibilidade: O agrupamento em cada múltiplo de sensibilidade.
    """

    fonte_id: str
    n_fotos: int
    limiar: float
    quantis: list[float]
    contagens_faixas: list[int]
    n_quase_ligadas: int
    relevante: bool
    sensibilidade: tuple[Sensibilidade, ...]


@dataclass(frozen=True, slots=True, eq=False)
class MatrizConferida:
    """Os vetores das fotos, já conferidos contra os grupos gravados.

    Attributes:
        fotos: As fotos, na ordem das linhas da matriz.
        matriz: Distâncias de cosseno entre todas as fotos.
        registro: O registro de grupos que forneceu o T.
    """

    fotos: tuple[str, ...]
    matriz: np.ndarray
    registro: RegistroGrupos


def matriz_conferida(
    raiz: Path,
    fonte_id: str,
    extrator: Extrator | None = None,
    progresso: Callable[[int, int], None] | None = None,
) -> MatrizConferida:
    """Refaz a matriz de distâncias e confere que ela reproduz os grupos gravados.

    Antes de extrair, confere que o manifesto de arquivos, os pesos e as fotos
    são os da gravação dos grupos; depois, que o agrupamento em T reproduz
    exatamente os grupos gravados.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com grupos gravados.
        extrator: Extrator de embeddings; None usa o DINOv2 com pesos conferidos.
        progresso: Função chamada com (fotos lidas, total).

    Returns:
        As fotos, a matriz e o registro de grupos.

    Raises:
        FileNotFoundError: Se faltar algum manifesto, foto ou arquivo de pesos.
        ValueError: Se o manifesto de arquivos, os pesos ou as fotos forem
            outros que os da gravação, ou se o agrupamento em T não reproduzir
            os grupos gravados.
    """
    registro = carregar_registro_grupos(caminho_grupos(raiz, fonte_id))
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    if sha256_do_arquivo(origem) != registro.sha256_manifesto:
        raise ValueError("O manifesto de arquivos mudou desde a gravação dos grupos.")
    pesos = carregar_registro_pesos(caminho_manifesto_pesos(raiz))
    if pesos.sha256 != registro.sha256_pesos:
        raise ValueError("Os pesos não são os mesmos da gravação dos grupos.")
    fotos = [
        arquivo.caminho
        for arquivo in carregar_manifesto(origem).arquivos
        if arquivo.caminho.startswith(PREFIXO_FOTOS)
    ]
    gravados = {frozenset(grupo) for grupo in registro.grupos}
    if set(fotos) != {foto for grupo in gravados for foto in grupo}:
        raise ValueError("As fotos do manifesto não são as dos grupos gravados.")
    if extrator is None:
        extrator = extrator_com_pesos_conferidos(raiz)
    pasta = pasta_dados_brutos(raiz, fonte_id)
    vetores = []
    for numero, foto in enumerate(fotos, start=1):
        caminho = pasta / foto
        orientacao = ler_cabecalho(caminho).orientacao_exif
        rgb = aplicar_orientacao(
            ler_rgb(caminho, REGRAS.fator_leitura_embeddings), orientacao
        )
        vetores.append(extrator.extrair(rgb))
        if progresso is not None:
            progresso(numero, len(fotos))
    matriz = matriz_de_distancias_cosseno(vetores)
    refeitos = {
        frozenset(fotos[i] for i in grupo)
        for grupo in agrupar(matriz, registro.limiar).grupos
    }
    if refeitos != gravados:
        raise ValueError("O agrupamento em T não reproduz os grupos gravados.")
    return MatrizConferida(tuple(fotos), matriz, registro)


def analisar_vizinhos(
    raiz: Path,
    fonte_id: str,
    extrator: Extrator | None = None,
    progresso: Callable[[int, int], None] | None = None,
) -> ResultadoVizinhos:
    """Mede a distância de cada foto ao vizinho mais próximo, conforme a A47.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com grupos gravados.
        extrator: Extrator de embeddings; None usa o DINOv2 com pesos conferidos.
        progresso: Função chamada com (fotos lidas, total).

    Returns:
        O resultado descritivo.

    Raises:
        FileNotFoundError: Se faltar algum manifesto, foto ou arquivo de pesos.
        ValueError: Se as conferências de ``matriz_conferida`` falharem.
    """
    conferida = matriz_conferida(raiz, fonte_id, extrator, progresso)
    fotos = conferida.fotos
    matriz = conferida.matriz
    limiar = conferida.registro.limiar
    vizinhos = distancias_ao_vizinho_mais_proximo(matriz)
    limites = [m * limiar for m in REGRAS.multiplos_faixas_vizinho]
    n_quase = quase_ligadas(vizinhos, limiar, REGRAS.multiplo_quase_ligadas)
    sensibilidade = []
    for multiplo in REGRAS.multiplos_sensibilidade_limiar:
        agrupamento = agrupar(matriz, multiplo * limiar)
        sensibilidade.append(
            Sensibilidade(
                multiplo,
                agrupamento.pares_ligados,
                len(agrupamento.grupos),
                agrupamento.maior_grupo,
            )
        )
    return ResultadoVizinhos(
        fonte_id=fonte_id,
        n_fotos=len(fotos),
        limiar=limiar,
        quantis=quantis(vizinhos),
        contagens_faixas=contar_por_faixas(vizinhos, limites),
        n_quase_ligadas=n_quase,
        relevante=limitacao_relevante(
            n_quase, len(fotos), REGRAS.fracao_maxima_quase_ligadas
        ),
        sensibilidade=tuple(sensibilidade),
    )


def _numero(valor: float) -> str:
    """Formata um número com 4 casas e vírgula decimal."""
    return f"{valor:.4f}".replace(".", ",")


def _multiplo(valor: float) -> str:
    """Formata um múltiplo de T sem casas desnecessárias (2 em vez de 2.0)."""
    return f"{valor:g}".replace(".", ",")


def _rotulos_faixas() -> list[str]:
    """Rótulos das faixas: até T, de T a 2T, ..., acima de 20T."""
    multiplos = [_multiplo(m) for m in REGRAS.multiplos_faixas_vizinho]
    nomes = ["T" if m == "1" else f"{m}T" for m in multiplos]
    rotulos = [f"até {nomes[0]}"]
    rotulos += [f"de {a} a {b}" for a, b in zip(nomes, nomes[1:], strict=False)]
    rotulos.append(f"acima de {nomes[-1]}")
    return rotulos


def formatar_vizinhos(resultado: ResultadoVizinhos) -> str:
    """Monta o relatório da análise, só com números.

    Args:
        resultado: O resultado a relatar.

    Returns:
        O texto do relatório.
    """
    n = resultado.n_fotos
    linhas = [
        f"Vizinho mais próximo das fotos de {resultado.fonte_id} (A47, descritiva)",
        f"Fotos: {n}; T gravado com os grupos: {_numero(resultado.limiar)}",
        "O agrupamento em T reproduziu os grupos gravados.",
        "",
        "Distância de cosseno ao vizinho mais próximo:",
    ]
    for rotulo, valor in zip(ROTULOS_QUANTIS, resultado.quantis, strict=True):
        linhas.append(f"  {rotulo:<8} {_numero(valor)}")
    linhas += ["", "Fotos por faixa:"]
    for rotulo, contagem in zip(
        _rotulos_faixas(), resultado.contagens_faixas, strict=True
    ):
        linhas.append(f"  {rotulo:<16} {contagem:4d}")
    linhas += ["", "Só para descrever a fragilidade (T continua o mesmo):"]
    for item in resultado.sensibilidade:
        linhas.append(
            f"  com {_multiplo(item.multiplo)}T: {item.pares_ligados} pares, "
            f"{item.n_grupos} grupos, maior grupo de {item.maior_grupo}"
        )
    multiplo = _multiplo(REGRAS.multiplo_quase_ligadas)
    fracao = f"{REGRAS.fracao_maxima_quase_ligadas:.0%}"
    classe = "RELEVANTE" if resultado.relevante else "PEQUENA"
    linhas += [
        "",
        f"Fotos quase ligadas (vizinho acima de T e até {multiplo}T): "
        f"{resultado.n_quase_ligadas} de {n} (relevante com mais de {fracao})",
        f"Limitação de T declarada: {classe}. A decisão da A46 não muda.",
    ]
    return "\n".join(linhas)


def _mostrar_progresso(lidas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada bloco de fotos e ao final."""
    if lidas % INTERVALO_PROGRESSO == 0 or lidas == total:
        print(f"  {lidas}/{total} fotos lidas", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a análise descritiva dos vizinhos.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.vizinhos",
        description="Distância de cada foto ao vizinho mais próximo (A47).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    try:
        resultado = analisar_vizinhos(
            args.raiz.resolve(), args.fonte_id, progresso=_mostrar_progresso
        )
    except (ValueError, OSError, RuntimeError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    print(formatar_vizinhos(resultado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
