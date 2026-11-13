# NOTES.md: diário de decisões

Registra decisões, hipóteses, trade-offs, pendências, limitações, riscos, descobertas,
resultados inesperados, divergências entre fontes, alterações metodológicas e
**resultados negativos**. Nada é apagado: uma correção entra como nova entrada.

As 11 alterações ao prompt original estão em `DISCOVERY.md`, seção 0.

## 1. Decisões datadas

| # | Data | Decisão | Origem |
|---|---|---|---|
| A1 | 2026-10-19 | O CI não instala torch na job `core`; a job `dl` instala a versão para CPU | Corrige a Lição 1 |
| A2 | 2026-10-19 | Pasta versionada `manifests/` (manifesto de dados e split) | Corrige a árvore da Lição 2 |
| A3 | 2026-10-19 | Selo do teste por conjunto: o teste do CCSD é avaliado uma vez (Sprint 4e); o S2DS, uma vez (Sprint 5) | Fecha lacuna do Discovery |
| A4 | 2026-10-19 | U-Net com decoder escrito pelo Gui sobre ResNet-18 do torchvision, sem `segmentation-models-pytorch` | Lição 3 |
| A5 | 2026-10-19 | PyTorch da runtime do Colab; runtime fixada nas execuções comparadas | Lição 3 |
| A6 | 2026-10-19 | Registro de experimentos em JSON no Git; sem MLflow, W&B ou Hydra | Lição 3 |
| A7 | 2026-10-19 | Escolha final do checkpoint pelo clDice de validação, não pelo Dice | Lição 5 (R19) |
| A8 | 2026-10-21 | Testes isentos de docstring e anotação (regras `D` e `ANN` do Ruff) | Lição 0.3 |
| A9 | 2026-10-21 | `config` e `domain` não importam nada do projeto; `presentation` é a raiz de composição | Lição 0.4 |
| A10 | 2026-10-21 | `.gitignore` e `.gitattributes` antecipados da lição 0.9 para a 0.5 | Lição 0.5 |
| A11 | 2026-10-21 | `PRE_COMMIT_HOME=C:\pc-cache`, permanente | Incidente de permissões (seção 4) |
| A12 | 2026-10-21 | Claude Code, `pre-commit`, `pytest` e `git commit` só em terminal comum (não elevado) | Incidente de permissões (seção 4) |
| A13 | 2026-10-22 | Seed do split = 20261022 | Lição 0.7 |
| A14 | 2026-10-22 | Repositório remoto criado antes do CI, que só roda no GitHub | Mudança de ordem |
| A15 | 2026-10-26 | Numeração: 0.8 repositório remoto, 0.9 CI, 0.10 documentos de raiz | Divisão de lição |
| A16 | 2026-10-26 | Repositório público desde a Sprint 0 | Decisão do Gui |
| A17 | 2026-10-26 | O lint do CI é `pre-commit run --all-files`, com os hooks fixados | Lição 0.9 |
| A18 | 2026-10-26 | O `pytest` padrão exclui os marcadores `torch` e `data` (`addopts`) | Lição 0.9 |
| A19 | 2026-10-26 | A job `dl` usa `torch==2.11.*`, a versão do Colab de julho/2026 | Lição 0.9 |
| A20 | 2026-10-26 | Licença MIT para o código | Decisão do Gui |
| A21 | 2026-10-27 | O projeto não usa o split publicado do S2DS (seção 9) | Lição 1.1 |
| A22 | 2026-10-27 | Divergência de licença do S2DS: vale o mais restritivo | Lição 1.1 |
| A23 | 2026-10-27 | Aquisição semiautomática: download manual e script que registra e verifica o hash | Lição 1.1 |
| A24 | 2026-10-27 | O pytest usa `--basetemp=.pytest_tmp` (pasta do projeto, ignorada pelo Git) em vez do `%TEMP%` compartilhado | Incidente de permissões (seção 4) |
| A25 | 2026-10-27 | Reenumeração da Sprint 1: a aquisição se divide em 1.2 (modelo do registro e comparação), 1.3 (hash em disco e manifesto em JSON) e 1.4 (aquisição do CCSD); as demais lições avançam | Lição 1.2 |
| A26 | 2026-10-27 | O registro de arquivos usa SHA-256 e caminhos relativos à pasta da fonte, sempre com `/` (sem `.`, `..`, `:` nem barra invertida); a comparação distingue ausente, inesperado e alterado | Lição 1.2 |
| A27 | 2026-10-28 | O manifesto de arquivos de cada fonte fica em `manifests/arquivos_<fonte>.json`, fora da pasta de dados que descreve; o hash é SHA-256 calculado em blocos de 1 MiB; os arquivos saem ordenados pela string do caminho; o JSON usa indentação de 2 espaços, LF e quebra de linha final | Lição 1.3 |
| A28 | 2026-10-28 | O extrator de RAR é o `UnRAR.exe` do WinRAR (já instalado), com `t` para testar a integridade e `x` para extrair; o `tar` do Windows não foi testado com este arquivo | Lição 1.4 |
| A29 | 2026-10-28 | A fonte do CCSD é o RAR baixado direto pelo ícone ao lado do arquivo; o Download All entregou um RAR truncado. Os arquivos truncados ficam em `data/raw/_tentativas/` (fora do registro) como evidência | Lição 1.4 |
| A30 | 2026-10-28 | Os comandos `registrar` e `verificar` ficam em `presentation/dados.py`, com códigos de saída 0, 1 e 2; só se registra fonte com ficha em `fontes.json`; o manifesto de arquivos é criado uma única vez e não é sobrescrito; o manifesto do CCSD registra o RAR e os 916 arquivos extraídos (917 entradas) | Lição 1.4 |
| A31 | 2026-10-28 | Protocolo de inspeção das máscaras do CCSD: 40 máscaras sorteadas entre as 458 (seed 20261022); veredito por imagem adequada, inadequada ou duvidosa; inadequada = omissão de fissura visível, excesso (marca algo que não é fissura) ou espessura visivelmente incompatível; reprova o CCSD com 8 ou mais inadequadas de 40 (20%); proporção relevante = 25%; as duvidosas são registradas e não entram na regra, e a sensibilidade (contá-las como inadequadas) é reportada | Lição 1.5 |
| A32 | 2026-10-28 | O sorteio ordena os nomes pelo SHA-256 de "seed:nome" e pega os primeiros n, sem depender da versão de nenhuma biblioteca de sorteio; um vetor conhecido trava o algoritmo; a amostra é gravada em `manifests/inspecao_ccsd.json` uma única vez e não é refeita | Lição 1.5 |
| A33 | 2026-10-28 | Só o Gui julga as 40 máscaras. Uma segunda leitura cega pelo Claude (auxiliar, só com concordância reportada) foi considerada e não adotada: imagens de cerca de 12 MPx chegam reduzidas a um modelo de visão, o juiz não tem calibração para a regra de 8 em 40 e seria mais uma camada de circularidade (R16) | Lição 1.5 |
| A34 | 2026-10-31 | Política de orientação do CCSD: as fotos são lidas com a orientação EXIF aplicada (a etiqueta 0x0112 é lida, mas o `ImageOps.exif_transpose` não entra na leitura do cabeçalho); as máscaras já estão na orientação de exibição (sem EXIF, ou EXIF 1). As dimensões de foto e máscara só são comparadas depois de aplicar a orientação (`tamanho_exibido`). Verificado em 458 de 458 pares pelo teste de contraste da A35 | Lição 1.6 |
| A35 | 2026-10-31 | Teste de alinhamento foto-máscara por contraste: para cada par, compara o contraste sob a máscara na orientação EXIF e na orientação oposta (180°); fotos e máscaras lidas com redução de 8x; fissura da máscara = pixels que diferem do fundo (mediana) em 32 níveis ou mais; um grupo de orientação é confirmado com 90% ou mais de vantagens positivas; método e critério fixados antes da rodada real; os grupos sem EXIF e EXIF 1 são o controle. Limites: resolução de 1/8, só orientação contra a oposta (sem espelhamentos), não prova alinhamento ao pixel | Lição 1.6 |
| A36 | 2026-11-01 | Visualizador de inspeção das máscaras: cada máscara da amostra vira um PNG de dois painéis (esquerda, a foto com a orientação EXIF aplicada; direita, a mesma foto com a máscara em vermelho) separados por uma faixa azul de 8 px, com redução de 5x. A sobreposição não binariza: o peso do vermelho em cada pixel é 0,5 vezes a intensidade da máscara, definida como a distância ao fundo (mediana da máscara) dividida por 255, para não engrossar a máscara nem depender de a fissura ser branca ou preta. As imagens são derivadas, ficam em `data/interim/inspecao_ccsd/` (fora do Git) e não são abertas antes da sessão de julgamento. O comando `preparar` recusa o trabalho se o manifesto de arquivos mudou desde o sorteio | Lição 1.7 |
| A37 | 2026-11-01 | A regra de decisão da inspeção mora em `domain/veredito.py` com o limiar recebido como argumento (o domínio não importa `config`, A9): reprova com 8 ou mais inadequadas em 40 (A31); as duvidosas ficam fora da regra, e a sensibilidade (contá-las como inadequadas) e o aviso `conclusao_depende_das_duvidosas` saem junto; intervalo de Wilson de 95% com z de `NormalDist().inv_cdf(0.975)`, conferido com os valores já registrados (8 em 40: 10,50% a 34,76%; 0 em 40: até 8,76%) | Lição 1.7 |
| A38 | 2026-11-02 | Registro de vereditos da inspeção: `domain/registro_vereditos.py` é imutável (`RegistroVereditos`, `Julgamento`, `Correcao`); cada máscara recebe um único veredito, e mudá-lo exige uma correção com motivo não vazio e veredito diferente, que mantém o anterior no histórico; o registro é preso à fonte e ao SHA-256 do arquivo da amostra (recusa se mudaram); as horas são ISO 8601 com fuso, fornecidas de fora (o domínio não lê o relógio); gravação em `manifests/vereditos_inspecao_<fonte>.json` por arquivo temporário e `os.replace` (atômica), JSON com indentação de 2 espaços, LF e quebra final | Lição 1.7 |
| A39 | 2026-11-02 | Sessão de julgamento em `presentation/sessao_julgamento.py`, com entrada, saída, abertura de imagem, relógio e gravação injetados: máscaras na ordem do sorteio; só a posição ("12 de 40"), nunca contagens parciais; rubrica da A31 no início e nas posições 11, 21 e 31; teclas a, i, d e s, com observação opcional; grava depois de cada veredito (retomável); sem confirmação por imagem; a imagem abre sozinha no visualizador do Windows (`os.startfile`); correções só pelo comando `corrigir` e só antes de calcular o resultado | Lição 1.7
| A40 | 2026-11-02 | Resultado da inspeção do CCSD (regra da A31): 40 adequadas, 0 inadequadas, 0 duvidosas, 0 correções; o CCSD é aprovado como fonte de máscaras; intervalo de Wilson de 95% das inadequadas: 0,0% a 8,8%; a sensibilidade às duvidosas é igual, pois não houve duvidosas. Julgamento só do Gui (A33), de 19:08:17 a 19:15:58 UTC de 2026-11-02 (7 min 41 s, cerca de 12 s por imagem; o Gui atribui o ritmo à qualidade evidente das imagens). O comando `resultado` foi commitado depois dos vereditos (`62c3b9f`, `01a9dd1`) e antes de ser rodado | Lição 1.7 |
| A41 | 2026-11-04 | Pré-registro do critério de binarização das máscaras, commitado antes de qualquer medição (`07d746d`): o desvio de um pixel é o valor absoluto da diferença para a mediana da máscara, arredondado para cima (assim os limiares inteiros são exatos), medido em resolução cheia e antes de qualquer redução; grade de limiares de 16 a 240 em passos de 16; limiar de treino 128 em qualquer caso (metade do contraste de 255); patamar entre 64 e 192, com binarização robusta se a área em 192 for pelo menos 0,80 da área em 64 e sensível caso contrário (limitação registrada); máscara anômala se a fração de fissura em 128 passar de 10% (listada com nome, tratada à parte, sem mudar o 128). Os valores ficam em `config/regras.py`, travados por teste | Lição 1.8 |
| A42 | 2026-11-04 | Resultado da medição de binarização (458 máscaras, 5.500.237.824 pixels, manifesto de arquivos com sha256 `80da125a8176`): área de fissura de 1,375% no limiar 16, 1,364% de 48 a 224 e 1,355% no 240; razão do patamar 1,000, binarização ROBUSTA; 0 máscaras anômalas; limiar de treino 128 mantido. O comando `medicao` foi commitado (`6b7be02`) antes de ser rodado nos dados. Desbalanceamento: cerca de 72 pixels de fundo por pixel de fissura | Lição 1.8 |
| A43 | 2026-11-06 | Pré-registro do método de quase-duplicatas, commitado antes de qualquer cálculo (`c1ac02b`): opção C (dHash como baseline e escalada para embeddings só se reprovado por critério medido). dHash duplo de 128 bits (8x9 horizontal e 9x8 vertical, por média de blocos), fotos lidas com redução de 8x e orientação EXIF aplicada antes do hash; controle positivo com 40 bases sorteadas (seed 20261106) e 5 variações cada (JPEG qualidade 70, brilho x0,85 e x1,15, recorte de 5% e 10% de um lado sorteado por hash); limiar T = menor inteiro que reconhece pelo menos 95% das 200 variações, sem nenhum par real na escolha; grupos por componentes conexos (distância <= T); o dHash é reprovado se o maior grupo tiver mais de 10% das fotos (46 ou mais em 458) ou se mais de 2% dos pares reais ficarem a distância <= T. Meta declarada: reconhecer o mesmo enquadramento com deslocamento de até 10% | Lição 1.9 |
| A44 | 2026-11-06 | Resultado do dHash no CCSD (458 fotos, manifesto sha256 `80da125a8176`): medianas das distâncias do controle de 0,5 (JPEG), 0,0 e 0,0 (brilhos), 10,0 (recorte 5%) e 19,5 (recorte 10%); T = 23, com 80% dos recortes de 10% reconhecidos e 100% das demais variações; 292 de 104.653 pares ligados (0,28%, passa); 311 grupos, sendo 301 de 1 foto, 7 de 2, 1 de 3, 1 de 4 e 1 de 136; **dHash REPROVADO** pelo maior grupo (136 > 45). O grupo de 136 com cerca de 275 ligações é uma corrente (efeito cascata), e os números não distinguem corrente de semelhanças fracas de série real. Pela A43, escalar para embeddings, sem mudar T nem a regra de agrupamento. O comando foi commitado (`49ac137`) antes de rodar nos dados | Lição 1.9 |
| A45 | 2026-11-06 | Pré-registro da escalada para embeddings, commitado antes de qualquer embedding calculado. **Método:** DINOv2 ViT-S/14 (`vit_small_patch14_dinov2.lvd142m`, pesos oficiais da Meta, licença Apache 2.0) via `timm==1.0.31`; escolhido em vez da ResNet-18 do ImageNet porque foi treinado para reconhecer a mesma imagem sob alterações, e uma rede de classificação tenderia a achar todo concreto parecido, o que tornaria um "não" ambíguo. Pesos baixados uma vez, com SHA-256 registrado em manifesto (confiança no primeiro uso) e conferido a cada uso, fora do Git. Entrada: RGB lido com redução de 4x, orientação EXIF aplicada, foto inteira redimensionada para 518x518 (sem corte) e normalizada com média e desvio do ImageNet. Controle positivo igual ao da A43, em cor (mesmas 40 bases, mesmas 5 variações e mesmos lados de recorte). Distância de cosseno; T = menor valor observado que cobre 95% das 200 variações; mesmos critérios (a) e (b). **Árvore de decisão:** aprovados, os grupos dos embeddings vão para a divisão; reprovados só por (a), calcula-se a densidade do maior grupo (ligações internas / pares possíveis; >= 0,5 declara série real, < 0,5 declara corrente) e o grupo vai inteiro para o treino (opção A), com os demais grupos sorteados; reprovados por (b), com ou sem (a), os embeddings são descartados e valem os grupos do dHash (A44) com a opção A, declarando que deslocamentos acima de 10% não são detectados; maior grupo acima de `proporcao_treino` (70%) das fotos, em qualquer método, leva o CCSD inteiro para treino e validação e o teste para outra fonte (S2DS), sem quebrar o grupo. **Métricas ruins no futuro:** seguir e relatar as limitações; ou revisar o método antes de abrir o teste, guiado só pela validação; ou depois, relatando o teste original como saiu e usando um conjunto de teste novo, nunca usado (`avaliacoes_teste_por_conjunto = 1`). **Julgamento humano fora desta etapa:** já há instrumento automático, e um julgamento de "mesma superfície?" correria o risco de viés para facilitar o projeto (observação do Gui). **Observação registrada antes da medição:** no julgamento das máscaras (lição 1.7), o Gui notou fotos parecidas, com nuances de diferença; é uma impressão de 40 fotos e não entra na decisão | Lição 1.10 |
| A46 | 2026-11-07 | Resultado dos embeddings DINOv2 no CCSD (458 fotos, manifesto de arquivos `80da125a8176`, pesos na revisão `4610ca14` com SHA-256 `04d27f34`; o comando `a65c035` foi commitado antes de rodar): medianas da distância de cosseno no controle de 0,0027 (JPEG 70, máximo 0,0708), 0,0001 e 0,0007 (brilhos), 0,0025 (recorte 5%) e 0,0037 (recorte 10%); T = 0,0050, reconhecendo 95% do JPEG, 100% dos brilhos, 92,5% dos recortes de 5% e 87,5% dos de 10%; 7 de 104.653 pares ligados (0,01%); 451 grupos (444 de 1 foto e 7 de 2); maior grupo de 2 fotos, densidade 1; **embeddings APROVADOS** pela A45, e os 451 grupos seguem para a divisão. O resultado reforça, sem provar, que o grupo de 136 do dHash era uma corrente. T = 0,0050 mede "quase idênticas" (a mesma foto com até 10% de recorte), não "mesma superfície": séries reais com mudança de ponto de vista provavelmente não são detectadas (limitação da A43 e da A45, agora com número). Nenhum número foi mudado depois da execução | Lição 1.10 |
| A47 | 2026-11-08 | Pré-registro da análise descritiva dos vizinhos mais próximos, commitado antes de qualquer cálculo. Para cada uma das 458 fotos, a distância de cosseno ao vizinho mais próximo, com os mesmos pesos e o T gravado em `grupos_ccsd.json` (não recalculado). Conferência: o agrupamento em T tem de reproduzir exatamente os 451 grupos gravados, senão o comando recusa. Relato só com números: quantis (mínimo, 5%, 25%, mediana, 75%, 95%, máximo); contagem de fotos por faixa (até T, de T a 2T, de 2T a 5T, de 5T a 10T, de 10T a 20T e acima de 20T); e, só para descrever a fragilidade, como ficariam pares, grupos e o maior grupo em 2T e 5T, sem que nenhum deles seja opção de limiar. Redação da limitação fixada antes: **relevante** se mais de 5% das fotos (23 ou mais de 458) tiverem o vizinho mais próximo acima de T e até 2T; **pequena** caso contrário. Em nenhum caso a decisão da A46 muda. Valores em `config/regras.py`, travados por teste | Lição 1.11 |
| A48 | 2026-11-08 | Resultado da análise descritiva da A47 (458 fotos, mesmos pesos e T = 0,0050 de `grupos_ccsd.json`; o agrupamento em T reproduziu os 451 grupos gravados; comando `4b7d911` commitado antes de rodar). Distância ao vizinho mais próximo: mínimo 0,0003; 5% 0,0098; 25% 0,0178; mediana 0,0228; 75% 0,0290; 95% 0,0427; máximo 0,1931. Fotos por faixa: até T 14; de T a 2T 14; de 2T a 5T 252; de 5T a 10T 165; de 10T a 20T 12; acima de 20T 1. Só descritivo: com 2T, 14 pares, 444 grupos e maior grupo de 2; com 5T, 602 pares, 208 grupos e maior grupo de 219. Quase ligadas: 14 de 458 (3,1%), abaixo do corte de 5%; **limitação de T declarada PEQUENA** pela regra da A47, e a A46 não muda. Observações registradas junto com o rótulo: (1) a folga acima de T é estreita (mediana de 4,6T; 55% das fotos com vizinho entre 2T e 5T); (2) entre 2T e 5T a medida passa de pares limpos para uma corrente de 219 fotos, e eventuais séries reais da mesma parede vista de outro ponto ficariam nessa faixa, misturadas com a semelhança genérica; (3) as 14 quase ligadas formam 7 pares mútuos não agrupados, e com 70/15/15 o esperado é que cerca de 2 deles (7 x 2 x 0,15 x 0,85) cruzem a fronteira do teste. Decidido: pré-registrar na lição da divisão uma auditoria só descritiva que conte quantos desses 7 pares cruzam a fronteira do teste, sem alterar a divisão | Lição 1.11 |
| A49 | 2026-11-08 | Pré-registro da divisão do CCSD, commitado antes de qualquer código da divisão. **Unidade:** os 451 grupos de `grupos_ccsd.json`, inteiros; as proporções valem para as 458 fotos: teste = validação = arredondamento de 15% x 458 = 69 fotos cada, e treino = o restante, 320 fotos. **Sorteio:** cada grupo recebe a chave `sha256("20261022:" + primeiro nome do grupo em ordem alfabética)` e os grupos são percorridos em ordem crescente de chave; cada grupo vai para o teste se couber nas 69, senão para a validação se couber nas 69, senão para o treino; um grupo nunca é partido. **Nenhum novo sorteio:** a seed é a 20261022 (A13) e não muda, qualquer que seja a distribuição resultante. **Arquivo:** `manifests/split_v1.json` com a seed, as proporções, o SHA-256 de `grupos_ccsd.json` e do manifesto de arquivos, e as fotos de cada conjunto; gravado uma única vez. **Vazamento, em dois níveis:** testes sintéticos no domínio (nenhum grupo em dois conjuntos, mesma seed gera a mesma divisão, seeds diferentes geram divisões diferentes, totais exatos, par nunca partido, e uma divisão de mini-dataset conferida à mão que trava o algoritmo) e um teste no CI sobre os arquivos versionados reais (todo grupo inteiro num só conjunto; as 458 fotos exatamente uma vez). **Só relatados, sem alterar a divisão:** por conjunto, número de fotos, resoluções armazenadas e fração de pixels de fissura no limiar 128 da A41 (mediana, quartis e total, máscaras em resolução cheia); e a auditoria dos 7 pares quase ligados da A48, gravados antes em `manifests/quase_ligadas_ccsd.json` por um comando que recusa se não reproduzir as 14 fotos, contando quantos pares têm uma foto no teste e a outra fora (esperado cerca de 1,8) e quantos estão em conjuntos diferentes quaisquer. **Ordem dos commits:** este pré-registro, o código, os pares quase ligados, `split_v1.json`, e depois a distribuição e a auditoria | Lição 1.12 |
| A50 | 2026-11-08 | Execução da A49, parte 1 (divisão e auditoria). **Divisão gravada** em `manifests/split_v1.json` (`3e8e25a`, SHA-256 `bd93defe4a45`): treino 320, validação 69, teste 69, seed 20261022, a partir de `grupos_ccsd.json` (`bd046b980247`) e do manifesto de arquivos (`80da125a8176`); o comando recusa se o manifesto mudou desde os grupos e não sorteia de novo. **Auditoria no CI** (`c8bbc50`): a cada push, confere tamanhos, seed e proporções, as 458 fotos uma única vez, nenhum grupo partido, os hashes de procedência, a reprodução da A49 e o arquivo byte a byte. **Auditoria dos 7 pares quase ligados** (comando `a4560a0`, commitado antes de rodar; só relata): 1 par com uma foto no teste e a outra fora (esperado ao acaso 1,80) e 2 pares em conjuntos diferentes quaisquer (esperado 3,27). O par que cruza o teste é `rgb/100.jpg` (teste) com `rgb/098.jpg` (validação); o outro é `rgb/534.JPG` (treino) com `rgb/536.JPG` (validação); os outros 5 pares estão inteiros no treino. **Leitura fixada antes de rodar, aplicada sem mudança:** k = 1, então `rgb/100.jpg` (1/69 = 1,4% do teste) fica listada e a avaliação final reporta a métrica do teste com as 69 fotos e sem ela (68). Observações, sem ação: a gêmea da foto do teste está na validação, não no treino, então nenhuma foto do teste tem quase gêmea no treino; uma foto da validação (`rgb/536.JPG`) tem quase gêmea no treino. A divisão não muda. **Pendente da A49:** distribuição de fissura por conjunto | Lição 1.12 |
| A51 | 2026-11-10 | Execução da A49, parte final (distribuição por conjunto; comando `82befb4`, commitado antes de rodar; só relata). Leitura fixada antes de rodar: razão da fração total e da mediana de validação e teste em relação ao treino; de 0,75 a 1,25, comparável; fora disso, diferente, registrado como contexto; nenhum caso muda a divisão. **Fissura no limiar 128** (fração total; quartis por máscara: 1º, mediana, 3º): treino 1,400% (0,950%, 1,192%, 1,588%); validação 1,345% (0,980%, 1,192%, 1,571%); teste 1,216% (0,869%, 1,057%, 1,364%). Razões em relação ao treino: validação 0,96 (total) e 1,00 (mediana); teste 0,87 e 0,89; **os dois conjuntos são comparáveis**. Observação, sem ação: o teste fica de 11% a 14% abaixo do treino em todas as medidas (fissuras em geral mais finas ou mais curtas), o que pode puxar levemente para baixo as métricas por pixel do teste por causa dos dados. **Resoluções armazenadas** (4032x3024, 3264x2448, 2448x3264): treino 306, 9, 5; validação 65, 2, 2; teste 67, 2, 0 (nenhuma foto armazenada em retrato no teste). **Conferência:** os pixels por conjunto somam 5.500.237.824 e a fração ponderada dá 1,3639%, reproduzindo a A42. Com isto, a A49 está executada por inteiro | Lição 1.12 |
| A52 | 2026-11-10 | Pré-registro dos tiles do CCSD, commitado antes de qualquer código de tiles, com os valores em `config/regras.py`. **(1) Tamanho:** 512 px na escala nativa e 256 px na escala reduzida 2×, os dois cobrindo a mesma área da foto (512×512 px nativos), para que o experimento de resolução da Sprint 4b mude só a resolução (R14); 512 é múltiplo de 32, dá contexto para a continuidade das fissuras e cabe em lotes razoáveis. **(2) Grade:** passo igual ao lado, sem sobreposição na geração; último tile encostado na borda (por exemplo, 3520 em 4032 e 2512 em 3024); cobertura de 100% da foto, sem padding e sem descarte; a sobreposição é da previsão (Sprint 3). **(3) Ordem:** orientação EXIF (A34), redução da foto inteira por média de área (só na escala 2×) e recorte; cada foto fica na resolução nativa, sem igualar tamanhos (o CCSD não tem escala em mm, e ampliar mudaria a largura das fissuras em pixels). **(4) Máscaras:** binarização da A41 antes de tudo; na escala 2×, redução por média, que deixa a máscara fracionária; a regra de volta ao binário (maioria, qualquer ou suave) é medida agora e escolhida na Sprint 4a, antes de rodar a 4b. **(5) Avaliação sempre na resolução nativa**, contra a máscara original; a previsão da escala 2× é ampliada antes das métricas. **(6) Índice de tiles** versionado em `manifests/tiles_v1.json` (foto, escala, x, y, lado, conjunto), auditado no CI: conjunto herdado da foto-mãe, cobertura completa e reprodução pela regra. **(7) Pixels:** derivados, nunca versionados nem gravados no Drive (9 GB livres, sem como ampliar); o Drive guarda só o RAR da A29; em cada sessão do Colab, o mesmo código gera os tiles no disco da máquina virtual e os confere contra um manifesto de hashes dos bytes dos pixels, gerado antes localmente; se um hash não bater, o treino não começa; localmente, os tiles ficam em `data/interim/`. **(8) Medição descritiva só no treino**, que não muda os itens de 1 a 7: (a) por escala, fração de tiles sem nenhum pixel de fissura e, nos tiles com fissura, mediana e quartis da fração de fissura; (b) na escala 2×, para as regras maioria e qualquer, fração dos pixels de fissura preservados e de pixels a mais na ida e volta, no total e por máscara; informa a escolha da 4a; (c) tempo de geração e tamanho em disco dos tiles. **Já decidido antes e mantido:** tiles depois da divisão, herdando o conjunto; duas escalas; tiles sem fissura tratados no treino (Sprint 3b); augmentation só no treino. **Correção da A51:** a falta de fotos armazenadas em retrato no teste pesa pouco para os tiles, porque o recorte é feito na orientação de exibição (as 179 fotos com EXIF 6 viram retrato) e as rotações de 90° estão no augmentation | Lição 1.14 |
| A53 | 2026-11-10 e 2026-11-11 | Execução da A52, parte 1 (grade e índice). **Grade** no domínio (`07a37d7`): passo igual ao lado e último tile encostado na borda; 48 tiles por foto de 12 MP e 35 por foto de 8 MP, em qualquer orientação e nas duas escalas. **Escalas alinhadas** (`0138500`): como o tile de 256 na escala 2× cobre a mesma área do tile de 512 na nativa, as posições da 2× multiplicadas por 2 são exatamente as da nativa (por exemplo, 1760 × 2 = 3520 e 1256 × 2 = 2512); cada tile da 2× é a mesma região da foto que um tile da nativa, o que permite comparar as escalas tile a tile na Sprint 4b. **Índice gravado** em `manifests/tiles_v1.json` (`96d6297`, SHA-256 `0a761279ce31`; comando `5ccef92`, commitado antes de rodar): 458 fotos, uma por linha (466 linhas), com o tamanho de exibição pela orientação EXIF (A34) lido só dos cabeçalhos; tamanhos 4032x3024 em 259 fotos, 3024x4032 em 179, 3264x2448 em 13 e 2448x3264 em 7; **43.448 tiles**, 21.724 por escala, com treino 15.178, validação 3.260 e teste 3.286 em cada uma. Todas as contagens previstas antes de rodar saíram exatas. **Auditoria no CI** (`2542213`): procedência (hashes da divisão e do manifesto), conjunto de cada foto igual ao da divisão, escalas pré-registradas, tamanhos de exibição, grade refeita pela regra, contagens e formato byte a byte. O CI não relê a orientação EXIF (não tem as fotos); ela foi travada pelo gate do comando e conferida indiretamente pelos tamanhos (179 em retrato). **Pendente da A52:** geração dos pixels com o manifesto de hashes (item 7) e a medição descritiva (item 8) | Lição 1.14 |
| A54 | 2026-11-13 | Execução da A52, item 7 (geração dos pixels): três escolhas aprovadas antes do código. **(A) O que o manifesto confere:** o manifesto de hashes (`manifests/pixels_tiles_v1.json`) confere a imagem inteira já preparada, por foto e por escala (foto orientada e reduzida; máscara binarizada e reduzida), num total de 458 × 2 × 2 = 1.832 hashes, em vez de um hash por tile; os tiles são recortes feitos por função pura e testada com a grade versionada, então são idênticos por construção. **(B) Máscara reduzida:** na escala nativa, a máscara é gravada como 0 e 255; nas reduzidas, como a contagem de pixels de fissura de cada bloco (de 0 a 4 na escala 2×, uint8, sem perdas), o que mantém as três regras da Sprint 4a disponíveis sem regerar nada (maioria: contagem ≥ 2; qualquer: ≥ 1; suave: contagem / 4). **(C) Decodificação:** a versão do Pillow fica registrada no manifesto, e o Colab usa a mesma; se um hash não bater, o treino não começa (A52). A binarização reusa a regra da A41 (desvio do fundo ≥ 128, em resolução cheia). Os tiles ficam em `data/interim/tiles_ccsd/`, fora do Git | Lição 1.14 |

