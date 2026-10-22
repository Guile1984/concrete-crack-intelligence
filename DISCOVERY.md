# concrete-crack-intelligence — Discovery v1.0

Sep 29, 2026 · @Guilherme Ferraz Stauffer

O Discovery mantém o problema de fissuras em concreto, com o CCSD como dataset primário e o S2DS como teste externo, e aguarda o seu "Discovery aprovado". Nenhum código foi escrito e nenhuma sprint foi iniciada.

## Alterações ao prompt original

Onze alterações ao prompt original, todas justificadas; devem ir para o NOTES.md na Sprint 0.

| # | Alteração | Motivo |
| --- | --- | --- |
| 1 | Critério de parada 3 removido (desempenho vs. discordância entre anotadores) | Exige a mesma imagem anotada por 2+ pessoas; nenhum dataset candidato tem isso e a reanotação própria foi descartada por custo. Decisão do Gui. |
| 2 | Pergunta de pesquisa v1.0 → v1.1 | "Visíveis", "diferentes" e "úteis" não eram mensuráveis; a v1.1 decompõe 1:1 nos critérios. |
| 3 | Seção 12.1 corrigida: saem "conjunto de teste próprio" e "anotação cega" | Contradiziam a seção 6 e o R16. |
| 4 | Parte G: "R1–R17" lido como R1–R16 + novos | O prompt só define R1–R16. |
| 5 | Seção 13, frase sobre o baseline corrigida | A construção do baseline não depende do ground truth, mas a avaliação depende. Ele não quebra a circularidade. |
| 6 | Classificação vira avaliação derivada da segmentação | Nenhum dataset de classificação sobrevive ao filtro de leakage; custo de treino zero. |
| 7 | Teto computacional: US$ 20 (avulso) | Decisão do Gui; substitui o teto em horas. |
| 8 | Regra de GPU fixa nas execuções comparadas | GPUs diferentes alteram resultados numéricos. |
| 9 | clDice como métrica de decisão do critério 1 | Neutraliza a vantagem de imitar a espessura do anotador (R19). |
| 10 | Novos riscos R17–R26 | Descobertos no Discovery. |
| 11 | Cabeçalho de modelos: "Sonnet 5 / Opus 5" → "Sonnet 5.5 / Opus 5.5" | Versões atuais. |

## Problem Definition v1.0

A pergunta v1.1 troca três termos vagos por mensuráveis e mapeia 1:1 nos critérios de parada.

**Pergunta de pesquisa v1.1**

> Até que ponto uma rede de segmentação supera um método clássico não neural na delimitação de fissuras visíveis na resolução da imagem; quanto desse desempenho se mantém em um dataset de origem diferente; e quais descritores geométricos em pixels permanecem estáveis o suficiente para serem reportados?

**Critérios de parada.** Responder "não" ou "inconclusivo" a qualquer um é resultado completo.

1. **A rede supera o baseline clássico?** Métrica de decisão: clDice. A rede "supera" se o intervalo de confiança da diferença pareada por imagem-mãe (bootstrap sobre imagens, não tiles) excluir o zero, com orçamento de ajuste simétrico.
2. **Quanto do desempenho sobrevive fora do domínio?** Reportado como "queda sob mudança de dataset", nunca como "queda sob mudança de condição física" (R16).
3. ~~Desempenho vs. discordância entre anotadores~~ — removido.
4. **Que descritores geométricos os dados suportam?** Só é "suportado" o descritor que passar em três testes pré-registrados: concordância, estabilidade e piso de resolução.

**Problema de Engenharia Civil.** Apoiar a triagem em inspeção visual: dado um volume grande de fotografias de concreto, localizar e delimitar fissuras visíveis para o inspetor priorizar onde olhar. A saída é evidência visual, nunca diagnóstico estrutural.

**Problema de Visão Computacional.** Segmentação semântica binária de estruturas finas e alongadas, com desbalanceamento extremo (fissura tipicamente abaixo de 1% dos pixels), rótulos ruidosos na fronteira, mudança de distribuição entre datasets e extração de descritores morfológicos em pixels.

## Dataset Strategy v1.0

O CCSD é o dataset primário e o S2DS o teste externo; a maioria dos datasets públicos de fissura é de pavimento, não de concreto estrutural, e isso eliminou mais candidatos que a licença.

