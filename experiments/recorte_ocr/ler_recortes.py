# -*- coding: utf-8 -*-
"""Passo 2 (ambiente com PaddleOCR 3.7): lê os recortes de visor e placa e avalia.

Uso: python ler_recortes.py <pasta dos recortes> <amostra_100_nitidas.csv> <fotos_excluir.txt opcional>
Cada recorte é ampliado até ter pelo menos 96 px de altura (no máximo 4x) e passa pelo
PaddleOCR 3.7 com a mesma configuração do baseline. A leitura é procurada só nos textos do
recorte do visor, e o número do medidor só nos do recorte da placa. Métricas iguais às do baseline.
"""
import csv, json, re, sys, time, warnings
from pathlib import Path
import cv2
warnings.filterwarnings("ignore")
from paddleocr import PaddleOCR

REC, AMOSTRA = Path(sys.argv[1]), Path(sys.argv[2])
EXCLUIR = set(Path(sys.argv[3]).read_text(encoding="utf-8").split()) if len(sys.argv) > 3 else set()
motor = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                  use_textline_orientation=False, lang="en", enable_mkldnn=False)
TMP = REC / "_tmp"; TMP.mkdir(exist_ok=True)

def ler(p):
    if not p.exists(): return None
    img = cv2.imread(str(p)); h = img.shape[0]
    f = min(4.0, max(1.0, 96 / h))
    if f > 1: img = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    q = TMP / p.name; cv2.imwrite(str(q), img)
    try: return list(motor.predict(str(q))[0]["rec_texts"])
    finally: q.unlink()

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

linhas = list(csv.DictReader(open(AMOSTRA, encoding="utf-8")))
saida, t0 = {}, time.time()
for i, r in enumerate(linhas, 1):
    nome = r["arquivo"].replace(".jpg", ".png")
    saida[r["arquivo"]] = {"visor": ler(REC / "visor" / nome), "placa": ler(REC / "placa" / nome)}
    if i % 20 == 0: print(f"{i}/100 {time.time() - t0:.0f}s", flush=True)
json.dump(saida, open(REC / "ocr_recortes.json", "w", encoding="utf-8"), ensure_ascii=False)

def avaliar(subconj):
    c = dict(fotos=0, visor_achado=0, placa_achada=0, leitura_sem_zeros=0, leitura_estrita=0,
             leitura_1_digito=0, medidor_igual=0, medidor_contido=0)
    for r in subconj:
        o = saida[r["arquivo"]]; c["fotos"] += 1
        leit = r["Posicao do medidor lida"].strip(); l0 = leit.lstrip("0") or "0"
        tv = [dig(t) for t in (o["visor"] or [])]
        tp = [dig(t) for t in (o["placa"] or [])]
        meds = [dig(m) for m in r["Numero do medidor"].split("/")]
        c["visor_achado"] += o["visor"] is not None
        c["placa_achada"] += o["placa"] is not None
        sem0 = any(t and t.lstrip("0") == l0 for t in tv)
        c["leitura_sem_zeros"] += sem0
        c["leitura_estrita"] += any(t == leit for t in tv)
        c["leitura_1_digito"] += (not sem0) and any(lev(t.lstrip("0"), l0) == 1 for t in tv if len(t) >= 3 and abs(len(t.lstrip("0")) - len(l0)) <= 1)
        c["medidor_igual"] += any(t == m for t in tp for m in meds)
        c["medidor_contido"] += any(m in "".join(tp) for m in meds if len(m) >= 6)
    return c

print("todas:", json.dumps(avaliar(linhas)))
if EXCLUIR:
    print("sem as fotos do treino do detector:", json.dumps(avaliar([r for r in linhas if r["arquivo"] not in EXCLUIR])))
