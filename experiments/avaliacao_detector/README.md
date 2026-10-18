# Avaliação do detector v0 em validação e teste (18/10/2026)

Primeira avaliação do [detector v0](../detector_v0/) num conjunto independente do treino: 100 fotos sorteadas do conjunto `validacao` e 100 do `teste` da divisão, sem estratificar (proporção real da base). O detector pré-anotou as caixas e o João Pedro corrigiu à mão no Label Studio, respondendo também as perguntas de legibilidade.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `preparar_avaliacao.py` | Sorteia as 200 fotos, copia para fora do Git e gera as caixas previstas |
| `importar_predicoes.py` | Envia as caixas previstas para o projeto do Label Studio (pré-anotação) |
| `avaliar.py` | Compara previsto com corrigido: AP50, precisão, revocação, "tem medidor?", caixas mudadas e legibilidade |
| `avaliacao_v1.csv` | As 200 fotos e o conjunto de cada uma. Só nomes de arquivo |

## Resultado

| Classe | AP50 | Precisão | Revocação | Caixas reais |
|---|---|---|---|---|
| Medidor | 0,942 | 0,873 | 0,952 | 188 |
| Placa | 0,928 | 0,957 | 0,936 | 141 |
| Visor | 0,957 | 0,939 | 0,966 | 175 |
| **mAP50** | **0,942** (validação 0,935, teste 0,951) | | | |

Precisão e revocação com confiança ≥ 0,25 e IoU ≥ 0,5. "Tem medidor?": 193 de 200 certas (3 falsos positivos, 4 falsos negativos).

O que foi mudado nas caixas previstas:

| Classe | Aceita sem mudança | Ajustada | Apagada | Desenhada do zero |
|---|---|---|---|---|
| Medidor | 161 | 21 | 23 | 6 |
| Placa | 129 | 3 | 6 | 9 |
| Visor | 162 | 7 | 11 | 6 |

**Viés de ancoragem:** a correção partiu das caixas previstas, então caixas "boas o bastante" tendem a ser aceitas como estão. Isso puxa o resultado para cima, sobretudo nas métricas que exigem caixa justa. As caixas apagadas e desenhadas do zero mostram os erros reais do detector.

## Legibilidade (amostra aleatória, proporção real)

| | 200 fotos |
|---|---|
| Leitura legível | 113 (56%) |
| Número do medidor legível | 97 (48%) |
| Os dois legíveis | 92 (46%) |
| Sem medidor | 22 (11%) |

Confirma, numa amostra independente e sem ponderação, a estimativa do piloto (56%, 53%, 48% e 11%).

Ambiente: o mesmo do [detector v0](../detector_v0/).
