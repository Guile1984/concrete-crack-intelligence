"""Geração dos tiles do CCSD, registrada ou conferida por hash (A52, A54).

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.tiles ccsd

Para cada foto do índice de tiles: lê a foto em resolução cheia e aplica a
orientação EXIF (A34); lê a máscara e a binariza pela regra da A41; prepara as
duas escalas; calcula os hashes das imagens inteiras; recorta pela grade do
índice e grava os tiles em PNG em ``data/interim/tiles_<fonte>/``.

Se ``manifests/pixels_tiles_v1.json`` não existe, o comando o grava ao fim
(modo registrar). Se existe, cada foto é conferida contra ele antes de gravar
os seus tiles, e qualquer diferença interrompe a geração (modo conferir).
"""

import argparse
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..config.caminhos import (
    caminho_indice_tiles,
    caminho_manifesto_arquivos,
    caminho_manifesto_pixels,
    caminho_split,
    pasta_dados_brutos,
    pasta_tiles,
)
from ..config.regras import REGRAS
from ..domain.alinhamento import marcar_fissura
from ..domain.manifesto_pixels import (
    HashesEscala,
    HashesFoto,
    ManifestoPixels,
    diferencas,
    montar_manifesto,
)
from ..domain.orientacao import aplicar_orientacao
from ..domain.pixels import hash_pixels, recortar
from ..domain.preparacao import preparar_escalas
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import (
    gravar_png,
    ler_cabecalho,
    ler_cinza,
    ler_rgb,
    versao_pillow,
)
from ..infrastructure.indice_tiles_json import carregar_indice_tiles
from ..infrastructure.manifesto_pixels_json import (
    carregar_manifesto_pixels,
    gravar_manifesto_pixels,
)
from .estrutura import parear_fonte

INTERVALO_PROGRESSO = 25


@dataclass(frozen=True, slots=True)
class ResultadoTiles:
    """O resumo de uma geração de tiles.

    Attributes:
        modo: ``"registrado"`` ou ``"conferido"``.
        n_fotos: Fotos processadas.
        n_tiles: Tiles gravados, somando as escalas (cada um com foto e
            máscara).
        bytes_gravados: Tamanho total dos PNG gravados.
    """

    modo: str
    n_fotos: int
    n_tiles: int
    bytes_gravados: int


def _conferir_procedencia(raiz: Path, fonte_id: str) -> None:
    """Recusa um índice que não venha da divisão e do manifesto atuais."""
    indice = carregar_indice_tiles(caminho_indice_tiles(raiz))
    if indice.fonte_id != fonte_id:
        raise ValueError(f"O índice de tiles é da fonte {indice.fonte_id!r}.")
    if indice.sha256_split != sha256_do_arquivo(caminho_split(raiz)):
        raise ValueError("A divisão mudou desde a gravação do índice de tiles.")
    manifesto = caminho_manifesto_arquivos(raiz, fonte_id)
    if indice.sha256_manifesto != sha256_do_arquivo(manifesto):
        raise ValueError("O manifesto de arquivos mudou desde o índice de tiles.")


