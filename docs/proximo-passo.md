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
| 1 | F1 | Analisar o feedback do SR1 e registrar em `contexto.md`. Professor gostou do SR1 no geral (17/10) | Grupo | feito |
| 2 | F1 | Dizer se o teste de legibilidade dos dígitos (19/09) foi feito e o resultado. Confirmado em 05/10: é o baseline PaddleOCR de 02/10 (ver `contexto.md`) | Henrique | feito |
| 3 | F1 | Piloto de anotação de caixas (medidor, ID, visor) em amostra de fotos. 300 fotos anotadas em 17/10 (ver `contexto.md`) | João Pedro | feito |
| 4 | F1 | Planejar os próximos experimentos (OCR em recortes do visor, detector). Plano apresentado ao professor em 17/10: ampliação 2x em 300 fotos, curva de cobertura e segurança, piloto de anotação, detector com limiar de confiança (ver `contexto.md`) | Grupo | feito |
| 5 | F1 | Enviar ao professor Erick (CESAR) as perguntas para a Neoenergia. Volume, gatilho da foto e D1 a D5 esclarecidos pelo grupo em 17/10 (ver `contexto.md`). Erro tolerado definido como zero. Sobra só o que fica sempre com o analista, que segue no item 11 | Grupo | feito |
| 6 | F1 | Apagar as cópias "Copy of ..." em Apresentações e definir versão oficial do Kickoff e do SR1. Cópias apagadas em 24/10 | Grupo | feito |
| 7 | F1 | Completar o Data Understanding do Drive (coluna de imagens vazia, EDA do SR1) | João Pedro | pendente |
| 8 | F2 | Rotular amostra suficiente para treino, validação e teste (divisão por medidor, 70/15/15). Feito em 17 e 18/10: 300 fotos de treino (piloto) e 200 de validação + teste | João Pedro | feito |
| 9 | F2 | Treinar detector de medidor, ID e visor. v0 treinado em 18/10 com as 300 fotos do piloto; mAP50 0,942 em validação + teste | João Pedro | feito |
| 10 | F2 | Testar OCR nos recortes do visor e comparar com a referência (PaddleOCR 3.7 com foto ampliada 2x: 28% na leitura, 41% no número do medidor). Feito em 18/10: OCR pronto no recorte não supera (18 na leitura); próximo é reconhecedor próprio para o visor | João Pedro | feito |
| 10a | F2 | Experimento de pré-processamento (ampliação e CLAHE) nas 100 fotos do baseline | João Pedro | feito |
| 10b | F2 | Atualizar o cronograma com avanços, atrasos e cortes de escopo, para o atendimento de 24/10. Feito no Notion em 24/10: status das fases corrigidos e seção "Avanços, atrasos e cortes" | Grupo | feito |
| 10c | F2 | Proposta de arquitetura do front-end para o atendimento de 24/10. Decidido desktop (ttkbootstrap) em 23/10. Apresentado ao professor em 24/10 com demo ao vivo; ele elogiou a integração front-end e IA | Grupo | feito |
| 10d | F2 | Repetir a ampliação 2x em umas 300 fotos, incluindo borradas, e medir a curva de cobertura e segurança por nível de confiança | Grupo | pendente |
| 10e | F2 | Medir o MVP nas 100 fotos de validação anotadas (cobertura, perdas, erros: "Confere" em foto ilegível tem de ser zero) e calibrar o limiar de confiança | João Pedro | pendente |
| 10f | F2 | Decidir se o sistema confere só a leitura (número do cadastro) ou leitura e número (teto 56% contra 46%). Decidido em 24/10: leitura e número, com saída para o analista (ver `contexto.md`) | Grupo | feito |
| 10k | F2 | Implementar no app a regra de 24/10: comparar o número do medidor com o CSV; número ilegível com leitura batendo vai ao analista com a leitura preenchida. Feito em 24/10 (status "Só a leitura confere") | João Pedro | feito |
| 10g | F2 | Acelerar o app: comparar PP-OCRv5 mobile com v6 medium e processar fotos em paralelo | João Pedro | pendente |
| 10i | F2 | Classificador de legibilidade e status "Ilegível (certeza alta)" no app (limiar 0,20). Falta o grupo definir o destino das fotos excluídas | João Pedro | feito |
| 10j | F2 | Conferir à mão os 10 "Confere" automáticos do lote_demo2 (prova do erro zero). Feito em 23/10: 10 de 10 certos | João Pedro | feito |
| 10h | F2 | Abrir e mesclar os PRs das branches `docs/guia-do-grupo` e `docs/baseline-ocr`; atualizar o Notion com o trabalho de 18/10 | João Pedro | pendente |
| 11 | F2 | Definir valor-alvo de localização, acerto exato da leitura e segurança, e pedir validação à Neoenergia pelo professor Erick. Se a resposta não vier, seguir com o valor do grupo e registrar como não validado | Grupo | pendente |
| 12 | F3 | Refinar modelos e analisar erros: reconhecedor próprio do visor (ajuste fino com recortes legíveis), comparar EasyOCR e Tesseract, melhorar a placa no detector | Grupo | pendente |
| 12a | F3 | Transcrever os 500 recortes do visor com as caixas de função e leitura (kit pronto em 24/10) e retreinar o leitor de dígitos | Grupo | pendente |
| 12b | F3 | App: zoom e pan na foto da checagem e barra divisória arrastável entre foto e painel, com a posição salva entre sessões (pedido do professor, 24/10). Feito em 24/10: divisórias entre fila, foto e campos, com largura mínima dos dois lados e posição em `gridvision_dados/interface.json` | João Pedro | feito |
| 12c | F3 | App: miniatura das fotos na lista de resultados e ícones de status além do texto (pedido do professor, 24/10) | Grupo | pendente |
| 12d | F3 | Consultar o professor Galindo (MLOps, quarta) sobre aprender com as correções do analista (tempo real ou retreino periódico) | Grupo | pendente |
| 12e | F3 | Mostrar o app ao professor Paulo na aula de Empreendedorismo (sexta) | Grupo | pendente |
| 12f | F3 | Versionar os pesos dos modelos (ex.: pasta no Drive). Pasta "GridVision modelos" criada em 24/10 com manifestos (ver `contexto.md`); pesos do detector v0 e do leitor v0/v1 enviados em 24/10 (tamanhos conferidos) | João Pedro | feito |
| 13 | F4 | Avaliar no teste temporal (lote de 03/07) e escolher o modelo candidato | Grupo | pendente |
| 14 | F4 | Fechar a arquitetura final e registrar em `contexto.md` | Grupo | pendente |
| 15 | F5 | Iniciar a integração do modelo no MVP, com tela de revisão do analista. Adiantado: modelo ligado ao app em 18/10, com revisão, histórico e exportação | João Pedro | em andamento |
| 16 | F6 | Pipeline de inferência e testes funcionais do MVP | Grupo | pendente |
| 17 | F7 | Avaliação ponta a ponta, ajustes do MVP e documentação | Grupo | pendente |
| 18 | SR2 | Apresentação final | Grupo | pendente |

Itens concluídos até o SR1 (para referência): EDA e números conferidos contra a base (03/10), baseline PaddleOCR (02/10), divisão dos dados decidida, problema oficial definido, design system, Notion atualizado.