## 2. Commits e verificações

| Commit | O que | Verificação |
|---|---|---|
| `3c0efd7` | Fundação: ambiente, pacote em camadas, pre-commit | Todos os hooks passaram |
| `fd7aee8` | Teste de arquitetura com 16 casos do analisador | 23 testes; falha provocada (`import torch` no `domain`) detectada |
| `77a65d4` | Regras pré-registradas travadas por teste (A13) | 33 testes; falha provocada (`4 == 3`) detectada |
| `d9f6634` | Marcadores `torch` e `data` fora do pytest padrão (A18) | 33 passed, 1 deselected |
| `2ef9a90` | CI com as jobs `core` e `dl` | Duas jobs verdes na `main` (51 s) |
| `5730f0f` | Falha proposital, só no PR #1 (não mesclado) | Ver seção 3 |
| `74a983f` | LICENSE MIT (A20) | Detectada pelo GitHub |
| `fd2eebd` | README inicial e NOTES.md (decisões A1 a A20) | Duas jobs verdes na `main` |
| `8aa3898` | Fechamento da Sprint 0 no NOTES.md | Árvore limpa, em dia com `origin/main` |
| `6f833c5` | Ficha de procedência e manifesto de fontes (CCSD e S2DS) | 49 passed; trava de licença do S2DS vista falhando (`assert True is False`) e desfeita |
| `ee6c985` | Sprint 1 aberta no NOTES.md (A21 a A23) | Duas jobs verdes na `main` |
| `8a6beb4` | Pytest usa pasta temporária do projeto (A24) | 49 passed no terminal novo, sem traceback; CI verde |
| `6c48d4b` | A24 e lição 1.1 concluída no NOTES.md | Duas jobs verdes na `main` |
| `edddc64` | Registro de arquivos e comparação de integridade (lição 1.2) | 76 passed; trava do caminho `.` vista falhando (`DID NOT RAISE`) e desfeita |
| `7e56d6c` | Lição 1.2 concluída no NOTES.md (A25 e A26) | Duas jobs verdes na `main` (76 passed, 1 passed) |
| `389203f` | Hash em disco e manifesto de arquivos em JSON (lição 1.3) | 87 passed; teste de arquivo grande visto falhando com o laço de blocos quebrado e desfeito |
| `55176da` | Lição 1.3 concluída no NOTES.md (A27) | Duas jobs verdes na `main` |
| `58434bc` | Comandos `registrar` e `verificar` para fontes de dados (lição 1.4, parte A) | 101 passed; a regra de não sobrescrever o manifesto foi vista falhando (2 failed) e desfeita |
| `5e18855` | Manifesto de arquivos do CCSD: 917 entradas, RAR direto (A29) | Hash do RAR confere com o `Get-FileHash`; `verificar ccsd` sem divergência |
| `e676540` | Ficha do CCSD com o download truncado e a estrutura observada | 101 passed |
| `46b9334` | Lição 1.4 concluída no NOTES.md (A28 a A30) | Duas jobs verdes na `main` |
| `7dd5ba9` | Protocolo de inspeção das máscaras travado em `REGRAS` (A31) | 104 passed; limiar trocado de 8 para 9 de propósito, falhou com `assert 9 == 8`, desfeito; CI verde |
| `df2b269` | Amostragem determinística por hash (A32) | 114 passed; separador do hash trocado de ":" para "-" de propósito, o vetor conhecido falhou (`('001', '003', '007')` contra `('001', '004', '009')`), desfeito; CI verde |
| `43888c4` | Comando `sortear` da amostra de inspeção | 123 passed; bloco que impede refazer o sorteio comentado, 2 failed (`DID NOT RAISE FileExistsError` e `assert 0 == 2`), desfeito; CI verde |
| `14e1dfe` | Amostra de inspeção do CCSD: 40 de 458 máscaras, sorteada antes de qualquer máscara ser vista | CI verde |
| `b3de743` | Lição 1.5 concluída no NOTES.md (A31 a A33) | CI verde |
| `566e0d4` | Pareamento de máscaras e fotos pelo nome (`domain/pareamento.py`) | 130 passed; CI verde |
| `f1865f4` | Comando `parear` (`presentation/estrutura.py`) | 140 passed; 458 pares, pareamento completo; CI verde |
| `7d06213` | Conferência de dimensões no domínio (`Cabecalho`, `conferir_dimensoes`) | CI verde |
| `ae99663` | Leitura do cabeçalho da imagem (largura, altura, orientação EXIF) em `infrastructure/imagens.py` | CI verde |
| `d2d044e` | Subcomando `dimensoes` | 179 pares com eixos trocados, achados no CCSD real; CI verde |
| `ed2fa18` | Tamanho exibido com a orientação EXIF na conferência de dimensões | 173 passed; 0 divergências de tamanho após a orientação; CI verde |
| `2fa0082` | Alinhamento foto-máscara: orientação EXIF verificada por contraste (A34, A35) | 244 passed; 458 de 458 pares com vantagem positiva; sentido da rotação 6 e 8 invertido de propósito reprovou o grupo 6 (0%) e quebrou 5 testes, desfeito; CI verde |
| `7704b51` | Lição 1.6 concluída no NOTES.md (A34 e A35) | CI verde |
| `12c63c4` | Visualizador de inspeção das máscaras: orientação em RGB, sobreposição, painel, `ler_rgb`, `gravar_png` e comando `preparar` (A36) | 296 passed; versão antiga de `orientacao.py` (com `.T`) reprovou o teste RGB das orientações 5 e 7 (2 failed); manifesto alterado de propósito fez o `preparar` recusar com código 2; CI verde |
| `77c2c70` | Vereditos, regra de reprovação e intervalo de Wilson (A37) | 318 passed; `>` no lugar de `>=` na regra reprovou 2 testes (`test_8_inadequadas_em_40_reprovam` e `test_sem_duvidosas_a_sensibilidade_nao_muda_a_decisao`), desfeito; CI verde |
| `109d99f` | Lição 1.7 (ferramenta de inspeção) registrada no NOTES.md (A36 e A37) | CI verde |
| `4f78647` | Registro imutável de vereditos e gravação atômica em JSON (A38) | 350 passed; com a gravação direta no destino, sem arquivo temporário nem `os.replace`, falhou 1 teste (`test_falha_na_troca_preserva_o_arquivo_anterior`, `DID NOT RAISE OSError`) e 7 passaram; o arquivo era novo e o `git checkout` não o restaurou, então foi recolado inteiro; CI verde |
| `5c584d1` | Sessão de julgamento e comandos `julgar` e `corrigir` (A39) | 385 passed; com a comparação do SHA-256 da amostra trocada por `False`, falhou 1 teste (`test_recusa_registro_de_outra_amostra`, `DID NOT RAISE ValueError`) e 18 passaram; desfeito pelo Git; CI verde |
| `62c3b9f` | Vereditos das 40 máscaras do CCSD (`manifests/vereditos_inspecao_ccsd.json`) | commitado antes de qualquer cálculo de resultado; CI verde |
| `01a9dd1` | Comando `resultado`: regra pré-registrada aplicada aos vereditos (A40) | 397 passed; CI verde |
| `1e22c54` | Lição 1.7 concluída e CCSD aprovado na inspeção das máscaras (A38 a A40) | CI verde |
| `07d746d` | Pré-registro do critério de binarização das máscaras (A41) | 411 passed; com a razão mínima do patamar trocada de 0,80 para 0,75, falhou 1 teste (`test_patamar_entre_64_e_192_com_razao_minima_de_80_por_cento`, `assert 0.75 == 0.8`) e 26 passaram; desfeito pelo Git; CI verde |
| `6f454c7` | Funções puras de binarização no domínio: contagem por desvio, patamar e anomalia | 434 passed; com `razao >= razao_minima` trocado por `>`, falhou 1 teste (`test_patamar_na_fronteira_de_80_por_cento_e_robusto`, `assert False`) e 22 passaram; desfeito pelo Git; CI verde |
| `6b7be02` | Comando `medicao`: mede a binarização das 458 máscaras (A42) | 450 passed; com a leitura em fator 2 em vez de resolução cheia, falharam 3 testes (`test_mede_em_resolucao_cheia`, `test_lista_a_mascara_anomala_com_a_fracao`, `test_relatorio_traz_numeros_curva_classificacao_e_nomes`) e 13 passaram; desfeito pelo Git; CI verde |
| `8889422` | Lição 1.8 concluída: binarização robusta e limiar 128 mantido (A41 e A42) | CI verde |
| `c1ac02b` | Pré-registro do método de quase-duplicatas (A43) | 470 passed; com a cobertura do limiar trocada de 0,95 para 0,90, falhou 1 teste (`test_limiar_reconhece_95_por_cento_das_variacoes`, `assert 0.9 == 0.95`) e 46 passaram; desfeito pelo Git; CI verde |
| `3fcd164` | Domínio: dHash duplo, limiar por cobertura, agrupamento e critério de escalada | 496 passed; sem a tolerância de ponto flutuante no limiar, falhou 1 teste (`test_limiar_com_produto_inexato_nao_exige_distancia_a_mais`, `assert 7 == 6`) e 25 passaram; desfeito pelo Git; CI verde |
| `8bdfb51` | Variações do controle positivo: brilho e recorte no domínio, recompressão JPEG na infraestrutura | 518 passed; sem a saturação do brilho, falhou 1 teste (`test_brilho_satura_em_255`, `[[230, 20, 37]]` em vez de `[[230, 255, 255]]`, igual no Windows e no Linux) e 21 passaram; desfeito pelo Git; CI verde |
| `49ac137` | Comando `duplicatas`: controle positivo, agrupamento e critério de escalada (A44) | 531 passed; ignorando a orientação EXIF, falhou 1 teste (`test_orientacao_exif_e_aplicada_antes_do_hash`, a foto deitada ficou sozinha) e 12 passaram; desfeito pelo Git; CI verde |
| `6ea6f41` | Lição 1.9 registrada: dHash reprovado pelo maior grupo e escalada para embeddings (A43 e A44) | CI verde |
| `fccf01b` | Pré-registro da escalada para embeddings e árvore de decisão (A45), com o NOTES no mesmo commit | 539 passed; com a densidade mínima de série trocada de 0,5 para 0,3, falhou 1 teste (`test_grupo_com_densidade_de_50_por_cento_ou_mais_e_serie_real`, `assert 0.3 == 0.5`) e 54 passaram; desfeito pelo Git; CI verde |
| `4e01b1c` | Adaptador de embeddings DINOv2 via `timm==1.0.31`, testado sem pesos; `timm` restrito à infraestrutura; extra `dl` instalado na job `dl` do CI | 539 passed e 11 com torch; sem a divisão por 255, falhou 1 teste (`test_preparo_de_imagem_uniforme_e_constante_por_canal`, 556,8 em vez de 0,074) e 10 passaram; desfeito pelo Git; CI verde |
| `6aae2fe` | Registro de procedência dos pesos e carregamento estrito com hash conferido | 555 passed e 14 com torch; sem a conferência do hash, falhou 1 teste (`test_hash_divergente_e_recusado_antes_de_carregar`, `DID NOT RAISE`) e 13 passaram; desfeito pelo Git; CI verde |
| `70f7873` | Comando `pesos` (`baixar` e `conferir`) com revisão fixa e manifesto; `huggingface_hub` restrito à infraestrutura | 560 passed e 17 com torch; baixando de `"main"` em vez da revisão consultada, falhou 1 teste (`test_baixar_usa_a_revisao_consultada_e_grava_o_manifesto`) e 4 passaram; desfeito pelo Git; CI verde |
| `7d1fcaa` | Manifesto dos pesos: `timm/vit_small_patch14_dinov2.lvd142m`, revisão `4610ca143709d58a633b6397a74412c2c3842454`, 88.240.510 bytes, SHA-256 `04d27f3400d059fc0cfd7d17dd1909a75bf3ea8fb3eeb48b97cb99e57ee20081` | download único; `conferir`: hash confere e a rede devolve 384 números; só o manifesto entrou no Git; CI verde |
| `279441f` | Variações em cor, distância de cosseno, densidade do grupo e corte de série | 577 passed; com o corte estrito (`>` em vez de `>=`), falhou 1 teste (`test_serie_real_a_partir_do_corte_inclusive`) e 36 passaram; desfeito pelo Git; CI verde |
| `a65c035` | Comando `duplicatas_embeddings` e árvore de decisão da A45 no domínio (A46) | 593 passed e 17 com torch; sem a pergunta (b), falharam 3 testes (`test_pares_demais_voltam_ao_dhash_mesmo_com_grupo_grande`, `test_fotos_todas_iguais_voltam_ao_dhash`, `test_relatorio_da_volta_ao_dhash`) e 13 passaram; desfeito pelo Git; CI verde |
| `a336f8f` | Lição 1.10 registrada: embeddings aprovados (A46) e limitação de T | CI verde |
| `b93054a` | Gravação dos grupos de quase-duplicatas conferida contra a A46 (registro com procedência, gravado uma única vez) | 606 passed e 17 com torch; sem a conferência contra a referência, falhou 1 teste (`test_execucao_que_nao_reproduz_a_referencia_e_recusada`, `DID NOT RAISE`) e 12 passaram; desfeito pelo Git; CI verde |
| `60774f3` | `manifests/grupos_ccsd.json`: 451 grupos com 458 fotos (444 isoladas e 7 pares), da segunda execução, que reproduziu a A46 exatamente | 1.369 linhas, conferidas pela estrutura (444 x 3 + 7 x 4 + 9); CI verde |
| `0dcf20f` | NOTES: grupos do CCSD gravados e conferidos contra a A46 | CI verde |
| `ffd611e` | Pré-registro da análise descritiva dos vizinhos (A47), com o NOTES no mesmo commit | 617 passed; com o corte de quase ligadas trocado de 0,05 para 0,10, falhou 1 teste (`test_limitacao_relevante_com_mais_de_5_por_cento_ate_2t`, `assert 0.1 == 0.05`) e 65 passaram; desfeito pelo Git; CI verde |
| `4b7d911` | Comando `vizinhos` e funções do domínio da análise descritiva (A48) | 632 passed; com `side="right"` nas faixas, falhou 1 teste (`test_faixas_com_o_limite_na_faixa_de_baixo`, `[0, 2, 2, 1]` em vez de `[1, 2, 1, 1]`) e 14 passaram; desfeito pelo Git; CI verde |
| `655d571` | NOTES: análise descritiva dos vizinhos (A48), limitação pequena com folga estreita | CI verde |
| `f3c45bb` | Pré-registro da divisão do CCSD e da auditoria de vazamento (A49), antes de qualquer código da divisão | CI verde |
| `3ffe08c` | Domínio da divisão por grupos (A49): tamanhos, chave por hash, preenchimento teste, validação e treino, testes sintéticos de vazamento | 649 passed (632 + 17 de `test_divisao.py`, contagem reconstruída na lição 1.12; a saída do gate não ficou registrada); CI verde |
| `75c265b` | Registro dos pares quase ligados da A48 (comando que só grava se reproduzir as 14 fotos), com a matriz conferida compartilhada entre `vizinhos` e `quase_ligadas` | 660 passed, mais 17 com torch (a saída do gate não ficou registrada); CI verde |
| `9ef1d30` | `manifests/quase_ligadas_ccsd.json`: 7 pares (14 fotos), da execução que reproduziu a A48 | 36 linhas; CI verde |
| `d93dd03` | Comando `divisao` e registro da divisão com procedência (hashes dos grupos e do manifesto), gravado uma única vez | 673 passed; sem a conferência do manifesto, falhou 1 teste (`test_manifesto_alterado_depois_dos_grupos_e_recusado`, `DID NOT RAISE`) e 12 passaram; desfeito pelo Git; CI verde |
| `3e8e25a` | `manifests/split_v1.json`: treino 320, validação 69, teste 69 (seed 20261022), SHA-256 `bd93defe4a45` | 475 linhas, como previsto; CI verde |
| `c8bbc50` | Auditoria de vazamento no CI sobre os arquivos versionados (`tests/test_split_v1.py`, 6 testes) | 679 passed; trocando `rgb/523.JPG` (par de `rgb/283.jpg`, no teste) com `rgb/011.jpg` (isolada, no treino), falharam 3 testes (grupo partido, reprodução da A49, byte a byte) e 3 passaram; desfeito pelo Git; CI verde |
| `a4560a0` | Comando `auditoria` e domínio da auditoria dos pares quase ligados, commitados antes de rodar nos dados | 691 passed; com o "ou exclusivo" trocado por "e", falharam 4 testes e 8 passaram; desfeito pelo Git; CI verde |
| `96ed4ab` | NOTES: divisão v1 e auditoria dos pares quase ligados (A50) | 19 linhas inseridas e 1 removida, como previsto; CI verde |
| `0ce5bb2` | Domínio da distribuição de fotos e fissura por conjunto (fração total ponderada pelos pixels, quartis por máscara com interpolação linear) | 703 passed; com a fração total trocada pela média simples, falhou 1 teste (`test_fracao_total_pondera_pelos_pixels`, 0,025 em vez de 0,034) e 11 passaram; desfeito pelo Git; CI verde |
| `82befb4` | Comando `distribuicao`, commitado antes de rodar nos dados | 711 passed; lendo a foto no lugar da máscara, falharam 2 testes (resumo e relatório, com fissura 0) e 6 passaram; desfeito pelo Git; CI verde |
| `4fc2a25` | NOTES: distribuição por conjunto (A51), lição 1.12 concluída | 10 linhas inseridas e 3 removidas, como previsto; CI verde |
| `ab8feb4` | Trava do manifesto real do CCSD no CI (`tests/test_manifesto_ccsd.py`, 6 testes): hash do manifesto, fonte e data, 917 entradas (RAR, 458 máscaras e 458 fotos), RAR do download direto, pareamento completo e ficha com 458 imagens | 717 passed; com o tamanho do RAR alterado em 1 byte, falharam 3 testes (hash do manifesto e RAR no teste novo; hashes registrados no `test_split_v1.py`) e 9 passaram; desfeito pelo Git; CI verde |
| `3487abe` | NOTES: trava do manifesto real do CCSD (lição 1.13) | 6 linhas inseridas (a linha em branco contada) e 2 removidas; CI verde |
| `474bed6` | Pré-registro dos tiles do CCSD (A52), com regras e NOTES no mesmo commit, antes de qualquer código de tiles | 725 passed; medindo só a regra "maioria", falhou 1 teste (`test_mede_as_regras_maioria_e_qualquer_da_mascara_reduzida`) e 73 passaram; desfeito pelo Git; CI verde |
| `07a37d7` | Grade de tiles no domínio, com o último tile encostado na borda (A52) | 741 passed; sem o tile encostado, falharam 11 testes (4032x3024 caiu de 48 para 35 tiles) e 5 passaram; desfeito pelo Git; CI verde |
| `0138500` | Índice de tiles por foto e escala, com as duas escalas alinhadas (A52) | 756 passed; com a escala 2× calculada sobre o tamanho nativo, falharam 6 testes (total de 645 em vez de 262) e 9 passaram; desfeito pelo Git; CI verde |
| `5ccef92` | Comando `indice_tiles`, grade na orientação de exibição, commitado antes de rodar nos dados | 763 passed; ignorando a orientação EXIF, falhou 1 teste (`(1024, 768)` em vez de `(768, 1024)`) e 6 passaram; o total de tiles não pega esse erro; desfeito pelo Git; CI verde |
| `96d6297` | `manifests/tiles_v1.json`: 458 fotos, 43.448 tiles em duas escalas, SHA-256 `0a761279ce31` | 466 linhas e contagens como previsto; CI verde |
| `2542213` | Auditoria do índice de tiles no CI (`tests/test_tiles_v1.py`, 7 testes) | 770 passed; com `rgb/001.jpg` trocada da validação para o treino no JSON, falharam 2 testes (conjunto e contagens, validação com 3.225) e 5 passaram, inclusive o byte a byte, que só detecta mudança de formato; desfeito pelo Git; CI verde |

