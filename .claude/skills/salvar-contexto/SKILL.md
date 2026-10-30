---
name: salvar-contexto
description: Resume a conversa atual, registra em docs/ só o que for decisão, número oficial ou pendência nova, e envia ao GitHub do projeto (commit e push). Use ao encerrar uma conversa, quando o contexto estiver ficando longo, ou quando o usuário pedir "salvar contexto", "resumir a conversa" ou "mandar pro github".
---

# salvar-contexto

Transfere para o repositório o que a conversa produziu, para a próxima conversa (ou outra pessoa do grupo) continuar sem perder nada.

## Princípios

- `docs/contexto.md` é a fonte única de verdade. Registre nele apenas o que é durável: decisões, números oficiais, definições, responsáveis, prazos.
- Não copie a conversa. Não registre o que já está em `docs/` nem o que o código/git já mostram.
- Nada de invenção: só entra o que foi dito ou decidido na conversa. Se algo estiver ambíguo, pergunte antes de registrar.
- Escreva em português.

## Passos

1. **Ler o estado atual.** Leia `docs/contexto.md`, `docs/inconsistencias.md` e rode `git status` e `git branch --show-current`.
2. **Extrair da conversa**, em lista curta:
   - decisões tomadas (e o motivo, quando houver);
   - números ou fatos oficiais novos;
   - conflitos com o que já está em `docs/` (vão para `docs/inconsistencias.md`);
   - pendências e próximos passos, com responsável se citado;
   - fontes novas consultadas (Drive, Notion, site), que vão para `docs/fontes/`.
3. **Descartar** o que for exploração sem conclusão, tentativas que falharam sem lição útil e conteúdo já registrado.
4. **Aplicar nos arquivos certos:**
   - decisão ou número oficial: `docs/contexto.md`, na seção que já existe (crie seção só se nenhuma servir);
   - conflito ou dúvida aberta: `docs/inconsistencias.md`;
   - resumo de fonte nova: `docs/fontes/<nome>.md` e linha em `docs/fontes/README.md`;
   - registro da sessão: crie `docs/sessoes/AAAA-MM-DD-<tema>.md` com resumo de 10 a 25 linhas (o que foi feito, decisões, pendências, próximos passos). Se já existir arquivo do dia e tema, atualize-o.
5. **Mostrar ao usuário** um resumo do que será gravado (arquivos e trechos) e pedir confirmação.
6. **Commit e push**, só depois da confirmação:
   - Se estiver em `main`, crie antes uma branch `docs/<tema>`. Nunca faça push direto em `main`.
   - Faça `git add` apenas dos arquivos de `docs/` tocados nesta tarefa. Não inclua mudanças alheias já pendentes sem avisar (ex.: `GridVision.code-workspace`).
   - Mensagem em português, estilo Conventional Commits (`docs: ...`), no mesmo commit das mudanças em `docs/contexto.md`.
   - Termine a mensagem com a linha de coautoria pedida pelo ambiente.
   - `git push -u origin <branch>`. Nunca use `--force`.
   - Informe o hash do commit e a branch. Se o usuário quiser PR, ofereça abrir.

## Se o push falhar

Mostre o erro exato e pare. Não tente contornar com force, outro remoto ou `--no-verify`.

## Limites

- A skill não dispara sozinha ao fim da conversa. O usuário a chama (`/salvar-contexto`), de preferência antes do contexto encher.
- Não grava segredos, tokens, e-mails pessoais ou dados da Neoenergia que não estejam já em `docs/`.
