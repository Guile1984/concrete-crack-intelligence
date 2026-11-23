"""Ajuste do Frangi na validação do CCSD, por busca em grade (A66).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.ajuste_frangi ccsd

Lê a divisão, os grupos da A49 e o registro do c; monta o cache dos mapas por
escala numa pasta própria deste registro do c; avalia as 240 configurações e
o preditor trivial nas fotos da validação; escolhe pela maior média por
imagem do clDice; e grava o resumo em ``experiments/frangi_ajuste_v1.json`` e
as 240 linhas em ``experiments/frangi_grade_v1.jsonl``. Nunca toca o teste.
Se o resumo já existe, o comando se recusa a rodar: a escolha é feita uma
única vez. Uma rodada interrompida pode ser retomada, porque os mapas já
calculados ficam no cache.
"""

import argparse
import dataclasses
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np
import scipy
import skimage

from ..config.caminhos import (
    caminho_ajuste_frangi,
    caminho_constante_c,
    caminho_grade_frangi,
    caminho_grupos,
    caminho_split,
    pasta_dados_brutos,
    pasta_mapas_frangi,
)
from ..config.regras import REGRAS
from ..domain.alinhamento import marcar_fissura
from ..domain.bootstrap import Intervalo
from ..domain.grade import configuracoes_da_grade
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.cache_mapas import CacheMapasFrangi
from ..infrastructure.imagens import ler_cinza
from ..infrastructure.registro_c_json import carregar_registro_c
from ..infrastructure.registro_divisao_json import carregar_registro_divisao
from ..infrastructure.registro_grupos_json import carregar_registro_grupos
from ..infrastructure.registro_json import gravar_json, gravar_jsonl
from ..ports.mapas_por_escala import MapasPorEscala
from ..services.ajuste_frangi import (
    ResultadoGrade,
    avaliar_grade,
    intervalo_cldice,
    resumir_grade,
)
from .estrutura import parear_fonte


def ajustar(
    fotos: Sequence[str],
    grupo_de: Mapping[str, str],
    ler_gabarito: Callable[[str], np.ndarray],
    mapas: MapasPorEscala,
    progresso: Callable[[int, int], None] | None = None,
) -> tuple[ResultadoGrade, Intervalo]:
    """Roda a grade pré-registrada e calcula o intervalo da escolhida.

    Args:
        fotos: As fotos da validação.
        grupo_de: O grupo da A49 de cada foto.
        ler_gabarito: Devolve a máscara booleana do gabarito de uma foto.
        mapas: A fonte dos mapas por escala.
        progresso: Função chamada com (fotos feitas, total) após cada foto.

    Returns:
        O resultado da grade e o intervalo do clDice da escolhida.
    """
    configuracoes = configuracoes_da_grade(
        REGRAS.faixas_escalas_frangi,
        REGRAS.sigmas_fundo_frangi,
        REGRAS.limiares_frangi,
        REGRAS.tamanhos_minimos_frangi,
    )
    avaliacao = avaliar_grade(
        fotos,
        ler_gabarito,
        mapas,
        configuracoes,
        REGRAS.conectividade_componentes,
        REGRAS.metodo_esqueleto,
        progresso,
    )
    resultado = resumir_grade(avaliacao)
    _, imagens = avaliacao.por_configuracao[resultado.indice_escolhida]
    intervalo = intervalo_cldice(
        imagens,
        grupo_de,
        REGRAS.n_reamostragens_bootstrap,
        REGRAS.nivel_confianca_bootstrap,
        REGRAS.seed_bootstrap,
    )
    return resultado, intervalo