## 3. Falha provocada do CI (resultado deliberado, mantido)

O PR #1 trocou `max_experimentos_adicionais` de 3 para 4. A job `core` falhou com
`assert 4 == 3` em `test_no_maximo_tres_experimentos_adicionais` (`1 failed, 32 passed,
1 deselected`); a job `dl` passou. O lint passou antes: a falha é de comportamento, não
de estilo. O PR foi fechado sem mesclar e a branch foi apagada. A execução fica visível
no histórico do Actions como prova de que o CI rejeita uma violação de regra
pré-registrada.

## 4. Incidente de permissões (cache do pre-commit e pasta temporária do pytest)

### Primeira manifestação: cache do pre-commit

**Fatos observados**

- A primeira execução do `pre-commit` falhou com `PermissionError` ao ler o clone de
  `pre-commit-hooks v6.0.0` no cache (`~\.cache\pre-commit`); o próprio `pre-commit clean`
  falhou na mesma pasta.
- Duas pastas do cache estavam inacessíveis ao usuário comum, criadas no mesmo minuto em
  07/10/2026: uma é `pre-commit-hooks v6.0.0` (a versão que este projeto usa) e a outra
  é `ruff-pre-commit v0.16.10`. Nem `icacls` nem `Get-Acl` conseguiram ler as permissões.
