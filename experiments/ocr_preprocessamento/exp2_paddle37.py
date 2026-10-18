# -*- coding: utf-8 -*-
"""Experimento 2 (17/10): pré-processamento com PaddleOCR 3.7 (mesma config do baseline).

Uso: python exp2_37.py V1   (ampliada 2x + CLAHE)
     python exp2_37.py V1b  (só ampliada 2x)
     python exp2_37.py V0   (avalia a saída bruta do baseline, sem rodar OCR)
Grava exp2_<variante>.json com os textos e imprime só agregados.
"""
import csv, json, re, sys, time, warnings
from pathlib import Path
import cv2
warnings.filterwarnings("ignore")

AQUI = Path(__file__).resolve().parent
BASE = AQUI / "baseline_ocr"
FOTOS = BASE / "fotos"
TMP = AQUI / "tmp_img"; TMP.mkdir(exist_ok=True)
var = sys.argv[1]

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

def prep(img):
    big = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    if var == "V1b": return big
    lab = cv2.cvtColor(big, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

linhas = list(csv.DictReader(open(BASE / "amostra_100_nitidas.csv", encoding="utf-8")))
if var == "V0":
    raw = json.load(open(AQUI.parent / "baseline" / "baseline_ocr" / "paddleocr_saida_bruta.json", encoding="utf-8")) \
        if (AQUI.parent / "baseline" / "baseline_ocr" / "paddleocr_saida_bruta.json").exists() else None
    if raw is None:
        import zipfile
        raw = json.loads(zipfile.ZipFile(r"C:\Users\joaop\Downloads\baseline_ocr.zip").read("baseline_ocr/paddleocr_saida_bruta.json"))
    saida = {f: v.get("texts", []) for f, v in raw.items()}
else:
    from paddleocr import PaddleOCR
    motor = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                      use_textline_orientation=False, lang="en", enable_mkldnn=False)
    saida = {}; t0 = time.time()
    for i, r in enumerate(linhas, 1):
        f = r["arquivo"]; p = TMP / f"{var}_{f}"
        cv2.imwrite(str(p), prep(cv2.imread(str(FOTOS / f))))
        try:
            saida[f] = list(motor.predict(str(p))[0]["rec_texts"])
        except Exception as e:
            saida[f] = []; print("erro", i, type(e).__name__, flush=True)
        p.unlink()
        if i % 10 == 0: print(f"{var} {i}/100 {time.time() - t0:.0f}s", flush=True)
    json.dump(saida, open(AQUI / f"exp2_{var}.json", "w", encoding="utf-8"), ensure_ascii=False)

res = [avaliar(saida.get(r["arquivo"], []), r["Posicao do medidor lida"].strip(), r["Numero do medidor"]) for r in linhas]
print(var, json.dumps({k: sum(x[k] for x in res) for k in res[0]}))
