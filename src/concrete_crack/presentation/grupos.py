"""Gravação dos grupos de quase-duplicatas aprovados na A46.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.grupos ccsd

Roda de novo a detecção por embeddings e só grava ``manifests/grupos_ccsd.json``
se a nova execução reproduzir exatamente os números registrados na A46 (limiar
com 4 casas, pares ligados, quantidade de grupos e maior grupo). Assim o
arquivo corresponde ao resultado que foi decidido, e não a outra execução.
Recusa se o arquivo já existir: os grupos são gravados uma única vez.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ..config.caminhos import caminho_grupos, caminho_manifesto_pesos
from ..domain.grupos import RegistroGrupos
from ..infrastructure.registro_grupos_json import gravar_registro_grupos
from ..infrastructure.registro_pesos_json import carregar_registro_pesos
from .duplicatas_embeddings import (
    Extrator,
    ResultadoEmbeddings,
    detectar_por_embeddings,
)

METODO = "embeddings DINOv2 ViT-S/14, aprovados na A46"
INTERVALO_PROGRESSO = 50


@dataclass(frozen=True, slots=True)
class Referencia:
    """Os números registrados de uma execução, para conferir a repetição.

    Attributes:
        limiar: Limiar com 4 casas decimais, como impresso no relatório.
        pares_ligados: Pares de fotos com distância <= limiar.
        n_grupos: Quantidade de grupos.
        maior_grupo: Tamanho do maior grupo.
    """

    limiar: str
    pares_ligados: int
    n_grupos: int
    maior_grupo: int


REFERENCIA_A46 = Referencia(
    limiar="0,0050", pares_ligados=7, n_grupos=451, maior_grupo=2
)


def divergencias(resultado: ResultadoEmbeddings, referencia: Referencia) -> list[str]:
    """Lista o que a execução não reproduziu da referência.

    Args:
        resultado: A nova execução.
        referencia: Os números registrados.

    Returns:
        Uma descrição por número divergente; vazia se tudo confere.
    """
    agrupamento = resultado.agrupamento
    obtidos = {
        "limiar": f"{resultado.limiar:.4f}".replace(".", ","),
        "pares ligados": agrupamento.pares_ligados,
        "grupos": len(agrupamento.grupos),
        "maior grupo": agrupamento.maior_grupo,
    }
    esperados = {
        "limiar": referencia.limiar,
        "pares ligados": referencia.pares_ligados,
        "grupos": referencia.n_grupos,
        "maior grupo": referencia.maior_grupo,
    }
    return [
        f"{nome}: esperado {esperados[nome]}, obtido {obtidos[nome]}"
        for nome in obtidos
        if obtidos[nome] != esperados[nome]
    ]


def gravar_grupos(
    raiz: Path,
    fonte_id: str,
    referencia: Referencia = REFERENCIA_A46,
    extrator: Extrator | None = None,
    progresso: Callable[[int, int], None] | None = None,
) -> RegistroGrupos:
    """Repete a detecção, confere com a referência e grava os grupos.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte.
        referencia: Números que a execução precisa reproduzir.
        extrator: Extrator de embeddings; None usa o DINOv2 com pesos conferidos.
        progresso: Função chamada com (fotos lidas, total).

    Returns:
        O registro gravado.

    Raises:
        FileExistsError: Se o registro de grupos já existir.
        FileNotFoundError: Se faltar algum manifesto, foto ou arquivo de pesos.
        ValueError: Se a execução não reproduzir a referência.
    """
    destino = caminho_grupos(raiz, fonte_id)
    if destino.exists():
        raise FileExistsError(
            f"Os grupos de {fonte_id} já foram gravados: {destino}. "
            "Eles não se regravam."
        )
    pesos = carregar_registro_pesos(caminho_manifesto_pesos(raiz))
    resultado = detectar_por_embeddings(raiz, fonte_id, extrator, progresso)
    problemas = divergencias(resultado, referencia)
    if problemas:
        raise ValueError(
            "A execução não reproduz o resultado registrado: " + "; ".join(problemas)
        )
    grupos = tuple(
        tuple(resultado.fotos[i] for i in grupo)
        for grupo in resultado.agrupamento.grupos
    )
    registro = RegistroGrupos(
        fonte_id=fonte_id,
        metodo=METODO,
        sha256_manifesto=resultado.sha256_manifesto,
        sha256_pesos=pesos.sha256,
        limiar=resultado.limiar,
        grupos=grupos,
    )
    gravar_registro_grupos(registro, destino)
    return registro


def _mostrar_progresso(lidas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada bloco de fotos e ao final."""
    if lidas % INTERVALO_PROGRESSO == 0 or lidas == total:
        print(f"  {lidas}/{total} fotos lidas", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a gravação dos grupos.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.grupos",
        description="Grava os grupos de quase-duplicatas aprovados na A46.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        registro = gravar_grupos(raiz, args.fonte_id, progresso=_mostrar_progresso)
    except (ValueError, OSError, RuntimeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    destino = caminho_grupos(raiz, args.fonte_id)
    tamanhos = sorted({len(grupo) for grupo in registro.grupos})
    print(f"A execução reproduziu a A46. Grupos gravados em {destino}")
    print(
        f"{len(registro.grupos)} grupos com {registro.n_fotos} fotos; "
        f"tamanhos de grupo: {tamanhos}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
