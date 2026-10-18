# Recorte do visor + OCR pronto (18/10/2026)

Teste do fluxo "detector acha o visor e a placa, recorta, OCR lê o recorte", nas mesmas 100 fotos nítidas do baseline. Detector: [detector v0](../detector_v0/). OCR: PaddleOCR 3.7, mesma configuração do baseline.

## Arquivos

| Arquivo | Ambiente | O que faz |
|---|---|---|
| `recortar.py` | ultralytics | Detecta visor e placa (caixa de maior confiança, conf ≥ 0,25, margem de 8%) e salva os recortes |
| `ler_recortes.py` | PaddleOCR 3.7 | Amplia cada recorte até 96 px de altura (máx. 4x), lê e avalia |
| `variantes.py` | PaddleOCR 3.7 | Variantes B (junta pedaços) e C (recorte lido como linha única, só o reconhecedor) |
| `fator_ampliacao.py` | PaddleOCR 3.7 | Recorte ampliado com fator fixo de 2x, 3x e 4x, juntando pedaços |

Recortes e saídas por foto ficam fora do Git (LGPD).

## Resultado (acertos em 100 fotos)

| Variante | Leitura (sem zeros) | Leitura estrita | Nº do medidor igual |
|---|---|---|---|
| Foto inteira, PaddleOCR 3.7 (baseline) | 20 | 3 | 38 |
| Foto inteira ampliada 2x (referência) | 28 | 8 | 41 |
| A. Recorte, OCR completo | 18 | 7 | 30 |
| B. Recorte, junta pedaços | 19 | 7 | 30 |
| C. Recorte, linha única | 11 | 3 | 34 |
| D. Recorte ampliado 2x, junta pedaços | **23** | **8** | 31 |
| E. Recorte ampliado 3x | 15 | 4 | 29 |
| F. Recorte ampliado 4x | 11 | 3 | 30 |

Detector achou o visor em 87 fotos e a placa em 70. Sem as 3 fotos que estavam no treino do detector, a leitura fica em 17 (A), 18 (B) e 11 (C) em 97.

## Conclusões

- O fator de ampliação importa: em A, B e C o recorte ia só até 96 px de altura (≈ 1,4x no visor típico). Com 2x fixo (D), a leitura sobe para 23 e empata com a foto inteira ampliada no critério estrito (8). Com 3x e 4x, piora: o OCR parte os dígitos grandes.
- Foto inteira ampliada (28) contra recorte 2x (23): 19 fotos acertadas pelos dois, 9 só pela foto inteira, 4 só pelo recorte. 7 dos 28 acertos da foto inteira são leituras de 1 a 3 dígitos, que podem coincidir com outros números impressos (ex.: "100" em "15(100)A").

- O detector não é o gargalo. O OCR pronto lê mal os dígitos de display (7 segmentos, roletes): nas fotos que o recorte perdeu, ele quase sempre leu um dígito errado ou partiu a leitura.
- A métrica "algum texto da foto igual à leitura" favorece a foto inteira, que gera dezenas de textos e pode coincidir por acaso. O recorte é a medida mais próxima do que o sistema faria.
- O recorte é muito mais rápido (≈ 1 s por foto contra ≈ 10 s da foto inteira ampliada).
- Próximo passo: reconhecedor próprio para o visor, treinado com recortes do detector e a leitura do CSV nas fotos marcadas como legíveis no piloto.
