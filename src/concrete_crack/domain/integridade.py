"""Registro de arquivos de dados e comparação de integridade, sem acesso a disco."""

import re
from dataclasses import dataclass
from datetime import date

PADRAO_SHA256 = re.compile(r"[0-9a-f]{64}")


def _caminho_valido(caminho: str) -> bool:
    """Diz se o caminho é relativo, sem desvios e com separador ``/``."""
    if not caminho or caminho.startswith("/") or "\\" in caminho or ":" in caminho:
        return False
    segmentos = caminho.split("/")
    return not any(segmento in ("", ".", "..") for segmento in segmentos)


@dataclass(frozen=True, slots=True)
class ArquivoRegistrado:
    """Um arquivo de dados identificado por caminho, tamanho e hash.

    Attributes:
        caminho: Caminho relativo à pasta da fonte, com separador ``/``.
        tamanho_bytes: Tamanho do arquivo em bytes.
        sha256: Hash SHA-256, com 64 caracteres hexadecimais minúsculos.
    """

    caminho: str
    tamanho_bytes: int
    sha256: str

    def __post_init__(self) -> None:
        """Recusa caminhos inseguros, tamanhos negativos e hashes mal formados."""
        if not _caminho_valido(self.caminho):
            raise ValueError(
                f"Caminho inválido: {self.caminho!r}. Use um caminho relativo, "
                "com '/', sem '.', '..' nem ':'."
            )
        if self.tamanho_bytes < 0:
            raise ValueError("tamanho_bytes não pode ser negativo.")
        if not PADRAO_SHA256.fullmatch(self.sha256):
            raise ValueError("sha256 deve ter 64 caracteres hexadecimais minúsculos.")


@dataclass(frozen=True, slots=True)
class ManifestoArquivos:
    """Os arquivos de uma fonte, registrados no momento do download.

    Attributes:
        fonte_id: Identificador da fonte (por exemplo ccsd).
        data_download: Data (AAAA-MM-DD) em que os arquivos foram baixados.
        arquivos: Os arquivos registrados.
    """

    fonte_id: str
    data_download: str
    arquivos: tuple[ArquivoRegistrado, ...]

    def __post_init__(self) -> None:
        """Recusa manifestos sem fonte, sem arquivos, com data inválida ou repetidos."""
        if not self.fonte_id.strip():
            raise ValueError("fonte_id não pode ser vazio.")
        try:
            date.fromisoformat(self.data_download)
        except ValueError as erro:
            raise ValueError(
                "data_download deve estar no formato AAAA-MM-DD."
            ) from erro
        if not self.arquivos:
            raise ValueError("O manifesto precisa de ao menos um arquivo.")
        caminhos = [arquivo.caminho for arquivo in self.arquivos]
        if len(caminhos) != len(set(caminhos)):
            raise ValueError("O manifesto tem caminhos repetidos.")


@dataclass(frozen=True, slots=True)
class Divergencias:
    """Diferenças entre o manifesto e o que foi observado.

    Attributes:
        ausentes: Caminhos que estão no manifesto e não foram encontrados.
        inesperados: Caminhos encontrados que não estão no manifesto.
        alterados: Caminhos presentes nos dois, com tamanho ou hash diferente.
    """

    ausentes: tuple[str, ...]
    inesperados: tuple[str, ...]
    alterados: tuple[str, ...]

    @property
    def vazio(self) -> bool:
        """Verdadeiro quando não há nenhuma divergência."""
        return not (self.ausentes or self.inesperados or self.alterados)


def comparar(
    esperado: ManifestoArquivos, observado: tuple[ArquivoRegistrado, ...]
) -> Divergencias:
    """Compara o manifesto com os arquivos observados.

    Args:
        esperado: O manifesto registrado no download.
        observado: Os arquivos encontrados agora, já com tamanho e hash.

    Returns:
        As divergências, cada grupo em ordem alfabética de caminho.

    Raises:
        ValueError: Se houver caminhos repetidos entre os arquivos observados.
    """
    do_manifesto = {arquivo.caminho: arquivo for arquivo in esperado.arquivos}
    do_disco = {arquivo.caminho: arquivo for arquivo in observado}
    if len(do_disco) != len(observado):
        raise ValueError("Há caminhos repetidos entre os arquivos observados.")
    ausentes = tuple(sorted(do_manifesto.keys() - do_disco.keys()))
    inesperados = tuple(sorted(do_disco.keys() - do_manifesto.keys()))
    alterados = tuple(
        sorted(
            caminho
            for caminho in do_manifesto.keys() & do_disco.keys()
            if do_manifesto[caminho] != do_disco[caminho]
        )
    )
    return Divergencias(ausentes, inesperados, alterados)
