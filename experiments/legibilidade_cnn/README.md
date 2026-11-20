# Legibilidade pelo recorte do visor com CNN (20/11/2026)

Pergunta do item 12h: dá para negar menos fotos com salvação do que o classificador v1? Script: [legibilidade_cnn.py](legibilidade_cnn.py).

## Por que

Na revisão cega de 11/11, 46 das 198 fotos negadas pelo v1 (limiar 0,40) tinham a leitura legível. O v1 usa sinais do detector e do OCR, então nega a foto boa quando o OCR falha. No Copel-AMR (Laroca et al., 2021), uma rede que olha o próprio recorte do contador recusou 98,9% dos ilegíveis e aceitou 99,8% dos legíveis.

## Como

- MobileNetV3-small pré-treinada no ImageNet, com a última camada trocada e ajuste fino no recorte do visor (detector v0, mesma folga do app, 96 x 224). Média de 5 sementes, 12 épocas, CPU, cerca de 3 min no total.
- Treino: 522 fotos (300 legíveis) do piloto, da avaliação de validação e do histórico do app. Nada do `lote_demo6`, do teste nem do teste temporal.
- Prova: as 225 fotos da revisão cega do `lote_demo6` (sem as 3 "sem medidor"), que nem o v1 nem a CNN viram. 74 são legíveis. Legível = "Legível" ou "Legível com esforço", o mesmo critério de 11/11.

## Resultado

AUC na revisão cega: v1 0,843, CNN 0,859, média dos dois 0,879. Entre as 195 negadas pelo v1, a CNN separa as salváveis com AUC 0,780.

Regra "nega só se v1 < 0,40 e CNN < t", comparada ao v1 sozinho com o mesmo número de negadas:

| Negadas | Com salvação: v1 sozinho | Com salvação: v1 + CNN |
|---|---|---|
| 91 | 11 | 8 |
| 112 | 14 | 12 |
| 141 | 19 | 17 |
| 155 | 25 | 23 |

## Conclusão

A CNN acrescenta informação: as salváveis caem de 2 a 3 com o mesmo volume de negadas. Mas nenhum ponto chega a zero salváveis com volume útil, e a amostra é pequena (diferenças de 2 a 3 fotos). Não basta, sozinha, para passar no teste do professor (07/11). Serve como mais um sinal para o classificador quando houver mais rótulos. A transcrição do 12a e a própria revisão cega podem entrar no treino, mas aí é preciso outra amostra cega para provar. O app não foi alterado.
