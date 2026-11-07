"""Registro de procedência dos pesos pré-treinados de uma rede.

Os pesos são baixados uma única vez; o registro guarda de onde vieram, em que
revisão, e o hash do arquivo recebido (confiança no primeiro uso). A cada uso,
o hash do arquivo em disco é comparado com o registrado.
"""

import re
from dataclasses import dataclass
from datetime import date

PADRAO_REPOSITORIO = re.compile(r"[A-Za-z0-9][\w.-]*/[A-Za-z0-9][\w.-]*")
PADRAO_REVISAO = re.compile(r"[0-9a-f]{40}")
PADRAO_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class RegistroPesos:
    """De onde vieram os pesos de uma rede e como conferi-los.

    Attributes:
        repositorio: Repositório de origem, no formato ``dono/nome``.
        revisao: Commit exato do repositório (40 caracteres hexadecimais).
        arquivo: Nome do arquivo de pesos, sem pastas.
        tamanho_bytes: Tamanho do arquivo recebido, positivo.
        sha256: Hash SHA-256 do arquivo recebido (64 hexadecimais minúsculos).
        data_download: Data do download, no formato AAAA-MM-DD.
    """

    repositorio: str
    revisao: str
    arquivo: str
    tamanho_bytes: int
    sha256: str
    data_download: str

    def __post_init__(self) -> None:
        """Recusa campos mal formados."""
        if not PADRAO_REPOSITORIO.fullmatch(self.repositorio):
            raise ValueError(f"Repositório inválido: {self.repositorio!r}.")
        if not PADRAO_REVISAO.fullmatch(self.revisao):
            raise ValueError("A revisão deve ter 40 caracteres hexadecimais.")
        if not self.arquivo or "/" in self.arquivo or "\\" in self.arquivo:
            raise ValueError("O arquivo deve ser um nome simples, sem pastas.")
        if self.tamanho_bytes <= 0:
            raise ValueError("O tamanho do arquivo deve ser positivo.")
        if not PADRAO_SHA256.fullmatch(self.sha256):
            raise ValueError("O SHA-256 deve ter 64 hexadecimais minúsculos.")
        try:
            date.fromisoformat(self.data_download)
        except ValueError as erro:
            raise ValueError("A data do download deve estar em AAAA-MM-DD.") from erro
