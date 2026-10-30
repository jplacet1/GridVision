# -*- coding: utf-8 -*-
"""Diagnóstico dos rótulos do leitor: a leitura do CSV aparece no recorte do visor? (18/10/2026)

Uso (ambiente do app): python diagnostico_rotulos.py <pasta leitor_digitos> [n]
Passa o PaddleOCR (recorte ampliado 2x) em n recortes de treino sorteados (os mesmos que o leitor usa:
chance de legível >= 0,6) e conta: o OCR lê exatamente a leitura do CSV; lê com confiança OUTRO
número de tamanho parecido (sinal de rótulo que não bate com a imagem); não lê dígitos; outros.
Só imprime contagens.
"""
import csv, random, sys, collections
from pathlib import Path
import cv2

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from gridvision import extracao as ex

P, N = Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 200
ex._carregar()
rs = [r for r in csv.DictReader(open(P / "recortes.csv", encoding="utf-8"))
      if r["conjunto"] == "treino" and float(r["prob_legivel"]) >= 0.6 and r["leitura"].lstrip("0")]
random.Random(1).shuffle(rs)
c, dif = collections.Counter(), collections.Counter()
for r in rs[:N]:
    img = cv2.imread(str(P / "recortes" / "treino" / r["arquivo"].replace(".jpg", ".png")))
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    o = ex._ocr.predict(img)[0]
    toks = [(ex._digitos(t), s) for t, s in zip(o["rec_texts"], o["rec_scores"]) if ex._digitos(t)]
    cands = [d for d, _ in toks] + (["".join(d for d, _ in toks)] if len(toks) > 1 else [])
    cands += [d[2:] for d in list(cands) if len(d) >= 7]
    alvo = r["leitura"].lstrip("0")
    fortes = [(d.lstrip("0"), s) for d, s in toks if len(d.lstrip("0")) >= 3 and s >= 0.9]
    if any(d.lstrip("0") == alvo for d in cands):
        c["OCR lê exatamente a leitura do CSV"] += 1
    elif any(abs(len(d) - len(alvo)) <= 1 for d, _ in fortes):
        c["OCR lê com confiança OUTRO número de tamanho parecido"] += 1
        d = max((x for x in fortes if abs(len(x[0]) - len(alvo)) <= 1), key=lambda x: x[1])[0]
        dif[sum(a != b for a, b in zip(d.zfill(6), alvo.zfill(6)))] += 1
    elif not toks:
        c["OCR não lê dígitos"] += 1
    else:
        c["OCR lê algo, mas fraco ou de outro tamanho"] += 1
for k, v in c.most_common():
    print(f"{v:3d}  {k}")
print('nos "outro número": quantos dígitos diferem do CSV (de 6):', dict(sorted(dif.items())))
