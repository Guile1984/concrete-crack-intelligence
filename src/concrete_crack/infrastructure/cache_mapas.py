"""Cache em disco dos mapas do Frangi por escala (A66, itens 1 e 6).

Implementa o port ``MapasPorEscala``. Na primeira vez que uma foto é pedida
num σ do fundo, lê a foto com a orientação EXIF aplicada (A34), calcula o
mapa de cada escala com o c do registro e grava todos em ``float32``; nas
vezes seguintes, só lê. Cada arquivo é gravado primeiro com outro nome e
depois renomeado, para que uma execução interrompida não deixe um mapa pela
metade que seria reaproveitado.
"""

import os
from pathlib import Path, PurePosixPath

import numpy as np

from ..domain.orientacao import aplicar_orientacao
from ..domain.registro_c import RegistroC
from .frangi import ParametrosFrangi, SegmentadorFrangi
from .imagens import ler_cabecalho, ler_rgb


class CacheMapasFrangi:
    """Mapas do Frangi de uma escala por vez, guardados em disco."""

    def __init__(
        self,
        pasta_fotos: Path,
        pasta_cache: Path,
        registro_c: RegistroC,
        escalas: tuple[float, ...],
        beta: float,
    ) -> None:
        """Guarda onde ler as fotos, onde guardar os mapas e os parâmetros.

        Args:
            pasta_fotos: Pasta dos dados brutos da fonte.
            pasta_cache: Pasta do cache, já específica deste registro do c.
            registro_c: O registro com o c de cada σ do fundo.
            escalas: As oitavas σ calculadas de uma vez.
            beta: ``REGRAS.beta_frangi``.
        """
        self.pasta_fotos = pasta_fotos
        self.pasta_cache = pasta_cache
        self.registro_c = registro_c
        self.escalas = escalas
        self.beta = beta

    def _arquivo(self, foto: str, sigma: float, sigma_fundo: float) -> Path:
        """Caminho do mapa de uma foto, escala e σ do fundo no cache."""
        nome = PurePosixPath(foto).stem
        return (
            self.pasta_cache
            / f"fundo_{sigma_fundo:g}"
            / f"sigma_{sigma:g}"
            / f"{nome}.npy"
        )

    def _calcular(self, foto: str, sigma_fundo: float) -> None:
        """Calcula e grava os mapas de todas as escalas de uma foto."""
        caminho = self.pasta_fotos / foto
        imagem = aplicar_orientacao(
            ler_rgb(caminho, 1), ler_cabecalho(caminho).orientacao_exif
        )
        c = self.registro_c.c_do_fundo(sigma_fundo)
        for sigma in self.escalas:
            parametros = ParametrosFrangi((sigma,), sigma_fundo, c, self.beta)
            mapa = SegmentadorFrangi(parametros).mapear(imagem).astype(np.float32)
            destino = self._arquivo(foto, sigma, sigma_fundo)
            destino.parent.mkdir(parents=True, exist_ok=True)
            temporario = destino.with_suffix(".tmp")
            with temporario.open("wb") as arquivo:
                np.save(arquivo, mapa)
            os.replace(temporario, destino)

    def mapa(self, foto: str, sigma: float, sigma_fundo: float) -> np.ndarray:
        """Devolve o mapa de uma foto numa escala e num σ do fundo.

        Args:
            foto: Caminho da foto no manifesto.
            sigma: Uma das escalas do cache.
            sigma_fundo: Um dos σ do fundo do registro do c.

        Returns:
            Mapa ``float32`` (altura, largura) em [0, 1].

        Raises:
            ValueError: Se a escala ou o σ do fundo não forem do cache.
        """
        if sigma not in self.escalas:
            raise ValueError(f"A escala {sigma} não está no cache.")
        fundos = [constante.sigma_fundo for constante in self.registro_c.constantes]
        if sigma_fundo not in fundos:
            raise ValueError(f"O σ do fundo {sigma_fundo} não tem c no registro.")
        destino = self._arquivo(foto, sigma, sigma_fundo)
        if not destino.exists():
            self._calcular(foto, sigma_fundo)
        return np.load(destino)
