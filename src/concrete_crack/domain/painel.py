"""Montagem de painéis lado a lado para inspeção visual, sem acesso a disco."""

import numpy as np

COR_SEPARADOR = (0, 0, 255)


def montar_painel(
    esquerda: np.ndarray,
    direita: np.ndarray,
    largura_separador: int,
    cor_separador: tuple[int, int, int] = COR_SEPARADOR,
) -> np.ndarray:
    """Junta duas imagens RGB lado a lado, com uma faixa de cor entre elas.

    Args:
        esquerda: Imagem RGB uint8 (linhas x colunas x 3).
        direita: Imagem RGB uint8 de mesma forma que a da esquerda.
        largura_separador: Largura da faixa, em pixels; 0 não deixa faixa.
        cor_separador: Cor da faixa, em RGB.

    Returns:
        Imagem RGB uint8 com a esquerda, a faixa e a direita, nessa ordem.

    Raises:
        ValueError: Se alguma imagem não for RGB, se as formas diferirem ou se
            a largura do separador for negativa.
    """
    for imagem in (esquerda, direita):
        if imagem.ndim != 3 or imagem.shape[2] != 3:
            raise ValueError("As imagens precisam ser RGB (linhas x colunas x 3).")
    if esquerda.shape != direita.shape:
        raise ValueError(
            f"Formas diferentes: esquerda {esquerda.shape}, direita {direita.shape}."
        )
    if largura_separador < 0:
        raise ValueError("A largura do separador não pode ser negativa.")
    altura = esquerda.shape[0]
    faixa = np.empty((altura, largura_separador, 3), dtype=np.uint8)
    faixa[:] = cor_separador
    return np.concatenate([esquerda, faixa, direita], axis=1)
