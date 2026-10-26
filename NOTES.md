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
| A11 | 2026-10-21 | `PRE_COMMIT_HOME=C:\pc-cache`, permanente | Incidente do cache (seção 4) |
| A12 | 2026-10-21 | Claude Code, `pre-commit` e `git commit` só em terminal comum (não elevado) | Incidente do cache (seção 4) |
| A13 | 2026-10-22 | Seed do split = 20261022 | Lição 0.7 |
| A14 | 2026-10-22 | Repositório remoto criado antes do CI, que só roda no GitHub | Mudança de ordem |
| A15 | 2026-10-26 | Numeração: 0.8 repositório remoto, 0.9 CI, 0.10 documentos de raiz | Divisão de lição |
| A16 | 2026-10-26 | Repositório público desde a Sprint 0 | Decisão do Gui |
| A17 | 2026-10-26 | O lint do CI é `pre-commit run --all-files`, com os hooks fixados | Lição 0.9 |
| A18 | 2026-10-26 | O `pytest` padrão exclui os marcadores `torch` e `data` (`addopts`) | Lição 0.9 |
| A19 | 2026-10-26 | A job `dl` usa `torch==2.11.*`, a versão do Colab de julho/2026 | Lição 0.9 |
| A20 | 2026-10-26 | Licença MIT para o código | Decisão do Gui |

## 2. Commits e verificações da Sprint 0

| Commit | O que | Verificação |
|---|---|---|
| `3c0efd7` | Fundação: ambiente, pacote em camadas, pre-commit | Todos os hooks passaram |
| `fd7aee8` | Teste de arquitetura com 16 casos do analisador | 23 testes; falha provocada (`import torch` no `domain`) detectada |
| `77a65d4` | Regras pré-registradas travadas por teste (A13) | 33 testes; falha provocada (`4 == 3`) detectada |
| d9f6634| Marcadorestorchedata fora do pytest padrão (A18) | 33 passed, 1 deselected |
| `2ef9a90` | CI com as jobs `core` e `dl` | Duas jobs verdes na `main` (51 s) |
| 74a983f | LICENSE MIT (A20) | Detectada pelo GitHub |
| fd2eebd| README inicial e NOTES.md (decisões A1 a A20) | Duas jobs verdes na main |
| `5730f0f` | Falha proposital, só no PR #1 (não mesclado) | Ver seção 3 |

## 3. Falha provocada do CI (resultado deliberado, mantido)

O PR #1 trocou `max_experimentos_adicionais` de 3 para 4. A job `core` falhou com
`assert 4 == 3` em `test_no_maximo_tres_experimentos_adicionais` (`1 failed, 32 passed,
1 deselected`); a job `dl` passou. O lint passou antes: a falha é de comportamento, não
de estilo. O PR foi fechado sem mesclar e a branch foi apagada. A execução fica visível
no histórico do Actions como prova de que o CI rejeita uma violação de regra
pré-registrada.

## 4. Incidente do cache do pre-commit

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

**Pendências deste incidente**

- Reproduzir a criação das pastas num diretório descartável, comparando uma sessão comum
  com uma elevada.
- Limpar as duas pastas antigas de um terminal elevado, depois de decidir se a evidência
  deve ser guardada.

## 5. Pendências abertas

- [ ] Sprint 1, antes de olhar as máscaras: fixar o limiar numérico de "máscaras inadequadas"
- [ ] Sprint 1: escolher o método de detecção de quase duplicatas, depois de ver os dados
- [ ] Sprint 1: ler e aceitar os termos de uso do S2DS antes do download
- [ ] Sprint 1, condicional: confirmar licença e download parcial do CiF
- [ ] Sprint 2: decidir onde mora o ajuste do Frangi (recomendação: serviço próprio de busca em grade)
- [ ] Sprint 3: a sonda escolhe L4 ou T4 e confirma a runtime ativa do Colab
- [ ] Sprint 7: decidir se os checkpoints serão publicados
- [ ] Sprint 7: avaliar fixar as ações do CI por hash de commit e congelar um `pip freeze`
- [ ] Conferir se o `ruff` instalado pelo pip está na mesma versão do hook; a autoridade é o hook (A17)

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
- **Reprodutibilidade em GPU:** o determinismo total não é garantido (R9) e é medido
  pelas três seeds.
- **Privacidade:** o e-mail do autor está visível nos commits públicos.

## 7. Versões observadas

Python 3.12.15 (local); pre-commit 4.7.0; hooks: `pre-commit-hooks v6.0.0`,
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
