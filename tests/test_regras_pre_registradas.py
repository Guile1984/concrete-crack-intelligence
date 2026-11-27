"""Trava das regras pré-registradas: mudar um valor exige editar este teste."""

from dataclasses import FrozenInstanceError, replace

import pytest

from concrete_crack.config.regras import REGRAS


def test_split_70_15_15() -> None:
    assert REGRAS.proporcao_treino == 0.70
    assert REGRAS.proporcao_validacao == 0.15
    assert REGRAS.proporcao_teste == 0.15


def test_seed_do_split_fixa() -> None:
    assert REGRAS.seed_split == 20261022


def test_no_maximo_tres_experimentos_adicionais() -> None:
    assert REGRAS.max_experimentos_adicionais == 3


def test_tres_seeds_por_configuracao() -> None:
    assert REGRAS.n_seeds_por_configuracao == 3


def test_teto_de_custo_de_20_dolares() -> None:
    assert REGRAS.teto_custo_usd == 20.0


def test_cldice_decide_o_criterio_1() -> None:
    assert REGRAS.metrica_decisao == "cldice"


def test_checkpoints_candidatos_por_dice_e_escolha_final_por_cldice() -> None:
    assert REGRAS.metrica_candidatos_checkpoint == "dice"
    assert REGRAS.n_candidatos_checkpoint == 3
    assert REGRAS.metrica_escolha_checkpoint == "cldice"


def test_cada_conjunto_de_teste_e_avaliado_uma_vez() -> None:
    assert REGRAS.avaliacoes_teste_por_conjunto == 1


def test_regras_sao_imutaveis() -> None:
    with pytest.raises(FrozenInstanceError):
        REGRAS.seed_split = 1


def test_proporcoes_que_nao_somam_um_sao_recusadas() -> None:
    with pytest.raises(ValueError, match="somam"):
        replace(REGRAS, proporcao_teste=0.20)


def test_inspecao_de_40_mascaras_com_seed_fixa() -> None:
    assert REGRAS.n_inspecao_mascaras == 40
    assert REGRAS.seed_inspecao_mascaras == 20261022


def test_mascaras_reprovadas_com_oito_ou_mais_inadequadas() -> None:
    assert REGRAS.limiar_reprovacao_mascaras == 8
    assert REGRAS.proporcao_relevante_mascaras == 0.25


def test_limiar_maior_que_a_amostra_e_recusado() -> None:
    with pytest.raises(ValueError, match="limiar"):
        replace(REGRAS, limiar_reprovacao_mascaras=41)


def test_binarizacao_no_meio_do_contraste_com_grade_de_16_em_16() -> None:
    assert REGRAS.limiares_binarizacao == tuple(range(16, 256, 16))
    assert REGRAS.limiar_binarizacao == 128


def test_patamar_entre_64_e_192_com_razao_minima_de_80_por_cento() -> None:
    assert REGRAS.limiar_patamar_baixo == 64
    assert REGRAS.limiar_patamar_alto == 192
    assert REGRAS.razao_minima_patamar == 0.80


def test_mascara_com_mais_de_10_por_cento_de_fissura_e_anomalia() -> None:
    assert REGRAS.fracao_maxima_fissura_por_mascara == 0.10


@pytest.mark.parametrize("grade", [(), (32, 16), (16, 16), (0, 128), (128, 256)])
def test_grade_invalida_e_recusada(grade: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="grade"):
        replace(REGRAS, limiares_binarizacao=grade)


def test_limiar_de_binarizacao_fora_da_grade_e_recusado() -> None:
    with pytest.raises(ValueError, match="binarização"):
        replace(REGRAS, limiar_binarizacao=100)


def test_patamar_invertido_ou_fora_da_grade_e_recusado() -> None:
    with pytest.raises(ValueError, match="patamar"):
        replace(REGRAS, limiar_patamar_baixo=192, limiar_patamar_alto=64)
    with pytest.raises(ValueError, match="patamar"):
        replace(REGRAS, limiar_patamar_alto=200)


@pytest.mark.parametrize("razao", [0.0, 1.5])
def test_razao_do_patamar_fora_do_intervalo_e_recusada(razao: float) -> None:
    with pytest.raises(ValueError, match="razão"):
        replace(REGRAS, razao_minima_patamar=razao)


@pytest.mark.parametrize("fracao", [0.0, 1.0])
def test_fracao_maxima_de_fissura_fora_do_intervalo_e_recusada(
    fracao: float,
) -> None:
    with pytest.raises(ValueError, match="fração"):
        replace(REGRAS, fracao_maxima_fissura_por_mascara=fracao)


