"""Detecção de quase-duplicatas e agrupamento por distância.

Funções puras sobre matrizes numpy, sem acesso a disco. Os parâmetros (lado do
hash, cobertura, frações máximas) vêm de fora (``config/regras.py``).

Duas medidas de distância convivem aqui. O dHash compara cada célula de uma
versão muito reduzida da imagem com a vizinha: na direção horizontal (imagem
reduzida a lado x (lado + 1)) e na vertical ((lado + 1) x lado); cada
comparação vira um bit, e a distância é a quantidade de bits diferentes
(Hamming, inteira). Os embeddings de uma rede são comparados pela distância de
cosseno, 1 menos o cosseno do ângulo entre os vetores (contínua, de 0 a 2). O
limiar, o agrupamento e o critério de escalada valem para as duas.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

TOLERANCIA_COBERTURA = 1e-9


def reduzir_por_blocos(cinza: np.ndarray, linhas: int, colunas: int) -> np.ndarray:
    """Reduz uma imagem a linhas x colunas pela média de blocos retangulares.

    As bordas dos blocos são ``(i * altura) // linhas`` (e o mesmo nas
    colunas), de modo que todo pixel entra em exatamente um bloco.

    Args:
        cinza: Imagem 2D (linhas x colunas de pixels), de qualquer tipo numérico.
        linhas: Quantidade de linhas da imagem reduzida, de 1 até a altura.
        colunas: Quantidade de colunas da imagem reduzida, de 1 até a largura.

    Returns:
        Matriz float64 de forma (linhas, colunas) com a média de cada bloco.

    Raises:
        ValueError: Se a imagem não for 2D ou for menor que a redução pedida.
    """
    if cinza.ndim != 2:
        raise ValueError("A imagem deve ser 2D.")
    altura, largura = cinza.shape
    if not (1 <= linhas <= altura and 1 <= colunas <= largura):
        raise ValueError(
            f"Não é possível reduzir {altura}x{largura} para {linhas}x{colunas}."
        )
    bordas_l = (np.arange(linhas) * altura) // linhas
    bordas_c = (np.arange(colunas) * largura) // colunas
    valores = cinza.astype(np.float64)
    somas = np.add.reduceat(np.add.reduceat(valores, bordas_l, axis=0), bordas_c, 1)
    alturas = np.diff(np.append(bordas_l, altura))
    larguras = np.diff(np.append(bordas_c, largura))
    return somas / np.outer(alturas, larguras)


def dhash_duplo(cinza: np.ndarray, lado: int) -> np.ndarray:
    """Calcula o dHash horizontal e vertical de uma imagem em tons de cinza.

    Args:
        cinza: Imagem 2D, com a orientação já aplicada.
        lado: Lado do hash, pelo menos 2.

    Returns:
        Vetor booleano de 2 x lado x lado bits: primeiro os horizontais (célula
        mais clara que a da direita), depois os verticais (mais clara que a de
        baixo).

    Raises:
        ValueError: Se o lado for menor que 2 ou a imagem não puder ser reduzida.
    """
    if lado < 2:
        raise ValueError("O lado do hash deve ser pelo menos 2.")
    horizontal = reduzir_por_blocos(cinza, lado, lado + 1)
    vertical = reduzir_por_blocos(cinza, lado + 1, lado)
    bits_h = horizontal[:, :-1] > horizontal[:, 1:]
    bits_v = vertical[:-1, :] > vertical[1:, :]
    return np.concatenate([bits_h.ravel(), bits_v.ravel()])


def distancia_hamming(a: np.ndarray, b: np.ndarray) -> int:
    """Conta os bits diferentes entre dois hashes.

    Args:
        a: Hash booleano.
        b: Hash booleano da mesma forma.

    Returns:
        A quantidade de posições em que os hashes diferem.

    Raises:
        ValueError: Se os hashes tiverem formas diferentes.
    """
    if a.shape != b.shape:
        raise ValueError("Os hashes devem ter a mesma forma.")
    return int(np.count_nonzero(a != b))


def limiar_por_cobertura(distancias: Sequence[float], cobertura: float) -> float:
    """Encontra o menor limiar que reconhece a fração pedida das distâncias.

    O limiar T é a menor distância observada tal que pelo menos ``cobertura``
    das distâncias satisfazem d <= T. Com distâncias inteiras (Hamming), T é
    inteiro; com distâncias contínuas (cosseno), T é uma das distâncias. Uma
    tolerância de 1e-9 evita que um produto como 0,07 x 100 = 7,000000000000001
    exija uma distância a mais.

    Args:
        distancias: Distâncias do controle positivo (>= 0), não vazias.
        cobertura: Fração em (0, 1].

    Returns:
        O limiar T.

    Raises:
        ValueError: Se não houver distâncias, alguma for negativa ou a
            cobertura estiver fora de (0, 1].
    """
    if not distancias:
        raise ValueError("Não há distâncias para calcular o limiar.")
    if min(distancias) < 0:
        raise ValueError("As distâncias não podem ser negativas.")
    if not 0 < cobertura <= 1:
        raise ValueError("A cobertura deve estar em (0, 1].")
    ordenadas = sorted(distancias)
    necessarias = math.ceil(cobertura * len(ordenadas) - TOLERANCIA_COBERTURA)
    return ordenadas[max(necessarias, 1) - 1]


def matriz_de_distancias(hashes: Sequence[np.ndarray]) -> np.ndarray:
    """Calcula a distância de Hamming entre todos os pares de hashes.

    Args:
        hashes: Hashes booleanos da mesma forma, pelo menos 2.

    Returns:
        Matriz int64 simétrica n x n, com zeros na diagonal.

    Raises:
        ValueError: Se houver menos de 2 hashes ou formas diferentes.
    """
    if len(hashes) < 2:
        raise ValueError("São necessários pelo menos 2 hashes.")
    if len({h.shape for h in hashes}) != 1:
        raise ValueError("Os hashes devem ter a mesma forma.")
    bits = np.stack(hashes)
    return (bits[:, None, :] != bits[None, :, :]).sum(axis=2).astype(np.int64)


@dataclass(frozen=True, slots=True)
class Agrupamento:
    """Os grupos de quase-duplicatas e as ligações que os formam.

    Attributes:
        grupos: Índices das imagens de cada grupo, em ordem crescente; os
            grupos vêm na ordem do seu menor índice. Imagens sem ligação
            formam grupos de 1.
        pares_ligados: Quantidade de pares com distância <= limiar.
        total_pares: Quantidade total de pares, n x (n - 1) / 2.
    """

    grupos: tuple[tuple[int, ...], ...]
    pares_ligados: int
    total_pares: int

    @property
    def n_imagens(self) -> int:
        """Quantidade de imagens agrupadas."""
        return sum(len(grupo) for grupo in self.grupos)

    @property
    def maior_grupo(self) -> int:
        """Tamanho do maior grupo."""
        return max(len(grupo) for grupo in self.grupos)

    @property
    def fracao_pares_ligados(self) -> float:
        """Fração dos pares com distância <= limiar."""
        return self.pares_ligados / self.total_pares


def agrupar(distancias: np.ndarray, limiar: float) -> Agrupamento:
    """Agrupa as imagens ligadas, direta ou indiretamente, por distância <= limiar.

    Se A está ligada a B e B a C, as três ficam no mesmo grupo, mesmo que A e C
    estejam distantes (componentes conexos).

    Args:
        distancias: Matriz n x n simétrica de distâncias, com n >= 2.
        limiar: Distância máxima para ligar duas imagens, >= 0.

    Returns:
        O agrupamento.

    Raises:
        ValueError: Se a matriz não for quadrada com n >= 2, não for simétrica
            ou o limiar for negativo.
    """
    if distancias.ndim != 2 or distancias.shape[0] != distancias.shape[1]:
        raise ValueError("A matriz de distâncias deve ser quadrada.")
    n = distancias.shape[0]
    if n < 2:
        raise ValueError("São necessárias pelo menos 2 imagens.")
    if not np.array_equal(distancias, distancias.T):
        raise ValueError("A matriz de distâncias deve ser simétrica.")
    if limiar < 0:
        raise ValueError("O limiar não pode ser negativo.")
    pai = list(range(n))

    def raiz(i: int) -> int:
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    linhas, colunas = np.nonzero(np.triu(distancias <= limiar, k=1))
    for i, j in zip(linhas.tolist(), colunas.tolist(), strict=True):
        pai[raiz(i)] = raiz(j)
    membros: dict[int, list[int]] = {}
    for i in range(n):
        membros.setdefault(raiz(i), []).append(i)
    grupos = tuple(sorted(tuple(m) for m in membros.values()))
    return Agrupamento(grupos, len(linhas), n * (n - 1) // 2)


@dataclass(frozen=True, slots=True)
class AvaliacaoHash:
    """O veredito do critério de escalada para embeddings.

    Attributes:
        grupo_grande_demais: O maior grupo passa da fração máxima das imagens.
        pares_demais: A fração de pares ligados passa da fração máxima.
    """

    grupo_grande_demais: bool
    pares_demais: bool

    @property
    def reprovado(self) -> bool:
        """Verdadeiro se qualquer um dos critérios reprovar o hash."""
        return self.grupo_grande_demais or self.pares_demais


def avaliar_hash(
    agrupamento: Agrupamento,
    fracao_maxima_grupo: float,
    fracao_maxima_pares: float,
) -> AvaliacaoHash:
    """Aplica o critério de escalada: reprova se algum limite for ultrapassado.

    Os limites são estritos: o maior grupo reprova se tiver mais que
    ``fracao_maxima_grupo`` das imagens; os pares, se a fração ligada for maior
    que ``fracao_maxima_pares``.

    Args:
        agrupamento: O agrupamento das imagens reais.
        fracao_maxima_grupo: Fração máxima das imagens no maior grupo.
        fracao_maxima_pares: Fração máxima de pares ligados.

    Returns:
        A avaliação com cada critério separado.
    """
    grande = agrupamento.maior_grupo > fracao_maxima_grupo * agrupamento.n_imagens
    pares = agrupamento.fracao_pares_ligados > fracao_maxima_pares
    return AvaliacaoHash(grande, pares)


def matriz_de_distancias_cosseno(vetores: Sequence[np.ndarray]) -> np.ndarray:
    """Calcula a distância de cosseno entre todos os pares de vetores.

    A distância é 1 menos o cosseno do ângulo entre os vetores: 0 para a mesma
    direção, 1 para direções perpendiculares e 2 para opostas. A matriz sai
    exatamente simétrica, com zeros na diagonal.

    Args:
        vetores: Vetores de mesma dimensão, pelo menos 2, nenhum nulo.

    Returns:
        Matriz float64 n x n, com valores de 0 a 2.

    Raises:
        ValueError: Se houver menos de 2 vetores, formas diferentes ou algum
            vetor nulo.
    """
    if len(vetores) < 2:
        raise ValueError("São necessários pelo menos 2 vetores.")
    if len({v.shape for v in vetores}) != 1:
        raise ValueError("Os vetores devem ter a mesma forma.")
    matriz = np.stack(vetores).astype(np.float64)
    normas = np.linalg.norm(matriz, axis=1)
    if not normas.all():
        raise ValueError("Há um vetor nulo: o cosseno não é definido.")
    unitarios = matriz / normas[:, None]
    distancias = np.clip(1.0 - unitarios @ unitarios.T, 0.0, 2.0)
    distancias = (distancias + distancias.T) / 2
    np.fill_diagonal(distancias, 0.0)
    return distancias


def densidade_do_grupo(
    distancias: np.ndarray, grupo: Sequence[int], limiar: float
) -> float:
    """Calcula a fração dos pares de um grupo ligados diretamente (d <= limiar).

    Numa série real, quase todos se parecem com quase todos (densidade perto de
    1); numa corrente, cada imagem se liga a poucas (densidade perto de 0).

    Args:
        distancias: Matriz n x n de distâncias.
        grupo: Índices das imagens do grupo, pelo menos 2.
        limiar: Distância máxima para uma ligação.

    Returns:
        Ligações internas divididas pelos pares possíveis, de 0 a 1.

    Raises:
        ValueError: Se o grupo tiver menos de 2 imagens.
    """
    if len(grupo) < 2:
        raise ValueError("A densidade exige um grupo com pelo menos 2 imagens.")
    indices = np.asarray(grupo)
    internas = distancias[np.ix_(indices, indices)]
    ligacoes = int(np.count_nonzero(np.triu(internas <= limiar, k=1)))
    possiveis = len(indices) * (len(indices) - 1) // 2
    return ligacoes / possiveis


def e_serie_real(densidade: float, densidade_minima: float) -> bool:
    """Diz se um grupo é declarado série real (densidade >= mínima) ou corrente.

    Args:
        densidade: Densidade do grupo, de 0 a 1.
        densidade_minima: Corte pré-registrado.

    Returns:
        Verdadeiro para série real; falso para corrente.
    """
    return densidade >= densidade_minima
