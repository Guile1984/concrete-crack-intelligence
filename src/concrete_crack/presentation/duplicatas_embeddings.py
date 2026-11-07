"""Detecção de quase-duplicatas por embeddings do DINOv2 (escalada da A44).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.duplicatas_embeddings ccsd

Segue a A45: as fotos são lidas em cor, com redução de 4x e a orientação EXIF
aplicada, e viram vetores da rede com os pesos conferidos pelo manifesto. O
controle positivo usa as mesmas 40 bases, as mesmas 5 variações e os mesmos
lados de recorte do dHash. O limiar vem da cobertura de 95%, os grupos dos
componentes conexos, e a árvore de decisão da A45 dá o desfecho. Imprime só
números agregados: nenhum nome de foto e nenhuma imagem.
"""

import argparse
import statistics
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from ..config.caminhos import (
    caminho_manifesto_arquivos,
    caminho_manifesto_pesos,
    pasta_dados_brutos,
    pasta_modelos,
)
from ..config.regras import REGRAS
from ..domain.amostragem import amostrar_por_hash
from ..domain.duplicatas import (
    Agrupamento,
    AvaliacaoHash,
    agrupar,
    avaliar_hash,
    densidade_do_grupo,
    limiar_por_cobertura,
    matriz_de_distancias_cosseno,
)
from ..domain.escalada import DecisaoEscalada, Desfecho, decidir_escalada
from ..domain.orientacao import aplicar_orientacao
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import ler_cabecalho, ler_rgb
from ..infrastructure.manifesto_arquivos import carregar_manifesto
from ..infrastructure.registro_pesos_json import carregar_registro_pesos
from .duplicatas import variacoes_da_base
from .estrutura import PREFIXO_FOTOS

INTERVALO_PROGRESSO = 50


class Extrator(Protocol):
    """O que o comando precisa de um extrator: uma imagem RGB vira um vetor."""

    def extrair(self, rgb: np.ndarray) -> np.ndarray:
        """Devolve o embedding de uma imagem uint8 (altura, largura, 3)."""
        ...


def extrator_com_pesos_conferidos(raiz: Path) -> Extrator:
    """Carrega a rede com os pesos do manifesto, conferindo o hash.

    Args:
        raiz: Raiz do projeto.

    Returns:
        O extrator do DINOv2 com os pesos pré-treinados.
    """
    registro = carregar_registro_pesos(caminho_manifesto_pesos(raiz))
    from ..infrastructure.embeddings import criar_extrator_com_pesos

    return criar_extrator_com_pesos(
        REGRAS.modelo_embeddings,
        REGRAS.lado_entrada_embeddings,
        pasta_modelos(raiz) / registro.arquivo,
        registro.sha256,
    )


def distancia_cosseno(a: np.ndarray, b: np.ndarray) -> float:
    """Distância de cosseno entre dois vetores (1 menos o cosseno)."""
    return float(matriz_de_distancias_cosseno([a, b])[0, 1])


@dataclass(frozen=True, slots=True)
class ResultadoEmbeddings:
    """Resultado da detecção de quase-duplicatas por embeddings.

    Attributes:
        fonte_id: Identificador da fonte.
        sha256_manifesto: Hash do manifesto de arquivos usado.
        fotos: Caminhos das fotos, na ordem dos índices dos grupos.
        distancias_controle: Distâncias base-variação, por tipo de variação.
        limiar: Limiar T derivado do controle positivo.
        agrupamento: Grupos das fotos reais com distância <= T.
        avaliacao: Critérios (a) e (b).
        densidade_maior_grupo: Densidade do maior grupo (0 se ele tiver 1 foto).
        decisao: Desfecho pela árvore da A45.
    """

    fonte_id: str
    sha256_manifesto: str
    fotos: tuple[str, ...]
    distancias_controle: dict[str, tuple[float, ...]]
    limiar: float
    agrupamento: Agrupamento
    avaliacao: AvaliacaoHash
    densidade_maior_grupo: float
    decisao: DecisaoEscalada


