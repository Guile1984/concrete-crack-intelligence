"""Registro de procedência de pesos pré-treinados baixados de uma URL fixa.

É o caso dos pesos do torchvision, publicados numa URL cujo nome de arquivo
traz os primeiros dígitos do SHA-256 do conteúdo (``resnet18-f37072fd.pth``).
O registro guarda o SHA-256 completo do arquivo recebido (confiança no
primeiro uso) e recusa um hash que não comece pelo prefixo publicado no nome:
são duas fontes independentes, a do editor e a nossa (A69).
"""

import re
from dataclasses import dataclass
from datetime import date

PADRAO_ARQUIVO = re.compile(r"[A-Za-z0-9][\w.-]*?-([0-9a-f]{8,64})\.\w+")
PADRAO_SHA256 = re.compile(r"[0-9a-f]{64}")


def prefixo_sha256(arquivo: str) -> str:
    """Extrai do nome do arquivo o prefixo do SHA-256 publicado pelo editor.

    Args:
        arquivo: Nome no formato ``nome-<prefixo hexadecimal>.extensao``.

    Returns:
        O prefixo, com 8 a 64 hexadecimais minúsculos.

    Raises:
        ValueError: Se o nome não trouxer o prefixo.
    """
    encontrado = PADRAO_ARQUIVO.fullmatch(arquivo)
    if encontrado is None:
        raise ValueError(
            f"O nome {arquivo!r} não traz o prefixo do SHA-256 "
            "(nome-<hexadecimal>.extensao)."
        )
    return encontrado.group(1)


@dataclass(frozen=True, slots=True)
class RegistroPesosUrl:
    """De onde vieram os pesos de uma rede e como conferi-los.

    Attributes:
        url: Endereço HTTPS de onde o arquivo foi baixado.
        arquivo: Nome do arquivo, igual ao último trecho da URL.
        tamanho_bytes: Tamanho do arquivo recebido, positivo.
        sha256: Hash SHA-256 do arquivo recebido (64 hexadecimais minúsculos),
            que começa pelo prefixo publicado no nome.
        data_download: Data do download, no formato AAAA-MM-DD.
    """

    url: str
    arquivo: str
    tamanho_bytes: int
    sha256: str
    data_download: str

    def __post_init__(self) -> None:
        """Recusa campos mal formados ou incoerentes entre si."""
        if not self.url.startswith("https://"):
            raise ValueError("A URL dos pesos deve usar https.")
        if not self.arquivo or "/" in self.arquivo or "\\" in self.arquivo:
            raise ValueError("O arquivo deve ser um nome simples, sem pastas.")
        if not self.url.endswith("/" + self.arquivo):
            raise ValueError("A URL deve terminar no nome do arquivo.")
        prefixo = prefixo_sha256(self.arquivo)
        if self.tamanho_bytes <= 0:
            raise ValueError("O tamanho do arquivo deve ser positivo.")
        if not PADRAO_SHA256.fullmatch(self.sha256):
            raise ValueError("O SHA-256 deve ter 64 hexadecimais minúsculos.")
        if not self.sha256.startswith(prefixo):
            raise ValueError(
                f"O SHA-256 recebido não começa pelo prefixo publicado ({prefixo})."
            )
        try:
            date.fromisoformat(self.data_download)
        except ValueError as erro:
            raise ValueError("A data do download deve estar em AAAA-MM-DD.") from erro
