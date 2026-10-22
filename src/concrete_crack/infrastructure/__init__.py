"""Adaptadores concretos: leitores de dataset, Frangi, U-Net e registro.

Implementa os contratos de ``ports``. Concentra o acesso a dados em disco, à
rede e ao PyTorch. Pode importar ``ports``, ``domain`` e ``config``; nunca
``services`` nem ``presentation``.
"""
