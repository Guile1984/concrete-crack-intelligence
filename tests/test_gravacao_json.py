"""Testes da gravação de registros em JSON e em JSON Lines."""

import json
from pathlib import Path

from concrete_crack.infrastructure.registro_json import (
    gravar_json,
    gravar_jsonl,
    ler_jsonl,
)


def test_json_com_indentacao_lf_e_quebra_final(tmp_path: Path) -> None:
    destino = tmp_path / "experiments" / "a.json"
    gravar_json({"c": 0.05, "nome": "fissura"}, destino)
    bruto = destino.read_bytes()
    assert bruto == b'{\n  "c": 0.05,\n  "nome": "fissura"\n}\n'
    assert json.loads(bruto) == {"c": 0.05, "nome": "fissura"}


def test_jsonl_tem_um_objeto_por_linha(tmp_path: Path) -> None:
    destino = tmp_path / "b.jsonl"
    linhas = [{"faixa": [1.0, 2.0], "valor": None}, {"faixa": [4.0], "valor": 0.5}]
    gravar_jsonl(linhas, destino)
    assert destino.read_text(encoding="utf-8").count("\n") == 2
    assert ler_jsonl(destino) == linhas


def test_acentos_sao_gravados_como_texto(tmp_path: Path) -> None:
    destino = tmp_path / "c.json"
    gravar_json({"metrica": "média"}, destino)
    assert "média" in destino.read_text(encoding="utf-8")
