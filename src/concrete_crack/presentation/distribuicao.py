"""Distribuição das fotos e da fissura por conjunto da divisão v1 (A49).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.distribuicao ccsd

Lê a divisão gravada, confere que o manifesto de arquivos é o da divisão, lê o
cabeçalho de cada foto e a máscara correspondente em resolução cheia, uma por
vez, e resume cada conjunto. Só relata: não grava nada e não altera a divisão.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ..config.caminhos import (
    caminho_manifesto_arquivos,
    caminho_split,
    pasta_dados_brutos,
)
from ..config.regras import REGRAS
from ..domain.binarizacao import contagem_por_desvio, contar_acima
from ..domain.distribuicao import MedidaFoto, ResumoConjunto, distribuir
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import ler_cabecalho, ler_cinza
from ..infrastructure.registro_divisao_json import carregar_registro_divisao
from .estrutura import parear_fonte

INTERVALO_PROGRESSO = 50


@dataclass(frozen=True, slots=True)
class DistribuicaoDivisao:
    """O resumo da divisão de uma fonte.

    Attributes:
        fonte_id: Identificador da fonte.
        sha256_manifesto: Hash do manifesto de arquivos, igual ao da divisão.
        limiar: Limiar de binarização usado.
        conjuntos: Resumos do treino, da validação e do teste.
    """

    fonte_id: str
    sha256_manifesto: str
    limiar: int
    conjuntos: tuple[ResumoConjunto, ResumoConjunto, ResumoConjunto]


def medir_distribuicao(
    raiz: Path,
    fonte_id: str,
    progresso: Callable[[int, int], None] | None = None,
) -> DistribuicaoDivisao:
    """Mede cada foto e máscara da fonte e resume os conjuntos da divisão.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte.
        progresso: Função chamada com (fotos medidas, total) após cada uma.

    Returns:
        A distribuição, com o limiar pré-registrado de ``REGRAS``.

    Raises:
        FileNotFoundError: Se faltar a divisão, o manifesto ou alguma imagem.
        OSError: Se algum arquivo não for uma imagem reconhecida.
        ValueError: Se a divisão for de outra fonte, se o manifesto mudou desde
            a divisão, se o pareamento estiver incompleto ou se as fotos não
            corresponderem às da divisão.
    """
    registro = carregar_registro_divisao(caminho_split(raiz))
    if registro.fonte_id != fonte_id:
        raise ValueError(f"A divisão gravada é da fonte {registro.fonte_id!r}.")
    sha_manifesto = sha256_do_arquivo(caminho_manifesto_arquivos(raiz, fonte_id))
    if sha_manifesto != registro.sha256_manifesto:
        raise ValueError("O manifesto de arquivos mudou desde a gravação da divisão.")
    pareamento = parear_fonte(raiz, fonte_id)
    if not pareamento.completo:
        raise ValueError("Há máscaras sem foto ou fotos sem máscara no manifesto.")
    mascara_de = {foto: mascara for mascara, foto in pareamento.pares}
    pasta = pasta_dados_brutos(raiz, fonte_id)
    medidas: dict[str, MedidaFoto] = {}
    for numero, foto in enumerate(sorted(mascara_de), start=1):
        cabecalho = ler_cabecalho(pasta / foto)
        contagem = contagem_por_desvio(ler_cinza(pasta / mascara_de[foto], 1))
        medidas[foto] = MedidaFoto(
            resolucao=(cabecalho.largura, cabecalho.altura),
            pixels_fissura=contar_acima(contagem, REGRAS.limiar_binarizacao),
            pixels_total=int(contagem.sum()),
        )
        if progresso is not None:
            progresso(numero, len(mascara_de))
    return DistribuicaoDivisao(
        fonte_id=fonte_id,
        sha256_manifesto=sha_manifesto,
        limiar=REGRAS.limiar_binarizacao,
        conjuntos=distribuir(registro.divisao, medidas),
    )


def _percentual(valor: float) -> str:
    """Formata uma proporção como percentual com três casas decimais."""
    return f"{valor * 100:.3f}%".replace(".", ",")


def formatar_distribuicao(distribuicao: DistribuicaoDivisao) -> str:
    """Monta o relatório da distribuição, só com números.

    Args:
        distribuicao: A distribuição a relatar.

    Returns:
        O texto do relatório, sem nenhum nome de foto.
    """
    linhas = [
        f"Distribuição da divisão v1 de {distribuicao.fonte_id} "
        f"(fissura no limiar {distribuicao.limiar})",
        f"Manifesto de arquivos (sha256): {distribuicao.sha256_manifesto[:12]}",
        "",
        "conjunto   fotos  fissura total  1º quartil    mediana  3º quartil",
    ]
    for resumo in distribuicao.conjuntos:
        q1, mediana, q3 = resumo.quartis
        linhas.append(
            f"{resumo.nome:<10} {resumo.n_fotos:5d}  "
            f"{_percentual(resumo.fracao_total):>13}  {_percentual(q1):>10}  "
            f"{_percentual(mediana):>9}  {_percentual(q3):>10}"
        )
    linhas += ["", "Resoluções armazenadas das fotos (largura x altura):"]
    for resumo in distribuicao.conjuntos:
        partes = [f"{lar}x{alt}: {n}" for (lar, alt), n in resumo.resolucoes]
        linhas.append(f"  {resumo.nome}: {'; '.join(partes)}")
    return "\n".join(linhas)


def _mostrar_progresso(medidas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada bloco de fotos e ao final."""
    if medidas % INTERVALO_PROGRESSO == 0 or medidas == total:
        print(f"  {medidas}/{total} fotos medidas", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a medição da distribuição.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.distribuicao",
        description="Resume fotos e fissura por conjunto da divisão (A49).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    try:
        distribuicao = medir_distribuicao(
            args.raiz.resolve(), args.fonte_id, _mostrar_progresso
        )
    except (ValueError, OSError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    print(formatar_distribuicao(distribuicao))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