| Papel | Dataset | Uso |
| --- | --- | --- |
| Primário | Concrete Crack Segmentation Dataset (CCSD), Özgenel | Treino, validação e teste in-domain |
| Externo | Structural Defects Dataset (S2DS), Benz & Rodehorst | Somente avaliação; nunca treino, nunca ajuste de limiar |
| Condicional | Cracks in the Foundation (CiF, 2026) | Só se licença e download parcial forem confirmados |

**Procedência (acesso em 2026-09-28)**

| Item | CCSD | S2DS |
| --- | --- | --- |
| Fonte | Mendeley Data, v1, 3/abr/2019, DOI 10.17632/jwsn7tfbrp.1 | github.com/ben-z-original/s2ds |
| Licença | CC BY 4.0: versionar derivados é permitido, com atribuição | Somente uso acadêmico: não versionado; script de aquisição |
| Conteúdo | 458 imagens de \~4032×3024 (\~12 MPx), edifícios da METU | 743 recortes de 1024×1024, majoritariamente concreto |
| Split | Nenhum predefinido | Fornecido; a auditar |
| Fissura nos pixels | A medir | ≈ 0,26% |
| Risco específico | Quase duplicatas sem metadado de origem | Link do Google Drive pode desaparecer (R26) |

O S2DS será binarizado como "fissura" contra todas as demais classes; a transformação e a contagem de pixels antes e depois são registradas.

**Excluídos e por quê**

| Dataset | Motivo |
| --- | --- |
| Concrete Crack Images for Classification (40.000 patches) | Derivado das mesmas 458 imagens; patches sem imagem-mãe identificável, então o leakage não é corrigível. Espelhos no Kaggle usam licença diferente da original. |
| SDNET2018 | Só rótulo por patch, sem máscaras; 230 fotos-mãe sem agrupamento |
| DeepCrack | Proveniência parcial das imagens; uso não comercial; resolução baixa e domínio misto |
| CFD | Pavimento; 118 imagens; licença não declarada |
| OmniCrack30k | Autores informam que não pode ser compartilhado |
| CrackSeg9k | Agregador; herda licenças e risco de duplicatas entre fontes |

**Resolução.** Reduzir \~4032×3024 para \~512×384 divide a escala por \~8: uma fissura de 6 px fica com menos de 1 px e some. Por isso os tiles são gerados depois do split, e a resolução de trabalho é um experimento, não uma conveniência.

**Split do CCSD**

1. Agrupar quase duplicatas por similaridade.
2. Dividir por grupo em 70/15/15 (treino/validação/teste), com seed fixa registrada.
3. Gerar os tiles só depois; cada tile herda o split da imagem-mãe.

O teste terá cerca de 65–70 imagens-mãe, então os intervalos de confiança serão largos. Essa é a evidência real que o dataset oferece.

**Regra de contingência, fixada antes de inspecionar o CCSD.** Máscaras inadequadas significam fissuras visíveis omitidas de forma sistemática, ou espessura incompatível em proporção relevante das imagens (limiar exato fixado no início da Sprint 1, antes de olhar as máscaras). Nesse caso, o S2DS vira primário e o CiF, externo, se verificado; se o CiF também falhar, o critério 2 fica "não avaliado, por indisponibilidade de dados adequados".

**Implicações estatísticas**

- A unidade independente é a imagem-mãe; o bootstrap reamostra imagens, não tiles.
- CCSD e S2DS têm escalas em mm/px diferentes e desconhecidas: descritores geométricos são reportados dentro de cada dataset, nunca comparados entre eles.
- A queda fora do domínio mistura shift visual e shift de protocolo de anotação, indistinguíveis sem anotação própria.

**Pendências de verificação (Sprint 1)**

- [ ] Inspecionar as máscaras do CCSD: espessura, consistência, fissuras omitidas
- [ ] Procurar quase duplicatas no CCSD
- [ ] Verificar se o split do S2DS agrupa recortes por foto-mãe
- [ ] Confirmar licença e download parcial do CiF

## Baseline Strategy v1.0

O baseline é o filtro de Frangi, que realça estruturas lineares escuras e produz a mesma saída que a rede: uma máscara binária por pixel.

**Por que não um detector de bordas.** Uma fissura tem duas bordas, uma de cada lado; o detector marca os contornos e deixa o interior vazio, e responde igualmente a poros, juntas e agregados. Seria um espantalho.

**Como o Frangi funciona.** A imagem é tratada como relevo; a fissura escura é um vale estreito e comprido. Em cada pixel, os dois autovalores da matriz Hessiana medem a curvatura máxima e mínima em direções perpendiculares.

