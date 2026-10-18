# -*- coding: utf-8 -*-
"""Experimento 1 (17/10): pré-processamento e leitura em duas etapas, nas 100 fotos do baseline.

V0  foto inteira, como no baseline (controle, PaddleOCR 2.10)
V1  foto ampliada 2x + CLAHE
V2  duas etapas: detecta caixas de texto na foto inteira, recorta cada caixa com margem,
    amplia 3x e reconhece só o recorte
Métricas iguais às do baseline. Só imprime agregados.
"""
import csv, json, re, sys, time, warnings
from pathlib import Path
import cv2, numpy as np
warnings.filterwarnings("ignore")
import logging; logging.disable(logging.WARNING)
from paddleocr import PaddleOCR

BASE = Path(__file__).resolve().parent / "baseline_ocr"
FOTOS = BASE / "fotos"
ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)

def dig(s): return re.sub(r"\D", "", s)

def lev(a, b):
    if len(a) < len(b): a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def textos_full(img):
    r = ocr.ocr(img, cls=False)[0] or []
    return [t[1][0] for t in r], [t[0] for t in r]

def v0(img): return textos_full(img)[0]

def v1(img):
    big = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    lab = cv2.cvtColor(big, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    return textos_full(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR))[0]

def v2(img):
    caixas = ocr.ocr(img, rec=False, cls=False)[0] or []
    out = []
    h, w = img.shape[:2]
    for c in caixas:
        p = np.array(c); x0, y0 = p.min(0); x1, y1 = p.max(0)
        mx, my = 0.15 * (x1 - x0) + 4, 0.3 * (y1 - y0) + 4
        x0, y0 = int(max(0, x0 - mx)), int(max(0, y0 - my))
        x1, y1 = int(min(w, x1 + mx)), int(min(h, y1 + my))
        if x1 - x0 < 8 or y1 - y0 < 8: continue
        crop = cv2.resize(img[y0:y1, x0:x1], None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        r = ocr.ocr(crop, det=False, cls=False)[0] or []
        out += [t[0] for t in r]
    return out

def avaliar(textos, leit, medidor):
    toks = [dig(t) for t in textos]; junto = "".join(toks)
    meds = [dig(m) for m in medidor.split("/")]
    l0 = leit.lstrip("0") or "0"
    sem0 = any(t and t.lstrip("0") == l0 for t in toks)
    return dict(
        sem_texto=len(textos) == 0,
        leitura_estrita=any(t == leit for t in toks),
        leitura_sem_zeros=sem0,
        leitura_1_digito=(not sem0) and any(lev(t.lstrip("0"), l0) == 1 for t in toks if len(t) >= 3 and abs(len(t.lstrip("0")) - len(l0)) <= 1),
        medidor_igual=any(t == m for t in toks for m in meds),
        medidor_contido=any(m in junto for m in meds if len(m) >= 6),
    )

linhas = list(csv.DictReader(open(BASE / "amostra_100_nitidas.csv", encoding="utf-8")))
variantes = {"V0 foto inteira": v0, "V1 ampliada 2x + CLAHE": v1, "V2 detecta, recorta e le": v2}
res = {k: [] for k in variantes}
for k, fn in variantes.items():
    t0 = time.time()
    for r in linhas:
        img = cv2.imread(str(FOTOS / r["arquivo"]))
        res[k].append(avaliar(fn(img), r["Posicao do medidor lida"].strip(), r["Numero do medidor"]))
    print(f"{k}: {time.time() - t0:.0f} s", flush=True)

chaves = list(res[next(iter(res))][0])
print("\n" + "metrica".ljust(20) + "".join(k[:24].rjust(26) for k in variantes))
for c in chaves:
    print(c.ljust(20) + "".join(str(sum(x[c] for x in res[k])).rjust(26) for k in variantes))
json.dump({k: {c: sum(x[c] for x in v) for c in chaves} for k, v in res.items()},
          open(Path(__file__).with_name("exp1_agregado.json"), "w"), indent=1)
