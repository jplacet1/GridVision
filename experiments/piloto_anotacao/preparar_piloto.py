# -*- coding: utf-8 -*-
"""Divisão treino/validação/teste e amostra do piloto de anotação (17/10/2026).

Regras (docs/contexto.md, decisão de 03/10):
- Lotes de maio (20, 21 e 22/05): divisão por medidor, 70/15/15. Fotos sem registro no CSV
  usam o código do nome do arquivo como chave.
- Lote de 03/07: teste temporal. Medidores que aparecem nele não entram no treino de maio
  (vão para teste), para não vazar o mesmo medidor entre treino e teste temporal.
- Piloto: 300 fotos do treino, misturando lotes, nítidas e borradas, e fotos fora do CSV.
  100 por pessoa; 50 delas também recebem um segundo anotador (concordância).

Uso:
    python preparar_piloto.py <zip da base> <pasta de saída fora do Git>

Grava no repositório só listas de arquivos (divisao_v1.csv e piloto_v1.csv).
As fotos do piloto são copiadas para <pasta de saída>/fotos, fora do Git.
"""
import csv, io, random, re, sys, zipfile
from collections import defaultdict
from pathlib import Path
import cv2, numpy as np

ZIP, SAIDA = Path(sys.argv[1]), Path(sys.argv[2])
AQUI = Path(__file__).resolve().parent
SEED = 42
LIMIAR_NITIDEZ = 100.0
ANOTADORES = ["João Pedro", "Alana", "Henrique"]

z = zipfile.ZipFile(ZIP)
fotos = {}                       # arquivo -> caminho no zip
registros = {}                   # arquivo -> número do medidor
for n in z.namelist():
    nome = n.split("/")[-1]
    if nome.lower().endswith(".jpg"):
        fotos[nome] = n
    elif nome.lower().endswith(".csv"):
        for r in csv.DictReader(io.StringIO(z.read(n).decode("utf-8")), delimiter=";"):
            f = r["Foto do medidor"].strip().split("/")[-1]
            if f and f != "NA":
                registros[f] = r["Numero do medidor"].strip()

def lote(f): return f.split("_")[2]
def chave(f): return "med:" + registros[f] if f in registros else "foto:" + re.search(r"_(\d{20})_", f).group(1)

maio = [f for f in fotos if lote(f) != "030726"]
julho = [f for f in fotos if lote(f) == "030726"]
chaves_julho = {chave(f) for f in julho if f in registros}

conjunto = {f: "teste_temporal" for f in julho}
chaves = sorted({chave(f) for f in maio})
random.Random(SEED).shuffle(chaves)
n = len(chaves)
destino = {}
for i, k in enumerate(chaves):
    destino[k] = "treino" if i < 0.70 * n else ("validacao" if i < 0.85 * n else "teste")
vazamento = 0
for f in maio:
    k = chave(f)
    c = destino[k]
    if k in chaves_julho and c == "treino":
        c = "teste"; vazamento += 1
    conjunto[f] = c

with open(AQUI / "divisao_v1.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["arquivo", "lote", "conjunto", "no_csv"])
    for f in sorted(conjunto):
        w.writerow([f, lote(f), conjunto[f], f in registros])

# --- amostra do piloto: só treino ---
treino = sorted(f for f, c in conjunto.items() if c == "treino")
rng = random.Random(SEED)
def nitidez(f):
    img = cv2.imdecode(np.frombuffer(z.read(fotos[f]), np.uint8), cv2.IMREAD_GRAYSCALE)
    return float(cv2.Laplacian(img, cv2.CV_64F).var())

orfas = [f for f in treino if f not in registros]
com_csv = [f for f in treino if f in registros]
rng.shuffle(com_csv)
nitidas, borradas = [], []
for f in com_csv:                       # mede nitidez até completar as cotas
    if len(nitidas) >= 150 and len(borradas) >= 110: break
    (nitidas if nitidez(f) >= LIMIAR_NITIDEZ else borradas).append(f)
amostra = [(f, "nitida") for f in nitidas[:150]] + [(f, "borrada") for f in borradas[:110]] \
        + [(f, "fora_do_csv") for f in rng.sample(orfas, 40)]
rng.shuffle(amostra)

dupla = set(rng.sample(range(len(amostra)), 50))
SAIDA.mkdir(parents=True, exist_ok=True); (SAIDA / "fotos").mkdir(exist_ok=True)
with open(AQUI / "piloto_v1.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["arquivo", "lote", "estrato", "anotador", "segundo_anotador"])
    for i, (f, estrato) in enumerate(amostra):
        a = ANOTADORES[i % 3]
        b = ANOTADORES[(i + 1) % 3] if i in dupla else ""
        w.writerow([f, lote(f), estrato, a, b])
        (SAIDA / "fotos" / f).write_bytes(z.read(fotos[f]))

cont = defaultdict(int)
for c in conjunto.values(): cont[c] += 1
print("divisão:", dict(cont), "| movidos do treino por aparecerem em 03/07:", vazamento)
print("piloto:", len(amostra), "fotos | nítidas", min(150, len(nitidas)), "borradas", min(110, len(borradas)), "fora do CSV 40 | dupla anotação", len(dupla))
