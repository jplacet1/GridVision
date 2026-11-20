# Leitor próprio do visor (CRNN + CTC)

Item 12. O leitor lê o recorte do visor e devolve os dígitos. As versões:

| Versão | Treino | Script |
|---|---|---|
| ctc_v0 (06/11) | 1.316 pseudo-rótulos (recortes em que o OCR leu exatamente a leitura do CSV) + displays sintéticos | [treinar_ctc.py](treinar_ctc.py) |
| ctc_v1 (20/11) | ctc_v0 + transcrição manual do 12a (~290 recortes legíveis, função separada por espaço) + sintéticos | [treinar_transcricao.py](treinar_transcricao.py) |
| ctc_v2 (20/11) | ctc_v0 + transcrição + pseudo-rótulos + sintéticos; modelo escolhido por checagem de 43 recortes | [treinar_v2.py](treinar_v2.py) |

Pesos fora do Git, em `gridvision_dados/leitor_digitos/`.

## Acerto na validação da transcrição (64 recortes legíveis, medido uma vez)

| Leitor | Texto exato | Leitura exata |
|---|---|---|
| OCR do app (pré-preenchimento) | 21 (33%) | 33 (52%) |
| ctc_v0 | 12 (19%) | 39 (61%) |
| ctc_v1 | 28 (44%) | 36 (56%) |
| ctc_v2 | 19 (30%) | **40 (62%)** |

## Como passe extra do app

Medido com [candidatos_visor.py](candidatos_visor.py) e a variante `visor_externo` de [passes_extras.py](../passes_extras/passes_extras.py). O pipeline do app decide, com a mesma regra e o limiar de 0,90.

| | Gabarito (390 fotos) | `lote_demo6` (500 fotos) |
|---|---|---|
| App atual | 17 Confere, 1 erro | 67 Confere |
| + ctc_v0 | 19 (+2), 1 erro | - |
| + ctc_v1 | 17 (+0), 1 erro | - |
| + ctc_v2 | 20 (+3), 1 erro | 66 (+3, −4) |

O ctc_v1 acerta 6 das 22 fotos em que só a leitura falhava, mas sempre com confiança abaixo de 0,90. No `lote_demo6`, o ctc_v2 ganha 3 Confere e perde 4. Quando o candidato dele bate com o CSV, a escolha do app pode preferi-lo a um candidato do OCR de confiança maior, e a foto cai em Revisão manual.

**Conclusão:** o leitor próprio lê melhor que o OCR fora do app (62% contra 52%), mas não converte em Confere com as regras atuais. Fica fora do app. Para ele valer, seria preciso calibrar a confiança dele e mudar a escolha entre candidatos, sem quebrar o erro zero. Aceitar a leitura só pela concordância não serve ([concordancia](../concordancia/README.md)). O gargalo da cobertura também está no número (25 de 59 fotos na [análise de erros](../analise_erros/README.md)) e no limiar de legibilidade de 0,02, escolhido pelo grupo na 12h.