def detectar_por_embeddings(
    raiz: Path,
    fonte_id: str,
    extrator: Extrator | None = None,
    progresso: Callable[[int, int], None] | None = None,
) -> ResultadoEmbeddings:
    """Calcula o limiar pelo controle positivo, agrupa e aplica a árvore da A45.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado.
        extrator: Extrator de embeddings; None carrega o DINOv2 com os pesos
            conferidos pelo manifesto.
        progresso: Função chamada com (fotos lidas, total) após cada leitura.

    Returns:
        O resultado, com os valores pré-registrados de ``REGRAS``.

    Raises:
        FileNotFoundError: Se algum manifesto, foto ou o arquivo de pesos não
            existir.
        OSError: Se algum arquivo não for uma imagem reconhecida.
        ValueError: Se o manifesto for de outra fonte, tiver menos fotos que o
            controle positivo exige, ou o hash dos pesos não conferir.
    """
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    manifesto = carregar_manifesto(origem)
    if manifesto.fonte_id != fonte_id:
        raise ValueError(
            f"O manifesto de {fonte_id} declara a fonte {manifesto.fonte_id!r}."
        )
    fotos = [
        arquivo.caminho
        for arquivo in manifesto.arquivos
        if arquivo.caminho.startswith(PREFIXO_FOTOS)
    ]
    if len(fotos) < REGRAS.n_bases_controle_duplicatas:
        raise ValueError(
            f"O manifesto de {fonte_id} tem {len(fotos)} fotos; o controle "
            f"positivo exige pelo menos {REGRAS.n_bases_controle_duplicatas}."
        )
    bases = set(
        amostrar_por_hash(
            fotos,
            REGRAS.n_bases_controle_duplicatas,
            REGRAS.seed_controle_duplicatas,
        )
    )
    if extrator is None:
        extrator = extrator_com_pesos_conferidos(raiz)
    pasta = pasta_dados_brutos(raiz, fonte_id)
    vetores: list[np.ndarray] = []
    distancias: dict[str, list[float]] = {}
    for numero, foto in enumerate(fotos, start=1):
        caminho = pasta / foto
        orientacao = ler_cabecalho(caminho).orientacao_exif
        rgb = aplicar_orientacao(
            ler_rgb(caminho, REGRAS.fator_leitura_embeddings), orientacao
        )
        original = extrator.extrair(rgb)
        vetores.append(original)
        if foto in bases:
            for nome, variacao in variacoes_da_base(rgb, foto).items():
                distancia = distancia_cosseno(original, extrator.extrair(variacao))
                distancias.setdefault(nome, []).append(distancia)
        if progresso is not None:
            progresso(numero, len(fotos))
    todas = [d for lista in distancias.values() for d in lista]
    limiar = limiar_por_cobertura(todas, REGRAS.cobertura_limiar_duplicatas)
    matriz = matriz_de_distancias_cosseno(vetores)
    agrupamento = agrupar(matriz, limiar)
    avaliacao = avaliar_hash(
        agrupamento,
        REGRAS.fracao_maxima_grupo_duplicatas,
        REGRAS.fracao_maxima_pares_duplicatas,
    )
    maior = max(agrupamento.grupos, key=len)
    densidade = densidade_do_grupo(matriz, maior, limiar) if len(maior) > 1 else 0.0
    decisao = decidir_escalada(
        avaliacao,
        agrupamento,
        densidade,
        REGRAS.proporcao_treino,
        REGRAS.densidade_minima_serie,
    )
    return ResultadoEmbeddings(
        fonte_id=fonte_id,
        sha256_manifesto=sha256_do_arquivo(origem),
        fotos=tuple(fotos),
        distancias_controle={k: tuple(v) for k, v in distancias.items()},
        limiar=limiar,
        agrupamento=agrupamento,
        avaliacao=avaliacao,
        densidade_maior_grupo=densidade,
        decisao=decisao,
    )


def _numero(valor: float, casas: int = 4) -> str:
    """Formata um número com vírgula decimal."""
    return f"{valor:.{casas}f}".replace(".", ",")


def _percentual(valor: float) -> str:
    """Formata uma proporção como percentual com duas casas decimais."""
    return f"{valor * 100:.2f}%".replace(".", ",")


