"""Conferência de dimensões entre máscaras e fotos, sem acesso a disco."""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

Tamanho = tuple[int, int]
ContagemTamanhos = tuple[tuple[Tamanho, int], ...]
ContagemOrientacoes = tuple[tuple[int | None, int], ...]

ORIENTACOES_COM_TROCA_DE_EIXOS = frozenset({5, 6, 7, 8})


@dataclass(frozen=True, slots=True)
class Cabecalho:
    """Dimensões e orientação gravadas no cabeçalho de uma imagem.

    Attributes:
        largura: Largura em pixels, como gravada no arquivo.
        altura: Altura em pixels, como gravada no arquivo.
        orientacao_exif: Valor da etiqueta EXIF de orientação (1 a 8), ou None
            quando a imagem não a tem.
    """

    largura: int
    altura: int
    orientacao_exif: int | None = None

    def __post_init__(self) -> None:
        """Recusa dimensões não positivas e orientações fora de 1 a 8."""
        if self.largura <= 0 or self.altura <= 0:
            raise ValueError("largura e altura devem ser positivas.")
        if self.orientacao_exif is not None and not 1 <= self.orientacao_exif <= 8:
            raise ValueError("orientacao_exif deve ser de 1 a 8, ou None.")

    @property
    def tamanho_exibido(self) -> Tamanho:
        """Largura e altura depois de aplicar a orientação EXIF.

        As orientações de 5 a 8 trocam os eixos; as demais não.
        """
        if self.orientacao_exif in ORIENTACOES_COM_TROCA_DE_EIXOS:
            return (self.altura, self.largura)
        return (self.largura, self.altura)


@dataclass(frozen=True, slots=True)
class ResultadoDimensoes:
    """Resultado da conferência de dimensões dos pares máscara-foto.

    Attributes:
        tamanhos_mascaras: Pares (tamanho, quantidade) das máscaras, do mais
            frequente ao menos frequente.
        tamanhos_fotos: O mesmo para as fotos.
        orientacoes_mascaras: Pares (orientação EXIF, quantidade) das máscaras.
        orientacoes_fotos: O mesmo para as fotos.
        diferentes: Pares (máscara, foto) de tamanhos gravados diferentes.
        eixos_trocados: Subconjunto de ``diferentes`` em que a largura de um é a
            altura do outro, o que indica rotação.
        orientacoes_fotos_dos_trocados: Orientações EXIF das fotos dos pares
            de ``eixos_trocados``.
        diferentes_apos_orientacao: Pares cujo tamanho exibido (com a orientação
            EXIF aplicada) ainda é diferente.
    """

    tamanhos_mascaras: ContagemTamanhos
    tamanhos_fotos: ContagemTamanhos
    orientacoes_mascaras: ContagemOrientacoes
    orientacoes_fotos: ContagemOrientacoes
    diferentes: tuple[tuple[str, str], ...]
    eixos_trocados: tuple[tuple[str, str], ...]
    orientacoes_fotos_dos_trocados: ContagemOrientacoes
    diferentes_apos_orientacao: tuple[tuple[str, str], ...]


def _cabecalho(cabecalhos: Mapping[str, Cabecalho], caminho: str) -> Cabecalho:
    """Devolve o cabeçalho de um caminho, ou recusa se ele faltar."""
    if caminho not in cabecalhos:
        raise ValueError(f"Falta o cabeçalho de {caminho!r}.")
    return cabecalhos[caminho]


def _tamanhos(lista: Sequence[Cabecalho]) -> ContagemTamanhos:
    """Conta os tamanhos, do mais frequente ao menos frequente."""
    contagem = Counter((c.largura, c.altura) for c in lista)
    return tuple(sorted(contagem.items(), key=lambda item: (-item[1], item[0])))


def _orientacoes(lista: Sequence[Cabecalho]) -> ContagemOrientacoes:
    """Conta as orientações EXIF, do mais frequente ao menos frequente."""
    contagem = Counter(c.orientacao_exif for c in lista)
    return tuple(sorted(contagem.items(), key=lambda item: (-item[1], item[0] or 0)))


def conferir_dimensoes(
    pares: Sequence[tuple[str, str]], cabecalhos: Mapping[str, Cabecalho]
) -> ResultadoDimensoes:
    """Compara as dimensões de cada máscara com as da sua foto.

    Args:
        pares: Pares (caminho da máscara, caminho da foto).
        cabecalhos: Cabeçalho de cada caminho citado em ``pares``.

    Returns:
        O resultado, com os pares divergentes em ordem alfabética.

    Raises:
        ValueError: Se faltar o cabeçalho de algum caminho dos pares.
    """
    das_mascaras: list[Cabecalho] = []
    das_fotos: list[Cabecalho] = []
    fotos_dos_trocados: list[Cabecalho] = []
    diferentes: list[tuple[str, str]] = []
    trocados: list[tuple[str, str]] = []
    apos_orientacao: list[tuple[str, str]] = []
    for mascara, foto in pares:
        cab_m = _cabecalho(cabecalhos, mascara)
        cab_f = _cabecalho(cabecalhos, foto)
        das_mascaras.append(cab_m)
        das_fotos.append(cab_f)
        if (cab_m.largura, cab_m.altura) != (cab_f.largura, cab_f.altura):
            diferentes.append((mascara, foto))
            if (cab_m.largura, cab_m.altura) == (cab_f.altura, cab_f.largura):
                trocados.append((mascara, foto))
                fotos_dos_trocados.append(cab_f)
        if cab_m.tamanho_exibido != cab_f.tamanho_exibido:
            apos_orientacao.append((mascara, foto))
    return ResultadoDimensoes(
        tamanhos_mascaras=_tamanhos(das_mascaras),
        tamanhos_fotos=_tamanhos(das_fotos),
        orientacoes_mascaras=_orientacoes(das_mascaras),
        orientacoes_fotos=_orientacoes(das_fotos),
        diferentes=tuple(sorted(diferentes)),
        eixos_trocados=tuple(sorted(trocados)),
        orientacoes_fotos_dos_trocados=_orientacoes(fotos_dos_trocados),
        diferentes_apos_orientacao=tuple(sorted(apos_orientacao)),
    )