- Outro projeto local do autor declara exatamente esse par de versões; nele o Claude Code
  foi executado dentro de um PowerShell elevado (administrador). A pasta-mãe do cache
  pertence ao grupo Administradores. O `git status` desse outro projeto não mostrou
  `dubious ownership`.
- Com `PRE_COMMIT_HOME=C:\pc-cache`, tudo passou.

**Hipótese (não verificada em todos os detalhes)**

As duas pastas foram criadas numa sessão elevada e ficaram inacessíveis à sessão comum.
O mecanismo exato das permissões não foi inspecionado.

### Segunda manifestação (2026-10-27): pasta temporária do pytest

**Fatos observados**

- O `pytest` terminou com `PermissionError` (WinError 5) em `pytest-current`, no `%TEMP%`,
  **depois** de os testes passarem: o erro está na limpeza final, que percorre links
  simbólicos. Os 16 testes de `test_procedencia.py` passaram, inclusive o que usa `tmp_path`.
- As entradas `pytest-275` a `277` e o link `pytest-current` são de 16/10/2026 (12:34 a
  12:39) e têm dono ilegível; as pastas criadas em 27/10 têm dono normal. O
  `pytest-current` é um ponto de reanálise (`Directory, ReparsePoint`) cujo tipo e destino
  o PowerShell não consegue ler.
