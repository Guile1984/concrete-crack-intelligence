"""Variações fabricadas de uma imagem para o controle positivo de duplicatas.

Funções puras sobre matrizes numpy, sem acesso a disco. A recompressão JPEG,
que precisa do Pillow, fica na infraestrutura (``recompressao.py``).
"""

import numpy as np

LADOS = ("esquerda", "direita", "cima", "baixo")


def ajustar_brilho(cinza: np.ndarray, fator: float) -> np.ndarray:
    """Multiplica o brilho de uma imagem, arredondando e saturando em 0 e 255.

    O arredondamento é o do numpy (``np.rint``): a metade vai para o par, de
    modo que 8,5 vira 8 e 85,5 vira 86. Vale para cinza e para cor: cada canal
    é multiplicado pelo mesmo fator.

    Args:
        cinza: Imagem uint8, em tons de cinza ou colorida.
        fator: Fator de brilho, positivo.

    Returns:
        A imagem uint8 com o brilho multiplicado.

    Raises:
        ValueError: Se a imagem não for uint8 ou o fator não for positivo.
    """
    if cinza.dtype != np.uint8:
        raise ValueError("A imagem deve ser uint8.")
    if fator <= 0:
        raise ValueError("O fator de brilho deve ser positivo.")
    escalada = np.rint(cinza.astype(np.float64) * fator)
    return np.clip(escalada, 0, 255).astype(np.uint8)


def recortar(cinza: np.ndarray, fracao: float, lado: str) -> np.ndarray:
    """Remove uma faixa de um lado da imagem, simulando um deslocamento.

    A largura da faixa é ``round(fracao x dimensão)``: colunas para esquerda e
    direita, linhas para cima e baixo. O ``round`` do Python leva a metade para
    o par (2,5 vira 2), como o ``np.rint``. Numa imagem colorida, só os dois
    primeiros eixos (linhas e colunas) são cortados; os canais ficam inteiros.

    Args:
        cinza: Imagem 2D (cinza) ou 3D (linhas x colunas x canais).
        fracao: Fração a remover, em (0, 0,5).
        lado: Um de ``LADOS``.

    Returns:
        A imagem sem a faixa (uma cópia).

    Raises:
        ValueError: Se a imagem não for 2D nem 3D, a fração estiver fora de
            (0, 0,5), o lado for desconhecido ou a faixa arredondar para zero.
    """
    if cinza.ndim not in (2, 3):
        raise ValueError("A imagem deve ser 2D ou 3D (com canais).")
    if not 0 < fracao < 0.5:
        raise ValueError("A fração do recorte deve estar em (0, 0,5).")
    if lado not in LADOS:
        raise ValueError(f"Lado desconhecido: {lado!r}.")
    altura, largura = cinza.shape[:2]
    dimensao = largura if lado in ("esquerda", "direita") else altura
    faixa = round(fracao * dimensao)
    if faixa == 0:
        raise ValueError("A imagem é pequena demais para esse recorte.")
    cortes = {
        "esquerda": cinza[:, faixa:],
        "direita": cinza[:, : largura - faixa],
        "cima": cinza[faixa:, :],
        "baixo": cinza[: altura - faixa, :],
    }
    return cortes[lado].copy()
