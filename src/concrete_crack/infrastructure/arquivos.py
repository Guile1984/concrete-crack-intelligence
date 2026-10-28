"""Leitura de arquivos em disco para o registro de integridade."""

import hashlib
from pathlib import Path

from ..domain.integridade import ArquivoRegistrado

TAMANHO_BLOCO = 1024 * 1024


def sha256_do_arquivo(caminho: Path) -> str:
    """Calcula o SHA-256 de um arquivo, lendo-o em blocos de 1 MiB.

    Args:
        caminho: Arquivo a ser lido.

    Returns:
        O hash em 64 caracteres hexadecimais minúsculos.
    """
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        while bloco := arquivo.read(TAMANHO_BLOCO):
            resumo.update(bloco)
    return resumo.hexdigest()


def registrar_pasta(raiz: Path) -> tuple[ArquivoRegistrado, ...]:
    """Registra todos os arquivos de uma pasta, incluindo as subpastas.

    Os caminhos são relativos a ``raiz`` e usam ``/``. A ordem é a do texto do
    caminho, igual em qualquer sistema operacional.

    Args:
        raiz: Pasta da fonte de dados.

    Returns:
        Os arquivos registrados, ordenados pelo caminho.

    Raises:
        NotADirectoryError: Se ``raiz`` não existir ou não for uma pasta.
    """
    if not raiz.is_dir():
        raise NotADirectoryError(f"Não é uma pasta: {raiz}")
    registros: list[ArquivoRegistrado] = []
    for caminho in raiz.rglob("*"):
        if caminho.is_file():
            registros.append(
                ArquivoRegistrado(
                    caminho=caminho.relative_to(raiz).as_posix(),
                    tamanho_bytes=caminho.stat().st_size,
                    sha256=sha256_do_arquivo(caminho),
                )
            )
    return tuple(sorted(registros, key=lambda registro: registro.caminho))
