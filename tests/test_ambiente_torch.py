"""Teste de ambiente do PyTorch: roda só na job dl do CI (marcador torch)."""

import pytest


@pytest.mark.torch
def test_torch_instalado_e_funciona_em_cpu() -> None:
    import torch

    x = torch.ones(2, 3)
    assert x.sum().item() == 6.0
    assert x.device.type == "cpu"