def test_dhash_duplo_de_128_bits_com_leitura_reduzida_em_8() -> None:
    assert REGRAS.fator_leitura_duplicatas == 8
    assert REGRAS.lado_hash_duplicatas == 8


def test_controle_positivo_com_40_bases_e_seed_fixa() -> None:
    assert REGRAS.n_bases_controle_duplicatas == 40
    assert REGRAS.seed_controle_duplicatas == 20261106


def test_variacoes_fabricadas_do_controle_positivo() -> None:
    assert REGRAS.qualidade_jpeg_controle == 70
    assert REGRAS.fatores_brilho_controle == (0.85, 1.15)
    assert REGRAS.recortes_controle == (0.05, 0.10)


def test_limiar_reconhece_95_por_cento_das_variacoes() -> None:
    assert REGRAS.cobertura_limiar_duplicatas == 0.95


def test_hash_reprovado_com_grupo_acima_de_10_ou_pares_acima_de_2_por_cento() -> None:
    assert REGRAS.fracao_maxima_grupo_duplicatas == 0.10
    assert REGRAS.fracao_maxima_pares_duplicatas == 0.02


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("fator_leitura_duplicatas", 0, "fator de leitura"),
        ("lado_hash_duplicatas", 1, "lado do hash"),
        ("n_bases_controle_duplicatas", 0, "base"),
        ("qualidade_jpeg_controle", 0, "qualidade"),
        ("qualidade_jpeg_controle", 96, "qualidade"),
        ("fatores_brilho_controle", (), "brilho"),
        ("fatores_brilho_controle", (1.0,), "brilho"),
        ("fatores_brilho_controle", (0.0,), "brilho"),
        ("recortes_controle", (), "recortes"),
        ("recortes_controle", (0.5,), "recortes"),
        ("recortes_controle", (0.0,), "recortes"),
        ("cobertura_limiar_duplicatas", 0.0, "cobertura"),
        ("cobertura_limiar_duplicatas", 1.5, "cobertura"),
        ("fracao_maxima_grupo_duplicatas", 1.0, "grupo"),
        ("fracao_maxima_pares_duplicatas", 0.0, "pares"),
    ],
)
def test_regras_de_duplicatas_invalidas_sao_recusadas(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGRAS, **{campo: valor})


def test_embeddings_dinov2_vit_s14_em_518_com_leitura_reduzida_em_4() -> None:
    assert REGRAS.modelo_embeddings == "vit_small_patch14_dinov2.lvd142m"
    assert REGRAS.lado_entrada_embeddings == 518
    assert REGRAS.fator_leitura_embeddings == 4


def test_grupo_com_densidade_de_50_por_cento_ou_mais_e_serie_real() -> None:
    assert REGRAS.densidade_minima_serie == 0.5


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("modelo_embeddings", " ", "modelo"),
        ("lado_entrada_embeddings", 0, "múltiplo de 14"),
        ("lado_entrada_embeddings", 520, "múltiplo de 14"),
        ("fator_leitura_embeddings", 0, "fator de leitura"),
        ("densidade_minima_serie", 0.0, "densidade"),
        ("densidade_minima_serie", 1.0, "densidade"),
    ],
)
def test_regras_de_embeddings_invalidas_sao_recusadas(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGRAS, **{campo: valor})


def test_faixas_de_vizinho_em_1_2_5_10_e_20_vezes_t() -> None:
    assert REGRAS.multiplos_faixas_vizinho == (1.0, 2.0, 5.0, 10.0, 20.0)
    assert REGRAS.multiplos_sensibilidade_limiar == (2.0, 5.0)


def test_limitacao_relevante_com_mais_de_5_por_cento_ate_2t() -> None:
    assert REGRAS.multiplo_quase_ligadas == 2.0
    assert REGRAS.fracao_maxima_quase_ligadas == 0.05


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("multiplos_faixas_vizinho", (), "faixas"),
        ("multiplos_faixas_vizinho", (2.0, 5.0), "faixas"),
        ("multiplos_faixas_vizinho", (1.0, 5.0, 2.0), "faixas"),
        ("multiplos_sensibilidade_limiar", (), "sensibilidade"),
        ("multiplos_sensibilidade_limiar", (1.0,), "sensibilidade"),
        ("multiplo_quase_ligadas", 3.0, "quase ligadas"),
        ("multiplo_quase_ligadas", 1.0, "quase ligadas"),
        ("fracao_maxima_quase_ligadas", 0.0, "quase ligadas"),
        ("fracao_maxima_quase_ligadas", 1.0, "quase ligadas"),
    ],
)
def test_regras_da_analise_de_vizinhos_invalidas_sao_recusadas(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGRAS, **{campo: valor})


