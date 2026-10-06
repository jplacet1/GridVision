# Guia do grupo: como usar este repositório

Para Alana, Henrique e João Pedro trabalharem no Projeto 4 a partir do mesmo repositório, cada um com o seu Claude Code, sem perder contexto nem vazar dados da Neoenergia.

Em caso de divergência com este guia, vale [contexto.md](contexto.md).

## 1. Para que serve o repositório

É o workspace do grupo. Ele guarda:

- **Contexto compartilhado** em `docs/`: dados, decisões, cronograma, checklist. É o que faz o Claude de cada um responder com os mesmos fatos.
- **Código** do projeto (detector, OCR, pipeline, MVP), quando começar a existir.
- **Resultados agregados** (métricas, tabelas, gráficos sem foto identificável).

Não guarda: fotos, CSV ou zip da Neoenergia. Ver seção 4.

## 2. Configuração inicial (uma vez)

Pré-requisitos: [Git](https://git-scm.com), [VS Code](https://code.visualstudio.com), a extensão **Claude Code** no VS Code (ou o CLI `claude`) e acesso ao repositório no GitHub (peça convite ao João Pedro, dono do [repositório](https://github.com/jplacet1/GridVision)).

```bash
git clone https://github.com/jplacet1/GridVision.git
cd GridVision
code .
```

Depois:

1. Abra o Claude Code dentro dessa pasta. Ele lê o `CLAUDE.md` da raiz sozinho; esse arquivo manda o Claude ler `docs/contexto.md` antes de qualquer tarefa.
2. Confira que ele leu: pergunte "qual é o objetivo do projeto e quais são os marcos?". A resposta deve bater com [contexto.md](contexto.md).
3. Python (quando for rodar código): crie um ambiente virtual na raiz com `python -m venv .venv`. A pasta `.venv/` já é ignorada pelo Git.

## 3. Mapa do repositório

| Caminho | O que é |
|---|---|
| `CLAUDE.md` | Instruções que o Claude lê sempre. Não é para consulta humana |
| `docs/contexto.md` | **Fonte única de verdade**: projeto, marcos, números da EDA, decisões |
| `docs/proximo-passo.md` | Fases do cronograma e checklist com responsável e status |
| `docs/inconsistencias.md` | Conflitos entre documentos e pendências abertas |
| `docs/fontes/` | Resumos fiéis dos documentos do Drive, Notion, Site e Classroom. Índice em [fontes/README.md](fontes/README.md) |
| `.claude/skills/` | Skills do projeto (hoje: `salvar-contexto`) |
| `README.md` | Apresentação geral do projeto |

Pastas de código (`src/`, `notebooks/`, `experiments/`, `app/`) ainda não existem. Crie quando precisar, seguindo o plano do [README](../README.md). Dados ficam fora, em `data/` ou `dados/` (ignoradas pelo Git) ou, melhor, fora da pasta do repositório.

## 4. Dados da Neoenergia (LGPD)

As fotos e os CSV mostram fachadas, números de porta e vias públicas. São dados pessoais.

- Nunca faça `git add` de foto, CSV, xlsx ou zip. O `.gitignore` bloqueia `*.jpg`, `*.csv`, `*.xlsx`, `*.zip`, `data/` e `dados/`, mas não confie só nele: confira `git status` antes de cada commit.
- Os dados não estão no Drive do projeto. Vieram em um zip (`Base de Dados Neoenergia PE.zip`) com o João Pedro. Peça a ele para repassar por canal privado e guarde **fora da pasta do repositório** (por exemplo `C:\dados\gridvision`).
- Para o Claude rodar ou escrever código que leia os dados, diga o caminho da pasta local. Ele nunca deve assumir que a base existe.
- Não cole foto sem desfoque em slide, Notion, issue, PR ou chat público. Em amostras publicadas, desfoque fachadas e números.
- O Claude de vocês também só vê o que vocês mostram. Se mandar uma foto para ele, é por sua conta.
- Repositórios públicos de disciplinas (MLOps, por exemplo) não podem ter imagem nem CSV do cliente, nem citar a Neoenergia. Ver [fontes/mlops.md](fontes/mlops.md).

## 5. Usando o Claude Code neste workspace

### Perguntas que funcionam bem

| Quero... | Diga ao Claude |
|---|---|
| Saber o que fazer agora | "Qual o próximo passo?" Ele segue [proximo-passo.md](proximo-passo.md) e responde sempre no mesmo formato (hoje, fase, atrasados, próximo passo, depois, bloqueios) |
| Um número ou decisão | "Quantas fotos tem no lote de 03/07?" Ele responde de `docs/`. Se não estiver lá, deve perguntar em vez de inventar |
| Entender um documento do Drive | "Resuma o que o SR1 diz sobre a arquitetura" (lê `docs/fontes/sr1.md`) |
| Montar slide ou tela | "Crie o slide X usando o design system". Ele deve ler o README do [design system](https://claude.ai/artifact/QE97oYdBevqSvzrTb9VWj5) antes. Se o link não abrir, peça ao João Pedro para compartilhar |
| Escrever código com dados | "Escreva o script de EDA. Os dados estão em `C:\dados\gridvision`" |

### Skill `/salvar-contexto`

Ao fim de uma conversa que produziu decisão, número oficial ou pendência nova, rode `/salvar-contexto`. A skill:

1. lê o estado atual de `docs/`;
2. separa o que é durável (decisão, número, pendência) do que foi só exploração;
3. mostra o que vai gravar e **pede sua confirmação**;
4. grava em `docs/`, cria branch (nunca usa `main` direto), faz commit e `push`.

Rode antes de o contexto da conversa ficar longo. Ela não dispara sozinha.

> Atenção: `.claude/` está no `.gitignore`, então a skill só chega a Alana e Henrique se a pasta `.claude/skills/` for versionada. Ver a nota em "Pendências deste guia" no fim.

### Regras que o Claude segue aqui (vêm do CLAUDE.md)

- Escreve em português.
- Dado ou número vem de `docs/`, nunca de memória ou de outra conversa.
- Se a informação não estiver em `docs/`, pergunta.
- Decisão nova ou número oficial vai para `docs/contexto.md` no mesmo commit.
- Nunca versiona foto ou CSV.

Se ele fugir de alguma, lembre-o: "siga o CLAUDE.md".

## 6. Fluxo de trabalho no dia a dia

1. **Atualize**: `git switch main` e `git pull`.
2. **Descubra a tarefa**: pergunte ao Claude "qual o próximo passo?" ou abra [proximo-passo.md](proximo-passo.md) e escolha um item `pendente` com o seu nome (ou "Grupo", combinando antes no grupo quem pega).
3. **Crie uma branch** a partir de `main`: `git switch -c <tipo>/<tema>`, com tipo `docs`, `feat`, `fix`, `exp` ou `chore`. Exemplos: `docs/feedback-sr1`, `exp/ocr-recorte-visor`.
4. **Trabalhe** com o Claude. Se surgir decisão ou número oficial, peça para registrar em `docs/contexto.md`.
5. **Marque o item** como `feito` em `proximo-passo.md`, no mesmo commit.
6. **Confira** `git status` e `git diff`: nada de dados, nada de arquivo alheio.
7. **Commit** em português, estilo Conventional Commits (`docs: registra feedback do SR1`, `feat: script de recorte do visor`).
8. **Push e Pull Request**: `git push -u origin <branch>` e abra PR para `main`. Peça revisão a outra pessoa do grupo antes do merge. Nunca `push` direto em `main` e nunca `--force`.

Para duas pessoas não editarem o mesmo trecho: combine no grupo quem mexe em `contexto.md` e `proximo-passo.md` em cada momento, faça PRs pequenos e dê `git pull` antes de começar.

## 7. Onde registrar cada coisa

| O que | Onde |
|---|---|
| Decisão, número oficial, definição, prazo | `docs/contexto.md` |
| Item concluído ou novo item do cronograma | `docs/proximo-passo.md` |
| Conflito entre documentos, dúvida aberta | `docs/inconsistencias.md` |
| Resumo de documento novo (Drive, Notion, Classroom) | `docs/fontes/<nome>.md` e linha em `docs/fontes/README.md` |
| Resumo de uma sessão de trabalho | `docs/sessoes/AAAA-MM-DD-<tema>.md` (a skill `/salvar-contexto` cria) |
| Resultado de experimento | `experiments/` (só métricas e tabelas agregadas) |

Não registre: conversa solta, tentativa que falhou sem lição, segredos, tokens, dados pessoais.

## 8. O que está em jogo agora (04/10/2026)

Fase atual: **F1 Refinamento pós-SR1 (04/10 a 16/10)**. Itens por responsável, conforme [proximo-passo.md](proximo-passo.md):

- **Henrique:** dizer se o teste de legibilidade dos dígitos (19/09) foi feito e o resultado; enviar o script e os resultados completos do baseline PaddleOCR de 02/10 (MLOps e Deep Learning dependem disso).
- **João Pedro:** completar o Data Understanding do Drive.
- **Alana:** ainda sem item nominal. Combinem no grupo (sugestões: piloto de anotação de caixas, planejamento dos experimentos).
- **Grupo:** analisar o feedback do SR1, piloto de anotação de caixas (medidor, ID e visor), planejar experimentos, mandar perguntas à Neoenergia pelo professor Erick, limpar cópias duplicadas no Drive.

Prazos de disciplinas que usam o projeto (detalhes em [contexto.md](contexto.md)):

| Entrega | Prazo |
|---|---|
| MLOps AV1, repositório (tag `sr1`) | 06/10 às 23:59 |
| MLOps AV1, apresentação | 07/10 às 19:00 |
| Deep Learning, Lab 02 | 08/10 às 23:59 |
| Atendimento com o professor | 17/10, 10:30 |
| SR2 (entrega final) | 05/12 |

O cliente (Neoenergia) não é acessível diretamente. Perguntas passam pela CESAR, a começar pelo professor Erick, e a resposta pode não vir.

## 9. Problemas comuns

| Sintoma | O que fazer |
|---|---|
| O Claude responde algo que não bate com `docs/` | Diga "leia docs/contexto.md e refaça". Se o erro estiver em `docs/`, corrija lá |
| O Claude diz que não tem os dados | Correto. Dê o caminho da pasta local, fora do Git |
| `git status` mostra `.jpg` ou `.csv` | Pare. Não adicione. Mova o arquivo para fora do repositório |
| Commitei dado sem querer (ainda local) | `git reset --soft HEAD~1`, tire o arquivo do stage e refaça. Se já deu `push`, avise o grupo antes de qualquer outra coisa |
| `git pull` dá conflito em `docs/` | Abra o arquivo, mantenha as duas versões quando forem decisões diferentes e peça ao Claude para ajudar a mesclar |
| O link do design system não abre | Peça ao João Pedro para compartilhar o artefato |
| `/salvar-contexto` não aparece | A skill não veio no clone. Ver pendência abaixo |

## Pendências deste guia

- **Skill versionada.** `.claude/` está ignorado no `.gitignore`. Para Alana e Henrique terem `/salvar-contexto`, é preciso versionar só `.claude/skills/` (mantendo `settings.local.json` ignorado). Sem isso, eles copiam a pasta à mão.
- **Papel da Alana.** Não há item nominal dela em `proximo-passo.md`. Definir no grupo e registrar lá.
- **Ambiente Python.** Não há `requirements.txt` ainda. Quando o primeiro código entrar, registrar a versão do Python e as dependências.
