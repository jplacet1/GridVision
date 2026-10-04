# Próximo passo

Fonte única para responder "qual o próximo passo para avançar no GridVision?". A resposta sai da comparação entre a data de hoje, a fase do [cronograma](fontes/cronograma.md) e a checklist abaixo. Não depende de interpretação da conversa.

## Como responder

1. Pegue a data de hoje e ache a fase correspondente na tabela de fases abaixo.
2. Percorra a checklist na ordem. O **próximo passo** é o primeiro item com status `pendente` cuja fase seja a atual ou anterior (atrasado). Se não houver, é o primeiro `pendente` da fase seguinte.
3. Responda sempre neste formato, sem acrescentar outras seções:

```
Hoje: <data>. Fase prevista: <fase> (<período>).
Atrasados: <itens pendentes de fases anteriores, ou "nenhum">.
Próximo passo: <item>. Responsável: <nome>.
Depois: <próximo item pendente>.
Bloqueios: <o que depende de terceiros ou de dados, ou "nenhum">.
```

4. O grupo não tem acesso direto à Neoenergia. Todo contato com o cliente passa pela CESAR, a começar pelo professor Erick, e a resposta pode demorar ou não vir. Item que dependa do cliente não trava os demais: em "Bloqueios" diga o que aguarda a CESAR e siga para o próximo item que o grupo resolve sozinho.
5. Se a checklist estiver desatualizada (algo foi feito e não está marcado), atualize este arquivo antes de responder e diga que atualizou.

## Fases (cronograma oficial)

| Fase | Período |
|---|---|
| F1 Refinamento pós-SR1 | 04/10 a 16/10 |
| F2 Modeling | 17/10 a 24/10 |
| F3 Modeling (refino e análise de erros) | 25/10 a 06/11 |
| F4 Modeling para Evaluation | 07/11 a 13/11 |
| F5 Evaluation para Deployment | 14/11 a 20/11 |
| F6 Deployment | 21/11 a 27/11 |
| F7 Evaluation + Deployment | 28/11 a 04/12 |
| SR2 | 05/12 |

Fases anteriores (Setup até SR1) estão encerradas.

## Checklist

Status: `feito`, `pendente`, `bloqueado` (depende de terceiros). Atualizar junto com `contexto.md`.

| # | Fase | Item | Responsável | Status |
|---|---|---|---|---|
| 1 | F1 | Analisar o feedback do SR1 e registrar em `contexto.md` | Grupo | pendente |
| 2 | F1 | Dizer se o teste de legibilidade dos dígitos (19/09) foi feito e o resultado | Henrique | pendente |
| 3 | F1 | Piloto de anotação de caixas (medidor, ID, visor) em amostra de fotos | Grupo | pendente |
| 4 | F1 | Planejar os próximos experimentos (OCR em recortes do visor, detector) | Grupo | pendente |
| 5 | F1 | Enviar ao professor Erick (CESAR) as perguntas para a Neoenergia (volume em leituras ou imagens, gatilho da foto, precisão aceitável, o que fica sempre humano, D1 a D5). Sem acesso direto ao cliente: a CESAR intermedeia | Grupo | pendente |
| 6 | F1 | Apagar as cópias "Copy of ..." em Apresentações e definir versão oficial do Kickoff e do SR1 | Grupo | pendente |
| 7 | F1 | Completar o Data Understanding do Drive (coluna de imagens vazia, EDA do SR1) | João Pedro | pendente |
| 8 | F2 | Rotular amostra suficiente para treino, validação e teste (divisão por medidor, 70/15/15) | Grupo | pendente |
| 9 | F2 | Treinar detector de medidor, ID e visor | Grupo | pendente |
| 10 | F2 | Testar OCR nos recortes do visor e comparar com o baseline (42% no ID, 20% na leitura) | Grupo | pendente |
| 11 | F2 | Definir valor-alvo de localização, acerto exato da leitura e segurança, e pedir validação à Neoenergia pelo professor Erick. Se a resposta não vier, seguir com o valor do grupo e registrar como não validado | Grupo | pendente |
| 12 | F3 | Refinar modelos e analisar erros | Grupo | pendente |
| 13 | F4 | Avaliar no teste temporal (lote de 03/07) e escolher o modelo candidato | Grupo | pendente |
| 14 | F4 | Fechar a arquitetura final e registrar em `contexto.md` | Grupo | pendente |
| 15 | F5 | Iniciar a integração do modelo no MVP, com tela de revisão do analista | Grupo | pendente |
| 16 | F6 | Pipeline de inferência e testes funcionais do MVP | Grupo | pendente |
| 17 | F7 | Avaliação ponta a ponta, ajustes do MVP e documentação | Grupo | pendente |
| 18 | SR2 | Apresentação final | Grupo | pendente |

Itens concluídos até o SR1 (para referência): EDA e números conferidos contra a base (03/10), baseline PaddleOCR (02/10), divisão dos dados decidida, problema oficial definido, design system, Notion atualizado.