def test_tiles_de_512_na_escala_nativa_e_256_na_reduzida_2x() -> None:
    assert REGRAS.lado_tile_nativo == 512
    assert REGRAS.fator_escala_reduzida == 2
    assert REGRAS.lado_tile_reduzido == 256


def test_mede_as_regras_maioria_e_qualquer_da_mascara_reduzida() -> None:
    assert REGRAS.regras_mascara_reduzida == ("maioria", "qualquer")


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("lado_tile_nativo", 500, "múltiplo de 32"),
        ("lado_tile_reduzido", 128, "mesma área"),
        ("fator_escala_reduzida", 1, "fator"),
        ("regras_mascara_reduzida", (), "regras da máscara"),
        ("regras_mascara_reduzida", ("maioria", "maioria"), "regras da máscara"),
        ("regras_mascara_reduzida", ("media",), "regras da máscara"),
    ],
)
def test_regras_de_tiles_invalidas_sao_recusadas(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGRAS, **{campo: valor})


def test_cores_do_s2ds_identificadas_pelas_contagens_do_treino() -> None:
    assert dict(REGRAS.cores_classes_s2ds) == {
        "fundo": (0, 0, 0),
        "fissura": (255, 255, 255),
        "desplacamento": (255, 0, 0),
        "corrosao": (255, 255, 0),
        "eflorescencia": (0, 255, 255),
        "vegetacao": (0, 255, 0),
        "ponto_de_controle": (0, 0, 255),
    }


def test_fissura_do_s2ds_e_o_branco_e_o_alfa_e_255() -> None:
    assert REGRAS.classe_fissura_s2ds == "fissura"
    assert dict(REGRAS.cores_classes_s2ds)["fissura"] == (255, 255, 255)
    assert REGRAS.alfa_rotulos_s2ds == 255


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("cores_classes_s2ds", (("a", (0, 0, 0)), ("b", (0, 0, 0))), "distintas"),
        ("cores_classes_s2ds", (("a", (0, 0, 0)), ("a", (1, 1, 1))), "distintas"),
        ("cores_classes_s2ds", (("fissura", (256, 0, 0)),), "canais"),
        ("classe_fissura_s2ds", "rachadura", "classe de fissura"),
        ("alfa_rotulos_s2ds", 300, "alfa"),
    ],
)
def test_regras_do_s2ds_invalidas_sao_recusadas(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGRAS, **{campo: valor})


def test_bootstrap_com_10000_reamostragens_e_intervalo_de_95_por_cento() -> None:
    assert REGRAS.n_reamostragens_bootstrap == 10_000
    assert REGRAS.nivel_confianca_bootstrap == 0.95


def test_seed_do_bootstrap_fixa_e_propria() -> None:
    assert REGRAS.seed_bootstrap == 20261117
    assert REGRAS.seed_bootstrap != REGRAS.seed_split


def test_esqueleto_do_cldice_pelo_metodo_de_zhang() -> None:
    assert REGRAS.metodo_esqueleto == "zhang"


def test_bootstrap_sorteia_grupos_no_ccsd_e_imagens_no_s2ds() -> None:
    assert dict(REGRAS.unidades_bootstrap) == {"ccsd": "grupo", "s2ds": "imagem"}


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("n_reamostragens_bootstrap", 999, "reamostragens"),
        ("nivel_confianca_bootstrap", 0.0, "nível"),
        ("nivel_confianca_bootstrap", 1.0, "nível"),
        ("metodo_esqueleto", "medial", "esqueleto"),
        ("unidades_bootstrap", (("ccsd", "grupo"), ("ccsd", "imagem")), "unidades"),
        ("unidades_bootstrap", (("ccsd", "foto"),), "unidades"),
    ],
)
def test_regras_de_metricas_invalidas_sao_recusadas(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGRAS, **{campo: valor})


def test_frangi_com_beta_de_meio_e_c_pela_metade_do_percentil_99() -> None:
    assert REGRAS.beta_frangi == 0.5
    assert (REGRAS.fracao_c_frangi, REGRAS.percentil_c_frangi) == (0.5, 99.0)


def test_limpeza_de_componentes_com_vizinhanca_de_8() -> None:
    assert REGRAS.conectividade_componentes == 8


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("beta_frangi", 0.0, "β"),
        ("fracao_c_frangi", 0.0, "fração"),
        ("fracao_c_frangi", 1.5, "fração"),
        ("percentil_c_frangi", 0.0, "percentil"),
        ("percentil_c_frangi", 101.0, "percentil"),
        ("conectividade_componentes", 6, "conectividade"),
    ],
)
def test_regras_do_frangi_invalidas_sao_recusadas(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGRAS, **{campo: valor})


