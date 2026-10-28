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

    def __post_init__(self) -> None:
        """Recusa um split que não soma 1 e um limiar maior que a amostra."""
        soma = self.proporcao_treino + self.proporcao_validacao + self.proporcao_teste
        if abs(soma - 1.0) > 1e-9:
            raise ValueError(f"As proporções do split somam {soma}, não 1.")
        if self.limiar_reprovacao_mascaras > self.n_inspecao_mascaras:
            raise ValueError("O limiar de reprovação excede o tamanho da amostra.")


REGRAS = RegrasPreRegistradas()
