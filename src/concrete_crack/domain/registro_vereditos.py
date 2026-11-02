"""Registro dos vereditos da inspeção: imutável, preso à amostra e auditável.

O registro nunca é alterado no lugar: cada operação devolve um registro novo. Um
veredito só é dado uma vez; mudá-lo exige uma correção com motivo, que guarda o
veredito anterior. As horas vêm de fora, para o domínio continuar puro.
"""

import re
from dataclasses import dataclass, replace
from datetime import datetime

from .veredito import Veredito

PADRAO_SHA256 = re.compile(r"[0-9a-f]{64}")


def _validar_hora(hora: str) -> None:
    """Exige data e hora ISO 8601 com fuso (por exemplo, em UTC)."""
    try:
        instante = datetime.fromisoformat(hora)
    except ValueError as erro:
        raise ValueError(f"Hora inválida: {hora!r}. Use ISO 8601.") from erro
    if instante.tzinfo is None:
        raise ValueError(f"A hora {hora!r} precisa informar o fuso (UTC).")


@dataclass(frozen=True, slots=True)
class Julgamento:
    """O veredito atual sobre uma máscara.

    Attributes:
        mascara: Caminho da máscara na amostra (por exemplo ``BW/001.jpg``).
        veredito: O veredito vigente (o corrigido, se houve correção).
        registrado_em: Hora ISO 8601 com fuso em que foi dado pela primeira vez.
        observacao: Comentário livre do Gui, possivelmente vazio.
    """

    mascara: str
    veredito: Veredito
    registrado_em: str
    observacao: str = ""

    def __post_init__(self) -> None:
        """Recusa horas inválidas."""
        _validar_hora(self.registrado_em)


@dataclass(frozen=True, slots=True)
class Correcao:
    """Mudança de um veredito já dado.

    Attributes:
        mascara: Caminho da máscara corrigida.
        de: Veredito anterior.
        para: Veredito novo.
        motivo: Por que o veredito mudou; não pode ser vazio.
        registrado_em: Hora ISO 8601 com fuso da correção.
    """

    mascara: str
    de: Veredito
    para: Veredito
    motivo: str
    registrado_em: str

    def __post_init__(self) -> None:
        """Recusa motivo vazio, veredito igual e hora inválida."""
        if not self.motivo.strip():
            raise ValueError("A correção precisa de um motivo.")
        if self.de is self.para:
            raise ValueError("A correção precisa mudar o veredito.")
        _validar_hora(self.registrado_em)


@dataclass(frozen=True, slots=True)
class RegistroVereditos:
    """Os vereditos de uma amostra de máscaras, na ordem do sorteio.

    Attributes:
        fonte_id: Identificador da fonte (por exemplo ccsd).
        sha256_amostra: SHA-256 do arquivo da amostra sorteada; prende o
            registro àquela amostra.
        amostra: Máscaras a julgar, na ordem do sorteio, sem repetição.
        julgamentos: Vereditos dados, na ordem em que foram dados.
        correcoes: Mudanças de veredito, na ordem em que ocorreram.
    """

    fonte_id: str
    sha256_amostra: str
    amostra: tuple[str, ...]
    julgamentos: tuple[Julgamento, ...] = ()
    correcoes: tuple[Correcao, ...] = ()

    def __post_init__(self) -> None:
        """Recusa registros incoerentes."""
        if not self.fonte_id.strip():
            raise ValueError("fonte_id não pode ser vazio.")
        if not PADRAO_SHA256.fullmatch(self.sha256_amostra):
            raise ValueError("sha256_amostra deve ter 64 hexadecimais minúsculos.")
        if not self.amostra:
            raise ValueError("A amostra não pode ser vazia.")
        if len(set(self.amostra)) != len(self.amostra):
            raise ValueError("A amostra tem máscaras repetidas.")
        julgadas = [j.mascara for j in self.julgamentos]
        if len(set(julgadas)) != len(julgadas):
            raise ValueError("Há máscara julgada mais de uma vez.")
        if not set(julgadas) <= set(self.amostra):
            raise ValueError("Há máscara julgada que não está na amostra.")
        if not {c.mascara for c in self.correcoes} <= set(julgadas):
            raise ValueError("Há correção de máscara que não foi julgada.")

    @property
    def pendentes(self) -> tuple[str, ...]:
        """Máscaras ainda não julgadas, na ordem do sorteio."""
        julgadas = {j.mascara for j in self.julgamentos}
        return tuple(m for m in self.amostra if m not in julgadas)

    @property
    def proxima(self) -> str | None:
        """A próxima máscara a julgar, ou None se todas foram julgadas."""
        pendentes = self.pendentes
        return pendentes[0] if pendentes else None

    @property
    def completo(self) -> bool:
        """Verdadeiro quando todas as máscaras da amostra foram julgadas."""
        return not self.pendentes

    @property
    def vereditos(self) -> tuple[Veredito, ...]:
        """Os vereditos vigentes das máscaras julgadas, na ordem do sorteio."""
        por_mascara = {j.mascara: j.veredito for j in self.julgamentos}
        return tuple(por_mascara[m] for m in self.amostra if m in por_mascara)

    def julgar(
        self,
        mascara: str,
        veredito: Veredito,
        registrado_em: str,
        observacao: str = "",
    ) -> "RegistroVereditos":
        """Registra o veredito de uma máscara que ainda não foi julgada.

        Args:
            mascara: Máscara da amostra.
            veredito: O veredito dado.
            registrado_em: Hora ISO 8601 com fuso.
            observacao: Comentário livre, opcional.

        Returns:
            Um novo registro; este não é alterado.

        Raises:
            ValueError: Se a máscara não estiver na amostra, já tiver sido
                julgada ou a hora for inválida.
        """
        if mascara not in self.amostra:
            raise ValueError(f"A máscara {mascara} não está na amostra.")
        if mascara not in self.pendentes:
            raise ValueError(
                f"A máscara {mascara} já foi julgada; use uma correção para mudar."
            )
        julgamento = Julgamento(mascara, veredito, registrado_em, observacao)
        return replace(self, julgamentos=(*self.julgamentos, julgamento))

    def corrigir(
        self, mascara: str, novo: Veredito, motivo: str, registrado_em: str
    ) -> "RegistroVereditos":
        """Muda o veredito de uma máscara já julgada, guardando o anterior.

        Args:
            mascara: Máscara já julgada.
            novo: O veredito novo, diferente do atual.
            motivo: Por que o veredito mudou; não pode ser vazio.
            registrado_em: Hora ISO 8601 com fuso da correção.

        Returns:
            Um novo registro com o veredito vigente trocado e a correção
            anotada; este não é alterado.

        Raises:
            ValueError: Se a máscara não tiver sido julgada, o motivo for
                vazio, o veredito não mudar ou a hora for inválida.
        """
        atual = next((j for j in self.julgamentos if j.mascara == mascara), None)
        if atual is None:
            raise ValueError(f"A máscara {mascara} ainda não foi julgada.")
        correcao = Correcao(mascara, atual.veredito, novo, motivo, registrado_em)
        julgamentos = tuple(
            replace(j, veredito=novo) if j.mascara == mascara else j
            for j in self.julgamentos
        )
        return replace(
            self, julgamentos=julgamentos, correcoes=(*self.correcoes, correcao)
        )