- Contorno provisório: `TEMP` e `TMP` apontando para `C:\pytest-tmp` no terminal. Com isso,
  49 passed.

**Hipótese do autor, compatível com a evidência e não inspecionada**

Execuções do pytest num PowerShell elevado, em outro projeto, no período em que o Claude
Code foi usado nessa condição.

**Correção duradoura (A24)**

`--basetemp=.pytest_tmp` no `addopts` e `.pytest_tmp/` no `.gitignore`. Verificada num
terminal novo, com o `%TEMP%` original: 49 passed, 1 deselected, resumo normal e sem
traceback. É **uma** execução; a eficácia duradoura se confirma com o uso. Se o erro
reaparecer, registrar aqui.

### Pendências deste incidente

- Reproduzir a criação das pastas num diretório descartável, comparando uma sessão comum
  com uma elevada.
- Limpar as pastas antigas (duas no cache do pre-commit; as de 16/10 no `%TEMP%`) de um
  terminal elevado, depois de decidir se a evidência deve ser guardada.
- Vigiar o `C:\pc-cache` (`dir /q`): como a variável vale para o usuário, uma sessão
  elevada também escreveria ali. Previsão ainda não observada.

## 5. Pendências abertas

- [x] Sprint 1, antes de olhar as máscaras: fixar o limiar numérico de "máscaras inadequadas" (A31: 8 ou mais em 40)
- [x] Sprint 1, lição 1.9: método de quase-duplicatas pré-registrado (A43) e dHash medido no CCSD: reprovado pelo maior grupo, 136 fotos (A44)
- [x] Sprint 1: método de embeddings pré-registrado (A45): DINOv2 ViT-S/14 via timm, mesmo controle positivo e mesmos critérios de escalada
- [x] Sprint 1: decidido, antes de rodar os embeddings, o que fazer com um grupo grande demais (A45: opção A, densidade com corte em 0,5, lacunas 1 e 2)
- [x] Sprint 1, lição 1.10: embeddings implementados e medidos (A46): aprovados, 451 grupos (444 fotos isoladas e 7 pares)
- [x] Sprint 1, lição 1.11: os 451 grupos dos embeddings estão gravados em `manifests/grupos_ccsd.json` (`60774f3`), conferidos contra a A46 antes da gravação
- [x] Sprint 1, lição 1.11: análise descritiva dos vizinhos feita (A48): limitação de T declarada pequena, com 14 fotos quase ligadas (7 pares mútuos)
- [x] Sprint 1: divisão do CCSD e auditoria dos 7 pares quase ligados pré-registradas (A49)
- [x] Sprint 1, lição 1.12: A49 executada em parte (A50): código da divisão, `quase_ligadas_ccsd.json`, `split_v1.json` (320/69/69), auditoria no CI e auditoria dos 7 pares quase ligados (1 cruza o teste)
- [x] Sprint 1, lição 1.12: distribuição de fissura por conjunto medida (A51): validação e teste comparáveis ao treino; a A49 está executada por inteiro
- [ ] Avaliação final: reportar a métrica do teste com as 69 fotos e sem a `rgb/100.jpg` (68), análise de sensibilidade da A50
- [ ] Sprint 1: ler e aceitar os termos de uso do S2DS antes do download
- [ ] Sprint 1: avaliar a cópia do S2DS no Drive privado, para o Colab, contra o termo que proíbe distribuir
- [ ] Sprint 1, condicional: confirmar licença e download parcial do CiF
- [ ] Sprint 2: decidir onde mora o ajuste do Frangi (recomendação: serviço próprio de busca em grade)
- [ ] Sprint 3: a sonda escolhe L4 ou T4 e confirma a runtime ativa do Colab
- [ ] Sprint 7: decidir se os checkpoints serão publicados
- [ ] Sprint 7: avaliar fixar as ações do CI por hash de commit e congelar um `pip freeze`
- [ ] Conferir se o `ruff` instalado pelo pip está na mesma versão do hook; a autoridade é o hook (A17)
- [x] Correção duradoura para a pasta temporária do pytest (A24)
- [x] Sprint 1, lição 1.8: binarização das máscaras do CCSD para o treino decidida e medida: desvio do fundo, resolução cheia, limiar 128; binarização ROBUSTA (razão 1,000) e 0 máscaras anômalas nas 458 (A41 e A42)
- [ ] Sprint 2: tratar o desbalanceamento de classes (cerca de 72 pixels de fundo por pixel de fissura) na escolha da função de perda
- [ ] Sprint 1, lição 1.14: medir a sobrevivência das fissuras finas na escala 2× (A52, item 8b), só no treino
- [ ] Sprint 1: decidir o destino de `data/raw/_tentativas/` (evidência do download truncado) ao fim da sprint
- [x] Sprint 1, lição 1.13: teste que trava o manifesto real do CCSD no CI (`ab8feb4`): 917 entradas, hash do RAR e hash do próprio manifesto
- [ ] Opcional: relatar ao Mendeley que o Download All entrega o RAR truncado
- [x] Sprint 1, lição 1.7: ferramenta, sessão de julgamento e resultado concluídos; CCSD aprovado, 0 inadequadas em 40 (A40). As 40 imagens continuam em `data/interim/inspecao_ccsd/` (derivadas, fora do Git)
- [x] Sprint 1, lição 1.14: heterogeneidade de resolução decidida (A52): cada foto na resolução nativa, com a mesma regra de grade (fotos armazenadas: 438 em 4032x3024, 13 em 3264x2448, 7 em 2448x3264)
- [x] Sprint 1, lição 1.14: índice de tiles gravado e auditado no CI (A53)
- [ ] Sprint 1, lição 1.14: geração dos pixels com o manifesto de hashes (A52, item 7) e medição descritiva (A52, item 8)
- [ ] Sprint 3: sobreposição na previsão e regra de remontagem dos tiles (A52, item 2)
- [ ] Sprint 4a: escolher a regra da máscara reduzida (maioria, qualquer ou suave) antes de rodar a 4b (A52, item 4)
- [x] Se a inspeção das 40 máscaras apontar deslocamentos, refazer o teste de alinhamento com resolução maior (limite da A35): não foi necessário, 0 inadequadas em 40 (A40)