| Forma local | Curvaturas | Exemplo |
| --- | --- | --- |
| Vale linear | Forte numa direção, quase nula na outra | Fissura |
| Mancha arredondada | Forte nas duas | Poro, bolha |
| Superfície plana | Fraca nas duas | Concreto sem defeito |

O filtro é multiescala; o parâmetro de escala corresponde à largura em pixels das fissuras que ele vê.

**Pipeline.** Tons de cinza, correção de iluminação (subtração de fundo), Frangi multiescala, limiarização e limpeza morfológica de componentes pequenos. Quatro parâmetros: faixa de escalas, limiar, tamanho mínimo de componente e intensidade da correção de iluminação.

**Limitações declaradas antes de rodar**

- Juntas, bordas de fôrma e riscos lineares também são vales lineares e serão marcados.
- Fissuras de contraste muito baixo ficam abaixo do ruído da textura.
- Cruzamentos e ramificações enfraquecem a resposta.

**Comparação justa com a rede**

1. **Ajuste simétrico:** busca em grade exaustiva só na validação, pela mesma métrica da rede; tudo congelado antes de tocar o teste.
2. **Mesmas imagens, resolução e implementação de métrica.**
3. **Comparação pareada:** diferença por imagem com intervalo de confiança por bootstrap de imagens-mãe. Se o intervalo contém zero, a resposta é "sem evidência de superioridade".
4. **Referência trivial "tudo é fundo":** não é baseline a vencer, é teste das métricas.
5. **R22:** se o experimento de resolução mudar a escala de trabalho, o Frangi é reajustado na mesma resolução.

**Decomposição no S2DS.** O Frangi, ajustado no CCSD, também roda no S2DS. Como não aprendeu com as máscaras, sua queda reflete sobretudo o efeito do dataset. A queda comum aos dois é efeito do dataset; a queda só da rede estima sua especialização no CCSD. É uma decomposição aproximada, não uma medida exata.

**R16: risco aceito, não resolvido.** A construção do baseline não depende do ground truth, mas a avaliação depende do mesmo ground truth que avalia a rede. O baseline testa se aprender com as máscaras agrega valor além da geometria genérica; não quebra a circularidade. Se os anotadores do CCSD desenharam máscaras mais grossas que a fissura, a rede aprende essa convenção e o Frangi não; o clDice é a defesa.

Frase obrigatória no README: todo número fora do domínio significa "concordância com o anotador do S2DS", não "acerto sobre fissuras reais".

## Experimental Strategy v1.0

A rede de referência é uma U-Net com encoder ResNet-18, avaliada por clDice e Dice lado a lado, com no máximo três experimentos adicionais e três seeds.

**Métricas.** Todas nascem da contagem de VP, FP, FN e VN por pixel.

| Métrica | O que mede | Como engana |
| --- | --- | --- |
| Accuracy | (VP+VN)/total | O fundo domina; "tudo é fundo" passa de 99%. Não usada para decisão. |
| Precision / Recall | Alarme falso / omissão | Não veem VN. Reportadas separadas, pois têm custos diferentes na inspeção. |
| Dice (= F1) | Sobreposição da classe fissura | Hipersensível a deslocamento: fissura de 3 px deslocada 1 px dá 0,67, e deslocada 2 px dá 0,33. Com 20 px de largura e 1 px de deslocamento, \~0,95. |
| IoU | VP/(VP+FP+FN) | Função do Dice (Dice = 2·IoU/(1+IoU)); mesma ordenação. Reporta-se o Dice. |
| F1 com tolerância k px | Acerto com margem | Infla o número. Sempre declarada, justificada e ao lado da versão estrita. |
| clDice | Precisão e sensibilidade topológicas pelo esqueleto | Cego à largura; espinhos de esqueletização podem enganar. Nunca sozinha. |
| Curva precision × recall | Desempenho sem depender do limiar | Mostra se a vantagem é efeito do ponto de corte. |

**Agregação.** Unidade = imagem-mãe, com tiles reagrupados; média por imagem como principal e soma global como complemento. Imagens sem fissura anotada ficam fora da média de Dice e entram numa métrica própria (taxa de alarme falso por imagem). A regra é fixada antes de rodar.

**Leitura cruzada pré-registrada**

| Resultado | Interpretação |
| --- | --- |
| Rede vence em Dice e empata em clDice | A vantagem vem da espessura, isto é, da convenção de anotação. Resultado negativo registrado. |
| Rede vence em clDice e não em Dice | Encontra melhor as fissuras, mas erra a largura. Informa o critério 4. |

**Split, augmentation e loss**

