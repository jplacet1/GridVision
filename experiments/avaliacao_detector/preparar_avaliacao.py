# -*- coding: utf-8 -*-
"""Amostra de avaliação (validação + teste) e pré-anotação com o detector v0 (18/10/2026).

Uso (ambiente com ultralytics):
    python preparar_avaliacao.py <zip da base> <best.pt> <pasta de saída fora do Git>

- 100 fotos sorteadas do conjunto `validacao` e 100 do `teste` da divisao_v1, sem estratificar,
  para manter a proporção real da base (nítidas, borradas, fora do CSV). Seed 42.
- Copia as fotos para <saída>/fotos/parte1 e parte2 (limite de 100 por envio no Label Studio).
- Roda o detector (conf >= 0.25) e grava <saída>/predicoes.json: por foto, as caixas em
  percentual da imagem, no formato de resultado do Label Studio.
- Grava avaliacao_v1.csv (só nomes de arquivo e conjunto) no repositório.
"""
import csv, json, random, sys, zipfile
from pathlib import Path
from ultralytics import YOLO

ZIP, PESOS, SAIDA = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
AQUI = Path(__file__).resolve().parent
NOMES = {0: "medidor", 1: "placa", 2: "visor"}

div = list(csv.DictReader(open(AQUI.parent / "piloto_anotacao" / "divisao_v1.csv", encoding="utf-8")))
rng = random.Random(42)
amostra = []
for conj in ("validacao", "teste"):
    fs = sorted(r["arquivo"] for r in div if r["conjunto"] == conj)
    amostra += [(f, conj) for f in rng.sample(fs, 100)]

z = zipfile.ZipFile(ZIP)
caminho = {n.split("/")[-1]: n for n in z.namelist() if n.lower().endswith(".jpg")}
modelo = YOLO(PESOS)
pred = {}
for i, (f, conj) in enumerate(amostra):
    destino = SAIDA / "fotos" / ("parte1" if i < 100 else "parte2")
    destino.mkdir(parents=True, exist_ok=True)
    p = destino / f
    p.write_bytes(z.read(caminho[f]))
    r = modelo.predict(str(p), imgsz=480, conf=0.25, device="cpu", verbose=False)[0]
    h, w = r.orig_shape
    res = []
    for k, ((x0, y0, x1, y1), c, s) in enumerate(zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())):
        res.append({"id": f"p{k}", "from_name": "caixas", "to_name": "foto", "type": "rectanglelabels",
                    "original_width": w, "original_height": h, "image_rotation": 0, "score": round(s, 3),
                    "value": {"x": 100 * x0 / w, "y": 100 * y0 / h, "width": 100 * (x1 - x0) / w,
                              "height": 100 * (y1 - y0) / h, "rotation": 0, "rectanglelabels": [NOMES[int(c)]]}})
    pred[f] = res

json.dump(pred, open(SAIDA / "predicoes.json", "w", encoding="utf-8"))
with open(AQUI / "avaliacao_v1.csv", "w", newline="", encoding="utf-8") as fh:
    wr = csv.writer(fh); wr.writerow(["arquivo", "conjunto"]); wr.writerows(amostra)
n = sum(len(v) for v in pred.values())
print("fotos", len(amostra), "| caixas previstas", n, "| fotos sem nenhuma caixa", sum(1 for v in pred.values() if not v))
