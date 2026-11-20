# Regra de concordância (20/11/2026)

Item 12. Pergunta: dá para aceitar a leitura com confiança abaixo de 0,90 quando vários passes leem o valor do CSV? Script: [concordancia.py](concordancia.py). O app não foi alterado.

Regra medida: o número do medidor confere com o CSV com confiança ≥ 0,90 (como hoje), e a leitura do CSV aparece em pelo menos k passes distintos, com qualquer confiança. Os passes são o OCR v6 e o v5 na foto e no recorte do visor, mais um leitor CTC.

Gabarito: 390 fotos da validação (162 decisões do histórico e 228 da revisão cega). Erro = Confere em foto cuja leitura é ilegível pelo gabarito, ou com leitura diferente da verdadeira.

| Regra | Leitor CTC como fonte | Confere | Erros |
|---|---|---|---|
| App atual | - | 17 | 1 (o caso conhecido dos 10 dígitos) |
| ≥ 1 passe | ctc_v0 | 29 | 1 |
| ≥ 1 passe | ctc_v2 | 31 | **2** |
| ≥ 2 passes | ctc_v0 ou ctc_v2 | 18 | 1 |

Com o ctc_v2, aceitar a leitura vista em um único passe criou um erro novo: Confere numa foto ilegível, por uma leitura de 4 dígitos que só o CTC viu. A maioria dos Confere novos vem só do CTC, e 2 têm leitura de 1 dígito, sujeita a coincidência. Com ≥ 2 passes, o ganho é de 1 foto.

**Conclusão:** a regra não entra. Em 1 passe ela quebra o erro zero; em 2 passes não ganha nada. A confiança do Confere continua exigindo 0,90.
