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

- [ ] Sprint 1, antes de olhar as máscaras: fixar o limiar numérico de "máscaras inadequadas"
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

**Dica operacional:** o `git log` abre um pager que pode prender o terminal do VS Code;
usar `git --no-pager log --oneline -n 5`.
