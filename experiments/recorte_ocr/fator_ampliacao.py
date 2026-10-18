# -*- coding: utf-8 -*-
"""Recorte + ampliação com fator fixo (2x, 3x, 4x) + PaddleOCR 3.7.

Uso: python fator_ampliacao.py <pasta dos recortes> <amostra_100_nitidas.csv> <fotos_excluir.txt>
Equivale a "ampliar a foto e depois recortar": a mesma interpolação bicúbica, aplicada só ao
recorte. No ler_recortes.py o recorte ia só até 96 px de altura (≈ 1,4x no visor típico);
na foto inteira ampliada 2x o visor ficava com o dobro do tamanho.
"""
import csv, json, re, sys, warnings
from pathlib import Path
import cv2
warnings.filterwarnings("ignore")
from paddleocr import PaddleOCR

REC, AMOSTRA = Path(sys.argv[1]), Path(sys.argv[2])
EXCLUIR = set(Path(sys.argv[3]).read_text(encoding="utf-8").split())
motor = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                  use_textline_orientation=False, lang="en", enable_mkldnn=False)
TMP = REC / "_tmp"; TMP.mkdir(exist_ok=True)
linhas = list(csv.DictReader(open(AMOSTRA, encoding="utf-8")))

def dig(s): return re.sub(r"\D", "", s)

def ler(p, fator):
    if not p.exists(): return None
    img = cv2.resize(cv2.imread(str(p)), None, fx=fator, fy=fator, interpolation=cv2.INTER_CUBIC)
    q = TMP / p.name; cv2.imwrite(str(q), img)
    try: return list(motor.predict(str(q))[0]["rec_texts"])
    finally: q.unlink()

def cand(v):
    if v is None: return []
    d = [dig(t) for t in v if dig(t)]
    return d + (["".join(d)] if len(d) > 1 else [])

for fator in (2, 3, 4):
    saida = {r["arquivo"]: {k: ler(REC / k / r["arquivo"].replace(".jpg", ".png"), fator) for k in ("visor", "placa")} for r in linhas}
    json.dump(saida, open(REC / f"ocr_recortes_{fator}x.json", "w", encoding="utf-8"), ensure_ascii=False)
    for nome, sub in (("100", linhas), ("97", [r for r in linhas if r["arquivo"] not in EXCLUIR])):
        c = dict(leitura_sem_zeros=0, leitura_estrita=0, medidor_igual=0)
        for r in sub:
            o = saida[r["arquivo"]]; leit = r["Posicao do medidor lida"].strip(); l0 = leit.lstrip("0") or "0"
            tv, tp = cand(o["visor"]), cand(o["placa"])
            meds = [dig(m) for m in r["Numero do medidor"].split("/")]
            c["leitura_sem_zeros"] += any(t.lstrip("0") == l0 for t in tv)
            c["leitura_estrita"] += any(t == leit for t in tv)
            c["medidor_igual"] += any(t == m for t in tp for m in meds)
        print(f"{fator}x | {nome} fotos:", json.dumps(c), flush=True)
