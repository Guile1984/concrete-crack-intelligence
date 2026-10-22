# concrete-crack-intelligence — Arquitetura e plano v1.0

Oct 19, 2026 · @Guilherme Ferraz Stauffer

A arquitetura detalha o Discovery aprovado em seis camadas com um único port Segmentador, e o plano tem 8 sprints obrigatórias e 1 opcional. A Sprint 0 só começa com o seu "Avançar".

## Decisões datadas e correções

O DISCOVERY.md continua congelado; sete decisões datadas entram no NOTES.md na Sprint 0.

| # | Data | Decisão | Origem |
| --- | --- | --- | --- |
| A1 | 2026-10-19 | O CI não instala torch na job core; a job dl instala a versão para CPU | Corrige a Lição 1 |
| A2 | 2026-10-19 | Acrescentada a pasta versionada manifests/ (manifesto de dados e arquivo de split) | Corrige a árvore da Lição 2 |
| A3 | 2026-10-19 | Selo do teste por conjunto: até a Sprint 4 só validação; o teste do CCSD é avaliado uma vez (Frangi e rede, Sprint 4e); o S2DS, uma vez (Sprint 5) | Fecha lacuna do Discovery |
| A4 | 2026-10-19 | U-Net com decoder escrito pelo Gui sobre ResNet-18 do torchvision, sem segmentation-models-pytorch | Lição 3 |
| A5 | 2026-10-19 | Usar o PyTorch da runtime do Colab e fixar a runtime nas execuções comparadas | Lição 3 |
| A6 | 2026-10-19 | Registro de experimentos em JSON no Git; sem MLflow, W&B ou Hydra | Lição 3 |
| A7 | 2026-10-19 | Escolha final entre checkpoints candidatos pelo clDice de validação, não pelo Dice | Lição 5 (R19) |

## Arquitetura em camadas

As dependências apontam para dentro: uma camada só importa de camadas mais internas.

| Camada | Contém | Não pode importar |
| --- | --- | --- |
| domain | Dice, clDice, F1 com tolerância, descritores geométricos, bootstrap pareado por imagem-mãe, regra de partição por grupo | torch, disco, rede, matplotlib |
| ports | Contratos (Protocol): Segmentador, ProvedorDataset, Treinador, RepositorioExperimentos | Qualquer implementação |
| infrastructure | Leitores CCSD e S2DS, aquisição com hash, Frangi, U-Net em PyTorch, registro de experimentos | services, presentation |
| services | Casos de uso: preparar dados, ajustar baseline, avaliar, comparar, generalizar, caracterizar | Implementações concretas |
| presentation | Linhas de comando, figuras, geração do relatório | — |
| config | Constantes pré-registradas, dataclasses de experimento | — |

**Um único port Segmentador** serve ao Frangi e à U-Net: recebe uma imagem e devolve um mapa de score em \[0, 1\], e o limiar é aplicado fora. A simetria da comparação passa a ser garantida pela estrutura, o que fecha R22 e R14. Para o Frangi o mapa é uma resposta normalizada, não uma probabilidade, então nenhuma análise de calibração se aplica a ele.

**O domain usa NumPy e scikit-image, nunca torch.** As métricas rodam em CPU e são testadas contra respostas conhecidas (R23). O torch vive só em dois adaptadores: a U-Net e o treino.

**As regras pré-registradas moram em config e são travadas por teste:** split 70/15/15, seed, máximo de 3 experimentos adicionais e teto de US$ 20. Mudar uma regra exige editar o teste de propósito, o que força o registro no NOTES.md.

Um teste de arquitetura lê os imports de cada camada e falha se a tabela for violada.

## Estrutura de diretórios

O pacote se chama concrete\_crack, em layout src/, e a pasta manifests/ é a única adição em relação à árvore da Lição 2.