- Ordem: dataset, split por grupo, tiles, augmentation apenas no treino.
- Entram: espelhamento, rotações de 90°, brilho e contraste leves. Ficam fora: deformação elástica (altera a geometria que o critério 4 mede) e desfoque forte (pode apagar fissuras finas).
- Loss BCE + Dice. A BCE dá sinal estável por pixel, mas o fundo domina; a Dice loss olha a sobreposição da fissura, mas herda a hipersensibilidade. A soma é o ponto de partida mais comum e compreendido, não a melhor.

**Arquitetura.** U-Net com encoder ResNet-18 pré-treinado: os atalhos levam detalhe fino ao decoder (uma fissura de 3 px some após redução de 32×), o pré-treino compensa as \~320 imagens de treino, e o modelo cabe com folga na GPU. Arquiteturas maiores só entram se a análise de erros apontar um problema que resolvam.

**Sequência de experimentos**

1. **S1:** configuração de referência.
2. **Análise de erros de S1:** inspeção visual obrigatória de FP, FN, melhores, piores e casos difíceis.
3. **Até 3 experimentos adicionais**, uma variável cada (tabela abaixo).
4. **Três seeds** para S1 e para a configuração final; diferença menor que a variação entre seeds é ruído.
5. O teste é tocado uma única vez, com tudo congelado.

| Candidato | Entra apenas se... |
| --- | --- |
| Resolução de trabalho (nativa vs. reduzida 2×) | Sempre: decide o critério 4 e o custo |
| Peso maior da classe fissura | Recall baixo com fissuras finas omitidas de forma sistemática |
| Encoder ResNet-34 | Subajuste (erro alto também no treino) |

O limite de três existe mesmo com GPU paga: cada experimento é avaliado nas mesmas \~70 imagens de validação, e escolher o melhor de muitos infla o resultado (viés de seleção).

**Generalização (S2DS)**

- Todas as imagens do S2DS formam o teste externo; bootstrap por foto-mãe quando identificável.
- Limiar congelado, vindo da validação do CCSD.
- Limiar oráculo (o melhor no próprio S2DS) só como diagnóstico, rotulado como não legítimo: se recupera quase tudo, a rede está descalibrada; se nem ele recupera, ela não reconhece as fissuras do novo domínio.

**Caracterização geométrica.** Descritores sempre em pixels: comprimento (pelo esqueleto), largura local, orientação predominante, ramificações e área. Um descritor é "suportado pelos dados" só se passar em três testes:

1. **Concordância** com a máscara anotada (concordância com o anotador, R16).
2. **Estabilidade** sob variação do limiar.
3. **Piso de resolução:** abaixo de uma largura mínima (fixada nos dados, Sprint 6), 1 px representa 30–100% do valor; nesse caso, reporta-se "abaixo da resolução mensurável", sem número.

Não há conversão para milímetros, pois nenhum dataset traz escala.

**Classificação como avaliação de triagem.** Derivada da segmentação, por tile: o rótulo verdadeiro é a máscara anotada com fissura acima de um mínimo de pixels; a previsão usa o mesmo critério na máscara prevista. Métrica principal: recall por tile. Custo de treino zero.

**Registro de experimentos.** Todos os campos da seção 10.3 do prompt, mais versões das bibliotecas, hash do commit, tipo de GPU verificado antes do treino e unidades de computação consumidas, em arquivo versionado no repositório.

## Compute Strategy v1.0

O teto é US$ 20 para o projeto inteiro; a GPU só entra no treino e na inferência em lote, e uma vez escolhida pela sonda ela fica fixa nas execuções comparadas.

**VS Code + Colab.** O repositório é o projeto e o Colab é só onde a GPU mora. O notebook não contém lógica: clona o repositório numa versão fixa, instala o pacote e chama módulos.

| Risco | Defesa |
| --- | --- |
| Desconexão da sessão | Checkpoint no Drive a cada época; treino retomável |
| Divergência de ambiente | Registro grava versões das bibliotecas e hash do commit |
| Leitura lenta do Drive | Copiar o dataset para o disco local da sessão antes do treino |

**Local × GPU**

| Local (CPU) | GPU |
| --- | --- |
| Aquisição, inspeção, duplicatas, split, tiles | Treino da U-Net |
| Todo o Frangi, inclusive a busca em grade | Inferência em lote (CCSD e S2DS) |
| Métricas, testes, análise de erros, figuras, bootstrap, geometria, CI, documentação |  |