## 6. Limitações conhecidas

- **Teste de arquitetura:** não detecta imports dinâmicos (`importlib`, `__import__`). A
  regra "domínio sem disco ou rede" usa uma lista de módulos como aproximação; um
  `open()` direto passaria.
- **Trava de regras:** protege contra mudança acidental, não contra quem edita o código e
  o teste juntos (o `git log` mostra a mudança). Nenhum teste garante que o resto do
  código use `REGRAS` em vez de números soltos; isso fica para a revisão de cada sprint.
- **CI:** não roda os testes que dependem dos dados reais (`data`); o CI verde não prova
  que os dados estão corretos. O torch só é testado em CPU, na versão fixada. As ações
  são fixadas por versão maior (`@v7`).
- **Ruff:** garante que as anotações de tipo existem, não que estão corretas. O mypy não
  foi adicionado.
- **Ficha de procedência:** o código valida o formato dos campos, não a verdade do que
  está escrito; a verdade depende de uma leitura humana da fonte, por isso a ficha tem
  data de consulta. O teste do manifesto roda no CI porque não depende de dados.
- **Pasta temporária do pytest:** com `--basetemp`, o pytest apaga e recria `.pytest_tmp`
  a cada execução, o que não permite rodar testes em paralelo; o caminho é relativo à
  pasta de onde o `pytest` é chamado (convenção: a raiz do projeto, como no CI). Uma
  sessão elevada que rode o pytest neste projeto pode deixar a pasta presa.
- **Reprodutibilidade em GPU:** o determinismo total não é garantido (R9) e é medido
  pelas três seeds.
- **Privacidade:** o e-mail do autor está visível nos commits públicos.
- **Registro de arquivos:** o hash é registrado no primeiro download (confiança no primeiro uso): protege contra mudança posterior, mas não prova que o arquivo é o publicado pelo autor, porque o Mendeley não fornece hash para comparação. A comparação do domínio não toca em disco; calcular o hash e ler a pasta é da lição 1.3.
- **Inspeção das máscaras (lição 1.5):** a decisão sobre as 458 máscaras vem de 40 imagens julgadas por uma só pessoa, sem segunda opinião; o erro humano não entra no cálculo binomial. Entre 10% e 20% de máscaras inadequadas a regra não decide com segurança (com a regra de 8 em 40: 4,2% de chance de reprovar um dataset com 10% de defeito, 81,8% de detectar um com 25%). O cálculo supõe imagens independentes; a amostra tem fotos de numeração vizinha (por exemplo 131 e 132, 142 e 143, 258 e 259), que podem ser da mesma parede e reduzir o número efetivo de situações independentes. O sorteio é aleatório simples e não garante cobertura de paredes diferentes.
- **Hash em disco:** `registrar_pasta` registra tudo o que estiver na pasta, inclusive arquivos que o sistema acrescenta (como `Thumbs.db` ou `desktop.ini`), que aparecerão como "inesperados" na verificação. O manifesto registra arquivos, não julga o conteúdo. Ler e calcular o hash de uma pasta grande custa tempo de leitura em disco.
- **Aquisição do CCSD:** o hash do RAR é o do arquivo que o Mendeley serviu em 28/10/2026 (confiança no primeiro uso); o Mendeley não publica hash para comparação. O `UnRAR.exe t` ("Tudo OK") prova que o download bate com as somas que o compressor do autor gravou, não que o conteúdo está correto. Não se sabe se o truncamento do Download All nasce no servidor ou na montagem do pacote. O CI não tem os dados, então os arquivos reais só são conferidos localmente com `verificar`; desde a lição 1.13, o CI trava o arquivo do manifesto (`ab8feb4`), o que protege o registro, mas não prova que os dados em disco batem com ele.
- **Julgamento das máscaras (lição 1.7):** um só juiz, sem segunda opinião e sem controle negativo (nenhuma máscara defeituosa de propósito foi misturada para mostrar que o procedimento reprova o que deve reprovar). O julgamento levou cerca de 12 s por imagem, registrado como fato; o Gui o atribui à qualidade evidente das imagens. As imagens foram vistas com redução de 5x, então espessuras finas e deslocamentos de poucos pixels podem passar: o resultado diz que as máscaras parecem adequadas ao olho nessa escala, não que estão corretas ao pixel. O limite superior de 8,8% vale para o critério visual da A31 e herda as ressalvas de independência da lição 1.5; o resultado vale para o CCSD (edifícios da METU), não para outras fontes.
- **Binarização (lição 1.8):** a robustez foi medida na área agregada das 458 máscaras, não por máscara; o critério (razão entre a área em 192 e em 64) não detecta uma máscara individual com fissura acinzentada, e a lista de anomalias só pega fissura acima de 10% no limiar 128. O desvio usa a mediana como fundo, o que pressupõe fissura em menos da metade dos pixels; nas 458 máscaras, nenhuma passou de 10% em 128. Binarizar em resolução cheia não garante que fissuras finas sobrevivam à redução de resolução dos tiles; isso é medido na etapa de tiles.
- **Quase-duplicatas por dHash (lição 1.9):** o dHash só reconhece o mesmo enquadramento com deslocamento pequeno (80% dos recortes de 10% reconhecidos no CCSD) e não reconhece a mesma superfície fotografada de outro ponto ou ângulo. O agrupamento por componentes conexos é conservador de propósito, mas forma correntes: fotos ligadas uma a uma podem acabar no mesmo grupo sem serem parecidas entre si. O controle positivo usa variações fabricadas, não pares reais, e mede só o que foi fabricado.
- **Quase-duplicatas por embeddings (lição 1.10):** T = 0,0050 foi calibrado só com variações fabricadas da mesma foto (recompressão, brilho, recorte de até 10%); ele detecta fotos quase idênticas, não a mesma superfície vista de outro ponto ou ângulo, que provavelmente fica a uma distância maior. Pode haver séries reais no CCSD que escapam (o Gui notou fotos parecidas no julgamento das máscaras). Os vetores são calculados em CPU e podem variar levemente entre máquinas, o que pode mudar um par na fronteira de T; por isso os grupos devem ser gravados em arquivo. A rede vê a foto inteira achatada para 518x518.
- **Folga do limiar dos embeddings (lição 1.11):** a limitação de T foi declarada pequena pela regra da A47, mas a folga é estreita: a mediana da distância ao vizinho mais próximo é 4,6T, e com 5T forma-se uma corrente de 219 fotos. A distância de cosseno do DINOv2 não separa "a mesma parede vista de outro ponto" de "fotos do mesmo tipo"; séries reais desse tipo, se existirem, não são detectadas. Os 7 pares quase ligados (até 2T) não estão agrupados e podem cair em conjuntos diferentes.
- **Divisão (lição 1.12):** a divisão respeita os grupos de T = 0,0050, que só detectam fotos quase idênticas; séries reais da mesma parede vista de outro ponto, se existirem, podem estar em conjuntos diferentes sem que nada detecte (herda a limitação da lição 1.11). Dos 7 pares quase ligados, 1 cruza o teste (`rgb/100.jpg`, com a gêmea na validação) e 1 liga treino e validação (`rgb/536.JPG`). Com 69 fotos no teste, cada foto vale 1,4% de qualquer métrica por imagem. A divisão é uma só (uma seed), então a variação das métricas devida ao sorteio não é medida.
- **Distribuição por conjunto (lição 1.12):** a comparação usa a área de fissura das máscaras, que não separa fissuras finas de fissuras curtas; o rótulo "comparável" (razão entre 0,75 e 1,25) é descritivo, não um teste estatístico. O teste tem de 11% a 14% menos área de fissura que o treino e nenhuma foto armazenada em retrato; com 69 máscaras, parte dessa diferença pode ser só do sorteio.

## 7. Versões observadas

Python 3.12.15 (local); pytest 9.1.1; pre-commit 4.7.0; hooks: `pre-commit-hooks v6.0.0`,
`ruff-pre-commit v0.17.1`, `nbstripout 0.9.1`; ações do CI: `checkout@v7`,
`setup-python@v7`; CI: `torch==2.11.*` para CPU. Runtime do Colab de julho/2026 (fonte
externa): Python 3.12.13, PyTorch 2.11.0, NumPy 2.0.2.

## 8. Fechamento da Sprint 0 (2026-10-26)

**Gates:** CI verde nas duas jobs (`2ef9a90`, `fd2eebd`); teste de arquitetura falhando de
propósito (`import torch` no `domain`); regras pré-registradas travadas, com falha provocada
(`4 == 3`); CI falhando de propósito num PR. Suíte: 33 testes passando e 1 de ambiente (torch),
Ruff limpo, pre-commit protegendo cada commit.

**Lições aprendidas**

1. Todo guarda-corpo foi provado falhando de propósito antes de ser aceito. Um teste que
   nunca viu falhar não prova nada; repetir o método nas próximas sprints.
2. Hook que corrige arquivo faz o primeiro commit falhar uma vez (fim de linha CRLF, formatação).
   É esperado: `git add` de novo e `git commit` de novo. Opcional no editor: `files.eol` = `\n`.
3. Sessão elevada contamina o cache do pre-commit (seção 4). Regra A12.
4. Falhas provocadas vão numa branch com PR, nunca na `main` pública.
5. Verificar a contagem antes de explicar: o `ruff format --check .` contou 10 arquivos
   (8 de Python e 2 Markdown), e uma primeira explicação diferente estava errada.
6. O plano mudou duas vezes (A10 e A15) sem afetar nenhum gate.

**Divergências corrigidas durante a sprint:** nome de teste com erro de grafia
(`clcdice`, corrigido para `cldice`); contagem de arquivos do Ruff (item 5 acima).

## 9. Sprint 1: Dados (em andamento)

**Fontes consultadas em 2026-10-27**

- CCSD: Mendeley Data v1, 3/abr/2019, DOI 10.17632/jwsn7tfbrp.1, CC BY 4.0; 458 imagens com
  mapas alfa binários, edifícios da METU. A lista de arquivos não aparece na página; nomes
  e tamanhos serão lidos após o download.
- S2DS: repositório sem versão nem release; download por link do Google Drive; os termos do
  README restringem a uso acadêmico e proíbem distribuir.

**Decisões e achados**

- **A21:** o projeto não usa o split publicado do S2DS. Ele é manual, e o teste só tem
  imagens com chance razoável de reconhecimento (imagens quase invisíveis ou de qualidade
  ruim foram para treino e validação). As 743 imagens formam o teste externo, como no
  Discovery. Os números não são comparáveis aos de trabalhos que usam o split publicado.
- **A22:** divergência de licença do S2DS (README: uso acadêmico; página: GPL-3.0): vale o
  mais restritivo.
- **A23:** aquisição semiautomática: download manual e script que registra e verifica o hash
  (SHA-256). Download automático só se houver URL estável verificada.

