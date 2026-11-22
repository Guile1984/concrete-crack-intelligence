"""Cálculo da constante c do Frangi no treino do CCSD (A65, item 4; A66, item 3).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.constante_frangi ccsd

Sorteia as fotos do treino e, em cada uma, os pixels, com a seed
pré-registrada; lê a foto em resolução cheia com a orientação EXIF aplicada
(A34); calcula S* em cada σ do fundo da grade; e grava
c = fração x percentil de S* em ``experiments/frangi_c_v1.json``. Usa só as
imagens, nunca as máscaras. O c é calculado uma única vez: se o registro já
existe, o comando se recusa a sobrescrevê-lo.
"""

import argparse
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import scipy
import skimage

from ..config.caminhos import caminho_constante_c, caminho_split, pasta_dados_brutos
from ..config.regras import REGRAS
from ..domain.constante_c import constante_c, sortear_fotos, sortear_pixels
from ..domain.orientacao import aplicar_orientacao
from ..domain.registro_c import ConstanteC, RegistroC
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.frangi import cinza_corrigido, estrutura_normalizada
from ..infrastructure.imagens import ler_cabecalho, ler_rgb
from ..infrastructure.registro_c_json import gravar_registro_c
from ..infrastructure.registro_divisao_json import carregar_registro_divisao


def amostrar_estrutura(
    caminhos: Sequence[Path],
    escalas: tuple[float, ...],
    fundos: tuple[float, ...],
    n_pixels: int,
    seed: int,
    progresso: Callable[[int, int], None] | None = None,
) -> dict[float, np.ndarray]:
    """Sorteia os pixels de cada foto e guarda S* neles, em cada σ do fundo.

    Os mesmos pixels de uma foto são usados em todos os fundos.

    Args:
        caminhos: As fotos, na ordem da amostra (a posição é o índice do
            sorteio dos pixels).
        escalas: As oitavas σ de S*.
        fundos: Os σ do fundo da grade.
        n_pixels: Pixels sorteados por foto.
        seed: Semente pré-registrada.
        progresso: Função chamada com (fotos feitas, total) após cada foto.

    Returns:
        Para cada σ do fundo, os valores de S* de todos os pixels sorteados.
    """
    valores: dict[float, list[np.ndarray]] = {fundo: [] for fundo in fundos}
    for indice, caminho in enumerate(caminhos):
        foto = aplicar_orientacao(
            ler_rgb(caminho, 1), ler_cabecalho(caminho).orientacao_exif
        )
        posicoes = sortear_pixels(foto.shape[0] * foto.shape[1], n_pixels, seed, indice)
        for fundo in fundos:
            estrutura = estrutura_normalizada(cinza_corrigido(foto, fundo), escalas)
            valores[fundo].append(estrutura.ravel()[posicoes])
        if progresso is not None:
            progresso(indice + 1, len(caminhos))
    return {fundo: np.concatenate(partes) for fundo, partes in valores.items()}


def calcular_registro_c(
    raiz: Path,
    fonte_id: str,
    progresso: Callable[[int, int], None] | None = None,
) -> RegistroC:
    """Calcula o c de cada σ do fundo a partir da amostra pré-registrada.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte.
        progresso: Função chamada com (fotos feitas, total) após cada foto.

    Returns:
        O registro do c.

    Raises:
        FileNotFoundError: Se faltar a divisão ou alguma foto.
        OSError: Se alguma foto não for uma imagem reconhecida.
        ValueError: Se a divisão for de outra fonte ou o c não for positivo.
    """
    origem_split = caminho_split(raiz)
    registro_divisao = carregar_registro_divisao(origem_split)
    if registro_divisao.fonte_id != fonte_id:
        raise ValueError(f"A divisão é da fonte {registro_divisao.fonte_id!r}.")
    fotos = sortear_fotos(
        registro_divisao.divisao.treino, REGRAS.n_fotos_c_frangi, REGRAS.seed_c_frangi
    )
    pasta = pasta_dados_brutos(raiz, fonte_id)
    valores = amostrar_estrutura(
        [pasta / foto for foto in fotos],
        REGRAS.escalas_frangi,
        REGRAS.sigmas_fundo_frangi,
        REGRAS.n_pixels_c_frangi,
        REGRAS.seed_c_frangi,
        progresso,
    )
    constantes = []
    for fundo in REGRAS.sigmas_fundo_frangi:
        percentil_s = float(np.percentile(valores[fundo], REGRAS.percentil_c_frangi))
        c = constante_c(
            valores[fundo], REGRAS.fracao_c_frangi, REGRAS.percentil_c_frangi
        )
        constantes.append(ConstanteC(fundo, percentil_s, c))
    return RegistroC(
        fonte_id=fonte_id,
        sha256_split=sha256_do_arquivo(origem_split),
        seed=REGRAS.seed_c_frangi,
        n_pixels_por_foto=REGRAS.n_pixels_c_frangi,
        escalas=REGRAS.escalas_frangi,
        percentil=REGRAS.percentil_c_frangi,
        fracao=REGRAS.fracao_c_frangi,
        fotos=fotos,
        constantes=tuple(constantes),
        versoes=(
            ("numpy", np.__version__),
            ("scikit-image", skimage.__version__),
            ("scipy", scipy.__version__),
        ),
    )


def _mostrar_progresso(feitas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada foto."""
    print(f"  {feitas}/{total} fotos", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Calcula e grava o c do Frangi.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro ou se o registro já existir.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.constante_frangi",
        description="Calcula a constante c do Frangi no treino (A66, item 3).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    destino = caminho_constante_c(raiz)
    if destino.exists():
        print(
            f"Erro: {destino} já existe; o c é calculado uma única vez (A66).",
            file=sys.stderr,
        )
        return 2
    inicio = time.perf_counter()
    try:
        registro = calcular_registro_c(raiz, args.fonte_id, _mostrar_progresso)
    except (ValueError, OSError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    gravar_registro_c(registro, destino)
    for constante in registro.constantes:
        print(
            f"σ do fundo {constante.sigma_fundo:g}: percentil {registro.percentil:g} "
            f"de S* = {constante.percentil_s:.6f}; c = {constante.c:.6f}"
        )
    print(
        f"Fotos: {len(registro.fotos)}; pixels por foto: {registro.n_pixels_por_foto}"
    )
    print(f"Tempo: {(time.perf_counter() - inicio) / 60:.1f} min".replace(".", ","))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