**Orçamento.** O avulso custa US$ 9,99 por 100 unidades, então o teto equivale a cerca de 200 unidades. O consumo por hora de cada GPU não é publicado oficialmente e as medições independentes divergem. No pior caso encontrado:

| GPU | Horas com \~200 unidades | Cabe no plano (\~20 h)? |
| --- | --- | --- |
| T4 | \~100 h | Sim, com folga de 5× |
| L4 | \~40 h | Sim, com folga de 2× |
| A100 | \~13 h | Não |

A previsão é de cerca de 10 treinos: S1 com 3 seeds, até 3 experimentos adicionais e a configuração final com 3 seeds, se diferente. A sonda da Sprint 3 mede tempo, memória e unidades gastas em T4 e L4, compara o custo por época e recalcula o orçamento. A preferência é a L4, sujeita à sonda. Estourar o teto exige revisão registrada no NOTES.md.

**Regra de GPU fixa**

1. A sonda escolhe a GPU, que fica fixa em todas as execuções comparadas.
2. O tipo é conferido no início de cada sessão, gravado e verificado antes do treino.
3. Se a GPU fixada não estiver disponível, não se treina com outra: espera-se ou tenta-se mais tarde.
4. Indisponibilidade persistente leva a troca formal, com registro e reexecução das referências na nova GPU.

Encerrar o runtime assim que o checkpoint e as previsões estiverem salvos, pois as unidades são consumidas com a sessão conectada, inclusive ociosa.

**Reprodutibilidade.** Seeds fixas e modo determinístico quando possível; o determinismo total em GPU não é garantido, é aceito e é medido pelas três seeds. Inferência e análises devem ser reproduzíveis sem custo (CPU local ou T4 gratuita) com os checkpoints publicados; o README informa hardware e tempo de treino.

## Risk Register v1.0

Dos 26 riscos, cinco podem invalidar conclusões: R2/R17 (leakage), R18 (máscaras), R19 (espessura), R22 (resolução do baseline) e R16 (circularidade, pela redação do README).

Status: **Desenho** = mitigado por decisão do Discovery; **Verificar** = depende de checagem nos dados; **Aceito** = declarado no README; **Monitorar** = pode surgir na execução.

| ID | Risco | Status | Resposta | Sprint |
| --- | --- | --- | --- | --- |
| R1 | Dataset inadequado | Verificar | CCSD por licença, domínio e resolução; contingência pré-registrada | 1 |
| R2 | Leakage entre splits | Desenho + Verificar | Split por grupo de imagem-mãe; tiles depois; dataset de classificação excluído | 1 |
| R3 | Ground truth imperfeito | Verificar | Inspeção com critério de rejeição fixado antes | 1 |
| R4 | Desbalanceamento | Desenho | Accuracy descartada; BCE + Dice; preditor trivial | 2–3 |
| R5 | Overfitting ao dataset | Monitorar | Split limpo; 3 seeds; decomposição rede × Frangi | 3–5 |
| R6 | Domain shift | Aceito como resultado | Objeto do critério 2 | 5 |
| R7 | Métricas enganosas | Desenho | Dice + clDice; média por imagem; curva P×R; regra para imagens sem fissura | 2 |
| R8 | Custo computacional | Desenho | Teto de US$ 20; sonda; unidades por experimento | 3–5 |
| R9 | Não reprodutibilidade | Desenho + Aceito | Seeds, versões, hash, GPU fixa; determinismo total aceito como impossível | 0, 3–5 |
| R10 | Interpretação estrutural indevida | Desenho | Seção de honestidade técnica; sem vocabulário de diagnóstico | 7 |
| R11 | Pixels convertidos em mm | Desenho | Proibido; piso de resolução declarado | 6 |
| R12 | Complexidade sem benefício | Desenho | Máximo de 3 experimentos, cada um ligado a um problema observado | 4 |
| R13 | Dependência de notebook | Desenho | Notebook sem lógica | 0, 3 |
| R14 | Alterações simultâneas | Desenho | Uma variável por experimento; GPU fixa como variável controlada | 4 |
| R15 | Licença | Parcial | CCSD ok; S2DS não versionado; CiF não verificado | 1 |
| R16 | Verificação circular | Aceito | Baseline não a quebra; README diz "concordância com o anotador" | 7 |
| R17 | Quase duplicatas no CCSD | Verificar | Similaridade antes do split; grupos | 1 |
| R18 | Máscaras do CCSD reprovadas | Verificar | Plano B pré-registrado | 1 |
| R19 | Rede premiada por imitar a espessura do anotador | Desenho | clDice como decisão; leitura cruzada pré-registrada | 2, 4 |
| R20 | Viés de seleção na validação | Desenho | Limite de experimentos; teste tocado uma vez | 4 |
| R21 | GPU não garantida pelo Colab | Monitorar | Conferência no início; sem GPU mista; troca formal | 3–5 |
| R22 | Baseline em resolução diferente da rede | Desenho | Frangi reajustado na mesma resolução | 2, 4 |
| R23 | Bug nas métricas | Desenho | Testes com resposta conhecida (linha de 3 px deslocada 1 px: Dice 0,667, clDice 1,0) | 2 |
| R24 | Teste pequeno (\~65–70 imagens) | Aceito | Intervalo largo reportado; "inconclusivo" é resposta válida | 4 |
| R25 | Recortes correlacionados no S2DS | Verificar | Bootstrap por foto-mãe quando identificável | 5 |
| R26 | Fonte de dados desaparece (S2DS via Drive) | Monitorar | Script com hash e data de acesso; cópia local fora do repositório | 1 |