**A medir:** 232 das 743 imagens do S2DS contêm fissura (180 + 25 + 27, pela tabela do
README) e a fissura soma ~0,10% dos pixels pela mesma tabela, contra 0,26% citado no
Discovery a partir de outra fonte.

**Lição 1.1 (concluída):** ficha de procedência (`FonteDados`), manifesto
`manifests/fontes.json` e 16 testes novos; suíte em 49 passed, 1 deselected. A trava de
licença do S2DS foi vista falhando (`assert True is False`) e desfeita. CI verde nas duas
jobs em `ee6c985`.

**Divergências corrigidas na lição 1.1:** uma linha da ficha de procedência tinha 89
caracteres (limite 88, regra E501), corrigida quebrando a chamada; a previsão de qual teste
falharia por causa do `tmp_path` estava errada (os 16 passaram; a falha estava na limpeza
final do pytest, seção 4).

**Lição 1.2 (concluída):** modelo do registro de arquivos (`ArquivoRegistrado`, `ManifestoArquivos`) e comparação (`comparar`) em `domain/integridade.py`, com 27 testes novos; suíte em 76 passed, 1 deselected. A trava do caminho `.` foi vista falhando (`DID NOT RAISE ValueError` em `test_caminho_invalido_e_recusado[./a.jpg]`) e desfeita.

**Divergências corrigidas na lição 1.2:** o `ruff format` reorganizou a lista do `parametrize` (quebra manual de linha), sem mudança de comportamento.

**Lição 1.3 (concluída):** `infrastructure/arquivos.py` (`sha256_do_arquivo`, `registrar_pasta`) e `infrastructure/manifesto_arquivos.py` (`gravar_manifesto`, `carregar_manifesto`), com 11 testes novos; suíte em 87 passed, 1 deselected. Os testes usam vetores padrão do SHA-256 (`abc` e arquivo vazio) e um arquivo de 2,5 MiB para exercitar a leitura em blocos, que foi vista falhando com o laço quebrado (`1 failed, 86 passed`) e desfeita.

**Divergências corrigidas na lição 1.3:** a instrução do gate trocava só o laço `while`, sem mostrar a função inteira, e a linha `return resumo.hexdigest()` ficou de fora na troca (oito testes falharam com `sha256=None`, em vez da falha única prevista). O gate foi refeito com o arquivo completo e passou como esperado. Regra daqui em diante: gates que alteram código vêm com o arquivo inteiro.

**Lição 1.4 (concluída):** parte A: `config/caminhos.py` e `presentation/dados.py` (comandos `registrar` e `verificar`), 14 testes novos; suíte em 101 passed, 1 deselected. Gate: com o bloco que impede sobrescrever o manifesto comentado, dois testes falharam (`DID NOT RAISE FileExistsError` e `assert 0 == 2`); desfeito. Parte B: aquisição do CCSD, sem abrir nenhuma imagem nem máscara. O Mendeley não pediu login nem aceite de termos.

**Achados da aquisição do CCSD:** o Download All (zip de 714.571.971 bytes, SHA-256 `7a53e401bad7a06d5c74395ad0c6df48fdf0c6e0bd6fce4bf4b031cc441602de`, `testzip` sem erro) continha um único arquivo, um RAR de 714.931.556 bytes, truncado: `UnRAR.exe t` deu "final inesperado do arquivo" e erro de soma de verificação em `rgb\593.JPG`; a listagem tinha 458 máscaras e 446 fotos. O RAR baixado direto (745.914.150 bytes, SHA-256 `1b8458ab6f84dc5086e9af8579e2cabccd3d209df97b46622096a4c105d5a6b2`) passou em "Tudo OK" e extraiu 458 fotos e 458 máscaras, todas em JPEG. O manifesto tem 917 entradas (RAR, 458 fotos e 458 máscaras); o hash do RAR no manifesto confere com o `Get-FileHash`, o que valida `sha256_do_arquivo` num arquivo real de 711 MiB, e `verificar ccsd` não achou divergência. Pelos nomes: máscaras em `BW/` (`.jpg`) e fotos em `rgb/` (`.JPG`), numeração com lacunas.

**Divergências corrigidas na lição 1.4:** (1) a ficha dizia que a lista de arquivos não aparecia na página; ela lista um único RAR de 711 MB (corrigido em `e676540`). (2) Esperava-se o dataset solto dentro do zip; havia um RAR, que o módulo `zipfile` não abre, e foi preciso o `UnRAR.exe`. (3) A hipótese de download interrompido foi levantada e descartada: o zip estava íntegro e já declarava o tamanho truncado do RAR. (4) A contagem de 459 entradas por pasta era ambígua; a extração mostrou 458 arquivos mais a própria pasta em cada grupo.

**Lição 1.5 (concluída):** protocolo de inspeção das máscaras do CCSD fixado e publicado antes de qualquer máscara ser vista (nenhuma imagem do CCSD foi aberta até o `14e1dfe`). Valores em `REGRAS`: 40 máscaras entre 458, seed 20261022, reprovação com 8 ou mais inadequadas (20%), proporção relevante de 25%. Pelo modelo binomial com N = 40, a regra reprova um dataset com 5% de inadequadas em 0,1% das vezes e com 10% em 4,2%; detecta 25% em 81,8% e 35% em 98,8%; entre 10% e 20% ela não decide com segurança. O resultado será reportado com intervalo de Wilson de 95% (por exemplo, 8 inadequadas em 40 dão de 10% a 35%; 0 em 40 dão até 9%). Sorteio por hash em `manifests/inspecao_ccsd.json`, que registra o SHA-256 do manifesto de arquivos (`80da125a8176fdabb7974c4c2665a6aafee4d779ab68b4741971f3f05b7652ef`). O comando lê só o manifesto, sem abrir imagens. Suíte em 123 passed, 1 deselected. As três travas (limiar, vetor do sorteio e "não refazer o sorteio") foram vistas falhando e desfeitas.

**Divergências corrigidas na lição 1.5:** (1) minha previsão de testes para a lição 1.5c saiu errada (anunciei 117 e depois 115); o correto era 114 (104 mais 10 novos). (2) A frase "revisão com Opus" para as duvidosas era ambígua: referia-se ao modelo para discutir a decisão de contingência, não a um segundo juiz das imagens; a regra foi reescrita (A31 e A33). (3) O gate do sorteio e o da amostra exigiram arquivos completos, conforme a regra do processo.

**Lição 1.6 (concluída):** integridade estrutural do CCSD, sem inspecionar nenhuma máscara e sem mostrar nenhuma imagem. Subdividida em 1.6a a 1.6k.

**Pareamento:** `domain/pareamento.py` pareia por nome (sem pasta, extensão nem maiúsculas) e recusa colisões. Resultado no CCSD: 458 pares, nenhuma máscara sem foto e nenhuma foto sem máscara. O nome prova a ausência de arquivo órfão, não que as duas imagens sejam da mesma cena; essa evidência veio do teste de alinhamento (os 458 pares tiveram sinal correto).

**Dimensões:** o cabeçalho é lido com o Pillow sem decodificar os pixels (`infrastructure/imagens.py`). Sem considerar a orientação EXIF, 179 pares tinham eixos trocados: todos têm foto com EXIF 6 e tamanho armazenado 4032x3024, enquanto a máscara correspondente está em 3024x4032, sem EXIF. Aplicando a orientação (`tamanho_exibido`), as divergências de tamanho caem a zero em 458 pares. Orientações EXIF das fotos: ausente 257, 6 em 179, 3 em 15, 1 em 7; as máscaras não têm orientação (ausente ou 1).

**Alinhamento:** igualdade de tamanho não prova alinhamento (o sentido da rotação e as 15 fotos com EXIF 3 ficavam sem verificação). O teste de contraste (A35) deu 100% de vantagens positivas em todos os grupos: ausente 257 pares (mediana 3,00, mín 0,82), EXIF 1 com 7 (2,03; 1,31), EXIF 3 com 15 (3,07; 1,61) e EXIF 6 com 179 (3,32; 0,97). Nenhuma máscara ficou sem contraste definido e nenhuma teve forma incompatível. Resultado: política A34. Gate: com o sentido de rotação das orientações 6 e 8 invertido, o comando nos dados reais deu para o grupo 6 `0.0% positivas, mediana -3,32, mín -7,64, máx -0,97` (o negativo exato do resultado correto, como previsto antes de rodar), código de saída 1, e o pytest falhou em 5 testes; desfeito, a saída voltou à original. Suíte em 244 passed, 1 deselected.

**Limitações do teste de alinhamento:** resolução de 1/8; compara só a orientação EXIF com a oposta (180°); não testa espelhamentos (inexistentes nas fotos do CCSD); não prova alinhamento ao pixel nem a qualidade do traçado, que é assunto da inspeção das 40 máscaras (lição 1.7). Os parâmetros (desvio 32, redução 8x, critério de 90%) valem só para este teste.

**Divergências corrigidas na lição 1.6:** (1) minha previsão de testes para a lição 1.6b saiu errada (139 em vez de 140). (2) Um erro de digitação no texto da 1.6a ("batería") foi corrigido. (3) O `ruff format` reformatou uma lista quebrada à mão em `tests/test_dimensoes.py`, sem mudança de comportamento. (4) O plano inicial de binarizar a máscara com limiar fixo (128) e regra de inversão foi trocado por "desvio do fundo", porque a redução de 8x acinzenta as fissuras finas e o limiar as apagaria, e porque dispensa saber a polaridade da máscara. (5) Após o gate, o Gui conferiu o `orientacao.py` restaurado antes de seguir. (6) O commit `2fa0082` ficou sem o prefixo `feat:` usado nos anteriores, sem consequência.

**Lição 1.7 (concluída):** inspeção visual das 40 máscaras sorteadas: ferramenta (1.7a a 1.7i), julgamento (1.7j) e resultado (1.7k). Suíte em 397 passed, 1 deselected.

**Ferramenta:** domínio com `aplicar_orientacao` para imagens RGB, `intensidade_da_mascara`, `sobrepor_mascara` e `montar_painel`; infraestrutura com `ler_rgb` e `gravar_png`; o comando `python -m concrete_crack.presentation.inspecao preparar ccsd` gerou as 40 imagens de dois painéis (nomes `01_001.png`, `02_064.png`, `03_081.png`, ...) sem erro, com o manifesto conferido contra o sorteio e as formas de foto e máscara coincidindo em todas. Domínio de decisão em `veredito.py` (A37), com os testes de fronteira 7 contra 8 inadequadas.

**Divergências corrigidas na lição 1.7:** (1) a `aplicar_orientacao` da 1.6 foi escrita para matrizes 2D e usava `m.T` nas orientações 5 e 7, o que embaralharia os canais de cor numa foto RGB; achado antes de qualquer uso real (as fotos do CCSD só têm as orientações ausente, 1, 3 e 6) e corrigido com `np.swapaxes`, com teste contra o Pillow em RGB. (2) O plano de binarizar a máscara no visualizador foi trocado pela intensidade proporcional ao desvio do fundo (A36), sem limiar. (3) O gate da regra usou uma substituição de uma linha por script, depois do commit e com restauração pelo Git, em vez do arquivo completo; combinado em sessão. (4) O comando `julgar` e o julgamento ficaram para 2 de novembro, por decisão de não julgar 40 máscaras com pressa e preservar a constância do critério.

**Registro, sessão e resultado (lição 1.7, segunda parte):** registro imutável de vereditos preso ao SHA-256 da amostra, gravado de forma atômica (A38); sessão de julgamento com E/S injetada, comandos `julgar` e `corrigir` (A39) e comando `resultado` (A40). Testes novos: 32 do registro e da gravação, 16 da sessão, 19 de `julgar` e `corrigir`, 12 do `resultado`. O julgamento foi feito numa só sentada, sem correções. O registro foi commitado (`62c3b9f`) antes de o comando `resultado` ser rodado, e o código do `resultado` (`01a9dd1`) antes do cálculo.

