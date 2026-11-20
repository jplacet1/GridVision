# Análise de erros do pipeline do app (20/11/2026)

Item 12 da checklist: por que uma foto com a leitura legível não vira "Confere"? Script: [analise_erros.py](analise_erros.py).

## Dados

- Gabarito: decisões do João Pedro no app gravadas no histórico (lotes demo da validação, 162 fotos). 88 têm a leitura verdadeira (61 Corrigido, 27 Confirmado) e 74 foram marcadas Ilegível. Teste e teste temporal não entram.
- Pipeline: o do app em 20/11/2026 (detector v0, OCR v6 + v5 em ONNX na foto inteira e nos recortes, classificador v1 com limiar 0,40, confiança 0,90).
- A legibilidade do número do medidor não foi anotada nessas fotos: o analista decide pela leitura. Parte das falhas do número pode ser placa ilegível de verdade.
- O detalhe por foto fica em `gridvision_dados/analise_erros/detalhe.csv`, fora do Git (LGPD).

## Resultado

Status atual das 88 fotos legíveis: 8 Confere, 41 Revisão manual, 25 Diverge, 7 Ilegível, 4 Lido, 3 Ilegível (certeza alta).

Causa da primeira falha nas 80 que não conferem:

| Causa | Fotos | O que resolve |
|---|---|---|
| CSV difere da leitura real | 19 | Nada: não conferir é o certo. 8 viraram Diverge, 9 Revisão manual e 2 Ilegível |
| Sem leitura informada | 9 | Nada: vão ao analista (4 como Lido, 5 em Revisão manual) |
| OCR leu outro valor | 20 | Leitor próprio do visor (item 12a) |
| OCR sem dígitos no visor | 4 | Leitor próprio do visor (item 12a) |
| Detector sem visor | 1 | Detector |
| Função recusada | 1 | A conferir: o analista confirmou como verdadeira a leitura que veio com a função recusada; pode ser recusa indevida |
| Confiança abaixo de 0,90 | 16 | Ver abaixo: em 13 delas o número também falha |
| Número lido diferente do informado | 9 | Leitura da placa |
| Leitura certa descartada | 1 | Escolha entre os candidatos: a leitura certa estava lá e o número conferia, mas a extração ficou sem leitura |

Onde está o gargalo, nas 59 fotos em que o CSV traz a mesma leitura do visor (as únicas que podem conferir; números impressos pelo script):

- leitura lida certa em 32 (54%) e número igual ao informado em 33 (56%), **os dois juntos em só 10**. Os dois lados falham em fotos diferentes, e o Confere exige os dois (decisão de 24/10);
- a leitura certa aparece entre os candidatos do OCR em 34, só 2 a mais do que as escolhidas certas, então escolher melhor entre eles ganharia pouco;
- o número sai vazio em 1 e diferente do informado em 25: o OCR acha texto na placa, mas não o número inteiro.

## Limiar de confiança

Curva nas 162 fotos (erro = Confere em foto que o analista marcou ilegível ou com leitura diferente):

| Limiar | Confere | Erros |
|---|---|---|
| sem trava (0) | 11 | 1 |
| 0,80 | 10 | 1 |
| 0,90 (atual) | 8 | 1 |
| 0,95 | 7 | 0 |

Baixar o limiar quase não ganha cobertura (3 fotos de 88): das 16 paradas por confiança, 13 cairiam no número diferente. Nenhuma foto marcada ilegível pelo analista virou Confere em nenhum limiar.

**O único "erro" precisa de conferência à mão.** O analista registrou uma leitura de 10 dígitos que começa pelos 6 dígitos lidos pelo OCR (iguais ao informado). Um visor de 6 dígitos não mostra 10. O mais provável é erro de digitação no histórico, não do OCR. A foto está no `detalhe.csv` (status Confere, leitura lida diferente da verdadeira). Até essa conferência, por prudência, tratar como possível quebra do erro zero (com limiar 0,95 ela não conferiria).

## Conclusões

1. O próximo ganho de cobertura está no **leitor próprio do visor** (24 fotos com leitura errada ou vazia) e na **leitura da placa** (25 números diferentes). Mexer no limiar de confiança não resolve.
2. Em 22% das fotos legíveis, a leitura do CSV não é a que aparece no visor. Para elas o certo é ir ao analista. Isso também limita a cobertura máxima pelo Confere.
3. O app não foi alterado por esta análise.
