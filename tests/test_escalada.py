"""Testes da árvore de decisão da escalada para embeddings (A45)."""

from concrete_crack.domain.duplicatas import Agrupamento, AvaliacaoHash
from concrete_crack.domain.escalada import Desfecho, decidir_escalada


def agrupamento_com(maior: int, n: int = 458) -> Agrupamento:
    grupos = (tuple(range(maior)), *((i,) for i in range(maior, n)))
    return Agrupamento(grupos, 0, n * (n - 1) // 2)


def decidir(grande: bool, pares: bool, maior: int, densidade: float = 0.03):
    return decidir_escalada(
        AvaliacaoHash(grande, pares), agrupamento_com(maior), densidade, 0.70, 0.5
    )


def test_sem_reprovacao_os_embeddings_sao_aprovados() -> None:
    decisao = decidir(False, False, 20)
    assert decisao.desfecho is Desfecho.APROVADO
    assert decisao.serie_real is None


def test_pares_demais_voltam_ao_dhash_mesmo_com_grupo_grande() -> None:
    assert decidir(False, True, 20).desfecho is Desfecho.VOLTAR_AO_DHASH
    decisao = decidir(True, True, 400)
    assert decisao.desfecho is Desfecho.VOLTAR_AO_DHASH
    assert decisao.serie_real is None


def test_grupo_grande_que_cabe_vai_para_o_treino_como_corrente() -> None:
    decisao = decidir(True, False, 136, densidade=0.03)
    assert decisao.desfecho is Desfecho.GRUPO_NO_TREINO
    assert decisao.serie_real is False


def test_grupo_grande_denso_e_declarado_serie_real() -> None:
    decisao = decidir(True, False, 60, densidade=0.5)
    assert decisao.desfecho is Desfecho.GRUPO_NO_TREINO
    assert decisao.serie_real is True


def test_grupo_de_320_em_458_ainda_cabe_e_de_321_nao() -> None:
    # 70% de 458 = 320,6
    assert decidir(True, False, 320).desfecho is Desfecho.GRUPO_NO_TREINO
    decisao = decidir(True, False, 321)
    assert decisao.desfecho is Desfecho.TESTE_EXTERNO
    assert decisao.serie_real is False
