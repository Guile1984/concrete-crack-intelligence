"""Inspeção das máscaras: sorteio, preparação das imagens e julgamento.

Uso, a partir da raiz do projeto::

    python -m concrete_crack.presentation.inspecao sortear ccsd
    python -m concrete_crack.presentation.inspecao preparar ccsd
    python -m concrete_crack.presentation.inspecao julgar ccsd
    python -m concrete_crack.presentation.inspecao resultado ccsd

O ``sortear`` lê só o manifesto (nomes e hashes): não abre nenhuma imagem. O
``preparar`` grava, para cada máscara sorteada, um PNG com dois painéis: a foto
limpa à esquerda e a foto com a máscara em vermelho à direita, separados por uma
faixa azul. O ``julgar`` conduz a sessão de julgamento, gravando cada veredito
na hora; o ``corrigir`` muda um veredito já dado e recebe, depois da fonte, a
máscara (como BW/001.jpg), o veredito novo e o motivo. O ``resultado`` aplica a
regra pré-registrada aos vereditos e só roda com os julgamentos completos.
"""

import argparse
import json
import os
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from ..config.caminhos import (
    caminho_amostra_inspecao,
    caminho_manifesto_arquivos,
    caminho_vereditos_inspecao,
    pasta_dados_brutos,
    pasta_imagens_inspecao,
)
from ..config.regras import REGRAS
from ..domain.amostragem import amostrar_por_hash
from ..domain.orientacao import aplicar_orientacao
from ..domain.painel import montar_painel
from ..domain.registro_vereditos import RegistroVereditos
from ..domain.sobreposicao import intensidade_da_mascara, sobrepor_mascara
from ..domain.veredito import ResultadoInspecao, Veredito, avaliar
from ..infrastructure.arquivos import sha256_do_arquivo
from ..infrastructure.imagens import gravar_png, ler_cabecalho, ler_cinza, ler_rgb
from ..infrastructure.manifesto_arquivos import carregar_manifesto
from ..infrastructure.registro_vereditos_json import carregar_registro, gravar_registro
from .estrutura import parear_fonte
from .sessao_julgamento import Ambiente, rodar_sessao

PREFIXO_MASCARAS = "BW/"
FATOR_VISUALIZACAO = 5
OPACIDADE_MASCARA = 0.5
LARGURA_SEPARADOR = 8


def nome_da_imagem(posicao: int, mascara: str) -> str:
    """Devolve o nome do arquivo da imagem preparada de uma máscara.

    Args:
        posicao: Posição da máscara na amostra, a partir de 1.
        mascara: Caminho da máscara na amostra (por exemplo ``BW/064.jpg``).

    Returns:
        O nome ``<posição com 2 dígitos>_<número da máscara>.png``.
    """
    return f"{posicao:02d}_{Path(mascara).stem}.png"


def sortear_amostra(raiz: Path, fonte_id: str) -> dict[str, object]:
    """Sorteia as máscaras a inspecionar e grava o registro do sorteio.

    O sorteio é pré-registrado: o arquivo é criado uma única vez e nunca
    refeito, pois refazê-lo depois de ver máscaras anularia o pré-registro.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado.

    Returns:
        O registro gravado em ``manifests/inspecao_<fonte_id>.json``.

    Raises:
        FileExistsError: Se a amostra da fonte já existir.
        FileNotFoundError: Se o manifesto de arquivos não existir.
        ValueError: Se o manifesto for de outra fonte ou tiver menos máscaras
            do que o tamanho da amostra.
    """
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    destino = caminho_amostra_inspecao(raiz, fonte_id)
    if destino.exists():
        raise FileExistsError(
            f"A amostra de {fonte_id} já existe: {destino}. O sorteio é "
            "pré-registrado e não se refaz."
        )
    manifesto = carregar_manifesto(origem)
    if manifesto.fonte_id != fonte_id:
        raise ValueError(
            f"O manifesto de {fonte_id} declara a fonte {manifesto.fonte_id!r}."
        )
    mascaras = [
        arquivo.caminho
        for arquivo in manifesto.arquivos
        if arquivo.caminho.startswith(PREFIXO_MASCARAS)
    ]
    amostra = amostrar_por_hash(
        mascaras, REGRAS.n_inspecao_mascaras, REGRAS.seed_inspecao_mascaras
    )
    registro: dict[str, object] = {
        "fonte_id": fonte_id,
        "seed": REGRAS.seed_inspecao_mascaras,
        "n": REGRAS.n_inspecao_mascaras,
        "limiar_reprovacao": REGRAS.limiar_reprovacao_mascaras,
        "total_mascaras": len(mascaras),
        "sha256_manifesto_de_arquivos": sha256_do_arquivo(origem),
        "amostra": list(amostra),
    }
    texto = json.dumps(registro, ensure_ascii=False, indent=2) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")
    return registro


