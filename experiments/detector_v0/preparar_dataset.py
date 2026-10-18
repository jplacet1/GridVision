# -*- coding: utf-8 -*-
"""Converte o export do Label Studio (piloto) para o formato YOLO (18/10/2026).

Uso:
    python preparar_dataset.py <piloto_final.json> <pasta das fotos do piloto> <pasta de saída fora do Git>

- Classes: 0 medidor, 1 placa, 2 visor.
- Uma anotação por foto (a mais antiga, quando a foto foi anotada duas vezes).
- Fotos sem caixa entram com arquivo de rótulo vazio (exemplos negativos: "sem medidor").
- Divisão interna do piloto: 80% treino, 20% checagem, estratificada por estrato (nítida,
  borrada, fora do CSV), seed 42. Todas as 300 fotos são do conjunto de treino da divisao_v1;
  a validação e o teste de verdade vêm depois, com fotos dos conjuntos validacao e teste.
"""
import csv, json, random, re, shutil, sys
from collections import defaultdict
from pathlib import Path

LS_JSON, FOTOS, SAIDA = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
AQUI = Path(__file__).resolve().parent
CLASSES = ["medidor", "placa", "visor"]
SEED = 42

estrato = {r["arquivo"]: r["estrato"] for r in csv.DictReader(open(AQUI.parent / "piloto_anotacao" / "piloto_v1.csv", encoding="utf-8"))}

anot = {}
for t in json.load(open(LS_JSON, encoding="utf-8")):
    arq = re.search(r"(PSP_EXTRATLEITIMPL_\d+_\d+_\d{20}_\d{3}\.jpg)", t["file_upload"]).group(1)
    for a in t["annotations"]:
        if a.get("was_cancelled"):
            continue
        if arq not in anot or a["created_at"] < anot[arq]["created_at"]:
            anot[arq] = a

por_estrato = defaultdict(list)
for arq in sorted(anot):
    por_estrato[estrato[arq]].append(arq)
conjunto = {}
rng = random.Random(SEED)
for e, fs in por_estrato.items():
    rng.shuffle(fs)
    corte = round(0.8 * len(fs))
    for i, f in enumerate(fs):
        conjunto[f] = "train" if i < corte else "val"

for parte in ("train", "val"):
    (SAIDA / "images" / parte).mkdir(parents=True, exist_ok=True)
    (SAIDA / "labels" / parte).mkdir(parents=True, exist_ok=True)

caixas = defaultdict(int)
for arq, a in anot.items():
    parte = conjunto[arq]
    linhas = []
    for r in a["result"]:
        if r["type"] != "rectanglelabels":
            continue
        v = r["value"]
        x, y = max(0.0, v["x"]), max(0.0, v["y"])
        w = min(100.0, v["x"] + v["width"]) - x
        h = min(100.0, v["y"] + v["height"]) - y
        if w <= 0 or h <= 0:
            continue
        c = CLASSES.index(v["rectanglelabels"][0])
        linhas.append(f"{c} {(x + w / 2) / 100:.6f} {(y + h / 2) / 100:.6f} {w / 100:.6f} {h / 100:.6f}")
        caixas[(parte, CLASSES[c])] += 1
    shutil.copy(FOTOS / arq, SAIDA / "images" / parte / arq)
    (SAIDA / "labels" / parte / arq.replace(".jpg", ".txt")).write_text("\n".join(linhas), encoding="utf-8")

(SAIDA / "dataset.yaml").write_text(
    f"path: {SAIDA.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n"
    + "".join(f"  {i}: {n}\n" for i, n in enumerate(CLASSES)), encoding="utf-8")

with open(AQUI / "divisao_interna_piloto.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["arquivo", "parte"])
    for arq in sorted(conjunto):
        w.writerow([arq, conjunto[arq]])

n = defaultdict(int)
for p in conjunto.values():
    n[p] += 1
print("fotos:", dict(n), "| caixas:", dict(caixas))
