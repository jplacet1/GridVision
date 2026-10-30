# -*- coding: utf-8 -*-
"""Variantes de leitura dos recortes (PaddleOCR 3.7).

Uso: python variantes.py <pasta dos recortes> <amostra_100_nitidas.csv> <fotos_excluir.txt>
A  recorte, OCR completo (detecção + leitura), qualquer texto igual (resultado do ler_recortes.py)
B  igual à A, mas junta os dígitos de todos os textos do recorte, na ordem devolvida
C  recorte lido como uma linha só (só o reconhecedor, sem detecção de texto)
"""
import csv, json, re, sys, warnings
from pathlib import Path
import cv2
warnings.filterwarnings("ignore")
from paddleocr import TextRecognition

REC, AMOSTRA = Path(sys.argv[1]), Path(sys.argv[2])
EXCLUIR = set(Path(sys.argv[3]).read_text(encoding="utf-8").split())
ocr_a = json.load(open(REC / "ocr_recortes.json", encoding="utf-8"))
rec = TextRecognition(model_name="en_PP-OCRv5_mobile_rec", enable_mkldnn=False)

def dig(s): return re.sub(r"\D", "", s)

def so_reconhecer(p):
    if not p.exists(): return None
    img = cv2.imread(str(p))
    r = rec.predict(img)[0]
    return [r["rec_text"]]

linhas = list(csv.DictReader(open(AMOSTRA, encoding="utf-8")))
C = {r["arquivo"]: {k: so_reconhecer(REC / k / r["arquivo"].replace(".jpg", ".png")) for k in ("visor", "placa")} for r in linhas}
json.dump(C, open(REC / "ocr_recortes_C.json", "w", encoding="utf-8"), ensure_ascii=False)

def candidatos(v, juntar):
    if v is None: return []
    d = [dig(t) for t in v if dig(t)]
    return d + (["".join(d)] if juntar and len(d) > 1 else [])

def avaliar(fonte, juntar, sub):
    c = dict(fotos=0, leitura_sem_zeros=0, leitura_estrita=0, medidor_igual=0)
    for r in sub:
        o = fonte[r["arquivo"]]; c["fotos"] += 1
        leit = r["Posicao do medidor lida"].strip(); l0 = leit.lstrip("0") or "0"
        tv, tp = candidatos(o["visor"], juntar), candidatos(o["placa"], juntar)
        meds = [dig(m) for m in r["Numero do medidor"].split("/")]
        c["leitura_sem_zeros"] += any(t.lstrip("0") == l0 for t in tv)
        c["leitura_estrita"] += any(t == leit for t in tv)
        c["medidor_igual"] += any(t == m for t in tp for m in meds)
    return c

sub97 = [r for r in linhas if r["arquivo"] not in EXCLUIR]
for nome, fonte, juntar in (("A recorte, OCR completo", ocr_a, False),
                            ("B recorte, junta pedaços", ocr_a, True),
                            ("C recorte, linha única", C, False)):
    print(nome, "| 100:", json.dumps(avaliar(fonte, juntar, linhas)), "| 97:", json.dumps(avaliar(fonte, juntar, sub97)))
