"""Medição da área de fissura das máscaras em função do limiar de binarização.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.medicao ccsd

O comando lê cada máscara em resolução cheia, uma por vez, e guarda apenas a
contagem de pixels por desvio do fundo. Aplica os valores pré-registrados em
``config/regras.py`` e imprime só números: a curva de área por limiar, a razão
do patamar com a classificação e a lista de máscaras anômalas (nome e fração).
Nenhuma imagem é mostrada.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config.caminhos import caminho_manifesto_arquivos, pasta_dados_brutos
from ..config.regras import REGRAS
from ..domain.binarizacao import (
    N_NIVEIS,
    ResumoPatamar,
    avaliar_patamar,
    contagem_por_desvio,
    e_anomala,
    fracao_de_fissura,
)
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import ler_cinza
from ..infrastructure.manifesto_arquivos import carregar_manifesto
from .estrutura import PREFIXO_MASCARAS

INTERVALO_PROGRESSO = 50


@dataclass(frozen=True, slots=True)
class Anomalia:
    """Uma máscara com fissura demais no limiar de binarização.

    Attributes:
        mascara: Caminho da máscara, como ``BW/064.jpg``.
        fracao: Fração de 0 a 1 de pixels de fissura no limiar de binarização.
    """

    mascara: str
    fracao: float


@dataclass(frozen=True, slots=True)
class MedicaoBinarizacao:
    """Resultado da medição de binarização de uma fonte.

    Attributes:
        fonte_id: Identificador da fonte.
        sha256_manifesto: Hash do manifesto de arquivos usado na medição.
        n_mascaras: Quantidade de máscaras medidas.
        n_pixels: Total de pixels das máscaras medidas.
        limiar: Limiar de binarização de treino pré-registrado.
        patamar: Curva de área agregada e classificação do patamar.
        anomalas: Máscaras anômalas, da maior fração para a menor.
    """

    fonte_id: str
    sha256_manifesto: str
    n_mascaras: int
    n_pixels: int
    limiar: int
    patamar: ResumoPatamar
    anomalas: tuple[Anomalia, ...]


def medir_binarizacao(
    raiz: Path,
    fonte_id: str,
    progresso: Callable[[int, int], None] | None = None,
) -> MedicaoBinarizacao:
    """Mede a área de fissura de todas as máscaras de uma fonte.

    Cada máscara é lida em resolução cheia e reduzida a uma contagem por desvio;
    a imagem é descartada antes da leitura da seguinte.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado.
        progresso: Função chamada com (máscaras medidas, total) após cada uma.

    Returns:
        A medição, com os valores pré-registrados de ``REGRAS``.

    Raises:
        FileNotFoundError: Se o manifesto ou alguma máscara não existir.
        OSError: Se algum arquivo não for uma imagem reconhecida.
        ValueError: Se o manifesto for de outra fonte, não tiver máscaras, ou
            se não houver pixels de fissura no limiar baixo do patamar.
    """
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    manifesto = carregar_manifesto(origem)
    if manifesto.fonte_id != fonte_id:
        raise ValueError(
            f"O manifesto de {fonte_id} declara a fonte {manifesto.fonte_id!r}."
        )
    mascaras = [
        arquivo.caminho
        for arquivo in manifesto.arquivos
        if arquivo.caminho.startswith(PREFIXO_MASCARAS)
    ]
    if not mascaras:
        raise ValueError(f"O manifesto de {fonte_id} não tem máscaras.")
    pasta = pasta_dados_brutos(raiz, fonte_id)
    agregada = np.zeros(N_NIVEIS, dtype=np.int64)
    anomalas: list[Anomalia] = []
    for numero, mascara in enumerate(mascaras, start=1):
        contagem = contagem_por_desvio(ler_cinza(pasta / mascara, 1))
        agregada += contagem
        if e_anomala(
            contagem,
            REGRAS.limiar_binarizacao,
            REGRAS.fracao_maxima_fissura_por_mascara,
        ):
            fracao = fracao_de_fissura(contagem, REGRAS.limiar_binarizacao)
            anomalas.append(Anomalia(mascara, fracao))
        if progresso is not None:
            progresso(numero, len(mascaras))
    patamar = avaliar_patamar(
        agregada,
        REGRAS.limiares_binarizacao,
        REGRAS.limiar_patamar_baixo,
        REGRAS.limiar_patamar_alto,
        REGRAS.razao_minima_patamar,
    )
    anomalas.sort(key=lambda a: a.fracao, reverse=True)
    return MedicaoBinarizacao(
        fonte_id=fonte_id,
        sha256_manifesto=sha256_do_arquivo(origem),
        n_mascaras=len(mascaras),
        n_pixels=int(agregada.sum()),
        limiar=REGRAS.limiar_binarizacao,
        patamar=patamar,
        anomalas=tuple(anomalas),
    )


def _percentual(valor: float) -> str:
    """Formata uma proporção como percentual com três casas decimais."""
    return f"{valor * 100:.3f}%".replace(".", ",")


def formatar_medicao(medicao: MedicaoBinarizacao) -> str:
    """Monta o relatório de texto da medição, só com números e nomes.

    Args:
        medicao: A medição a relatar.

    Returns:
        O texto do relatório.
    """
    patamar = medicao.patamar
    classe = "ROBUSTA" if patamar.robusta else "SENSÍVEL"
    linhas = [
        f"Binarização das máscaras de {medicao.fonte_id}",
        f"Manifesto de arquivos (sha256): {medicao.sha256_manifesto[:12]}",
        f"Máscaras medidas: {medicao.n_mascaras} ({medicao.n_pixels} pixels)",
        f"Limiar de treino pré-registrado: {medicao.limiar}",
        "",
        "Área de fissura (fração dos pixels) por limiar:",
    ]
    for limiar, area in zip(patamar.limiares, patamar.areas, strict=True):
        linhas.append(f"  limiar {limiar:3d}: {_percentual(area)}")
    razao = f"{patamar.razao:.3f}".replace(".", ",")
    minimo = f"{REGRAS.razao_minima_patamar:.2f}".replace(".", ",")
    linhas += [
        "",
        f"Patamar {REGRAS.limiar_patamar_baixo}-{REGRAS.limiar_patamar_alto}: "
        f"razão {razao} (mínimo {minimo}) -> binarização {classe}.",
        "",
        f"Máscaras anômalas (fissura acima de "
        f"{_percentual(REGRAS.fracao_maxima_fissura_por_mascara)} no limiar "
        f"{medicao.limiar}): {len(medicao.anomalas)}",
    ]
    for anomalia in medicao.anomalas:
        linhas.append(f"  {anomalia.mascara}  {_percentual(anomalia.fracao)}")
    return "\n".join(linhas)


def _mostrar_progresso(medidas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada bloco de máscaras e ao final."""
    if medidas % INTERVALO_PROGRESSO == 0 or medidas == total:
        print(f"  {medidas}/{total} máscaras medidas", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a medição de binarização.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.medicao",
        description="Mede a área de fissura das máscaras por limiar de binarização.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    try:
        medicao = medir_binarizacao(
            args.raiz.resolve(), args.fonte_id, _mostrar_progresso
        )
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    print(formatar_medicao(medicao))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