**Resultado da inspeção:** 40 adequadas (100,0%), 0 inadequadas (0,0%; Wilson 95%: 0,0% a 8,8%), 0 duvidosas, 0 correções; decisão: CCSD aprovado; a conclusão não depende das duvidosas. Duração do julgamento: 7 min 41 s. Saída completa do comando guardada no histórico da conversa da lição 1.7k. Limitações: seção 6 (julgamento das máscaras).

**Divergências corrigidas na segunda parte da lição 1.7:** (1) o gate da 1.7g partiu do `git checkout` em arquivo novo, que o Git não rastreava e não podia restaurar; o arquivo ficou na versão quebrada e foi recolado inteiro. Regra: gate sobre arquivo novo exige `git add` antes. (2) O `Set-Content -Encoding utf8` do PowerShell 5.1 gravou BOM e o `ruff format --check` acusou; o `ruff format` o removeu. Regra: scripts de gate em Python, não em PowerShell. (3) O `Format-Hex -Count` não existe no PowerShell 5.1 (comando trocado por `Select-Object -First 1`). (4) Minha previsão de arquivos formatados na 1.7i saiu errada (56; o correto era 55). (5) Entreguei o `inspecao.py` em edições parciais numeradas e a Edição 1 ficou confusa; o Gui pediu o arquivo completo, e a regra passa a valer para todo arquivo de código.

**Lição 1.8 (concluída):** binarização das máscaras do CCSD para o treino, em quatro partes: pré-registro do critério (A41, `07d746d`), funções puras no domínio (`6f454c7`, 23 testes), comando `medicao` (`6b7be02`, 16 testes) e medição nos dados reais (A42). Suíte em 450 passed, 1 deselected.

**Resultado da medição:** 458 máscaras lidas em resolução cheia, uma por vez, somando 5.500.237.824 pixels, valor que bate exatamente com 438 × (4032 × 3024) + 13 × (3264 × 2448) + 7 × (2448 × 3264). Área de fissura de 1,375% no limiar 16, 1,364% de 48 a 224 e 1,355% no 240: as máscaras são praticamente binárias, e as pontas da curva (0,011% e 0,009%) vêm do halo e das bordas da compressão JPEG. Razão do patamar 1,000, binarização ROBUSTA, 0 máscaras anômalas, limiar de treino 128 mantido. A previsão feita antes de rodar (robusta, poucas ou nenhuma anomalia, fissura entre 1% e 3% dos pixels) foi confirmada nos três pontos.

**Divergências corrigidas na lição 1.8:** (1) minha previsão do gate 1.8b saiu errada (27 testes passando em vez de 26; o arquivo tem 27 testes e 1 falhou). (2) Nos testes do comando `medicao`, uma máscara com 20 de 40 linhas de fissura (50%) fazia a mediana virar o valor da fissura e a fração sair 100% em vez de 50%; foi trocada por 15 linhas (37,5%), e o achado virou a limitação da mediana na seção 6. (3) Os gates das lições 1.8c e 1.8d foram ensaiados antes e saíram como previsto.

**Lição 1.9 (dHash concluído, embeddings pendentes):** detecção de quase-duplicatas em cinco partes: escolha do método (opção C, baseline simples com escalada medida), pré-registro (A43, `c1ac02b`), domínio do hash e do agrupamento (`3fcd164`, 26 testes), variações do controle positivo (`8bdfb51`, 22 testes) e comando `duplicatas` (`49ac137`, 13 testes). Suíte em 531 passed, 1 deselected.

**Resultado do dHash:** T = 23; 0,28% dos pares ligados (passa); maior grupo de 136 fotos (reprova); dHash REPROVADO e escalada para embeddings (A44). A previsão feita antes de rodar acertou as medianas das variações, a faixa de T (20 a 35) e os pares abaixo de 2%, e errou o veredito (previ aprovado): o risco apontado antes de rodar, fotos de concreto com padrões globais parecidos, se manifestou como efeito cascata e não como excesso de pares.

**Divergências corrigidas na lição 1.9:** (1) no plano da 1.9c escrevi "mais de 10% das fotos (46)", que podia ser lido como 46 permitido; na 1.9d ficou explícito que 10% de 458 é 45,8 e que um grupo de 46 já reprova, e há teste de fronteira para isso. (2) A previsão de veredito da 1.9h saiu errada, como registrado acima. (3) Os gates das lições 1.9d a 1.9g foram ensaiados antes e saíram como previsto.

**Lição 1.10 (concluída):** escalada para embeddings: árvore de decisão completa antes de medir (A45, `fccf01b`), adaptador do DINOv2 via timm (`4e01b1c`), registro e carregamento estrito dos pesos (`6aae2fe`), download único com revisão fixa (`70f7873`, `7d1fcaa`), variações em cor, cosseno e densidade (`279441f`) e comando com a árvore no domínio (`a65c035`). Torch 2.11 para CPU e timm 1.0.31 passaram a rodar também na máquina do Gui. Suíte em 593 passed, mais 17 com torch.

**Resultado dos embeddings:** aprovados (A46), com 7 pares ligados e 451 grupos; a corrente de 136 fotos do dHash não se repetiu. A previsão feita antes de rodar acertou o JPEG e os brilhos abaixo de 0,01, os pares abaixo de 2% e o veredito, e errou por uma ordem de grandeza os recortes e o T (previ T entre 0,03 e 0,12; saiu 0,0050): a rede é bem mais insensível a recortes do que eu supunha. O T pequeno é o que define a limitação registrada na seção 6.

**Divergências corrigidas na lição 1.10:** (1) a parte dos pesos foi dividida em duas (registro e carregamento; download), e a numeração das partes seguintes mudou em relação ao plano inicial. (2) Na 1.10f escrevi "seis arquivos" no Passo 1 e corrigi para cinco na mesma mensagem. (3) Na 1.10h, minha cópia de trabalho ainda tinha o exemplo antigo da docstring do limiar (0,95 x 200), já corrigido no repositório para 0,07 x 100; as alterações foram refeitas sobre os arquivos do repositório, conferidos por SHA-256, antes da entrega. (4) A previsão de T da execução errou por uma ordem de grandeza, como registrado acima.

**Lição 1.11, primeira parte (grupos gravados):** a execução da A46 só imprimiu o resumo, e os grupos não tinham sido gravados. O comando `grupos` (`b93054a`) refaz a detecção e só grava se reproduzir os quatro números registrados (T com 4 casas, 7 pares, 451 grupos, maior grupo de 2). A segunda execução reproduziu tudo, o que mostra que a extração é determinística na máquina do Gui; em outra máquina, a conferência recusaria uma partição diferente em vez de gravá-la em silêncio. Suíte em 606 passed, mais 17 com torch.

**Lição 1.11, segunda parte (vizinhos mais próximos):** pré-registro da análise e da redação da limitação (A47, `ffd611e`), código (`4b7d911`) e execução (A48): limitação declarada pequena, com as observações da folga estreita e dos 7 pares quase ligados registradas junto com o rótulo. A previsão feita antes de rodar acertou as 14 fotos até T e a declaração, e errou as três grandezas: a mediana (previ de 0,03 a 0,15; saiu 0,0228), as quase ligadas (previ menos de 10; saíram 14) e a ausência de cascata em 5T (houve uma de 219 fotos). Pela segunda vez, subestimei o quanto as fotos do CCSD ficam próximas entre si no espaço do DINOv2. Correção na proposta da 1.11c: escrevi "24 ou mais" para mais de 5% de 458; o certo é 23 ou mais (5% de 458 é 22,9), e o NOTES e os testes usam 23. Suíte em 632 passed, mais 17 com torch.

**Lição 1.12 (concluída):** divisão do CCSD por grupos, em oito commits: pré-registro (A49, `f3c45bb`), domínio da divisão (`3ffe08c`), registro dos pares quase ligados (`75c265b`, `9ef1d30`), comando `divisao` (`d93dd03`), `split_v1.json` (`3e8e25a`), auditoria no CI sobre os arquivos versionados (`c8bbc50`) e auditoria dos pares quase ligados (`a4560a0`). O teste de vazamento existe em dois níveis: o sintético prova o código e o dos arquivos reais prova os dados a cada push. O gate do segundo mostrou por que o teste de "grupo partido" não basta sozinho: uma troca entre duas fotos isoladas não parte nenhum grupo, e só a reprodução da A49 e a comparação byte a byte a pegam. Suíte em 691 passed, mais 17 com torch.

**Resultado da divisão e da auditoria:** tamanhos 320/69/69 e 475 linhas, como previsto. Na auditoria, previ 2 pares cruzando o teste e 3 em conjuntos diferentes; saíram 1 e 2, os dois dentro da faixa que fixei antes de rodar (de 0 a 3 e de 2 a 4; pela binomial, 30,3% e 19,7% de chance). A leitura do resultado foi fixada antes de rodar e aplicada sem mudança (A50).

**Divergências na lição 1.12:** (1) a conversa foi compactada durante a lição; as saídas dos gates de `3ffe08c` e `75c265b` ficaram na parte resumida e não estão registradas aqui, e a contagem de 649 testes do `3ffe08c` foi reconstruída pelos testes coletados (632 + 17). (2) O commit `d93dd03` ficou sem o prefixo `feat:`, sem consequência. (3) Errei o ponto das duas contagens da auditoria (uma a menos em cada), dentro da faixa prevista.

**Distribuição por conjunto (lição 1.12, parte final):** domínio (`0ce5bb2`) e comando (`82befb4`), commitados antes de rodar, e execução (A51): validação e teste comparáveis ao treino, com o teste de 11% a 14% abaixo em área de fissura. A soma ponderada reproduziu os 1,364% da A42, o que confere a medição. A previsão acertou os tamanhos, as resoluções, a faixa da fração total, a mediana abaixo da fração total e a conferência, e errou os quartis (previ cerca de 0,6% e 1,8%; saíram de 0,87% a 0,98% e de 1,36% a 1,59%): as máscaras do CCSD são mais homogêneas do que eu supunha. Suíte em 711 passed, mais 17 com torch.

**Lição 1.13 (concluída):** trava do manifesto real do CCSD no CI (`ab8feb4`), pendente desde a aquisição. O manifesto é a âncora da cadeia (inspeção, grupos e divisão registram o hash dele); antes, uma edição só seria pega de forma indireta pelo `test_split_v1.py`, sem dizer o que mudou. Os valores esperados estão escritos no teste, não lidos do arquivo. O gate alterou 1 byte no tamanho do RAR e as duas auditorias falharam, a nova apontando o campo alterado. Suíte em 717 passed, mais 17 com torch.

**Lição 1.14 (em andamento):** tiles do CCSD. Seis lições de teoria antes de qualquer decisão (o que é um tile e por que o projeto precisa dele; tamanho; bordas e sobreposição; resoluções e orientação; sobrevivência das fissuras finas; armazenamento) e o pré-registro (A52), aprovado ponto a ponto. Ao reler o Discovery e o ARQUITETURA, corrigi a lista de perguntas que eu tinha proposto: a escala (duas, nativa e 2×) e o destino dos tiles sem fissura (Sprint 3b) já estavam decididos. Com 9 GB livres no Drive, o armazenamento ficou numa terceira via, não apresentada na lição: gerar os tiles na própria sessão a partir do RAR, conferidos por hash dos pixels.

**Lição 1.14, execução parte 1 (grade e índice):** domínio da grade (`07a37d7`) e do índice (`0138500`), comando (`5ccef92`), `tiles_v1.json` (`96d6297`) e auditoria no CI (`2542213`); resultado na A53. Todas as previsões saíram exatas: as contagens por conjunto e escala, as 466 linhas e os quatro gates. Dois aprendizados ficaram registrados nos gates: o total de tiles não detecta uma grade "deitada" (uma foto de 2 × 2 tiles tem 4 tiles nas duas orientações), por isso há um teste das posições; e o teste byte a byte só detecta mudança de formato, não de conteúdo, por isso há testes de conteúdo ao lado dele. Suíte em 770 passed, mais 17 com torch.

**Dica operacional:** o `git log` abre um pager que pode prender o terminal do VS Code;
usar `git --no-pager log --oneline -n 5`.
