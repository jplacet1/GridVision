# -*- coding: utf-8 -*-
"""Passo 1 (ambiente com ultralytics): detector v0 acha visor e placa e salva os recortes.

Uso: python recortar.py <best.pt> <pasta de fotos> <pasta de saída fora do Git>
Para cada foto, guarda a caixa de maior confiança de cada classe (conf >= 0.25),
com margem de 8% de cada lado. Grava deteccoes.json com caixa e confiança.
"""
import json, sys
from pathlib import Path
import cv2
from ultralytics import YOLO

PESOS, FOTOS, SAIDA = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
NOMES = {0: "medidor", 1: "placa", 2: "visor"}
MARGEM = 0.08
modelo = YOLO(PESOS)
for c in ("visor", "placa"):
    (SAIDA / c).mkdir(parents=True, exist_ok=True)

det = {}
for img_path in sorted(FOTOS.glob("*.jpg")):
    img = cv2.imread(str(img_path)); h, w = img.shape[:2]
    r = modelo.predict(str(img_path), imgsz=480, conf=0.25, device="cpu", verbose=False)[0]
    melhor = {}
    for (x0, y0, x1, y1), c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
        nome = NOMES[int(c)]
        if nome not in melhor or s > melhor[nome][1]:
            melhor[nome] = ((x0, y0, x1, y1), s)
    det[img_path.name] = {}
    for nome, ((x0, y0, x1, y1), s) in melhor.items():
        det[img_path.name][nome] = {"caixa": [round(v, 1) for v in (x0, y0, x1, y1)], "conf": round(s, 3)}
        if nome in ("visor", "placa"):
            mx, my = MARGEM * (x1 - x0), MARGEM * (y1 - y0)
            X0, Y0 = int(max(0, x0 - mx)), int(max(0, y0 - my))
            X1, Y1 = int(min(w, x1 + mx)), int(min(h, y1 + my))
            cv2.imwrite(str(SAIDA / nome / img_path.name.replace(".jpg", ".png")), img[Y0:Y1, X0:X1])
json.dump(det, open(SAIDA / "deteccoes.json", "w", encoding="utf-8"), indent=1)
print("fotos", len(det), "| com visor", sum("visor" in d for d in det.values()),
      "| com placa", sum("placa" in d for d in det.values()))
