# Inconsistências entre os documentos do Drive

Levantamento feito em 03/10/2026 comparando os 10 documentos em [fontes/](fontes/). Nada aqui é decisão oficial: cada item precisa ser resolvido pelo grupo e, depois, registrado em [contexto.md](contexto.md).

## Situação dos 15 itens (atualizado em 03/10/2026)

| # | Item | Situação | Onde ficou registrado |
|---|---|---|---|
| 1 | Pivô do problema | Resolvido: vale o SR1 | contexto.md, Decisões |
| 2 | Teste de 19/09 | Em aberto (responsável: Henrique) | contexto.md, Decisões |
| 3 | Meta de automação | Resolvido: 50% é piso, validado pela Neoenergia. Demais metas provisórias | contexto.md, Decisões |
| 4 | Rotulagem e tabela de evidência | Resolvido por substituição: pertenciam ao desenho antigo. Piloto de anotação de caixas é o próximo passo do SR1 | contexto.md |
| 5 | Volume e gatilho | Parcial: faixa 50 a 70 mil registrada. Unidade e gatilho pendentes com a Neoenergia | Pendências |
| 6 | O "92%" | Pendente: conferir no CSV | Pendências |
| 7 | Formato e tamanho da base | Parcial: números do SR1 registrados. Formato e coluna pendentes | contexto.md, Pendências |
| 8 | Classes de I2 contra detector | Resolvido pelo item 1: I2 descartada. Arquitetura final em aberto até o SR2 | contexto.md |
| 9 | Datas de entregáveis | Resolvido: vale o cronograma do Drive | contexto.md, Marcos |
| 10 | Nome do João Pedro | Resolvido | contexto.md, Grupo |
| 11 | Identificação da disciplina | Resolvido | contexto.md, Projeto |
| 12 | Descrição do problema | Resolvido pelo item 1 | contexto.md, Projeto |
| 13 | Perguntas ao cliente D1 a D5 | Pendente com a Neoenergia | Pendências |
| 14 | Ordem das verificações | Resolvido pelo item 1 (ordem do desenho antigo não vale) | fontes/README.md |
| 15 | Arquivos duplicados | Pendente: ação no Drive | Pendências |

Os itens abaixo continuam descritos como foram encontrados. Leia junto com a tabela acima.

Siglas das fontes: BU (business-understanding), DU (data-understanding), IDE (ideacao), MAT (matriz-impacto-esforco), DEF (definicao-da-solucao), S29 (slides-29-08), KO (kickoff), SR1 (sr1), CRO (cronograma).

## Críticas (mudam o escopo do projeto)

### 1. O problema mudou entre o Kickoff e o SR1

- IDE, MAT, DEF, S29 e KO: o produto verifica se a foto combina com a **nota de ocorrência** (classificar o conteúdo com CNN, I2, e comparar com tabela de evidência, I3). O veredito é aprovada, reprovada ou revisar.
- SR1: o produto **lê o número do medidor e a leitura** da foto (detector de medidor, ID e visor, mais reconhecedor de caracteres). A nota de ocorrência "não vem junto" na operação. A saída é leitura, confere ou diverge, ou revisão.
- BU (18/08) já descrevia o problema como identificar informações nas imagens, mais próximo do SR1 do que do Kickoff.
- O site (a vitrine do projeto) fala em "automatizar parte do processo de leitura" e em reduzir o trabalho manual dos analistas. Isso também está alinhado ao SR1 e à BU, não ao desenho de veredito por nota. Só o Kickoff, a Ideação, a Matriz e a Definição seguem o desenho antigo.
- O SR1 assume o pivô sem dizer o que acontece com I2, I3, a tabela de evidência e a tela do auditor.

Decidir: o que sobrevive do desenho antigo (I1, I6, I7, I8)? I2 e I3 foram abandonadas? O `contexto.md` hoje descreve o problema no formato antigo (Aprovado, Reprovado, Revisão manual).

### 2. I4 (ler dígitos) passou de "fora do MVP" a centro do projeto

