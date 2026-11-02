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
- [ ] Sprint 1: escolher o método de detecção de quase duplicatas, depois de ver os dados
- [ ] Sprint 1: ler e aceitar os termos de uso do S2DS antes do download
- [ ] Sprint 1: avaliar a cópia do S2DS no Drive privado, para o Colab, contra o termo que proíbe distribuir
- [ ] Sprint 1, condicional: confirmar licença e download parcial do CiF
- [ ] Sprint 2: decidir onde mora o ajuste do Frangi (recomendação: serviço próprio de busca em grade)
- [ ] Sprint 3: a sonda escolhe L4 ou T4 e confirma a runtime ativa do Colab
- [ ] Sprint 7: decidir se os checkpoints serão publicados
- [ ] Sprint 7: avaliar fixar as ações do CI por hash de commit e congelar um `pip freeze`
- [ ] Conferir se o `ruff` instalado pelo pip está na mesma versão do hook; a autoridade é o hook (A17)
- [x] Correção duradoura para a pasta temporária do pytest (A24)
- [ ] Sprint 1: as máscaras do CCSD são JPEG, com perdas; decidir e registrar a binarização para o treino (o teste de alinhamento usou só um critério provisório, desvio de 32 do fundo, A35; a decisão definitiva exige o histograma agregado dos valores)
- [ ] Sprint 1: decidir o destino de `data/raw/_tentativas/` (evidência do download truncado) ao fim da sprint
- [ ] Sprint 1: teste que trave o manifesto real do CCSD (917 entradas e hash do RAR), para rodar no CI
- [ ] Opcional: relatar ao Mendeley que o Download All entrega o RAR truncado
- [x] Sprint 1, lição 1.7: ferramenta, sessão de julgamento e resultado concluídos; CCSD aprovado, 0 inadequadas em 40 (A40). As 40 imagens continuam em `data/interim/inspecao_ccsd/` (derivadas, fora do Git)
- [ ] Sprint 1: tratar a heterogeneidade de resolução nos tiles (fotos armazenadas: 438 em 4032x3024, 13 em 3264x2448, 7 em 2448x3264)
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
- **Aquisição do CCSD:** o hash do RAR é o do arquivo que o Mendeley serviu em 28/10/2026 (confiança no primeiro uso); o Mendeley não publica hash para comparação. O `UnRAR.exe t` ("Tudo OK") prova que o download bate com as somas que o compressor do autor gravou, não que o conteúdo está correto. Não se sabe se o truncamento do Download All nasce no servidor ou na montagem do pacote. O CI não tem os dados, então o manifesto real só é conferido localmente com `verificar`.
- **Julgamento das máscaras (lição 1.7):** um só juiz, sem segunda opinião e sem controle negativo (nenhuma máscara defeituosa de propósito foi misturada para mostrar que o procedimento reprova o que deve reprovar). O julgamento levou cerca de 12 s por imagem, registrado como fato; o Gui o atribui à qualidade evidente das imagens. As imagens foram vistas com redução de 5x, então espessuras finas e deslocamentos de poucos pixels podem passar: o resultado diz que as máscaras parecem adequadas ao olho nessa escala, não que estão corretas ao pixel. O limite superior de 8,8% vale para o critério visual da A31 e herda as ressalvas de independência da lição 1.5; o resultado vale para o CCSD (edifícios da METU), não para outras fontes.

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

**Dica operacional:** o `git log` abre um pager que pode prender o terminal do VS Code;
usar `git --no-pager log --oneline -n 5`.
