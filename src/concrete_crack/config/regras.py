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


REGRAS = RegrasPreRegistradas()
