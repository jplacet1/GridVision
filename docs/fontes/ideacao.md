# Ideação da solução (documento 1 de 4)

Fonte: `Ideação.docx` (Drive, Entregáveis SR1). Modificado em 29/08/2026.

Disciplina BD023, Projeto 4 (Dados), CESAR School. Docente Erick Simões de Matos. Turma BD20262_4A, semestre 2026.2. Integrantes: Alana Cecília Costa Cavalcanti, Henrique Valença Bouwman, João Pedro Lins Lacet Dias.

Método: Matriz CSD, How Might We e Crazy 8s. Insumo: briefing da Neoenergia e conversa com o cliente em 15/08/2026.

A base de imagens chegou ao grupo em 22/08, depois da sessão. A ideação partiu do problema descrito pelo cliente, não do que os dados permitem.

SCAMPER não foi usado (parte de processo existente, e nunca houve tentativa anterior). Brainwriting 6-3-5 não foi usado (pressupõe seis pessoas, são três).

## Matriz CSD

### Certezas (o que o cliente afirmou)

- C1: a foto existe para comprovar a leitura feita em campo.
- C2: todos os clientes são visitados mensalmente, e o volume de fotos é enorme.
- C3: esse volume "torna difícil garantir que todas sejam verificadas com atenção".
- C4: "nem sempre é possível confirmar se a foto corresponde exatamente ao medidor do cliente".
- C5: revisar manualmente milhares de fotos consome recursos e atrasa processos.
- C6: nunca houve tentativa anterior de resolver o problema.
- C7: quem sofre primeiro é o cliente final, porque o erro chega na fatura.
- C8: o cliente sugeriu a solução: IA que valide se a foto está legível, se mostra o medidor e se combina com a nota registrada. Exemplo: nota I100, casa fechada, em que a foto precisa mostrar o portão.

### Suposições

| # | Suposição | Como validar |
|---|---|---|
| S1 | A auditoria hoje é por amostragem, não em tudo | Perguntar o percentual auditado e o tamanho da equipe |
| S2 | Existe critério formal de foto válida por tipo de nota | Pedir o manual do leiturista |
| S3 | O sistema deixa fechar ocorrência que exige foto sem anexar foto | Verificar em extração real |
| S4 | Parte relevante das fotos é ilegível | Medir em amostra |
| S5 | As fotos contêm dados pessoais (LGPD) | Inspecionar imagens e consultar o cliente |

### Dúvidas (só o cliente responde)

- D1: existe manual ou critério formal de foto válida por nota?
- D2: existe amostra de fotos já auditada?
- D3: qual a resolução original das fotos? (define se dá para ler os dígitos)
- D4: qual percentual das fotos é auditado hoje, e em quanto tempo? (baseline de ganho)
- D5: há restrição de LGPD sobre o uso das imagens?

## How Might We

- HMW1: verificar automaticamente se uma foto serve como prova da leitura (C1, C4).
- HMW2: tirar da fila do auditor as fotos que nem um humano conseguiria julgar (C3, C5).
- HMW3: saber se o que a foto mostra combina com a ocorrência registrada (C8).
- HMW4: detectar ocorrências fechadas sem foto (C1, S3).
- HMW5: entregar o resultado num formato que o auditor use de verdade (C5, C7).

## As 8 ideias (Crazy 8s)

| # | Ideia | O que faz | Como | HMW |
|---|---|---|---|---|
| I1 | Foto legível | Marca como ilegível a foto desfocada, escura ou sem contraste | Variância do Laplaciano, brilho, contraste | 2 |
| I2 | O que a foto mostra | Classifica em medidor, fachada ou portão, caixa fechada, outro | CNN treinada com imagens rotuladas por nós | 1 |
| I3 | Foto bate com a nota | Compara a classe da foto com a evidência esperada para a ocorrência | Saída de I2 contra tabela de evidência esperada por nota | 3 |
| I4 | Ler os dígitos do display | Extrai o valor e compara com o digitado | Detecção do visor mais OCR | 1 |
| I5 | Foto repetida | Acha a mesma imagem em visitas ou medidores diferentes | Hash perceptual | 1 |
| I6 | Ocorrência sem foto | Sinaliza registro cuja nota exige foto e não tem foto | Regra sobre o CSV | 4 |
| I7 | Veredito por foto | Junta as verificações: aprovada, reprovada ou revisar, com motivo | Regra de combinação | 5 |
| I8 | Tela do auditor | Ver resultado, olhar a foto, confirmar ou discordar | Aplicação web simples | 5 |

Ideias de mudança de processo interno da Neoenergia ficaram de fora.

## O que a base mostrou (chegou em 22/08)

| Suposição | Situação | Evidência |
|---|---|---|
| S3 | Confirmada | 296 registros com nota que exige foto e sem foto anexada |
| S4 | Confirmada | 31,8% das imagens abaixo do limiar de nitidez, em amostra de 1.200 |
| S5 | Confirmada | Fachadas, números de porta e vias públicas aparecem |
| S2 | Enfraquecida | 92% dos registros cuja nota não exige foto têm foto assim mesmo |
| S1 | Aberta | Depende do cliente |

Não previsto: nenhuma das 12.340 imagens tem metadado EXIF (reforça I5). 42 das 61 notas do dicionário não têm um único exemplo.