## Sprint Budget v1.0

O projeto tem 8 sprints obrigatórias e 1 opcional (o projeto anterior teve 7), e a Sprint 1 concentra os riscos que invalidam resultados.

| Sprint | Conteúdo | Critério |
| --- | --- | --- |
| 0 — Fundação | Repositório, ambiente, camadas, pre-commit, CI | — |
| 1 — Dados | Aquisição, inspeção das máscaras (com contingência), quase duplicatas, split por grupo, tiles, binarização do S2DS, verificações pendentes | Todos |
| 2 — Métricas + baseline | Métricas com testes unitários; Frangi ajustado e congelado | 1 |
| 3 — Rede de referência | Sonda de GPU, S1 com 3 seeds, inspeção visual, análise de erros | 1 |
| 4 — Experimentos + comparação | Até 3 experimentos de uma variável; comparação pareada com o baseline | 1 |
| 5 — Generalização | S2DS, limiar oráculo, decomposição rede × Frangi | 2 |
| 6 — Caracterização | Descritores, piso de resolução, visão de triagem por tile | 4 |
| 7 — Fechamento | README com honestidade técnica e magnitudes, NOTES.md consolidado, reprodução completa | — |
| 8 — Opcional | API + dashboard | — |

**O que sai se o escopo estourar, nesta ordem**

1. Sprint 8 (API e dashboard).
2. CiF como segundo teste externo.
3. Experimentos adicionais de 3 para 1: fica só o de resolução.
4. Descritores reduzidos a comprimento e largura.
5. Visão de triagem por tile vira trabalho futuro.

**O que nunca sai (núcleo do projeto)**

- Split agrupado por imagem-mãe
- Baseline clássico com ajuste simétrico
- Avaliação no S2DS
- Três seeds nas configurações comparadas
- Inspeção visual
- Seção de honestidade técnica com magnitudes

## Próximos passos e fontes

O Discovery só avança com a sua resposta "Discovery aprovado"; a Sprint 0 exige, além disso, o seu "Avançar".

1. Avaliar o Discovery e responder "Discovery aprovado" ou apontar ajustes.
2. Depois da aprovação, propor arquitetura em camadas, estrutura de diretórios, stack definitiva, plano detalhado de sprints, CI e formato do registro de experimentos.
3. Iniciar a Sprint 0 somente após o "Avançar".

**Fontes consultadas (acesso em 2026-09-28)**

- [Concrete Crack Segmentation Dataset (Özgenel, 2019)](https://data.mendeley.com/datasets/jwsn7tfbrp/1)
- [Concrete Crack Images for Classification (Özgenel, 2019)](https://data.mendeley.com/datasets/5y9wdsg2zt/2)
- [S2DS: Structural Defects Dataset](https://github.com/ben-z-original/s2ds)
- [DeepCrack (Liu et al., 2019)](https://github.com/yhlleo/DeepCrack)
- [SDNET2018 (Dorafshan et al., 2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6247444/)
- [Cracks in the Foundation (Farronato et al., 2026)](https://arxiv.org/html/2605.18413v2)
- [OmniCrack30k (Benz & Rodehorst, 2024)](https://github.com/ben-z-original/omnicrack30k)
- [dacl10k (Flotzinger et al.)](https://arxiv.org/pdf/2309.00460)
- [Colab: taxas de consumo de compute units (medição independente, não oficial)](https://www.thundercompute.com/blog/colab-alternatives-for-cheap-deep-learning-in-2025)
