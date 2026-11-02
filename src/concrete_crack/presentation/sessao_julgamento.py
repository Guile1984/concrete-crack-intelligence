"""Sessão interativa de julgamento das máscaras, com entrada e saída injetadas.

O laço não chama ``input`` nem ``print`` diretamente: recebe funções. Assim os
testes simulam uma sessão inteira sem console, e o mesmo laço serve ao comando
real. O registro é gravado depois de cada resposta, então interromper a sessão
em qualquer ponto não perde nenhum veredito já dado.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..domain.registro_vereditos import RegistroVereditos
from ..domain.veredito import Veredito

INTERVALO_RUBRICA = 10

RUBRICA = """\
Critério (A31): compare a máscara em vermelho com a fissura visível na foto.
  inadequada: omite fissura visível, marca o que não é fissura (excesso) ou
              tem espessura visivelmente incompatível.
  adequada:   nenhum desses problemas.
  duvidosa:   você não consegue decidir; registre e siga.
Julgue o que vê. Só você julga (A33)."""

PERGUNTA = "[a]dequada  [i]nadequada  [d]uvidosa  [s]air > "
PERGUNTA_OBSERVACAO = "Observação (Enter para pular) > "

TECLAS = {
    "a": Veredito.ADEQUADA,
    "i": Veredito.INADEQUADA,
    "d": Veredito.DUVIDOSA,
}


@dataclass(frozen=True, slots=True)
class Ambiente:
    """As funções de que a sessão precisa do mundo exterior.

    Attributes:
        ler: Mostra uma pergunta e devolve a resposta digitada; levanta
            ``EOFError`` quando a entrada acaba.
        escrever: Mostra uma linha de texto.
        abrir: Abre uma imagem no visualizador.
        agora: Devolve a hora atual em ISO 8601 com fuso.
        gravar: Grava o registro de forma durável.
    """

    ler: Callable[[str], str]
    escrever: Callable[[str], None]
    abrir: Callable[[Path], None]
    agora: Callable[[], str]
    gravar: Callable[[RegistroVereditos], None]


def rodar_sessao(
    registro: RegistroVereditos,
    imagem_de: Callable[[int, str], Path],
    ambiente: Ambiente,
) -> RegistroVereditos:
    """Conduz o julgamento das máscaras pendentes, uma por vez, em ordem.

    Mostra só a posição ("12 de 40"), nunca contagens parciais de vereditos.
    Reimprime a rubrica no início e a cada ``INTERVALO_RUBRICA`` máscaras.
    Grava o registro depois de cada veredito.

    Args:
        registro: Registro atual; a sessão continua das máscaras pendentes.
        imagem_de: Dada a posição (a partir de 1) e a máscara, devolve o
            caminho da imagem preparada.
        ambiente: Entrada, saída, visualizador, relógio e gravação.

    Returns:
        O registro ao final: completo, ou parcial se a sessão foi interrompida.
    """
    escrever = ambiente.escrever
    if registro.completo:
        escrever("Todas as máscaras já foram julgadas.")
        return registro
    total = len(registro.amostra)
    posicao_inicial = registro.amostra.index(registro.pendentes[0]) + 1
    escrever(RUBRICA)
    while (mascara := registro.proxima) is not None:
        posicao = registro.amostra.index(mascara) + 1
        if posicao != posicao_inicial and (posicao - 1) % INTERVALO_RUBRICA == 0:
            escrever(RUBRICA)
        imagem = imagem_de(posicao, mascara)
        escrever(f"\nMáscara {posicao} de {total}: {imagem}")
        try:
            ambiente.abrir(imagem)
        except OSError:
            escrever("Não consegui abrir a imagem; abra-a pelo caminho acima.")
        veredito = _perguntar_veredito(ambiente)
        if veredito is None:
            escrever("Sessão interrompida. Rode de novo para continuar.")
            return registro
        instante = ambiente.agora()
        observacao = _perguntar_observacao(ambiente)
        registro = registro.julgar(mascara, veredito, instante, observacao)
        ambiente.gravar(registro)
    escrever(f"\nTodas as {total} máscaras foram julgadas.")
    return registro


def _perguntar_veredito(ambiente: Ambiente) -> Veredito | None:
    """Pergunta até receber a, i, d ou s; devolve None para sair."""
    while True:
        try:
            resposta = ambiente.ler(PERGUNTA).strip().lower()
        except EOFError:
            return None
        if resposta == "s":
            return None
        if resposta in TECLAS:
            return TECLAS[resposta]
        ambiente.escrever("Entrada inválida. Use a, i, d ou s.")


def _perguntar_observacao(ambiente: Ambiente) -> str:
    """Pergunta a observação opcional; entrada encerrada vale como vazia."""
    try:
        return ambiente.ler(PERGUNTA_OBSERVACAO).strip()
    except EOFError:
        return ""
