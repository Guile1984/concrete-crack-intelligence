"""Ficha de procedência de um dataset (regra 8.2 do prompt)."""

from dataclasses import dataclass
from datetime import date

PAPEIS_VALIDOS = frozenset({"primario", "externo", "condicional"})


@dataclass(frozen=True, slots=True)
class FonteDados:
    """Ficha de procedência de um dataset.

    Um dataset sem procedência rastreável não entra no projeto: a criação da
    ficha recusa campos de rastreabilidade vazios.

    Attributes:
        id: Identificador curto, em minúsculas e sem espaços (por exemplo ccsd).
        nome: Nome oficial do dataset.
        versao: Versão declarada pela fonte, ou "nao declarada".
        papel: "primario", "externo" ou "condicional".
        autores: Autores, na ordem da publicação.
        publicacao: Citação da publicação ou do depósito dos dados.
        url: Endereço da fonte original.
        doi: DOI, quando existir.
        licenca: Licença ou termos de uso, como declarados pela fonte.
        licenca_permite_redistribuir: Se a licença permite redistribuir os dados.
        exige_aceite_termos: Se o uso exige leitura e aceite de termos.
        data_consulta: Data (AAAA-MM-DD) em que a fonte foi consultada.
        finalidade_original: Para que o dataset foi criado.
        n_imagens: Número de imagens declarado pela fonte.
        resolucao: Resolução declarada, ou "a medir".
        anotacoes: Estrutura das anotações.
        observacoes: Divergências e ressalvas registradas.
        transformacoes_do_projeto: Transformações que o projeto aplicou.
    """

    id: str
    nome: str
    versao: str
    papel: str
    autores: tuple[str, ...]
    publicacao: str
    url: str
    doi: str | None
    licenca: str
    licenca_permite_redistribuir: bool
    exige_aceite_termos: bool
    data_consulta: str
    finalidade_original: str
    n_imagens: int
    resolucao: str
    anotacoes: str
    observacoes: tuple[str, ...] = ()
    transformacoes_do_projeto: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Recusa fichas sem rastreabilidade ou mal formadas."""
        obrigatorios = {
            "id": self.id,
            "nome": self.nome,
            "versao": self.versao,
            "publicacao": self.publicacao,
            "url": self.url,
            "licenca": self.licenca,
            "finalidade_original": self.finalidade_original,
            "resolucao": self.resolucao,
            "anotacoes": self.anotacoes,
        }
        vazios = [campo for campo, valor in obrigatorios.items() if not valor.strip()]
        if vazios:
            raise ValueError(f"Campos obrigatórios vazios: {', '.join(vazios)}")
        if self.id != self.id.lower() or " " in self.id:
            raise ValueError("O id deve ser minúsculo e sem espaços.")
        if self.papel not in PAPEIS_VALIDOS:
            raise ValueError(f"Papel inválido: {self.papel}")
        if not self.autores or not all(autor.strip() for autor in self.autores):
            raise ValueError("A ficha precisa de ao menos um autor.")
        if not self.url.startswith("https://"):
            raise ValueError("A URL da fonte deve começar com https://.")
        if self.n_imagens <= 0:
            raise ValueError("n_imagens deve ser positivo.")
        try:
            date.fromisoformat(self.data_consulta)
        except ValueError as erro:
            raise ValueError(
                "data_consulta deve estar no formato AAAA-MM-DD."
            ) from erro