def gerar_tiles(
    raiz: Path,
    fonte_id: str,
    progresso: Callable[[int, int], None] | None = None,
) -> ResultadoTiles:
    """Gera os tiles de todas as fotos do índice, registrando ou conferindo.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte.
        progresso: Função chamada com (fotos feitas, total) após cada foto.

    Returns:
        O resumo da geração.

    Raises:
        FileNotFoundError: Se faltar o índice, a divisão, o manifesto ou
            alguma imagem.
        OSError: Se algum arquivo não for uma imagem reconhecida.
        ValueError: Se a procedência não bater, se a versão do Pillow for
            outra, se uma foto preparada não tiver o tamanho do índice ou se,
            no modo conferir, algum hash for diferente.
    """
    _conferir_procedencia(raiz, fonte_id)
    origem_indice = caminho_indice_tiles(raiz)
    indice = carregar_indice_tiles(origem_indice)
    sha_indice = sha256_do_arquivo(origem_indice)
    destino_manifesto = caminho_manifesto_pixels(raiz)
    registrado: ManifestoPixels | None = None
    if destino_manifesto.exists():
        registrado = carregar_manifesto_pixels(destino_manifesto)
        if registrado.sha256_indice != sha_indice:
            raise ValueError("O manifesto de pixels é de outro índice de tiles.")
        if registrado.versao_pillow != versao_pillow():
            raise ValueError(
                f"O manifesto de pixels foi gerado com o Pillow "
                f"{registrado.versao_pillow}; este ambiente tem o "
                f"{versao_pillow()} (A54, escolha C)."
            )
    pareamento = parear_fonte(raiz, fonte_id)
    mascara_de = {foto: mascara for mascara, foto in pareamento.pares}
    pasta = pasta_dados_brutos(raiz, fonte_id)
    saida = pasta_tiles(raiz, fonte_id)
    fatores = [fator for fator, _ in indice.escalas]
    lados = dict(indice.escalas)
    hashes: list[HashesFoto] = []
    n_tiles = 0
    bytes_gravados = 0
    for numero, item in enumerate(indice.fotos, start=1):
        cabecalho = ler_cabecalho(pasta / item.foto)
        foto = aplicar_orientacao(
            ler_rgb(pasta / item.foto, 1), cabecalho.orientacao_exif
        )
        mascara = marcar_fissura(
            ler_cinza(pasta / mascara_de[item.foto], 1), REGRAS.limiar_binarizacao
        )
        if foto.shape[:2] != (item.altura, item.largura):
            raise ValueError(
                f"{item.foto}: a foto preparada tem {foto.shape[:2]}, e o índice "
                f"registra {(item.altura, item.largura)}."
            )
        escalas = preparar_escalas(foto, mascara, fatores)
        obtido = HashesFoto(
            item.foto,
            tuple(
                HashesEscala(e.fator, hash_pixels(e.foto), hash_pixels(e.mascara))
                for e in escalas
            ),
        )
        if registrado is not None:
            problemas = diferencas(registrado.da_foto(item.foto), obtido)
            if problemas:
                raise ValueError(f"{item.foto}: {'; '.join(problemas)} diferente(s).")
        hashes.append(obtido)
        nome = PurePosixPath(item.foto).stem
        for escala, grade in zip(escalas, item.grades, strict=True):
            lado = lados[escala.fator]
            pasta_foto = saida / f"escala_{escala.fator}" / nome
            for y in grade.ys:
                for x in grade.xs:
                    for sufixo, imagem in (
                        ("foto", escala.foto),
                        ("mascara", escala.mascara),
                    ):
                        arquivo = pasta_foto / f"{x}_{y}_{sufixo}.png"
                        gravar_png(arquivo, recortar(imagem, x, y, lado))
                        bytes_gravados += arquivo.stat().st_size
                    n_tiles += 1
        if progresso is not None:
            progresso(numero, len(indice.fotos))
    if registrado is None:
        manifesto = montar_manifesto(fonte_id, sha_indice, versao_pillow(), hashes)
        gravar_manifesto_pixels(manifesto, destino_manifesto)
        modo = "registrado"
    else:
        modo = "conferido"
    return ResultadoTiles(modo, len(indice.fotos), n_tiles, bytes_gravados)


def _mostrar_progresso(feitas: int, total: int) -> None:
    """Escreve o andamento em stderr a cada bloco de fotos e ao final."""
    if feitas % INTERVALO_PROGRESSO == 0 or feitas == total:
        print(f"  {feitas}/{total} fotos", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a geração dos tiles.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.tiles",
        description="Gera os tiles, registrando ou conferindo os hashes (A54).",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    parser.add_argument("fonte_id")
    args = parser.parse_args(argv)
    inicio = time.perf_counter()
    try:
        resultado = gerar_tiles(args.raiz.resolve(), args.fonte_id, _mostrar_progresso)
    except (ValueError, OSError, KeyError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    segundos = time.perf_counter() - inicio
    print(f"Hashes dos pixels {resultado.modo} (Pillow {versao_pillow()})")
    print(f"Fotos: {resultado.n_fotos}; tiles: {resultado.n_tiles}")
    print(f"Tamanho dos PNG: {resultado.bytes_gravados / 1e9:.2f} GB".replace(".", ","))
    print(f"Tempo: {segundos / 60:.1f} min".replace(".", ","))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