def preparar_imagens(raiz: Path, fonte_id: str) -> list[Path]:
    """Grava uma imagem de dois painéis para cada máscara da amostra.

    Esquerda: a foto com a orientação EXIF aplicada (política A34). Direita: a
    mesma foto com a máscara em vermelho, proporcional à intensidade da máscara.
    Os arquivos se chamam ``<posição>_<número da máscara>.png``, na ordem da
    amostra, e são recriados a cada execução.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com manifesto de arquivos registrado
            e amostra sorteada.

    Returns:
        Os caminhos das imagens gravadas, na ordem da amostra.

    Raises:
        FileNotFoundError: Se a amostra, o manifesto ou alguma imagem não
            existir.
        OSError: Se algum arquivo não for uma imagem reconhecida.
        ValueError: Se o manifesto mudou desde o sorteio, se uma máscara da
            amostra não tiver foto ou se as formas de foto e máscara diferirem.
    """
    registro = json.loads(
        caminho_amostra_inspecao(raiz, fonte_id).read_text(encoding="utf-8")
    )
    origem = caminho_manifesto_arquivos(raiz, fonte_id)
    if sha256_do_arquivo(origem) != registro["sha256_manifesto_de_arquivos"]:
        raise ValueError("O manifesto de arquivos mudou desde o sorteio da amostra.")
    foto_de = dict(parear_fonte(raiz, fonte_id).pares)
    pasta = pasta_dados_brutos(raiz, fonte_id)
    saida = pasta_imagens_inspecao(raiz, fonte_id)
    gravadas: list[Path] = []
    for posicao, mascara in enumerate(registro["amostra"], start=1):
        if mascara not in foto_de:
            raise ValueError(f"A máscara {mascara} da amostra não tem foto.")
        foto = pasta / foto_de[mascara]
        orientacao = ler_cabecalho(foto).orientacao_exif
        limpa = aplicar_orientacao(ler_rgb(foto, FATOR_VISUALIZACAO), orientacao)
        intensidade = intensidade_da_mascara(
            ler_cinza(pasta / mascara, FATOR_VISUALIZACAO)
        )
        if intensidade.shape != limpa.shape[:2]:
            raise ValueError(
                f"{mascara}: a máscara {intensidade.shape} e a foto "
                f"{limpa.shape[:2]} têm formas diferentes."
            )
        com_mascara = sobrepor_mascara(limpa, intensidade, OPACIDADE_MASCARA)
        painel = montar_painel(limpa, com_mascara, LARGURA_SEPARADOR)
        destino = saida / nome_da_imagem(posicao, mascara)
        gravar_png(destino, painel)
        gravadas.append(destino)
    return gravadas


def abrir_imagem(caminho: Path) -> None:
    """Abre a imagem no visualizador padrão do sistema.

    Args:
        caminho: Imagem a abrir.

    Raises:
        OSError: Se o sistema não abrir arquivos sozinho (só o Windows abre).
    """
    abrir = getattr(os, "startfile", None)
    if abrir is None:
        raise OSError("Este sistema não abre imagens automaticamente.")
    abrir(caminho)