def montar_registros(
    resultado: ResultadoGrade,
    intervalo: Intervalo,
    procedencia: Mapping[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Monta o resumo do ajuste e as linhas da grade, prontos para o JSON.

    Args:
        resultado: O resultado da grade.
        intervalo: O intervalo do clDice da escolhida.
        procedencia: Hashes, fotos e versões, copiados para o resumo.

    Returns:
        O resumo e uma linha por configuração, na ordem da grade.
    """
    configuracao, resumo = resultado.escolhida
    resumo_ajuste = {
        **procedencia,
        "metrica_de_escolha": "media por imagem do clDice, recorte da A63",
        "escolhida": {
            "indice": resultado.indice_escolhida,
            "configuracao": dataclasses.asdict(configuracao),
            "resumo": dataclasses.asdict(resumo),
            "intervalo": {
                **dataclasses.asdict(intervalo),
                "nivel": REGRAS.nivel_confianca_bootstrap,
                "n_reamostragens": REGRAS.n_reamostragens_bootstrap,
                "seed": REGRAS.seed_bootstrap,
                "otimista": "maldicao do vencedor: escolhida entre 240",
            },
        },
        "trivial": {
            "resumo": dataclasses.asdict(resultado.trivial),
            "acuracia_global": resultado.acuracia_trivial,
        },
    }
    linhas = [
        {
            "configuracao": dataclasses.asdict(c),
            "resumo": dataclasses.asdict(r),
        }
        for c, r in resultado.resumos
    ]
    return resumo_ajuste, linhas


def _mostrar_progresso(feitas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada foto."""
    print(f"  {feitas}/{total} fotos", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Ajusta o Frangi na validação e grava os registros.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro ou se o resumo já existir.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.ajuste_frangi",
        description="Ajusta o Frangi na validação por busca em grade (A66).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    destino = caminho_ajuste_frangi(raiz)
    if destino.exists():
        print(
            f"Erro: {destino} já existe; a escolha é feita uma única vez (A66).",
            file=sys.stderr,
        )
        return 2
    inicio = time.perf_counter()
    try:
        origem_split = caminho_split(raiz)
        origem_grupos = caminho_grupos(raiz, args.fonte_id)
        origem_c = caminho_constante_c(raiz)
        divisao = carregar_registro_divisao(origem_split)
        registro_c = carregar_registro_c(origem_c)
        if registro_c.sha256_split != sha256_do_arquivo(origem_split):
            raise ValueError("O registro do c não é desta divisão.")
        grupo_de = {
            foto: grupo[0]
            for grupo in carregar_registro_grupos(origem_grupos).grupos
            for foto in grupo
        }
        mascara_de = {foto: m for m, foto in parear_fonte(raiz, args.fonte_id).pares}
        pasta = pasta_dados_brutos(raiz, args.fonte_id)

        def ler_gabarito(foto: str) -> np.ndarray:
            """Lê a máscara da foto e a binariza pela regra da A41."""
            cinza = ler_cinza(pasta / mascara_de[foto], 1)
            return marcar_fissura(cinza, REGRAS.limiar_binarizacao)

        sha_c = sha256_do_arquivo(origem_c)
        mapas = CacheMapasFrangi(
            pasta,
            pasta_mapas_frangi(raiz, args.fonte_id) / sha_c[:12],
            registro_c,
            REGRAS.escalas_frangi,
            REGRAS.beta_frangi,
        )
        fotos = sorted(divisao.divisao.validacao)
        resultado, intervalo = ajustar(
            fotos, grupo_de, ler_gabarito, mapas, _mostrar_progresso
        )
    except (ValueError, OSError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    procedencia = {
        "fonte_id": args.fonte_id,
        "sha256_split": sha256_do_arquivo(origem_split),
        "sha256_grupos": sha256_do_arquivo(origem_grupos),
        "sha256_registro_c": sha_c,
        "versoes": {
            "numpy": np.__version__,
            "scikit-image": skimage.__version__,
            "scipy": scipy.__version__,
        },
        "fotos": list(fotos),
    }
    resumo, linhas = montar_registros(resultado, intervalo, procedencia)
    gravar_jsonl(linhas, caminho_grade_frangi(raiz))
    gravar_json(resumo, destino)
    configuracao, escolhida = resultado.escolhida
    print(f"Escolhida (posição {resultado.indice_escolhida}): {configuracao}")
    print(
        f"clDice médio na validação: {escolhida.cldice.valor:.4f} "
        f"[{intervalo.inferior:.4f}, {intervalo.superior:.4f}] (otimista)"
    )
    print(
        f"Trivial: clDice {resultado.trivial.cldice.valor}; "
        f"acurácia {resultado.acuracia_trivial:.4f}"
    )
    print(f"Tempo: {(time.perf_counter() - inicio) / 60:.1f} min".replace(".", ","))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