```
concrete-crack-intelligence/
├── src/concrete_crack/
│   ├── domain/            métricas, descritores, bootstrap, agrupamento
│   ├── ports/             Segmentador, ProvedorDataset, ...
│   ├── infrastructure/    leitores, Frangi, U-Net, registro
│   ├── services/          casos de uso
│   ├── presentation/      linha de comando, figuras
│   └── config/            regras pré-registradas
├── tests/                 espelha src/ + test_arquitetura.py
├── notebooks/             só GPU, sem lógica
├── scripts/               reproduzir_estudo.py
├── experiments/           registros versionados (um JSON por execução)
├── manifests/             manifesto de dados e split (versionado)
├── data/                  ignorado pelo Git
│   ├── raw/               downloads originais
│   ├── interim/           grupos, splits, tiles
│   └── predictions/       mapas de score salvos
├── reports/figures/       figuras finais
├── DISCOVERY.md
├── ARQUITETURA.md
├── NOTES.md
├── README.md
├── pyproject.toml
├── environment.yml
├── .pre-commit-config.yaml
└── .github/workflows/ci.yml
```

1. **data/ inteiro fora do Git**, com manifesto versionado (hash de cada arquivo e data de acesso), o que cobre o R26.
2. **experiments/ versionado, checkpoints não.** O registro guarda o hash de cada checkpoint, que fica no Drive.
3. **Notebooks sem lógica:** clonam o repositório numa versão fixa, instalam e chamam um caso de uso. scripts/ guarda só a orquestração da reprodução ponta a ponta. Isso fecha o R13.
4. **tests/ espelha src/**, com o teste extra de arquitetura.

## Stack

A stack é Python 3.12 com PyTorch opcional, e a configuração e o registro dispensam serviços externos.

| Peça | Escolha | Porquê |
| --- | --- | --- |
| Linguagem | Python 3.12 | A runtime do Colab de julho/2026 usa 3.12.13; igual ao projeto anterior |
| Ambiente local | conda + pip install -e ".\[dev\]" | O pyproject.toml é a única fonte de dependências; o environment.yml só declara Python e pip |
| Núcleo numérico | NumPy, SciPy, scikit-image, Pillow | Frangi, esqueleto e morfologia; transformada de distância; imagens de \~12 MPx |
| Rede | PyTorch + torchvision, decoder U-Net próprio | torch é dependência opcional (\[dl\]) |
| Figuras e tabelas | matplotlib, pandas | Só em presentation e services |
| Qualidade | Ruff (formato, lint, docstring Google, anotações de tipo), pytest, pre-commit | Mesmo conjunto dos projetos anteriores |
| Configuração | Dataclasses congeladas | Podem ser travadas por teste |
| Registro | JSON no Git | Auditável com git log; sem conta externa |

**U-Net própria (A4).** O decoder e os atalhos são o motivo de a U-Net ter sido escolhida; escrevê-los é a forma de entender por que funcionam. A versão mais recente do segmentation-models-pytorch que encontrei no [PyPI](https://pypi.org/project/segmentation-models-pytorch/) é a 0.5.0, com mais de um ano e meio, e não consegui confirmar release mais novo. O encoder é a ResNet-18 do torchvision, com os mesmos pesos do ImageNet. A biblioteca caberia atrás do port Segmentador se você preferir.

**PyTorch do Colab (A5).** A [runtime de julho/2026](https://research.google.com/colaboratory/runtime-version-faq.html) traz PyTorch 2.11.0 e NumPy 2.0.2, enquanto a [versão mais recente](https://github.com/pytorch/pytorch/releases) do PyTorch já é a 2.14.x. Reinstalar a mais nova custaria unidades e adicionaria uma variável. O treino usa o PyTorch da runtime, a versão é gravada no registro e a runtime é fixada durante o projeto. Localmente, uma versão próxima (2.11) serve só para testar adaptadores. A sonda da Sprint 3 confirma a runtime ativa.

**Limite.** O Ruff garante que as anotações de tipo existem, não que estão corretas. O mypy não foi adicionado para não somar atrito; entra depois se erros de tipo aparecerem.

## Testes e CI

Um teste verde só vale se puder falhar pelo motivo certo; por isso a maioria compara o código com uma resposta conhecida de antemão.

| Camada | O que é verificado |
| --- | --- |
| domain | Métricas contra casos calculados à mão (linha de 3 px deslocada 1 px: Dice 0,667 e clDice 1,0); Dice = 2·IoU/(1+IoU); métricas em \[0, 1\]; preditor "tudo é fundo" (accuracy acima de 99%, Dice 0); partição por grupo (nenhum grupo em dois splits, mesma seed gera o mesmo split, tiles herdam o split) |
| infrastructure | Frangi em imagens sintéticas (resposta na linha maior que no fundo e maior que na mancha redonda); U-Net em CPU (formato da saída, atalhos compatíveis, um passo de otimização reduz a loss num mini-batch) |
| services | Fluxo completo com dados sintéticos; baseline e rede avaliados pelo mesmo serviço |
| config | Regras pré-registradas travadas |
| arquitetura | Imports por camada |

Há ainda um teste de leakage (mini-dataset sintético com imagens-mãe conhecidas) e um de regressão numérica (métrica sobre um par de máscaras fixo).

**Fora do CI:** os testes que dependem dos dados reais (marcados com data) rodam só localmente. O CI verde não prova que os dados reais estão corretos; a inspeção das máscaras e a verificação de duplicatas são tarefas da Sprint 1.

**CI no GitHub Actions, em duas jobs (A1):**

| Job | Instala | Roda |
| --- | --- | --- |
| core | Pacote e dependências de desenvolvimento, sem torch | ruff check, ruff format --check, pytest (menos torch) |
| dl | Mais PyTorch para CPU | Testes de adaptador (marcados com torch) |

O CI usa pip a partir do pyproject.toml, com cache. A job dl pode rodar só na main se o tempo incomodar.

**Pre-commit:** Ruff, fim de arquivo e espaços finais, bloqueio de arquivos grandes (protege data/ e checkpoints) e nbstripout, que limpa as saídas dos notebooks.

**Cobertura:** sem meta de percentual, porque ela mede linhas executadas, não correção.

## Pipeline experimental

O pipeline é uma cadeia de artefatos com hash: cada etapa lê só o que a anterior gravou e registra o hash do que leu.

| Etapa | Lê | Grava | Roda |
| --- | --- | --- | --- |
| Aquisição | URLs, manifesto | data/raw/ (hash conferido) | Local |
| Agrupamento e split | data/raw/ | manifests/split\_v1.json (grupos, seed) | Local |
| Tiles | raw + split | data/interim/ | Local |
| Ajuste do Frangi | Tiles de treino e validação | Registro com parâmetros congelados | Local |
| Treino | Tiles + registro planejado | Checkpoints (Drive) + registro | GPU |
| Predição | Checkpoint + tiles | data/predictions/ (mapas de score) | GPU |
| Avaliação | Previsões + máscaras + limiar congelado | Métricas no registro | Local |
| Comparação | Registros | Figuras e tabelas | Local |

A predição grava mapas de score, não máscaras binárias. Assim a curva precision × recall, o limiar oráculo e qualquer reavaliação saem sem retreinar nem reinferir.

**Registro de cada execução.** Um JSON por execução em experiments/, com os campos da seção 10.3 do prompt mais: hash do commit e se havia alterações não commitadas; versões das bibliotecas e da runtime do Colab; tipo de GPU verificado antes do treino e unidades consumidas (saldo antes e depois); hash do manifesto de dados e do split; hash de cada checkpoint; hipótese, variável alterada e execução de referência; status (planejado, em execução, concluído, falhou, abandonado); eventos de retomada. O Frangi usa o mesmo esquema, com GPU "nenhuma".

**Mecanismos contra autoengano**

| Mecanismo | Como funciona | Cobre |
| --- | --- | --- |
| Hipótese antes do resultado | O registro nasce planejado, com hipótese e regra de decisão, e é commitado antes do treino; o Colab clona esse commit | R20 |
| Uma variável por vez | Um serviço recusa registrar se mais de um campo diferir da referência (a seed não conta) | R14 |
| Selo do teste (A3) | A avaliação no teste exige configuração e limiar congelados e grava teste\_avaliado; uma segunda tentativa falha, salvo justificativa registrada; vale por conjunto de teste | R20 |
| Falhas ficam | Execuções falhadas ou abandonadas permanecem; o número de execuções por hipótese vai ao relatório | Resultados negativos |

Esses mecanismos protegem contra erro e distração, não contra má-fé; um contorno apareceria no histórico do Git.

**Checkpoints (no Drive).** O last é gravado a cada época, com pesos, otimizador, scheduler, estado dos geradores aleatórios e época. Os 3 melhores por Dice de validação ficam como candidatos. A escolha final usa o clDice de validação, calculado localmente (A7); se Dice e clDice discordarem na ordem, isso vai ao registro. Uma execução retomada é registrada como tal, pois o determinismo total em GPU não existe (R9).

## Plano de sprints

São 8 sprints obrigatórias e 1 opcional, cada uma com um gate que precisa ser verdadeiro para seguir. Em toda sprint valem o ritual de fim (ruff check, pytest, revisar resultados, NOTES.md, git status, commit), a revisão de fechamento com lições aprendidas e a palavra "Avançar" antes da seguinte. Ao pausar, entra um commit wip. No início de cada sprint declara-se o modelo padrão.

| Sprint | Objetivo | Gate | Modelo padrão |
| --- | --- | --- | --- |
| 0 | Fundação | CI verde nas duas jobs | Sonnet |
| 1 | Dados | Decisão de contingência tomada; split sem leakage verificado | Sonnet (Opus se as máscaras surpreenderem) |
| 2 | Métricas + baseline | Métricas aprovadas nos testes de resposta conhecida; Frangi congelado | Sonnet |
| 3 | Rede de referência | Orçamento recalculado pela sonda dentro do teto | Sonnet (Opus na análise de erros, se houver surpresa) |
| 4 | Experimentos + comparação | Teste do CCSD tocado uma vez | Opus |
| 5 | Generalização | S2DS tocado uma vez | Opus |
| 6 | Caracterização | Três testes por descritor aplicados | Sonnet |
| 7 | Fechamento | Reprodução completa roda do zero | Sonnet (Haiku para Git e formatação) |
| 8 | API + dashboard (opcional) | Só se sobrar orçamento | Sonnet |

**Sprint 0: Fundação.** Entregam-se o repositório com a árvore da seção de diretórios, conda + pyproject.toml, as seis camadas com docstring, pre-commit, CI com core e dl, test\_arquitetura.py, os testes das regras pré-registradas, a LICENSE e o NOTES.md com as decisões datadas. Pronto quando as duas jobs passam e o teste de arquitetura falha de propósito num import proibido, o que prova que ele funciona.

**Sprint 1: Dados.**

- 1a Aquisição e procedência: termos de uso do S2DS lidos e aceitos, script com hash, manifesto e ficha de procedência.
- 1b Inspeção das máscaras: o limiar numérico de "máscaras inadequadas" é fixado antes de olhar. Gate de contingência: se o CCSD reprovar, replanejar antes da 1c.
- 1c Duplicatas, grupos e split: método escolhido depois de ver os dados, split\_v1.json com seed, teste de leakage e verificação do agrupamento do split do S2DS.
- 1d Tiles e binarização: tamanho do tile decidido com teoria, duas escalas (nativa e reduzida 2×) e binarização do S2DS com contagem de pixels antes e depois.

Pronto quando nenhum grupo cruza splits, a distribuição de fissuras por split foi reportada e a decisão sobre o CCSD está registrada.

**Sprint 2: Métricas + baseline.** A 2a cobre as métricas (teoria, implementação, testes de resposta conhecida, preditor trivial, bootstrap por imagem-mãe); a 2b, o Frangi atrás do port Segmentador, com testes sintéticos; a 2c, o ajuste por busca em grade com tamanho definido antes, só na validação. Pronto quando o baseline tem número de validação com intervalo de confiança e o teste não foi tocado.

**Sprint 3: Rede de referência.** A 3a é a U-Net (teoria, encoder, decoder, testes em CPU); a 3b, o treino (BCE + Dice, amostragem de tiles sem fissura, last e candidatos, registro planejado); a 3c, a sonda (T4 contra L4, runtime fixada, orçamento recalculado; se a previsão passar de US$ 20, revisar o plano antes de gastar); a 3d, o S1 com 3 seeds; a 3e, a inspeção visual e a análise de erros. Pronto quando há S1 com três seeds, a variação entre elas medida e a análise de erros escrita. Antes de fechar, revisão transversal com o Claude Code.

**Sprint 4: Experimentos e comparação.** A 4a registra as hipóteses antes de rodar; a 4b testa a resolução (sempre, com o Frangi reajustado na mesma resolução, R22); a 4c roda até dois experimentos adicionais, só se a análise de erros os pedir; a 4d congela a configuração final e o limiar, com 3 seeds; a 4e avalia o teste do CCSD uma única vez (Frangi e rede, diferença pareada de clDice com intervalo, leitura cruzada Dice × clDice, recall por tile). Pronto quando o critério 1 tem resposta com intervalo, mesmo que seja "inconclusivo".

**Sprint 5: Generalização.** Inferência no S2DS uma vez, limiar oráculo como diagnóstico rotulado, decomposição rede × Frangi e análise dos falsos positivos por classe original. Pronto quando o critério 2 tem resposta com a frase obrigatória sobre concordância com o anotador.

**Sprint 6: Caracterização.** Descritores em pixels sobre as máscaras previstas, os três testes por descritor, o piso de resolução nos dados e a visão de triagem por tile, se o orçamento permitir. Pronto quando cada descritor está classificado como "suportado" ou "não suportado", com o motivo; isso responde o critério 4.

**Sprint 7: Fechamento.** README com a seção de honestidade técnica (cada limitação com magnitude medida), NOTES.md consolidado, script de reprodução completa, decisão sobre publicar checkpoints, verificação visual de todas as figuras e revisão transversal final com o Claude Code. Pronto quando a reprodução roda do zero em CPU, sem pagar nada.

**Sprint 8 (opcional).** Só se as Sprints 0 a 7 fecharem dentro do orçamento; é a primeira a sair.

**Ferramentas.** O Claude Code entra como revisor ao fim das Sprints 3, 4 e 7, não como autor. O Cowork não tem uso previsto. O Colab é usado apenas nas Sprints 3, 4 e 5.

## Pendências e fontes

Nenhuma das sete pendências bloqueia a Sprint 0.

- [ ] Sprint 1, antes de olhar as máscaras: fixar o limiar numérico de "máscaras inadequadas"
- [ ] Sprint 1: escolher o método de detecção de quase duplicatas, depois de ver os dados
- [ ] Sprint 1: ler e aceitar os termos de uso do S2DS antes do download
- [ ] Sprint 1, condicional: confirmar licença e download parcial do CiF
- [ ] Sprint 2: decidir onde mora o ajuste do Frangi (recomendação: serviço próprio de busca em grade, pois o port Treinador não o cobre)
- [ ] Sprint 3: a sonda escolhe L4 ou T4 e confirma a runtime ativa do Colab
- [ ] Sprint 7: decidir se os checkpoints serão publicados

**Fontes consultadas (acesso em 2026-10-10)**

- [Colab: versões de runtime](https://research.google.com/colaboratory/runtime-version-faq.html)
- [PyTorch: releases](https://github.com/pytorch/pytorch/releases)
- [segmentation-models-pytorch no PyPI](https://pypi.org/project/segmentation-models-pytorch/)
- [segmentation-models-pytorch no conda-forge](https://anaconda.org/cf-post-staging/segmentation-models-pytorch)