- MAT, DEF e S29: I4 é esticada, esforço 5, só entra se o teste de 19/09 em 100 recortes der certo. S29 afirma que a resolução "inviabiliza" o OCR.
- SR1: leitura é o objetivo principal.
- Não há resultado do teste de 19/09 em nenhum documento. O único dado é o baseline de 02/10 (PaddleOCR na foto inteira: 42% no ID, 20% no display), que não é o mesmo teste (não usa recortes do visor).

### 3. Meta de automação: 40% ou 50%

- DEF: pelo menos 40% do lote resolvido sem auditor.
- S29: pelo menos 50%.
- As outras metas (revocação 0,85, precisão 0,70, 10 minutos para 3.500 fotos) coincidem. No SR1, essas metas não aparecem, e as métricas passam a ser localização, acerto exato e segurança.
- BU diz que os valores quantitativos "ainda deverão ser definidos" com a Neoenergia. Nenhum documento diz que o cliente validou as metas.

### 4. Cronograma de rotulagem não bate com a realidade do SR1

- DEF: tabela de evidência em 05/09 e 900 a 1.200 fotos rotuladas em 26/09; rotulagem começa na semana de 30/08.
- SR1 (02/10): "nenhuma caixa ou texto anotado" e o piloto de anotação ainda é próximo passo.
- A tabela de evidência de 05/09 não é mencionada em nenhum documento posterior. KO ainda lista "validar com a Neoenergia o critério de foto por nota" como próximo passo.
- MAT: "I6 e I1 até o Kickoff". Não há registro de entrega.

## Importantes (números e fatos)

### 5. Volume e gatilho do processo

- Site (home): 50 mil a 70 mil **leituras** por mês, a maioria manual, equipe de seis. BU fala em 70 mil **imagens**. Faixa e unidade diferem.
- BU: cerca de 70 mil imagens por mês, seis funcionários, fotos geradas quando a leitura está fora da faixa esperada (revisita).
- IDE e KO: todo cliente é visitado todo mês e **toda leitura** gera foto.
- DEF e MAT: lote diário de 3.500 fotos. A base tem 12.340 fotos em 4 dias (cerca de 3.085 por dia).
- DEF diz que hoje só parte das fotos é conferida (suposição S1, ainda aberta). S29 diz auditoria 100% manual "inviável". BU diz que as 70 mil são analisadas por seis pessoas.

Decidir: 70 mil é o total de fotos ou só as de revisita? A auditoria é por amostragem?

### 6. Interpretação do "92%" (suposição S2)

- IDE: "92% dos registros **cuja nota não exige foto** têm foto assim mesmo".
- S29: "92% das **fotos anexadas** referiam-se a notas que não exigiam foto".
- São denominadores diferentes e dão leituras opostas sobre o critério de foto. Conferir no CSV qual é o correto.

### 7. Formato e tamanho da base

- DU: planilhas .xlsx, cerca de 12 mil imagens, 4 pastas de cerca de 3.000, uma planilha por pasta.
- SR1: CSVs (com o problema do texto "NA"), 13.669 registros, 12.340 fotos, 4 lotes com datas (20, 21 e 22/05 e 03/07/2026).
- DU não traz os números exatos nem as datas. DU lista a coluna "Posicao do medidor lida"; DEF e SR1 falam em "leitura". Confirmar se são a mesma coisa.
- DU está incompleto (coluna de imagens com `___`) e não registra EDA, nem os achados do SR1.

### 8. Metas de I2 e classes da rede

- DEF: 4 classes (medidor, fachada ou portão, caixa fechada, outro) e F1 macro.
- SR1: detector de 3 regiões (medidor, ID, visor). Métricas são localização e acerto exato.
- Os dois desenhos não se somam sem uma decisão explícita.

### 9. Datas de entregáveis (DEF) contra o cronograma (CRO)

- DEF: modelo em 24/10, pipeline em 14/11, app em 21/11, relatório em 28/11.
- CRO: Data Preparation de 13/09 a 19/09 e baseline até 02/10 (sem rotulagem prevista). Modeling até 13/11, Deployment de 21/11 a 27/11.
- Faltam no CRO a rotulagem e o teste de OCR de 19/09 que DEF e MAT prometem.
- MAT: I5 (foto repetida) "depois do SR1". O SR1 não cita I5.

## Menores

### 10. Nome do integrante

