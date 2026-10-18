# Detector v0: medidor, placa e visor (18/10/2026)

Primeira versão do detector, treinada só com as 300 fotos do [piloto de anotação](../piloto_anotacao/). Serve para provar que o caminho funciona e para pré-anotar as fotos de validação e teste. Não é o resultado oficial.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `preparar_dataset.py` | Converte o export do Label Studio para o formato YOLO e divide o piloto em 240 fotos de treino e 60 de checagem (estratificado por nítida, borrada e fora do CSV, seed 42) |
| `treinar.py` | Treina o YOLO11n pré-treinado e avalia na checagem, incluindo o acerto de "tem medidor?" |
| `divisao_interna_piloto.csv` | Qual foto do piloto foi para treino e qual para checagem. Só nomes de arquivo |

Fotos, rótulos e pesos (`best.pt`) ficam fora do Git, em `gridvision_dados/detector_v0/`.

## Configuração

YOLO11n (Ultralytics 8.4.182) pré-treinado no COCO, imagem de 480 px, 60 épocas, batch 16, seed 42, espelhamento horizontal desligado. Treino em CPU, 27 minutos.

## Resultado na checagem (60 fotos do piloto)

| Métrica | Valor |
|---|---|
| mAP50, três classes | 0,917 |
| mAP50 medidor | 0,987 |
| mAP50 visor | 0,936 |
| mAP50 placa | 0,829 |
| mAP50-95 | 0,555 |
| Precisão / revocação | 0,904 / 0,870 |
| "Tem medidor?" (confiança ≥ 0,25) | 59 de 60, 1 falso positivo, 0 falso negativo |

Ressalvas: só 60 fotos de checagem, todas do mesmo conjunto (treino da `divisao_v1`) e anotadas pela mesma pessoa que fez o treino. A placa é a classe mais difícil: é a menor caixa e a de regra mais ambígua no piloto.

## Ambiente

PC do João Pedro: AMD Ryzen 5 5600X (6 núcleos), 16 GB de RAM, Windows 11, só CPU. Python 3.12, PyTorch 2.14.1+cpu.
