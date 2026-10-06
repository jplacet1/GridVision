# Baseline de OCR — GridVision (SR1, 02/10/2026)

> **Neste repositório só estão o script, o `requirements.txt` e este README.** `fotos/`, `amostra_100_nitidas.csv`, `paddleocr_saida_bruta.json` e `resultado_baseline_ocr.csv` contêm dados da Neoenergia (LGPD) e ficam fora do Git, com o Henrique (autor do baseline). Para rodar, copie o pacote completo para uma pasta local fora do repositório. Ver [docs/guia-do-grupo.md](../../docs/guia-do-grupo.md).

OCR pronto (PaddleOCR, PP-OCRv5, modelo `en`, CPU) rodado na foto inteira, sem recorte e sem treino,
em 100 fotos nítidas sorteadas da base da Neoenergia. Os textos reconhecidos são comparados com o
nº do medidor e a leitura registrados no CSV.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python baseline_ocr.py avaliar     # só reavalia a saída de 02/10 (segundos)
python baseline_ocr.py ocr         # refaz o OCR nas 100 fotos (~9 min em CPU); depois rode `avaliar`
```

`python baseline_ocr.py amostrar` refaz o sorteio das 100 fotos, mas exige que esta pasta esteja dentro de
"Projeto 4", ao lado de `Entregaveis/` (saídas do `eda_projeto4.py`) e de `Classroom/Base de Dados Neoenergia PE/`.
Não é necessário para reproduzir o resultado.

## O que tem na pasta

| Arquivo | O que é |
|---|---|
| `baseline_ocr.py` | script com as três etapas: amostrar, ocr, avaliar |
| `requirements.txt` | versões usadas em 02/10 |
| `amostra_100_nitidas.csv` | as 100 fotos sorteadas (seed=1, nitidez ≥ 100), com nº do medidor e leitura do CSV |
| `fotos/` | cópia das 100 fotos |
| `paddleocr_saida_bruta.json` | textos e confianças que o PaddleOCR devolveu por foto |
| `resultado_baseline_ocr.csv` | uma linha por foto: acertos de leitura e de nº do medidor |

## Protocolo

- Amostra: das 1.200 fotos da amostra de qualidade da EDA, as 765 com variância do Laplaciano ≥ 100
  e registro no CSV; 100 sorteadas com `random_state=1`.
- OCR na imagem inteira (360×480), sem pré-processamento. Dos textos reconhecidos, só os dígitos.
- Leitura: acerto se algum texto é igual à leitura do CSV ignorando zeros à esquerda (o display mostra
  `042884`, o CSV tem `42884`). "Erro de 1 dígito": distância de Levenshtein 1 e tamanho igual ou ±1.
- Nº do medidor: acerto se algum texto é igual a um dos números do campo (que pode trazer vários,
  separados por `/`, e letras).

## Resultado (100 fotos nítidas)

| | acertos |
|---|---|
| Nº do medidor lido corretamente (texto impresso na placa) | 42 |
| Leitura lida corretamente, ignorando zeros à esquerda (display) | 20 |
| Leitura errada por exatamente 1 dígito | 8 |
| Nenhum texto detectado | 16 |

Três conclusões: o OCR genérico lê a placa mas não o display, que precisa de tratamento próprio;
acurácia por caractere esconde erros de 1 dígito, por isso a métrica é acerto exato; e em 16% das fotos
nítidas o OCR não acha texto, o que justifica a etapa de localização antes da leitura.

## Limitações

Só fotos nítidas (melhor caso), um único OCR, sem recorte e sem ajuste fino. Não testado em fotos
desfocadas ou escuras.

## Observação

`enable_mkldnn=False` no construtor do PaddleOCR é necessário: com o PaddlePaddle 3.3 em CPU, sem isso
a inferência falha e devolve zero textos sem levantar erro visível.
