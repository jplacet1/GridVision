# Definição da solução (documento 4 de 4)

Fonte: `Definição da Solução.docx` (Drive, Entregáveis SR1). Modificado em 11/09/2026. Entrada: documentos 1 (ideação) e 3 (matriz).

## O produto

Verificador automático de fotos de leitura. Recebe o lote de um dia de campo (CSV mais pasta de fotos), processa sem intervenção e devolve um veredito por registro: aprovada, reprovada ou revisar, sempre com o motivo escrito.

Hoje o trabalho é manual e, pelo volume, só parte das fotos é conferida. O GridVision faz a máquina olhar todas, e a pessoa olha só as reprovadas ou duvidosas.

| Item | Definição |
|---|---|
| Quem usa | Analista da equipe de fiscalização de leitura da Neoenergia PE |
| Entrada | CSV com número do medidor, leitura e nota de ocorrência, mais a pasta de fotos |
| Saída | A lista de registros com veredito e motivo por linha, e tela para revisar os reprovados |
| Decide | Se a foto existe, se está legível, o que mostra e se combina com a nota |
| Tecnologia | OpenCV para legibilidade e CNN para classificar o conteúdo |
| Não faz | Não pune ninguém, não decide sozinho o caso duvidoso. Toda reprovação tem motivo e o auditor pode discordar |

## Fluxo do auditor

Aponta para o lote, espera o processamento, vê aprovadas, reprovadas e em dúvida, filtra reprovadas (foto ao lado da nota e do motivo) e confirma ou discorda. A discordância vira exemplo novo para o próximo treino. Números da tela de exemplo são ilustrativos, do lote de 03/07/2026.

## Verificações (da mais barata para a mais cara)

Foto reprovada na verificação 1 não chega à rede neural. Cada verificação funciona sozinha, então as primeiras já formam um produto que roda se a terceira atrasar.

| Ideia | Técnica | Rótulo? | Saída |
|---|---|---|---|
| I6, ocorrência sem foto | Regra sobre o CSV com o dicionário de notas | Não | sim/não |
| I1, foto legível | OpenCV: variância do Laplaciano, média e desvio da intensidade | Pouco, só para limiar | legível/ilegível |
| I2, o que a foto mostra | CNN com ajuste fino (MobileNetV3 ou EfficientNet-B0), PyTorch | Sim, é o gargalo | medidor / fachada ou portão / caixa fechada / outro |
| I3, bate com a nota | Classe de I2 contra tabela de evidência esperada por nota, escrita por nós e validada com o cliente | Não | conforme/divergente |
| I5, foto repetida | imagehash, distância de Hamming | Não | repetida/única |
| I4, ler dígitos (esticado) | Detecção do visor e OCR | Sim, caixas | valor lido/ilegível |
| I7, veredito | Regra de combinação | Não | aprovada/reprovada/revisar |
| I8, tela | Streamlit | Não | interface |

Ferramentas: Python, OpenCV, PyTorch com torchvision, imagehash, Streamlit, Google Colab com GPU. Rotulagem no Label Studio. Código no GitHub, dados e pesos com DVC.

## Entregáveis

| # | Entregável | Prazo |
|---|---|---|
| 1 | Tabela de evidência esperada por nota (também guia de rotulagem) | 05/09 |
| 2 | Conjunto de 900 a 1.200 fotos rotuladas, com concordância entre rotuladores medida | 26/09 |
| 3 | Modelo treinado, código de treino e experimentos | 24/10 |
| 4 | Pipeline que recebe um lote e devolve o CSV com veredito e motivo | 14/11 |
| 5 | Aplicação do auditor em Streamlit | 21/11 |
| 6 | Relatório de resultados: métricas por verificação, análise de erros, limitações | 28/11 |

## Metas

| Métrica | Meta |
|---|---|
| Percentual do lote resolvido sem auditor humano | Pelo menos 40% |
| Revocação na classe reprovada | Pelo menos 0,85 |
| Precisão na classe reprovada | Pelo menos 0,70 |
| Acerto de I2 | F1 macro com intervalo, meta definida após o piloto de rotulagem |
| Tempo de processamento | Menos de 10 minutos para 3.500 fotos |

Acurácia não é a métrica principal: dois terços dos registros não têm ocorrência, então chutar a classe majoritária daria acurácia alta. Deixar passar foto ruim custa mais que mandar foto boa para revisão.

## Fora do escopo

- Ler dígitos do display (I4): testar em 100 recortes até 19/09 e decidir.
- 42 notas sem exemplo na base (de 61 no dicionário, só 19 aparecem). Declarado no relatório.
- Qualquer alteração no app de campo (vira recomendação).
- Integração com sistemas da Neoenergia (roda sobre lote exportado).

## Riscos

| Risco | Mitigação |
|---|---|
| Rotulagem atrasa | Começar na semana de 30/08. I1, I6 e I7 rodam sem rótulo |
| Cliente não fornece critério de foto válida | Escrever a tabela com o melhor critério e declarar a premissa |
| Quatro classes de I2 não cobrem os casos reais | Revisar classes após piloto de 200 imagens |
| Resolução inviabiliza OCR | I4 já está fora do MVP. Testar até 19/09 |
| Imagens com dados pessoais (LGPD) | Repositório privado, sem fotos no site público, desfoque nas amostras publicadas |

## O que precisamos do cliente

O critério de foto válida por nota (ou o manual do leiturista); a resolução original das fotos; qualquer amostra já auditada.