"João Pedro Lacet" (S29), "João Pedro Lins" (KO, SR1), "João Pedro Lins Lacet Dias" (IDE, MAT, DEF). Definir a forma de uso nas apresentações.

### 11. Nome e identificação do grupo e da disciplina

`contexto.md` diz "Grupo 4" e "Projeto 4 (Dados)". Os documentos usam "Grupo G4", disciplina BD023, turma BD20262_4A, docente Erick Simões de Matos. O `contexto.md` não registra código, turma nem docente.

### 12. Problema descrito no `contexto.md`

Resultado "Aprovado, Reprovado ou Revisão manual, com motivo" segue DEF e KO. O SR1 usa "confere, diverge ou revisão". Depende do item 1.

### 13. Perguntas do cliente ainda sem resposta (D1 a D5, BU)

Nenhum documento registra resposta do cliente para: critério formal de foto por nota (D1), amostra auditada (D2), resolução original (D3), percentual auditado hoje (D4), restrição de LGPD (D5). BU também lista em aberto o tempo médio atual, tipos de medidores mais frequentes, precisão aceitável e o que fica sempre humano. SR1 repete "qual taxa de acerto o cliente aceita".

### 14. Detalhes de ordem das verificações

DEF diz que "foto reprovada na verificação 1 não chega à rede neural", mas a ordem lista I6 (CSV) primeiro. S29 lista I5 no fluxo do MVP, apesar de I5 estar fora do MVP.

### 15. Arquivos duplicados no Drive

A pasta Apresentações tem "Copy of GridVision SR1.pdf" e "Copy of GridVision_Kickoff.pdf" (mesmos tamanhos dos originais). O Kickoff tem título interno "v2". O SR1 tem título interno "Recriação de slides GridVision". Convém definir qual é a versão oficial.

## Pontos que batem entre os documentos

- 31,8% abaixo do limiar de nitidez, amostra de 1.200 (IDE, S29, SR1).
- 296 registros com nota que exige foto e sem foto (IDE, MAT, S29, SR1).
- 12.340 fotos, sem EXIF (IDE, S29, SR1). 360x480 (MAT, S29, SR1).
- 61 notas no dicionário e 19 com exemplos, ou seja, 42 sem (IDE, DEF). Dois terços dos registros sem ocorrência (DEF) batem com as 9.109 notas nulas em 13.669 registros (SR1).
- Marcos 12/09, 03/10 e 05/12 (CRO, `contexto.md`). Links do Site, Notion e Drive (Links Úteis, `contexto.md`).
- Metas de revocação 0,85, precisão 0,70 e 10 minutos para 3.500 fotos (DEF, S29).

## Pendências

| Item | O que falta | Responsável sugerido |
|---|---|---|
| 2 | Dizer se o teste de legibilidade dos dígitos em recortes foi feito e qual o resultado | Henrique |
| 5 | Confirmar com a Neoenergia se o volume mensal é de leituras ou de imagens, se a faixa é 50 a 70 mil ou 70 mil, e se a foto só existe quando a leitura está fora da faixa esperada (BU) ou em toda visita (Kickoff) | Grupo, na próxima conversa com o cliente |
| 6 | Conferir no CSV qual definição do "92%" está certa: registros cuja nota não exige foto que têm foto, ou fotos anexadas que são de notas que não exigem foto | João Pedro (fez a EDA) |
| 7 | Confirmar se a base original veio em .xlsx e foi convertida para CSV, e se a coluna "Posicao do medidor lida" é a leitura | João Pedro |
| 13 | Perguntas D1 a D5 da Ideação (critério formal de foto, amostra auditada, resolução original, percentual auditado hoje, LGPD) e as da BU (tempo médio de análise, tipos de medidor mais frequentes, precisão aceitável, o que fica sempre humano). A resposta "50% é válido" cobre só parte da pergunta de precisão aceitável | Grupo, com a Neoenergia |
| 15 | Escolher a versão oficial do Kickoff e do SR1 e apagar as cópias em Apresentações ("Copy of ...") | Grupo |
| Metas | Definir valor-alvo para localização, acerto exato da leitura e segurança, e validar com a Neoenergia | Grupo, antes do SR2 |
| Data Understanding | Completar o documento do Drive (coluna de imagens vazia, EDA do SR1 fora dele) | João Pedro |