def agora_utc() -> str:
    """Devolve a hora atual em UTC, em ISO 8601 com fuso, até o segundo."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def _carregar_registro_da_inspecao(raiz: Path, fonte_id: str) -> RegistroVereditos:
    """Lê o registro de vereditos, ou cria um vazio preso à amostra sorteada."""
    arquivo_amostra = caminho_amostra_inspecao(raiz, fonte_id)
    if not arquivo_amostra.exists():
        raise FileNotFoundError(
            f"A amostra de {fonte_id} não existe: rode 'sortear' antes."
        )
    sha = sha256_do_arquivo(arquivo_amostra)
    destino = caminho_vereditos_inspecao(raiz, fonte_id)
    if not destino.exists():
        amostra = json.loads(arquivo_amostra.read_text(encoding="utf-8"))["amostra"]
        return RegistroVereditos(fonte_id, sha, tuple(amostra))
    registro = carregar_registro(destino)
    if registro.fonte_id != fonte_id:
        raise ValueError(
            f"O registro {destino} é da fonte {registro.fonte_id!r}, "
            f"não de {fonte_id!r}."
        )
    if registro.sha256_amostra != sha:
        raise ValueError(
            f"O registro {destino} pertence a outra amostra: o arquivo da "
            "amostra mudou desde o primeiro julgamento."
        )
    return registro


def julgar_amostra(
    raiz: Path,
    fonte_id: str,
    ler: Callable[[str], str],
    escrever: Callable[[str], None],
    abrir: Callable[[Path], None],
    agora: Callable[[], str],
) -> RegistroVereditos:
    """Conduz a sessão de julgamento das máscaras da amostra.

    Continua de onde parou: o registro é lido do disco e gravado depois de cada
    veredito.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com amostra sorteada e imagens
            preparadas.
        ler: Mostra uma pergunta e devolve a resposta digitada.
        escrever: Mostra uma linha de texto.
        abrir: Abre uma imagem no visualizador.
        agora: Devolve a hora atual em ISO 8601 com fuso.

    Returns:
        O registro ao final da sessão.

    Raises:
        FileNotFoundError: Se a amostra não existir ou faltarem imagens.
        ValueError: Se o registro for de outra fonte ou de outra amostra.
    """
    registro = _carregar_registro_da_inspecao(raiz, fonte_id)
    pasta = pasta_imagens_inspecao(raiz, fonte_id)
    ausentes = [
        mascara
        for posicao, mascara in enumerate(registro.amostra, start=1)
        if mascara in registro.pendentes
        and not (pasta / nome_da_imagem(posicao, mascara)).exists()
    ]
    if ausentes:
        raise FileNotFoundError(
            f"Faltam {len(ausentes)} imagens em {pasta}: rode 'preparar' antes."
        )
    destino = caminho_vereditos_inspecao(raiz, fonte_id)

    def imagem_de(posicao: int, mascara: str) -> Path:
        return pasta / nome_da_imagem(posicao, mascara)

    def gravar(novo: RegistroVereditos) -> None:
        gravar_registro(novo, destino)

    ambiente = Ambiente(ler, escrever, abrir, agora, gravar)
    return rodar_sessao(registro, imagem_de, ambiente)


def corrigir_veredito(
    raiz: Path,
    fonte_id: str,
    mascara: str,
    novo: Veredito,
    motivo: str,
    agora: Callable[[], str],
) -> RegistroVereditos:
    """Muda o veredito de uma máscara já julgada, com motivo, e grava.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte.
        mascara: Máscara já julgada (por exemplo ``BW/064.jpg``).
        novo: O veredito novo.
        motivo: Por que o veredito mudou; não pode ser vazio.
        agora: Devolve a hora atual em ISO 8601 com fuso.

    Returns:
        O registro gravado, com a correção anotada.

    Raises:
        FileNotFoundError: Se ainda não houver nenhum veredito registrado.
        ValueError: Se a máscara não foi julgada, o motivo for vazio, o
            veredito não mudar ou o registro for de outra amostra.
    """
    destino = caminho_vereditos_inspecao(raiz, fonte_id)
    if not destino.exists():
        raise FileNotFoundError(f"Ainda não há vereditos registrados em {destino}.")
    registro = _carregar_registro_da_inspecao(raiz, fonte_id)
    corrigido = registro.corrigir(mascara, novo, motivo, agora())
    gravar_registro(corrigido, destino)
    return corrigido


def calcular_resultado(
    raiz: Path, fonte_id: str
) -> tuple[RegistroVereditos, ResultadoInspecao]:
    """Aplica a regra pré-registrada aos vereditos de uma inspeção completa.

    Args:
        raiz: Raiz do projeto.
        fonte_id: Identificador da fonte, com todas as máscaras julgadas.

    Returns:
        O registro lido e o resultado da avaliação.

    Raises:
        FileNotFoundError: Se não houver vereditos registrados.
        ValueError: Se o registro for de outra amostra, a amostra não tiver o
            tamanho pré-registrado ou ainda houver máscaras sem julgamento.
    """
    destino = caminho_vereditos_inspecao(raiz, fonte_id)
    if not destino.exists():
        raise FileNotFoundError(f"Ainda não há vereditos registrados em {destino}.")
    registro = _carregar_registro_da_inspecao(raiz, fonte_id)
    if len(registro.amostra) != REGRAS.n_inspecao_mascaras:
        raise ValueError(
            f"A amostra tem {len(registro.amostra)} máscaras; o pré-registro "
            f"exige {REGRAS.n_inspecao_mascaras}."
        )
    if not registro.completo:
        raise ValueError(
            f"O julgamento está incompleto: faltam {len(registro.pendentes)} máscaras."
        )
    resultado = avaliar(registro.vereditos, REGRAS.limiar_reprovacao_mascaras)
    return registro, resultado


def _percentual(valor: float) -> str:
    """Formata uma proporção como percentual com uma casa decimal."""
    return f"{valor * 100:.1f}%"


def formatar_resultado(
    fonte_id: str, registro: RegistroVereditos, resultado: ResultadoInspecao
) -> str:
    """Monta o texto do resultado da inspeção, pronto para ler e registrar.

    Args:
        fonte_id: Identificador da fonte.
        registro: O registro completo da inspeção.
        resultado: O resultado calculado pela regra pré-registrada.

    Returns:
        O relatório em várias linhas.
    """
    n = resultado.n
    horas = [datetime.fromisoformat(j.registrado_em) for j in registro.julgamentos]
    duracao = (max(horas) - min(horas)).total_seconds() / 60
    inferior, superior = resultado.intervalo_inadequadas
    inf_sens, sup_sens = resultado.intervalo_sensibilidade
    decisao = "REPROVADA" if resultado.reprovada else "APROVADA"
    decisao_sens = (
        "REPROVADA"
        if resultado.reprovada_se_duvidosas_forem_inadequadas
        else "APROVADA"
    )
    depende = "sim" if resultado.conclusao_depende_das_duvidosas else "não"
    linhas = [
        f"Inspeção das máscaras de {fonte_id}",
        f"Máscaras julgadas: {n}",
        f"Adequadas:   {resultado.adequadas} ({_percentual(resultado.adequadas / n)})",
        f"Inadequadas: {resultado.inadequadas} "
        f"({_percentual(resultado.inadequadas / n)}); "
        f"Wilson 95%: {_percentual(inferior)} a {_percentual(superior)}",
        f"Duvidosas:   {resultado.duvidosas} ({_percentual(resultado.duvidosas / n)})",
        f"Regra A31: reprova com {resultado.limiar_reprovacao} ou mais inadequadas.",
        f"Decisão: fonte {decisao}.",
        "Sensibilidade (duvidosas contadas como inadequadas): "
        f"fonte {decisao_sens}; "
        f"Wilson 95%: {_percentual(inf_sens)} a {_percentual(sup_sens)}.",
        f"A conclusão depende das duvidosas: {depende}.",
        f"Correções registradas: {len(registro.correcoes)}.",
        f"Duração do julgamento: {duracao:.0f} min "
        f"({min(horas).isoformat()} a {max(horas).isoformat()}).",
    ]
    return "\n".join(linhas)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa os comandos de inspeção.

    Args:
        argv: Argumentos da linha de comando; None usa ``sys.argv``.

    Returns:
        0 em sucesso; 2 em erro; 130 se a sessão for interrompida com Ctrl+C.
    """
    parser = argparse.ArgumentParser(
        prog="python -m concrete_crack.presentation.inspecao",
        description="Sorteia, prepara e julga as máscaras a inspecionar.",
    )
    parser.add_argument(
        "--raiz", type=Path, default=Path("."), help="raiz do projeto (padrão: .)"
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    sortear = comandos.add_parser("sortear", help="sorteia e grava a amostra")
    sortear.add_argument("fonte_id")
    preparar = comandos.add_parser("preparar", help="grava as imagens da amostra")
    preparar.add_argument("fonte_id")
    julgar = comandos.add_parser("julgar", help="conduz a sessão de julgamento")
    julgar.add_argument("fonte_id")
    resultado = comandos.add_parser("resultado", help="aplica a regra aos vereditos")
    resultado.add_argument("fonte_id")
    corrigir = comandos.add_parser("corrigir", help="corrige um veredito já dado")
    corrigir.add_argument("fonte_id")
    corrigir.add_argument("mascara", help="máscara da amostra, como BW/064.jpg")
    corrigir.add_argument("veredito", choices=[v.value for v in Veredito])
    corrigir.add_argument("motivo", help="por que o veredito mudou")
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    try:
        if args.comando == "sortear":
            registro = sortear_amostra(raiz, args.fonte_id)
            destino = caminho_amostra_inspecao(raiz, args.fonte_id)
            print(
                f"Sorteadas {registro['n']} de {registro['total_mascaras']} "
                f"máscaras em {destino}"
            )
        elif args.comando == "preparar":
            gravadas = preparar_imagens(raiz, args.fonte_id)
            print(
                f"Gravadas {len(gravadas)} imagens em "
                f"{pasta_imagens_inspecao(raiz, args.fonte_id)}"
            )
            print(
                "Em cada uma: foto à esquerda, foto com a máscara à direita, "
                "faixa azul."
            )
        elif args.comando == "julgar":
            julgar_amostra(raiz, args.fonte_id, input, print, abrir_imagem, agora_utc)
        elif args.comando == "resultado":
            registro, avaliacao = calcular_resultado(raiz, args.fonte_id)
            print(formatar_resultado(args.fonte_id, registro, avaliacao))
        else:
            corrigir_veredito(
                raiz,
                args.fonte_id,
                args.mascara,
                Veredito(args.veredito),
                args.motivo,
                agora_utc,
            )
            print(f"Correção registrada para {args.mascara}.")
    except KeyboardInterrupt:
        print("\nSessão interrompida. O que foi julgado está gravado.")
        return 130
    except (ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
