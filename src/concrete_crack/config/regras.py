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
    """

    proporcao_treino: float = 0.70
    proporcao_validacao: float = 0.15
    proporcao_teste: float = 0.15
    seed_split: int = 20261022
    max_experimentos_adicionais: int = 4
    n_seeds_por_configuracao: int = 3
    teto_custo_usd: float = 20.0
    metrica_decisao: str = "cldice"
    metrica_candidatos_checkpoint: str = "dice"
    n_candidatos_checkpoint: int = 3
    metrica_escolha_checkpoint: str = "cldice"
    avaliacoes_teste_por_conjunto: int = 1

    def __post_init__(self) -> None:
        """Recusa um split cujas proporções não somam 1."""
        soma = self.proporcao_treino + self.proporcao_validacao + self.proporcao_teste
        if abs(soma - 1.0) > 1e-9:
            raise ValueError(f"As proporções do split somam {soma}, não 1.")


REGRAS = RegrasPreRegistradas()
