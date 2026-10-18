# -*- coding: utf-8 -*-
"""Treina a primeira versão do detector (medidor, placa, visor) com as 300 fotos do piloto.

Uso:
    python treinar.py <pasta do dataset (com dataset.yaml)> [modelo base] [épocas]

YOLO11n pré-treinado no COCO, CPU, imagem de 480 px (as fotos têm 360 x 480).
Espelhamento horizontal desligado: texto espelhado não acontece nas fotos reais.
Ao fim, avalia na checagem interna e mede se o detector acerta "tem medidor / não tem".
"""
import json, sys
from pathlib import Path
from ultralytics import YOLO

DATA = Path(sys.argv[1])
BASE = sys.argv[2] if len(sys.argv) > 2 else "yolo11n.pt"
EPOCAS = int(sys.argv[3]) if len(sys.argv) > 3 else 60

modelo = YOLO(BASE)
modelo.train(data=str(DATA / "dataset.yaml"), epochs=EPOCAS, imgsz=480, batch=16, device="cpu",
             workers=0, seed=42, deterministic=True, patience=25, fliplr=0.0,
             project=str(DATA / "runs"), name="v0", exist_ok=True, plots=True, verbose=False)

melhor = YOLO(str(DATA / "runs" / "v0" / "weights" / "best.pt"))
m = melhor.val(data=str(DATA / "dataset.yaml"), imgsz=480, device="cpu", workers=0, split="val",
               project=str(DATA / "runs"), name="v0_val", exist_ok=True, verbose=False)
nomes = ["medidor", "placa", "visor"]
res = {"mAP50": round(float(m.box.map50), 3), "mAP50-95": round(float(m.box.map), 3),
       "por_classe_mAP50": {nomes[c]: round(float(m.box.ap50[i]), 3) for i, c in enumerate(m.box.ap_class_index)},
       "precisao": round(float(m.box.mp), 3), "revocacao": round(float(m.box.mr), 3)}

# "tem medidor?": detector acha alguma caixa de medidor com confiança >= 0.25
ok = tot = fp = fn = 0
for img in sorted((DATA / "images" / "val").glob("*.jpg")):
    rot = (DATA / "labels" / "val" / img.with_suffix(".txt").name).read_text(encoding="utf-8").split("\n")
    tem = any(l.startswith("0 ") for l in rot)
    r = melhor.predict(str(img), imgsz=480, conf=0.25, device="cpu", verbose=False)[0]
    achou = any(int(c) == 0 for c in r.boxes.cls.tolist())
    tot += 1; ok += tem == achou; fp += achou and not tem; fn += tem and not achou
res["tem_medidor"] = {"acerto": f"{ok}/{tot}", "falso_positivo": fp, "falso_negativo": fn}
(DATA / "runs" / "resultado_v0.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False))
