# concrete-crack-intelligence

[![CI](https://github.com/Guile1984/concrete-crack-intelligence/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Guile1984/concrete-crack-intelligence/actions/workflows/ci.yml)

Segmentação de fissuras visíveis em superfícies de concreto: um baseline clássico
não neural (filtro de Frangi) contra uma rede U-Net, com rigor experimental
(split por imagem-mãe, métricas que não se deixam enganar pela espessura da máscara,
teste externo e regras decididas antes de ver resultados).

> **Estado:** em desenvolvimento. A Sprint 0 (fundação) está concluída.
> **Não existe nenhum resultado experimental ainda.** Este README será reescrito na
> Sprint 7, com os resultados e com cada limitação acompanhada da sua magnitude medida.

## Pergunta de pesquisa

Até que ponto uma rede de segmentação supera um método clássico não neural na
delimitação de fissuras visíveis na resolução da imagem; quanto desse desempenho se
mantém em um dataset de origem diferente; e quais descritores geométricos em pixels
permanecem estáveis o suficiente para serem reportados?

O projeto termina quando estas perguntas tiverem resposta com evidência. Responder
"não" ou "inconclusivo" é um resultado completo.

1. A rede supera o baseline clássico? (métrica de decisão: clDice, com intervalo de
   confiança da diferença pareada por imagem-mãe)
2. Quanto do desempenho sobrevive fora do domínio de treinamento?
3. Que descritores geométricos os dados suportam?

## O que este projeto não é

- Não analisa condição estrutural: analisa manifestações visuais.
- Segmentação não equivale a diagnóstico; ausência de fissura detectada não prova
  ausência de dano, e presença detectada não determina gravidade.
- Medidas em pixels não representam dimensões físicas sem calibração.
- As métricas valem para os datasets avaliados, e a generalização é limitada pelos dados.
- Finalidade acadêmica e de portfólio. Não substitui inspeção profissional, não
  constitui laudo nem parecer técnico e não deve ser usado isoladamente em decisões
  de segurança.

As magnitudes destas limitações serão medidas e publicadas na Sprint 7.

## Como o projeto é conduzido

- [`DISCOVERY.md`](DISCOVERY.md): problema, datasets, baseline, estratégia experimental,
  computação, riscos e orçamento de sprints (congelado).
- [`ARQUITETURA.md`](ARQUITETURA.md): camadas, diretórios, stack, testes, CI, pipeline e
  plano de sprints.
- [`NOTES.md`](NOTES.md): diário de decisões datadas, falhas provocadas, pendências e
  limitações.

O código tem seis camadas (`domain`, `ports`, `infrastructure`, `services`,
`presentation`, `config`); um teste de arquitetura impede que uma camada importe o que
não deve. As regras pré-registradas (split, seed, limite de experimentos, teto de custo)
estão travadas por teste.

## Instalação

Requer Python 3.12.

```bash
conda env create -f environment.yml
conda activate concrete-crack
pip install -e ".[dev]"
pre-commit install
pytest
```

O PyTorch é opcional (`pip install -e ".[dev,dl]"`); só os adaptadores da rede o usam.

## Dados e licenças

Nenhum dado é versionado neste repositório. Os datasets previstos são o
[Concrete Crack Segmentation Dataset](https://doi.org/10.17632/jwsn7tfbrp.1) (Özgenel,
CC BY 4.0) e o [S2DS](https://github.com/ben-z-original/s2ds) (Benz e Rodehorst, uso
acadêmico). O script de aquisição e a ficha de procedência entram na Sprint 1.

## Licença

O código está sob a licença [MIT](LICENSE). Os datasets seguem as licenças dos seus
autores.