def test_grade_do_frangi_com_oitavas_e_quatro_faixas() -> None:
    assert REGRAS.escalas_frangi == (1.0, 2.0, 4.0, 8.0, 16.0)
    assert REGRAS.faixas_escalas_frangi == (
        (1.0, 2.0, 4.0),
        (1.0, 2.0, 4.0, 8.0),
        (2.0, 4.0, 8.0, 16.0),
        (1.0, 2.0, 4.0, 8.0, 16.0),
    )


def test_grade_do_frangi_com_fundo_limiares_e_tamanhos() -> None:
    assert REGRAS.sigmas_fundo_frangi == (0.0, 64.0)
    assert REGRAS.limiares_frangi == (
        0.05,
        0.15,
        0.25,
        0.35,
        0.45,
        0.55,
        0.65,
        0.75,
        0.85,
        0.95,
    )
    assert REGRAS.tamanhos_minimos_frangi == (0, 100, 1000)


def test_grade_do_frangi_tem_240_configuracoes() -> None:
    tamanho = (
        len(REGRAS.faixas_escalas_frangi)
        * len(REGRAS.sigmas_fundo_frangi)
        * len(REGRAS.limiares_frangi)
        * len(REGRAS.tamanhos_minimos_frangi)
    )
    assert tamanho == 240


def test_c_do_frangi_com_40_fotos_e_100_mil_pixels_e_seed_propria() -> None:
    assert (REGRAS.n_fotos_c_frangi, REGRAS.n_pixels_c_frangi) == (40, 100_000)
    assert REGRAS.seed_c_frangi == 20261120
    outras = {REGRAS.seed_split, REGRAS.seed_bootstrap, REGRAS.seed_controle_duplicatas}
    assert REGRAS.seed_c_frangi not in outras


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("escalas_frangi", (2.0, 1.0), "escalas"),
        ("faixas_escalas_frangi", ((1.0, 3.0),), "faixas"),
        ("faixas_escalas_frangi", ((1.0, 2.0), (1.0, 2.0)), "faixas"),
        ("sigmas_fundo_frangi", (0.0, 32.0), "fundo"),
        ("limiares_frangi", (0.5, 0.05), "limiares"),
        ("limiares_frangi", (0.0, 0.5), "limiares"),
        ("tamanhos_minimos_frangi", (100, 0), "tamanhos"),
        ("n_pixels_c_frangi", 0, "amostra"),
    ],
)
def test_grade_do_frangi_invalida_e_recusada(
    campo: str, valor: object, trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGRAS, **{campo: valor})


def test_unet_com_encoder_resnet18_e_pesos_do_imagenet() -> None:
    assert REGRAS.encoder_unet == "resnet18"
    assert REGRAS.pesos_encoder_unet == "IMAGENET1K_V1"


def test_decoder_com_cinco_blocos_e_subida_por_vizinho_mais_proximo() -> None:
    assert REGRAS.canais_decoder_unet == (256, 128, 64, 32, 16)
    assert REGRAS.modo_subida_unet == "nearest"


def test_normalizacao_do_imagenet() -> None:
    assert REGRAS.media_normalizacao == (0.485, 0.456, 0.406)
    assert REGRAS.desvio_normalizacao == (0.229, 0.224, 0.225)


def test_fator_de_reducao_casa_com_o_decoder_e_com_os_tiles() -> None:
    assert REGRAS.fator_reducao_unet == 32 == 2 ** len(REGRAS.canais_decoder_unet)
    assert REGRAS.lado_tile_nativo // REGRAS.fator_reducao_unet == 16
    assert REGRAS.lado_tile_reduzido // REGRAS.fator_reducao_unet == 8


@pytest.mark.parametrize(
    ("mudancas", "trecho"),
    [
        ({"encoder_unet": "resnet34"}, "encoder"),
        ({"pesos_encoder_unet": "IMAGENET1K_V2"}, "pesos"),
        ({"canais_decoder_unet": (16, 32, 64, 128, 256)}, "canais"),
        ({"canais_decoder_unet": (256, 128, 64, 32, 0)}, "canais"),
        ({"canais_decoder_unet": (256, 128, 64, 32)}, "fator"),
        (
            {
                "canais_decoder_unet": (4096, 2048, 1024, 512, 256, 128, 64, 32, 16),
                "fator_reducao_unet": 512,
            },
            "múltiplos",
        ),
        ({"modo_subida_unet": "bilinear"}, "subida"),
        ({"media_normalizacao": (0.485, 0.456)}, "normalização"),
        ({"desvio_normalizacao": (0.229, 0.0, 0.225)}, "normalização"),
    ],
)
def test_arquitetura_da_unet_invalida_e_recusada(
    mudancas: dict[str, object], trecho: str
) -> None:
    with pytest.raises(ValueError, match=trecho):
        replace(REGRAS, **mudancas)
