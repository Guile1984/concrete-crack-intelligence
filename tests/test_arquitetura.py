"""Teste de arquitetura: cada camada só importa o que a tabela permite."""

import ast
from pathlib import Path

import pytest

PACOTE = "concrete_crack"
RAIZ = Path(__file__).resolve().parents[1] / "src" / PACOTE

PERMITIDAS: dict[str, set[str]] = {
    "config": set(),
    "domain": set(),
    "ports": {"domain", "config"},
    "infrastructure": {"ports", "domain", "config"},
    "services": {"ports", "domain", "config"},
    "presentation": {"config", "domain", "ports", "infrastructure", "services"},
}

# Biblioteca externa -> camadas em que ela pode aparecere.
SO_EM: dict[str, set[str]] = {
    "torch": {"infrastructure"},
    "torchvision": {"infrastructure"},
    "matplotlib": {"presentation", "services"},
    "pandas": {"presentation", "services"},
}

# Substitutos de "o domínio não acessa disco nem rede". É uma aproximação:
# um open() direto não seria detectado.
PROIBIDAS_NO_DOMINIO: set[str] = {
    "pathlib",
    "shutil",
    "socket",
    "urllib",
    "http",
    "requests",
    "PIL",
}


def importacoes(codigo: str, modulo: str, eh_pacote: bool) -> list[str]:
    """Lista os módulos importados, com os imports relativos já resolvidos."""
    arvore = ast.parse(codigo)
    pacote = modulo.split(".") if eh_pacote else modulo.split(".")[:-1]
    alvos: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            alvos.extend(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom):
            if no.level == 0:
                base = no.module.split(".") if no.module else []
            else:
                base = pacote[: len(pacote) - (no.level - 1)]
                if no.module:
                    base = base + no.module.split(".")
            alvo = ".".join(base)
            alvos.append(alvo)
            # "From pacote import nome": o nome pode ser um submódulo.
            alvos.extend(f"{alvo}.{alias.name}" for alias in no.names)
    return alvos


def camadas_internas(alvos: list[str]) -> set[str]:
    """Extrai as camadas do projeto que aparecem entre os imports."""
    camadas: set[str] = set()
    for alvo in alvos:
        partes = alvo.split(".")
        if partes[0] == PACOTE and len(partes) > 1 and partes[1] in PERMITIDAS:
            camadas.add(partes[1])
    return camadas


def bibliotecas_externas(alvos: list[str]) -> set[str]:
    """Extrai o nome de topo das bibliotecas que não são do projeto."""
    topo = {alvo.split(".")[0] for alvo in alvos}
    return {nome for nome in topo if nome and nome != PACOTE}


def violacoes(camada: str, alvos: list[str]) -> list[str]:
    """Devolve as regras quebradas por uma camada, dado o que ela importa."""
    problemas: list[str] = []
    for outra in sorted(camadas_internas(alvos) - PERMITIDAS[camada] - {camada}):
        problemas.append(f"importa a camada '{outra}', proibida para '{camada}'")
    externas = bibliotecas_externas(alvos)
    for biblioteca, onde in SO_EM.items():
        if biblioteca in externas and camada not in onde:
            permitido = ", ".join(sorted(onde))
            problemas.append(f"usa '{biblioteca}', permitido só em: {permitido}")
    if camada == "domain":
        for biblioteca in sorted(externas & PROIBIDAS_NO_DOMINIO):
            problemas.append(f"usa '{biblioteca}' no domínio (disco ou rede)")
    return problemas


def modulo_de(arquivo: Path) -> tuple[str, bool]:
    """Converte o caminho de um arquivo no nome do módulo e diz se é pacote."""
    partes = list(arquivo.relative_to(RAIZ.parent).with_suffix("").parts)
    eh_pacote = partes[-1] == "__init__"
    if eh_pacote:
        partes = partes[:-1]
    return ".".join(partes), eh_pacote


@pytest.mark.parametrize("camada", sorted(PERMITIDAS))
def test_camada_respeita_a_tabela_de_imports(camada: str) -> None:
    problemas: list[str] = []
    for arquivo in sorted((RAIZ / camada).rglob("*.py")):
        modulo, eh_pacote = modulo_de(arquivo)
        alvos = importacoes(arquivo.read_text(encoding="utf-8"), modulo, eh_pacote)
        for problema in violacoes(camada, alvos):
            problemas.append(f"{arquivo.relative_to(RAIZ)}: {problema}")
    assert not problemas, "\n".join(problemas)


def test_nenhuma_pasta_fica_fora_da_tabela() -> None:
    pastas = {p.name for p in RAIZ.iterdir() if p.is_dir() and p.name != "__pycache__"}
    assert pastas == set(PERMITIDAS)


# (camada, código, deve ser detectada alguma violação?)
CASOS: list[tuple[str, str, bool]] = [
    ("domain", "import numpy as np", False),
    ("domain", "from concrete_crack.infrastructure import leitor", True),
    ("domain", "from ..services import avaliar", True),
    ("domain", "from ..import ports", True),
    ("domain", "import torch", True),
    ("domain", "import matplotlib.pyplot as plt", True),
    ("domain", "from pathlib import Path", True),
    ("ports", "from ..domain import metricas", False),
    ("ports", "from ..infrastructure import frangi", True),
    ("services", "from ..ports import segmentador", False),
    ("services", "from ..infrastructure import frangi", True),
    ("services", "import pandas as pd", False),
    ("infrastructure", "import torch", False),
    ("infrastructure", "from ..services import avaliar", True),
    ("presentation", "from ..infrastructure import frangi", False),
    ("config", "from ..domain import metricas", True),
]


@pytest.mark.parametrize(("camada", "codigo", "deve_falhar"), CASOS)
def test_analisador_detecta_so_o_que_deve(
    camada: str, codigo: str, deve_falhar: bool
) -> None:
    alvos = importacoes(codigo, f"{PACOTE}.{camada}.exemplo", eh_pacote=False)
    assert bool(violacoes(camada, alvos)) is deve_falhar