DESCRICOES = {
    Desfecho.APROVADO: "embeddings APROVADOS: os grupos seguem para a divisão.",
    Desfecho.GRUPO_NO_TREINO: (
        "embeddings REPROVADOS pelo maior grupo: ele vai inteiro para o treino "
        "(opção A) e os demais grupos são sorteados."
    ),
    Desfecho.VOLTAR_AO_DHASH: (
        "embeddings REPROVADOS por pares demais: descartar os embeddings e usar "
        "os grupos do dHash (A44) com a opção A."
    ),
    Desfecho.TESTE_EXTERNO: (
        "embeddings REPROVADOS e o maior grupo não cabe no treino: CCSD inteiro "
        "em treino e validação, teste de outra fonte (S2DS)."
    ),
}


def formatar_embeddings(resultado: ResultadoEmbeddings) -> str:
    """Monta o relatório da detecção, só com números agregados.

    Args:
        resultado: O resultado a relatar.

    Returns:
        O texto do relatório, sem nenhum nome de foto.
    """
    agrupamento = resultado.agrupamento
    n_controle = sum(len(v) for v in resultado.distancias_controle.values())
    t = resultado.limiar
    linhas = [
        f"Quase-duplicatas das fotos de {resultado.fonte_id} (DINOv2, A45)",
        f"Manifesto de arquivos (sha256): {resultado.sha256_manifesto[:12]}",
        f"Fotos: {len(resultado.fotos)}; distância de cosseno (0 a 2)",
        "",
        f"Controle positivo: {n_controle} variações fabricadas "
        f"(distância à foto base):",
    ]
    for nome, valores in resultado.distancias_controle.items():
        reconhecidas = sum(d <= t for d in valores) / len(valores)
        mediana = statistics.median(valores)
        linhas.append(
            f"  {nome:<12} n={len(valores):3d}  mediana={_numero(mediana)}"
            f"  máx={_numero(max(valores))}  reconhecidas em T: "
            f"{_percentual(reconhecidas)}"
        )
    cobertura = _percentual(REGRAS.cobertura_limiar_duplicatas)
    linhas += [
        f"Limiar T (menor valor que reconhece {cobertura}): {_numero(t)}",
        "",
        f"Pares de fotos reais com distância <= T: {agrupamento.pares_ligados} "
        f"de {agrupamento.total_pares} "
        f"({_percentual(agrupamento.fracao_pares_ligados)}; "
        f"máximo {_percentual(REGRAS.fracao_maxima_pares_duplicatas)})",
        f"Grupos: {len(agrupamento.grupos)}; maior grupo: "
        f"{agrupamento.maior_grupo} fotos (máximo: mais de "
        f"{_percentual(REGRAS.fracao_maxima_grupo_duplicatas)} das fotos reprova)",
        f"Densidade do maior grupo: {_numero(resultado.densidade_maior_grupo)} "
        f"(série real a partir de {_numero(REGRAS.densidade_minima_serie, 2)})",
        "Grupos por tamanho:",
    ]
    tamanhos = Counter(len(grupo) for grupo in agrupamento.grupos)
    for tamanho in sorted(tamanhos):
        linhas.append(f"  {tamanho:3d} foto(s): {tamanhos[tamanho]} grupo(s)")
    linhas += ["", f"Decisão (A45): {DESCRICOES[resultado.decisao.desfecho]}"]
    if resultado.decisao.serie_real is not None:
        tipo = "SÉRIE REAL" if resultado.decisao.serie_real else "CORRENTE"
        linhas.append(f"Maior grupo declarado: {tipo}.")
    return "\n".join(linhas)


def _mostrar_progresso(lidas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada bloco de fotos e ao final."""
    if lidas % INTERVALO_PROGRESSO == 0 or lidas == total:
        print(f"  {lidas}/{total} fotos lidas", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a detecção de quase-duplicatas por embeddings.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso (qualquer desfecho); 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.duplicatas_embeddings",
        description="Detecta quase-duplicatas entre as fotos (DINOv2, A45).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    try:
        resultado = detectar_por_embeddings(
            args.raiz.resolve(), args.fonte_id, progresso=_mostrar_progresso
        )
    except (ValueError, OSError, RuntimeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    print(formatar_embeddings(resultado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
