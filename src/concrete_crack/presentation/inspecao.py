"""Inspeção das máscaras: sorteio da amostra e preparação das imagens.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.inspecao sortear ccsd
    python -m concrete_crack.presentation.inspecao preparar ccsd

O ``sortear`` lê só o manifesto (nomes e hashes): não abre nenhuma imagem. O
``preparar`` grava, para cada máscara sorteada, um PNG com dois painéis: a foto
limpa à esquerda e a foto com a máscara em vermelho à direita, separados por uma
faixa azul.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from ..config.caminhos import (
    caminho_amostra_inspecao,
    caminho_manifesto_arquivos,
    pasta_dados_brutos,
    pasta_imagens_inspecao,
)
from ..config.regras import REGRAS
from ..domain.amostragem import amostrar_por_hash
from ..domain.orientacao import aplicar_orientacao
from ..domain.painel import montar_painel
from ..domain.sobreposicao import intensidade_da_mascara, sobrepor_mascara
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import gravar_png, ler_cabecalho, ler_cinza, ler_rgb
from ..infrastructure.manifesto_arquivos import carregar_manifesto
from .estrutura import parear_fonte

PREFIXO_MASCARAS = "BW/"
FATOR_VISUALIZACAO = 5
OPACIDADE_MASCARA = 0.5
LARGURA_SEPARADOR = 8


def sortear_amostra(raiz: Path, fonte_id: str) -> dict[str, object]:
    """Sorteia as máscaras a inspecionar e grava o registro do sorteio.

    O sorteio é pré-registrado: o arquivo é criado uma única vez e nunca
    refeito, pois refazê-lo depois de ver máscaras anularia o pré-registro.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado.

    Returns:
        O registro gravado em ``manifests/inspecao_<fonte_id>.json``.

    Raises:
        FileExistsError: Se a amostra da fonte já existir.
        FileNotFoundError: Se o manifesto de arquivos não existir.
        ValueError: Se o manifesto for de outra fonte ou tiver menos máscaras
            do que o tamanho da amostra.
    """
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    destino = caminho_amostra_inspecao(raiz, fonte_id)
    if destino.exists():
        raise FileExistsError(
            f"A amostra de {fonte_id} já existe: {destino}. O sorteio é "
            "pré-registrado e não se refaz."
        )
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
    amostra = amostrar_por_hash(
        mascaras, REGRAS.n_inspecao_mascaras, REGRAS.seed_inspecao_mascaras
    )
    registro: dict[str, object] = {
        "fonte_id": fonte_id,
        "seed": REGRAS.seed_inspecao_mascaras,
        "n": REGRAS.n_inspecao_mascaras,
        "limiar_reprovacao": REGRAS.limiar_reprovacao_mascaras,
        "total_mascaras": len(mascaras),
        "sha256_manifesto_de_arquivos": sha256_do_arquivo(origem),
        "amostra": list(amostra),
    }
    texto = json.dumps(registro, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")
    return registro


def preparar_imagens(raiz: Path, fonte_id: str) -> list[Path]:
    """Grava uma imagem de dois painéis para cada máscara da amostra.

    Esquerda: a foto com a orientação EXIF aplicada (política A34). Direita: a
    mesma foto com a máscara em vermelho, proporcional à intensidade da máscara.
    Os arquivos se chamam ``<posição>_<número da máscara>.png``, na ordem da
    amostra, e são recriados a cada execução.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado
            e amostra sorteada.

    Returns:
        Os caminhos das imagens gravadas, na ordem da amostra.

    Raises:
        FileNotFoundError: Se a amostra, o manifesto ou alguma imagem não
            existir.
        OSError: Se algum arquivo não for uma imagem reconhecida.
        ValueError: Se o manifesto mudou desde o sorteio, se uma máscara da
            amostra não tiver foto ou se as formas de foto e máscara diferirem.
    """
    registro = json.loads(
        caminho_amostra_inspecao(raiz, fonte_id).read_text(encoding="utf-8")
    )
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    if sha256_do_arquivo(origem) != registro["sha256_manifesto_de_arquivos"]:
        raise ValueError("O manifesto de arquivos mudou desde o sorteio da amostra.")
    foto_de = dict(parear_fonte(raiz, fonte_id).pares)
    pasta = pasta_dados_brutos(raiz, fonte_id)
    saida = pasta_imagens_inspecao(raiz, fonte_id)
    gravadas: list[Path] = []
    for posicao, mascara in enumerate(registro["amostra"], start=1):
        if mascara not in foto_de:
            raise ValueError(f"A máscara {mascara} da amostra não tem foto.")
        foto = pasta / foto_de[mascara]
        orientacao = ler_cabecalho(foto).orientacao_exif
        limpa = aplicar_orientacao(ler_rgb(foto, FATOR_VISUALIZACAO), orientacao)
        intensidade = intensidade_da_mascara(
            ler_cinza(pasta / mascara, FATOR_VISUALIZACAO)
        )
        if intensidade.shape != limpa.shape[:2]:
            raise ValueError(
                f"{mascara}: a máscara {intensidade.shape} e a foto "
                f"{limpa.shape[:2]} têm formas diferentes."
            )
        com_mascara = sobrepor_mascara(limpa, intensidade, OPACIDADE_MASCARA)
        painel = montar_painel(limpa, com_mascara, LARGURA_SEPARADOR)
        destino = saida / f"{posicao:02d}_{Path(mascara).stem}.png"
        gravar_png(destino, painel)
        gravadas.append(destino)
    return gravadas


def main(argv: Sequence[str] | None = None) -> int:
    """Executa os comandos de inspeção.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.inspecao",
        description="Sorteia e prepara as máscaras a inspecionar.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    sortear = comandos.add_parser("sortear", help="sorteia e grava a amostra")
    sortear.add_argument("fonte_id")
    preparar = comandos.add_parser("preparar", help="grava as imagens da amostra")
    preparar.add_argument("fonte_id")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        if args.comando == "sortear":
            registro = sortear_amostra(raiz, args.fonte_id)
        else:
            gravadas = preparar_imagens(raiz, args.fonte_id)
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    if args.comando == "sortear":
        destino = caminho_amostra_inspecao(raiz, args.fonte_id)
        print(
            f"Sorteadas {registro['n']} de {registro['total_mascaras']} máscaras "
            f"em {destino}"
        )
        return 0
    print(
        f"Gravadas {len(gravadas)} imagens em "
        f"{pasta_imagens_inspecao(raiz, args.fonte_id)}"
    )
    print("Em cada uma: foto à esquerda, foto com a máscara à direita, faixa azul.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
