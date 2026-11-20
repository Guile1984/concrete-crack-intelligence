"""Regras pré-registradas do projeto, decididas antes de ver qualquer resultado."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegrasPreRegistradas:
    """Constantes decididas no Discovery e na arquitetura, antes dos resultados.

    Alterar qualquer valor exige editar ``tests/test_regras_pre_registradas.py``
    e registrar a decisão datada no NOTES.md.

    Attributes:
        proporcao_treino: Fração das imagens-mãe no conjunto de treino.
        proporcao_validacao: Fração das imagens-mãe na validação.
        proporcao_teste: Fração das imagens-mãe no teste.
        seed_split: Semente do embaralhamento dos grupos no split.
        max_experimentos_adicionais: Máximo de experimentos além da referência.
        n_seeds_por_configuracao: Repetições com seeds diferentes por configuração.
        teto_custo_usd: Teto de custo de GPU para o projeto inteiro.
        metrica_decisao: Métrica que decide o critério 1.
        metrica_candidatos_checkpoint: Métrica que seleciona os candidatos.
        n_candidatos_checkpoint: Quantos checkpoints candidatos são guardados.
        metrica_escolha_checkpoint: Métrica que escolhe o checkpoint final.
        avaliacoes_teste_por_conjunto: Quantas vezes cada conjunto de teste é usado.
        n_inspecao_mascaras: Quantas imagens do CCSD entram na inspeção das máscaras.
        limiar_reprovacao_mascaras: Número mínimo de imagens inadequadas na amostra
            que reprova as máscaras do CCSD (aciona a contingência R18).
        proporcao_relevante_mascaras: Fração de imagens inadequadas considerada
            relevante; a regra foi calibrada para detectá-la.
        seed_inspecao_mascaras: Semente do sorteio das imagens a inspecionar.
        limiares_binarizacao: Grade de limiares de desvio do fundo (1 a 255),
            em ordem crescente, em que se mede a área de fissura das máscaras.
        limiar_binarizacao: Desvio do fundo a partir do qual um pixel da máscara
            vira fissura no treino; metade do contraste total (255).
        limiar_patamar_baixo: Limiar baixo da faixa em que se testa o patamar
            da curva de área.
        limiar_patamar_alto: Limiar alto da mesma faixa.
        razao_minima_patamar: Razão mínima entre a área no limiar alto e no
            baixo para a binarização ser classificada como robusta.
        fracao_maxima_fissura_por_mascara: Fração de pixels de fissura, no
            limiar de binarização, acima da qual uma máscara entra na lista de
            anomalias (suspeita de polaridade ou limiar inadequado).
        fator_leitura_duplicatas: Redução das fotos na leitura para o hash de
            quase-duplicatas (a orientação EXIF é aplicada depois da leitura).
        lado_hash_duplicatas: Lado do dHash; cada direção (horizontal e
            vertical) gera lado x lado bits, num total de 2 x lado x lado.
        n_bases_controle_duplicatas: Quantas fotos servem de base para as
            duplicatas fabricadas do controle positivo.
        seed_controle_duplicatas: Semente do sorteio das bases e dos lados de
            recorte do controle positivo.
        qualidade_jpeg_controle: Qualidade da recompressão JPEG fabricada.
        fatores_brilho_controle: Fatores de brilho das variações fabricadas.
        recortes_controle: Frações recortadas de um lado nas variações.
        cobertura_limiar_duplicatas: Fração mínima das variações fabricadas
            reconhecidas no limiar; o limiar é o menor inteiro que a atinge.
        fracao_maxima_grupo_duplicatas: O hash é reprovado se o maior grupo
            tiver mais que esta fração das fotos.
        fracao_maxima_pares_duplicatas: O hash é reprovado se mais que esta
            fração dos pares de fotos reais ficar a distância <= limiar.
        modelo_embeddings: Nome do modelo do timm que gera os embeddings
            (DINOv2 ViT-S/14, pesos oficiais da Meta, licença Apache 2.0).
        lado_entrada_embeddings: Lado da imagem quadrada na entrada da rede;
            518 é a resolução nativa do modelo e precisa ser múltiplo do
            patch de 14 pixels.
        fator_leitura_embeddings: Redução das fotos na leitura para os
            embeddings, antes do redimensionamento para a entrada da rede.
        densidade_minima_serie: Densidade do maior grupo (ligações internas
            dividido pelos pares possíveis) a partir da qual ele é declarado
            série real; abaixo, corrente. Não muda a ação, só o que se declara.
        multiplos_faixas_vizinho: Limites das faixas de distância ao vizinho
            mais próximo, como múltiplos do limiar T (análise descritiva).
        multiplos_sensibilidade_limiar: Múltiplos de T em que se descreve como
            o agrupamento ficaria; nenhum deles é uma opção de limiar.
        multiplo_quase_ligadas: Uma foto é "quase ligada" se o vizinho mais
            próximo estiver acima de T e até este múltiplo de T.
        fracao_maxima_quase_ligadas: A limitação de T é declarada relevante se
            mais que esta fração das fotos estiver quase ligada. Não muda a
            decisão da A46, só o que se declara.
        lado_tile_nativo: Lado do tile quadrado na escala nativa, em pixels;
            múltiplo de 32 para caber nas reduções da U-Net.
        fator_escala_reduzida: Fator de redução da foto inteira na segunda
            escala (média de área), antes do recorte.
        lado_tile_reduzido: Lado do tile na escala reduzida; cobre a mesma
            área da foto que o tile nativo (lado nativo / fator), para que a
            comparação entre escalas mude só a resolução.
        regras_mascara_reduzida: Regras de volta ao binário da máscara
            reduzida que a medição descritiva compara: "maioria" (fração de
            fissura >= 0,5) e "qualquer" (fração > 0). A escolha é da Sprint
            4a, antes do experimento de resolução.
        cores_classes_s2ds: Cor RGB de cada classe nos rótulos do S2DS,
            identificada pelas contagens de imagens e pixels do treino
            publicadas no README (A58).
        classe_fissura_s2ds: Classe que vira fissura na binarização do S2DS;
            todas as outras viram fundo.
        alfa_rotulos_s2ds: Valor do canal alfa exigido em todo pixel dos
            rótulos do S2DS; outro valor faz a binarização recusar o rótulo.
        n_reamostragens_bootstrap: Reamostragens do bootstrap pareado que dá
            o intervalo de confiança das diferenças entre métodos (A62).
        nivel_confianca_bootstrap: Nível do intervalo percentil do bootstrap.
        seed_bootstrap: Semente das reamostragens do bootstrap.
        metodo_esqueleto: Método do ``skeletonize`` do scikit-image usado no
            clDice; fixado porque o padrão pode mudar entre versões.
        unidades_bootstrap: Unidade sorteada no bootstrap, por fonte: no CCSD,
            o grupo de quase-duplicatas (A49), para as fotos de um grupo
            entrarem juntas; no S2DS, a imagem (A61).
        beta_frangi: Parâmetro β do Frangi, que pune formas arredondadas
            (o valor do artigo original, A65).
        fracao_c_frangi: Fração do percentil de S que dá a constante c do
            Frangi: "metade", como no artigo original (A65).
        percentil_c_frangi: Percentil de S, normalizado por σ² e medido uma
            vez nas imagens de treino, que dá a constante c (A65).
        conectividade_componentes: Vizinhança da limpeza de componentes
            pequenos: 8, para não quebrar fissuras diagonais (A65).
        escalas_frangi: Oitavas σ, em pixels, cujos mapas o ajuste calcula
            uma vez por foto e por fundo (A66).
        faixas_escalas_frangi: Faixas de escalas da grade; o mapa de uma faixa
            é o máximo dos mapas das suas escalas.
        sigmas_fundo_frangi: σ do borrão do fundo na grade; 0 desliga a
            correção, e os outros valores têm pelo menos 4 vezes a maior
            escala, para o borrão não apagar a fissura larga.
        limiares_frangi: Limiares da grade, aplicados ao mapa em [0, 1].
        tamanhos_minimos_frangi: Tamanhos mínimos de componente da grade, em
            pixels; 0 desliga a limpeza.
        n_fotos_c_frangi: Fotos do treino sorteadas para calcular o c.
        n_pixels_c_frangi: Pixels sorteados por foto para o percentil do c.
        seed_c_frangi: Semente do sorteio das fotos e dos pixels do c.
    """

    proporcao_treino: float = 0.70
    proporcao_validacao: float = 0.15
    proporcao_teste: float = 0.15
    seed_split: int = 20261022
    max_experimentos_adicionais: int = 3
    n_seeds_por_configuracao: int = 3
    teto_custo_usd: float = 20.0
    metrica_decisao: str = "cldice"
    metrica_candidatos_checkpoint: str = "dice"
    n_candidatos_checkpoint: int = 3
    metrica_escolha_checkpoint: str = "cldice"
    avaliacoes_teste_por_conjunto: int = 1
    n_inspecao_mascaras: int = 40
    limiar_reprovacao_mascaras: int = 8
    proporcao_relevante_mascaras: float = 0.25
    seed_inspecao_mascaras: int = 20261022
    limiares_binarizacao: tuple[int, ...] = tuple(range(16, 256, 16))
    limiar_binarizacao: int = 128
    limiar_patamar_baixo: int = 64
    limiar_patamar_alto: int = 192
    razao_minima_patamar: float = 0.80
    fracao_maxima_fissura_por_mascara: float = 0.10
    fator_leitura_duplicatas: int = 8
    lado_hash_duplicatas: int = 8
    n_bases_controle_duplicatas: int = 40
    seed_controle_duplicatas: int = 20261106
    qualidade_jpeg_controle: int = 70
    fatores_brilho_controle: tuple[float, ...] = (0.85, 1.15)
    recortes_controle: tuple[float, ...] = (0.05, 0.10)
    cobertura_limiar_duplicatas: float = 0.95
    fracao_maxima_grupo_duplicatas: float = 0.10
    fracao_maxima_pares_duplicatas: float = 0.02
    modelo_embeddings: str = "vit_small_patch14_dinov2.lvd142m"
    lado_entrada_embeddings: int = 518
    fator_leitura_embeddings: int = 4
    densidade_minima_serie: float = 0.5
    multiplos_faixas_vizinho: tuple[float, ...] = (1.0, 2.0, 5.0, 10.0, 20.0)
    multiplos_sensibilidade_limiar: tuple[float, ...] = (2.0, 5.0)
    multiplo_quase_ligadas: float = 2.0
    fracao_maxima_quase_ligadas: float = 0.05
    lado_tile_nativo: int = 512
    fator_escala_reduzida: int = 2
    lado_tile_reduzido: int = 256
    regras_mascara_reduzida: tuple[str, ...] = ("maioria", "qualquer")
    cores_classes_s2ds: tuple[tuple[str, tuple[int, int, int]], ...] = (
        ("fundo", (0, 0, 0)),
        ("fissura", (255, 255, 255)),
        ("desplacamento", (255, 0, 0)),
        ("corrosao", (255, 255, 0)),
        ("eflorescencia", (0, 255, 255)),
        ("vegetacao", (0, 255, 0)),
        ("ponto_de_controle", (0, 0, 255)),
    )
    classe_fissura_s2ds: str = "fissura"
    alfa_rotulos_s2ds: int = 255
    n_reamostragens_bootstrap: int = 10_000
    nivel_confianca_bootstrap: float = 0.95
    seed_bootstrap: int = 20261117
    metodo_esqueleto: str = "zhang"
    unidades_bootstrap: tuple[tuple[str, str], ...] = (
        ("ccsd", "grupo"),
        ("s2ds", "imagem"),
    )
    beta_frangi: float = 0.5
    fracao_c_frangi: float = 0.5
    percentil_c_frangi: float = 99.0
    conectividade_componentes: int = 8
    escalas_frangi: tuple[float, ...] = (1.0, 2.0, 4.0, 8.0, 16.0)
    faixas_escalas_frangi: tuple[tuple[float, ...], ...] = (
        (1.0, 2.0, 4.0),
        (1.0, 2.0, 4.0, 8.0),
        (2.0, 4.0, 8.0, 16.0),
        (1.0, 2.0, 4.0, 8.0, 16.0),
    )
    sigmas_fundo_frangi: tuple[float, ...] = (0.0, 64.0)
    limiares_frangi: tuple[float, ...] = (
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
    tamanhos_minimos_frangi: tuple[int, ...] = (0, 100, 1000)
    n_fotos_c_frangi: int = 40
    n_pixels_c_frangi: int = 100_000
    seed_c_frangi: int = 20261120

    def __post_init__(self) -> None:
        """Recusa um split que não soma 1 e regras incoerentes entre si."""
        soma = self.proporcao_treino + self.proporcao_validacao + self.proporcao_teste
        if abs(soma - 1.0) > 1e-9:
            raise ValueError(f"As proporções do split somam {soma}, não 1.")
        if self.limiar_reprovacao_mascaras > self.n_inspecao_mascaras:
            raise ValueError("O limiar de reprovação excede o tamanho da amostra.")
        grade = self.limiares_binarizacao
        if (
            not grade
            or list(grade) != sorted(set(grade))
            or grade[0] < 1
            or grade[-1] > 255
        ):
            raise ValueError(
                "A grade de limiares deve ser crescente, sem repetição, de 1 a 255."
            )
        if self.limiar_binarizacao not in grade:
            raise ValueError("O limiar de binarização precisa estar na grade.")
        patamar = (self.limiar_patamar_baixo, self.limiar_patamar_alto)
        if not set(patamar) <= set(grade):
            raise ValueError("Os limiares do patamar precisam estar na grade.")
        if self.limiar_patamar_baixo >= self.limiar_patamar_alto:
            raise ValueError("O limiar baixo do patamar deve ser menor que o alto.")
        if not 0 < self.razao_minima_patamar <= 1:
            raise ValueError("A razão mínima do patamar deve estar em (0, 1].")
        if not 0 < self.fracao_maxima_fissura_por_mascara < 1:
            raise ValueError(
                "A fração máxima de fissura por máscara deve estar em (0, 1)."
            )
        self._validar_duplicatas()

    def _validar_duplicatas(self) -> None:
        """Recusa regras de quase-duplicatas fora dos intervalos válidos."""
        if self.fator_leitura_duplicatas < 1:
            raise ValueError("O fator de leitura das duplicatas deve ser >= 1.")
        if self.lado_hash_duplicatas < 2:
            raise ValueError("O lado do hash deve ser pelo menos 2.")
        if self.n_bases_controle_duplicatas < 1:
            raise ValueError("O controle positivo precisa de pelo menos 1 base.")
        if not 1 <= self.qualidade_jpeg_controle <= 95:
            raise ValueError("A qualidade JPEG do controle deve estar entre 1 e 95.")
        brilhos = self.fatores_brilho_controle
        if not brilhos or any(f <= 0 or f == 1 for f in brilhos):
            raise ValueError(
                "Os fatores de brilho devem ser positivos e diferentes de 1."
            )
        recortes = self.recortes_controle
        if not recortes or any(not 0 < r < 0.5 for r in recortes):
            raise ValueError("Os recortes devem estar em (0, 0,5).")
        if not 0 < self.cobertura_limiar_duplicatas <= 1:
            raise ValueError("A cobertura do limiar deve estar em (0, 1].")
        fracoes = (
            self.fracao_maxima_grupo_duplicatas,
            self.fracao_maxima_pares_duplicatas,
        )
        if any(not 0 < f < 1 for f in fracoes):
            raise ValueError(
                "As frações máximas de grupo e de pares devem estar em (0, 1)."
            )
        self._validar_embeddings()

    def _validar_embeddings(self) -> None:
        """Recusa regras de embeddings fora dos intervalos válidos."""
        if not self.modelo_embeddings.strip():
            raise ValueError("O nome do modelo de embeddings não pode ser vazio.")
        lado = self.lado_entrada_embeddings
        if lado < 14 or lado % 14 != 0:
            raise ValueError("O lado da entrada deve ser múltiplo de 14 (o patch).")
        if self.fator_leitura_embeddings < 1:
            raise ValueError("O fator de leitura dos embeddings deve ser >= 1.")
        if not 0 < self.densidade_minima_serie < 1:
            raise ValueError("A densidade mínima de série deve estar em (0, 1).")
        self._validar_vizinhos()

    def _validar_vizinhos(self) -> None:
        """Recusa regras da análise de vizinhos fora dos intervalos válidos."""
        faixas = self.multiplos_faixas_vizinho
        if not faixas or faixas[0] != 1.0 or list(faixas) != sorted(set(faixas)):
            raise ValueError(
                "As faixas de vizinho devem começar em 1 e ser crescentes."
            )
        sensibilidade = self.multiplos_sensibilidade_limiar
        if not sensibilidade or any(m <= 1 for m in sensibilidade):
            raise ValueError("Os múltiplos de sensibilidade devem ser maiores que 1.")
        if self.multiplo_quase_ligadas not in faixas[1:]:
            raise ValueError(
                "O múltiplo de quase ligadas deve ser uma das faixas acima de 1."
            )
        if not 0 < self.fracao_maxima_quase_ligadas < 1:
            raise ValueError("A fração máxima de quase ligadas deve estar em (0, 1).")
        self._validar_tiles()

    def _validar_tiles(self) -> None:
        """Recusa regras de tiles fora dos intervalos válidos."""
        for lado in (self.lado_tile_nativo, self.lado_tile_reduzido):
            if lado < 32 or lado % 32 != 0:
                raise ValueError("O lado do tile deve ser múltiplo de 32.")
        if self.fator_escala_reduzida < 2:
            raise ValueError("O fator da escala reduzida deve ser >= 2.")
        if (
            self.lado_tile_reduzido * self.fator_escala_reduzida
            != self.lado_tile_nativo
        ):
            raise ValueError(
                "O tile reduzido deve cobrir a mesma área da foto que o nativo."
            )
        regras = self.regras_mascara_reduzida
        validas = {"maioria", "qualquer", "suave"}
        if not regras or len(set(regras)) != len(regras) or not set(regras) <= validas:
            raise ValueError(
                "As regras da máscara reduzida devem ser distintas, entre "
                "maioria, qualquer e suave."
            )
        self._validar_s2ds()

    def _validar_s2ds(self) -> None:
        """Recusa um mapa de cores do S2DS ambíguo ou incompleto."""
        nomes = [nome for nome, _ in self.cores_classes_s2ds]
        cores = [cor for _, cor in self.cores_classes_s2ds]
        if len(set(nomes)) != len(nomes) or len(set(cores)) != len(cores):
            raise ValueError("As classes e as cores do S2DS devem ser distintas.")
        if any(not 0 <= canal <= 255 for cor in cores for canal in cor):
            raise ValueError("Os canais das cores do S2DS devem estar em [0, 255].")
        if self.classe_fissura_s2ds not in nomes:
            raise ValueError("A classe de fissura do S2DS deve estar no mapa.")
        if not 0 <= self.alfa_rotulos_s2ds <= 255:
            raise ValueError("O alfa dos rótulos do S2DS deve estar em [0, 255].")
        self._validar_metricas()

    def _validar_metricas(self) -> None:
        """Recusa regras de métricas e de bootstrap fora dos valores válidos."""
        if self.n_reamostragens_bootstrap < 1000:
            raise ValueError("O bootstrap precisa de pelo menos 1000 reamostragens.")
        if not 0 < self.nivel_confianca_bootstrap < 1:
            raise ValueError("O nível de confiança deve estar em (0, 1).")
        if self.metodo_esqueleto not in {"zhang", "lee"}:
            raise ValueError("O método do esqueleto deve ser zhang ou lee.")
        fontes = [fonte for fonte, _ in self.unidades_bootstrap]
        unidades = {unidade for _, unidade in self.unidades_bootstrap}
        if (
            not fontes
            or len(set(fontes)) != len(fontes)
            or not unidades <= {"grupo", "imagem"}
        ):
            raise ValueError(
                "As unidades do bootstrap devem ter fontes distintas e ser "
                "grupo ou imagem."
            )
        self._validar_frangi()

    def _validar_frangi(self) -> None:
        """Recusa regras do Frangi e da limpeza fora dos valores válidos."""
        if self.beta_frangi <= 0:
            raise ValueError("O β do Frangi deve ser positivo.")
        if not 0 < self.fracao_c_frangi <= 1:
            raise ValueError("A fração do c do Frangi deve estar em (0, 1].")
        if not 0 < self.percentil_c_frangi <= 100:
            raise ValueError("O percentil do c do Frangi deve estar em (0, 100].")
        if self.conectividade_componentes not in {4, 8}:
            raise ValueError("A conectividade dos componentes deve ser 4 ou 8.")
        self._validar_grade_frangi()

    def _validar_grade_frangi(self) -> None:
        """Recusa uma grade do Frangi mal formada."""

        def crescente(valores: tuple[float, ...]) -> bool:
            """Diz se os valores são não vazios, crescentes e sem repetição."""
            return bool(valores) and list(valores) == sorted(set(valores))

        escalas = self.escalas_frangi
        if not crescente(escalas) or escalas[0] <= 0:
            raise ValueError("As escalas devem ser positivas e crescentes.")
        faixas = self.faixas_escalas_frangi
        if (
            not faixas
            or len(set(faixas)) != len(faixas)
            or any(not crescente(f) or not set(f) <= set(escalas) for f in faixas)
        ):
            raise ValueError(
                "As faixas devem ser distintas, crescentes e feitas das escalas."
            )
        fundos = self.sigmas_fundo_frangi
        if not crescente(fundos) or any(
            0 < f < 4 * escalas[-1] or f < 0 for f in fundos
        ):
            raise ValueError(
                "Os σ do fundo devem ser crescentes e 0 ou pelo menos 4 vezes "
                "a maior escala."
            )
        limiares = self.limiares_frangi
        if not crescente(limiares) or limiares[0] <= 0 or limiares[-1] >= 1:
            raise ValueError("Os limiares devem ser crescentes e estar em (0, 1).")
        tamanhos = self.tamanhos_minimos_frangi
        if not crescente(tamanhos) or tamanhos[0] < 0:
            raise ValueError("Os tamanhos mínimos devem ser crescentes e >= 0.")
        if self.n_fotos_c_frangi < 1 or self.n_pixels_c_frangi < 1:
            raise ValueError("A amostra do c precisa de fotos e pixels.")


REGRAS = RegrasPreRegistradas()
