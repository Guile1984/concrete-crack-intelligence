"""O port Segmentador, conforme a A65 (item 1).

Um contrato único para o Frangi e para a rede: recebe a imagem inteira e
devolve um mapa de score em [0, 1]. O limiar e a limpeza de componentes são
aplicados fora, pelas mesmas funções do domínio, para os dois métodos.
"""

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Segmentador(Protocol):
    """Qualquer método que transforma uma imagem num mapa de fissura."""

    def mapear(self, imagem: np.ndarray) -> np.ndarray:
        """Calcula o mapa de score de uma imagem.

        Args:
            imagem: Imagem RGB ``uint8`` inteira, de formato (altura, largura,
                3), na resolução de trabalho.

        Returns:
            Mapa ``float`` de formato (altura, largura), com valores em [0, 1];
            quanto maior, mais parecido com fissura. Para o Frangi é uma
            resposta normalizada, não uma probabilidade.
        """
        ...
