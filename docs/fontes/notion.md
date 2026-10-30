# Notion do GridVision

Fonte: workspace do grupo, página [GridVision](https://app.notion.com/p/GridVision-3c10a1e8539280048ea3ec14161c1709). Lido e atualizado em 03/10/2026.

## Estrutura

- **GridVision** (página raiz), com quatro subpáginas:
  - **Tarefas:** Kanban do Kick-off e Gráfico de Gantt.
  - **Cronograma:** tabela do Kick-off e banco `db_cronograma` com as fases CRISP-DM.
  - **Pesquisas e Fontes:** vazia (só blocos de link que a leitura não resolve).
  - **Links úteis e Horários de Atendimento:** links do Drive e do Site, e tabela de atendimentos.
- Fora do GridVision: Anotações, Bloco de notas e Atas de reuniões (modelos vazios do Notion).

## Atendimentos com o docente

Fonte: `[Projeto 4] Cronograma de Atendimentos - Cronograma.pdf` (pasta Utilitários do Drive). Horários do Grupo 4, sábados:

29/08 9:45 a 10:30; 12/09 chegada 9:00 (kick-off), 9:35 a 9:50; 19/09 12:15 a 13:00; 26/09 11:30 a 12:15; 03/10 SR1, chegada 9:30, ordem por sorteio; 17/10 10:30 a 11:15; 24/10 9:45 a 10:30; 07/11 9:00 a 9:45; 14/11 12:15 a 13:00; 21/11 11:30 a 12:15; 28/11 10:30 a 11:15; 05/12 SR2, chegada 9:00, ordem por sorteio.

O Notion dizia 9:00 para o SR1; o PDF diz 9:30. Corrigido em 03/10/2026.

## Atualização feita em 03/10/2026

Antes, o Notion tinha parado de ser atualizado em 30/08. Foi corrigido:

- **Kanban:** Apresentação Kick-off passou a Concluído; Data Preparation passou a Em andamento; criados os cards Apresentação SR1 (Concluído) e seis tarefas novas do pós-SR1 (anotar conjunto piloto, repetir OCR nos recortes e treinar detector, confirmar teste de 19/09 com o Henrique, confirmar volume e perguntas D1 a D5 com a Neoenergia, definir valor-alvo das métricas do SR1, apagar cópias duplicadas no Drive). Os cards novos estão sem responsável.
- **db_cronograma:** Data Understanding para Data Preparation, Kick-off, Modeling + avaliação inicial e SR1 passaram a Finalizada; Data Preparation e Data Preparation para Modeling ficaram Em andamento (falta anotar o conjunto piloto). Criadas as 8 fases de 04/10 a 05/12 (refinamento, Modeling, Evaluation, Deployment e SR2), iguais ao PDF do Drive.
- **Gantt:** Business Understanding (15/08 a 21/08) e Data Understanding (22/08 a 28/08) com datas iguais ao PDF e status Concluído; item "Data Preparation" renomeado para "Data Understanding → Data Preparation" e Concluído; criadas as demais fases até o SR2.

## Revisão de 03/10/2026 (tarde)

- "Kanban do Kick-off" renomeado para "Kanban do Projeto". O banco do Gantt, antes "Nova fonte de dados", virou "Gantt do Projeto".
- Página Cronograma: título "Kick-off" virou "Cronograma do projeto", a tabela passou a ir até o SR2 e Business Understanding foi corrigido para 15/08 a 21/08.
- Página Pesquisas e Fontes preenchida com o que já temos.

## Divergências que continuam

- No Kanban, "Confirmar com a Neoenergia: volume, gatilho da foto e perguntas D1 a D5" e "Definir valor-alvo das métricas do SR1 e validar com a Neoenergia" estão Concluído, mas `proximo-passo.md` e `contexto.md` os mantêm pendentes (sem validação do cliente). Conferir com quem mexeu.
- O card "Documentação - Data Understanding" segue Em andamento porque o documento do Drive está incompleto.
- Os cards antigos têm responsáveis, mas só como IDs de usuário.
