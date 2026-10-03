# Matriz Impacto x Esforço (documento 3 de 4)

Fonte: `Matriz Impacto Esforço.docx` (Drive, Entregáveis SR1). Modificado em 29/08/2026. Entrada: documento 1 (ideação). Saída: documento 4 (definição da solução).

## Critérios (escala 1 a 5)

Impacto: quanto a verificação reduz o trabalho manual do auditor ou pega um erro que hoje passa. Esforço: custo para o grupo (rotulagem, treino, risco técnico), com três pessoas.

| Nota | Impacto | Esforço |
|---|---|---|
| 1 | Não muda nada na auditoria | Regra simples sobre o CSV, horas |
| 2 | Pega caso pontual | Processamento de imagem sem treino, dias |
| 3 | Reduz trabalho em situação específica | Rotulagem e treino, semanas |
| 4 | Reduz trabalho manual de forma mensurável | Rotulagem volumosa ou risco técnico alto |
| 5 | Sem isso a solução não fecha | Depende de algo ainda não sabido se é viável |

## Matriz

Divisórias em impacto 3,5 e esforço 2,75. O quadrante baixo impacto e alto esforço ficou vazio.

| # | Ideia | Imp. | Esf. | Justificativa |
|---|---|---|---|---|
| I7 | Veredito por foto | 5,0 | 2,5 | Sem ele as verificações ficam soltas. Só regra de combinação |
| I3 | Foto bate com a nota | 5,0 | 4,0 | Desafio literal do cliente. Depende de I2 e da tabela de evidência |
| I1 | Foto legível | 4,5 | 2,0 | Tira do caminho quase um terço das imagens. Sem rótulo nem treino |
| I2 | O que a foto mostra | 4,5 | 3,0 | Coração de visão computacional. Precisa de imagens rotuladas |
| I8 | Tela do auditor | 4,0 | 3,0 | Sem ela vira notebook com números |
| I4 | Ler os dígitos | 4,0 | 5,0 | Em 360x480 sobram poucas dezenas de pixels por dígito, não se sabe se dá |
| I6 | Ocorrência sem foto | 3,8 | 1,0 | Pega 296 casos com regra de uma linha |
| I5 | Foto repetida | 3,0 | 2,0 | Barata, cobre a falta de EXIF. Não se sabe se o reaproveitamento ocorre |

## Decisão

| Prioridade | Ideias | Quando |
|---|---|---|
| MVP | I6, I1, I2, I3, I7, I8 | I6 e I1 até o Kickoff. I2, I3, I7 e I8 até o SR2 |
| Se sobrar tempo | I5 | Depois do SR1 |
| Esticado, depende de teste | I4 | Só se o teste de legibilidade dos dígitos der certo em 19/09 |

I4 fora do MVP: imagens de 360x480 sem metadado. Teste em 100 recortes até 19/09.

I2 é o centro do projeto: I1 e I6 pegam problemas grosseiros sem aprendizado de máquina, e I3 depende inteiramente de I2.
