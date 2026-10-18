# Classificador de legibilidade da leitura (18/10/2026)

Dá a cada foto a chance de a leitura do visor ser legível (opção A: classificador simples sobre sinais que o detector já produz, sem rede nova). Abaixo do limiar, o app marca "Ilegível (certeza alta)" e tira a foto da fila de revisão.

- **Sinais** (`sinais_legibilidade` em [src/gridvision/extracao.py](../../src/gridvision/extracao.py)): confiança do detector no medidor, visor e placa; nitidez, contraste, brilho, altura e área do recorte do visor; nitidez e brilho da foto. Sem OCR, menos de 1 s por foto.
- **Alvo:** "leitura legível" marcada à mão no piloto e na avaliação.
- **Treino:** 144 fotos com medidor que o detector não viu (60 de checagem do piloto + validação). As 240 que treinaram o detector ficaram de fora (confianças otimistas).
- **Modelo:** regressão logística (AUC 0,851 na validação cruzada; gradient boosting 0,814). Coeficientes em [src/gridvision/legibilidade_v0.json](../../src/gridvision/legibilidade_v0.json).
- **Teste** (86 fotos com medidor, usado uma vez): AUC 0,926.

| Exclui se chance de legível < | Validação cruzada: excluídas / legíveis entre elas / ilegíveis pegas | Teste: excluídas / legíveis / ilegíveis pegas (de 31) |
|---|---|---|
| 0,10 | 15 / 1 / 14 | 10 / 0 / 10 |
| **0,20 (escolhido)** | 20 / 1 / 19 | 15 / 0 / 15 |
| 0,30 | 25 / 3 / 22 | 20 / 1 / 19 |
| 0,40 | 37 / 5 / 32 | 26 / 3 / 23 |

Limiar 0,20 escolhido pelo grupo em 18/10: pega cerca de metade das fotos ilegíveis, sem excluir legível no teste (1 em 20 na validação cruzada). Outro valor: `GRIDVISION_LIMIAR_ILEGIVEL`. Uma foto que confere com a leitura informada nunca é excluída.

Rodar: `python treinar_legibilidade.py <gridvision_dados>` no ambiente do app (precisa de scikit-learn).
