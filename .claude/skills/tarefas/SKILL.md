---
name: tarefas
description: Atualiza as tarefas do GridVision nos três lugares ao mesmo tempo (artefato de checklist, Kanban do Notion e docs/proximo-passo.md). Use sempre que o usuário pedir algo sobre tarefas - mudar status, reordenar prioridade, criar, cancelar, concluir ou listar o que falta.
---

# Tarefas do GridVision

As tarefas vivem em três lugares que precisam ficar iguais. Toda mudança pedida vai para os três na mesma resposta.

| Lugar | Onde | Como escrever |
|---|---|---|
| Artefato "Tarefas do GridVision" | https://claude.ai/artifact/FeAAptM1vMPiDHF3AJX3Eu, coleção `tarefas` | `ArtifactData` (carregar com ToolSearch) |
| Kanban do Projeto (Notion, página Tarefas) | data source `collection://3c10a1e8-5392-80c0-bb50-000b0d2eb9ea` | `notion-update-page` / `notion-create-pages` |
| Checklist do repositório | `docs/proximo-passo.md` (e decisões em `docs/contexto.md`) | Edit |

## Passos

1. **Ler antes de escrever.** `ArtifactData` `list` da coleção `tarefas` (limit 100). O grupo marca itens pela página, então o estado do artefato pode estar mais novo que a conversa. Use a `version` lida como `if_version`. Se uma escrita falhar por versão, releia e preserve o que a pessoa mudou.
2. **Aplicar no artefato** com um único `batch`.
3. **Aplicar no Notion**: cada documento tem o campo `notion` com o id da página no Kanban. Sem esse campo, crie a página no data source e grave o id de volta em `notion`.
4. **Aplicar em `docs/proximo-passo.md`**: status na última coluna da tabela. Mudanças de escopo (cancelar, trocar o conteúdo de um item, nova ordem de prioridade) vão também para a seção do dia em `docs/contexto.md`.
5. Não fazer commit sem o usuário pedir. Responder com a tabela atualizada.

## Campos do documento (artefato)

`num` (ex.: "12a"), `texto`, `nota`, `fase` (F1 a F7, SR2), `resp`, `ordem` (posição na checklist), `status`, `feito`, `feitoEm` ("dd/mm"), `prioridade` (1 = mais urgente, só para tarefas abertas), `quem` ("Manual", "Decisão do grupo" ou "Claude"), `notion` (id da página).

Ao mudar `status`, grave junto `feito` (true só em concluida) e `feitoEm` (data de hoje em concluida, senão null).

## Mapeamento de status

| Artefato (`status`) | Notion (`Status`) | proximo-passo.md |
|---|---|---|
| `afazer` | Não iniciada | pendente |
| `andamento` | Em andamento | em andamento |
| `concluida` | Concluído | feito |
| `cancelada` | Cancelada | cancelado |

No Notion, `Prioridade` (número), `Quem faz` (Manual, Decisão do grupo, Claude) e `Fase` (select) seguem os campos do artefato.

## Prioridade

Ao reordenar, renumere de 1 em diante só as tarefas abertas (a fazer e em andamento), sem lacunas, nos três lugares. Tarefa concluída ou cancelada perde a prioridade no Notion (`null`).

## Regras

- Texto no Notion não cita o repositório, `docs/` nem `contexto.md`.
- Item que existe só no Notion (criado pelo grupo) não é apagado: pergunte se entra na checklist.
- Nenhum dado da Neoenergia (fotos, leituras, nomes de arquivo) vai para o Notion ou para o artefato.
