# Experimento de OCR 1: pré-processamento (17/10/2026)

Primeiro teste da fase de Modeling, sem treino e sem anotação. Mesmas 100 fotos nítidas do [baseline](../baseline_ocr/) (seed 1, nitidez ≥ 100) e mesmas métricas. Página com o resultado: [artefato "Experimento de OCR 1"](https://claude.ai/artifact/5ebXfTqPCAmeJuMRWBxqPN) (privado, compartilhar pelo Share).

## Arquivos

| Arquivo | O que faz |
|---|---|
| `exp1_paddle210.py` | Rodada 1, PaddleOCR 2.10: V0 foto inteira, V1 ampliada 2x + CLAHE, V2 detecta texto, recorta, amplia 3x e lê |
| `exp2_paddle37.py` | Rodada 2, PaddleOCR 3.7 (mesma config do baseline): `V0` avalia a saída bruta do baseline, `V1` ampliada 2x + CLAHE, `V1b` só ampliada 2x |
| `etapas_sintetico.py` | Gera as imagens das etapas usadas no artefato, a partir de um medidor sintético (nenhum dado da Neoenergia) |

Os scripts esperam, na mesma pasta e fora do Git, a pasta `baseline_ocr/` do pacote do Henrique (`fotos/` e `amostra_100_nitidas.csv`). Fotos, CSV e saídas por foto não entram no repositório (LGPD).

## Resultado (acertos em 100 fotos)

| Métrica | 2.10 V0 | 2.10 V1 (2x + CLAHE) | 2.10 V2 (recorte) | 3.7 V0 (baseline) | 3.7 V1 (2x + CLAHE) | 3.7 V1b (só 2x) |
|---|---|---|---|---|---|---|
| Leitura correta, ignora zeros à esquerda | 14 | 19 | 9 | 20 | 22 | **28** |
| Leitura correta, estrita | 5 | 3 | 4 | 3 | 6 | **8** |
| Leitura errada por 1 dígito | 13 | 7 | 12 | 8 | 10 | 11 |
| Nº do medidor igual ao texto | 26 | 30 | 24 | 38 | 40 | **41** |
| Nº do medidor contido no texto | 30 | 34 | 25 | 42 | **46** | **46** |
| Nenhum texto detectado | 23 | 17 | 22 | 16 | **11** | 12 |

Teste pareado (McNemar exato), 3.7 V0 contra V1b: leitura 9 contra 1 (p = 0,02); nº do medidor 4 contra 1 (p = 0,38).

Conclusões: ampliar 2x é a melhor mudança isolada; o CLAHE ajuda no 2.10 e atrapalha no 3.7; recortar com o detector de texto genérico piora (o recorte precisa de detector treinado para visor e placa).

## Ambiente de execução

| Item | Valor |
|---|---|
| Máquina | PC pessoal do João Pedro |
| CPU | AMD Ryzen 5 5600X, 6 núcleos / 12 threads |
| RAM | 16 GB |
| GPU | AMD Radeon RX 6600 (não usada; tudo em CPU) |
| Sistema | Windows 11 Home 10.0.26200 |
| Rodada 1 | Python 3.12, PaddleOCR 2.10.0, PaddlePaddle 2.6.2, OpenCV 4.10 (ambiente do serviço de MLOps), modelos PP-OCRv4 `en` |
| Rodada 2 | Python 3.12, PaddleOCR 3.7.0, PaddlePaddle 3.3.1, `opencv-python-headless`, modelos PP-OCRv5 `en`, `enable_mkldnn=False` |

Tempos (100 fotos): 2.10 V0 29 s, V1 44 s, V2 32 s. 3.7 V1 e V1b ≈ 18 min cada, rodando os dois em paralelo. O baseline 3.7 (foto inteira) levou ≈ 9 min na máquina do Henrique.
