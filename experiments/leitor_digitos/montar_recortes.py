# -*- coding: utf-8 -*-
"""Conjunto de recortes do visor para o leitor de dígitos (CNN), 18/10/2026.

Uso (ambiente do app):
    python montar_recortes.py <zip da base> <pasta de saída fora do Git>

Para cada foto de treino, validação e teste da divisao_v1 (o teste temporal fica intocado):
- roda o detector v0 e recorta a melhor caixa de visor (margem de 8%);
- calcula a chance de a leitura ser legível (classificador de legibilidade v0);
- guarda o recorte em <saída>/recortes/<conjunto>/<arquivo>.png e uma linha em <saída>/recortes.csv
  com a leitura do CSV (rótulo fraco: o que o leiturista informou), a chance de legível e a
  confiança do visor.
Fotos sem visor detectado ou sem registro no CSV ficam de fora. Nada vai para o Git.
"""
import csv, io, sys, time, zipfile
from pathlib import Path
import cv2, numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from gridvision import extracao as ex

ZIP, SAIDA = Path(sys.argv[1]), Path(sys.argv[2])
MARGEM = 0.08
CONJUNTOS = ("treino", "validacao", "teste")

z = zipfile.ZipFile(ZIP)
caminho = {n.split("/")[-1]: n for n in z.namelist() if n.lower().endswith(".jpg")}
leitura = {}
for n in z.namelist():
    if n.lower().endswith(".csv"):
        for r in csv.DictReader(io.StringIO(z.read(n).decode("utf-8")), delimiter=";"):
            f = r["Foto do medidor"].strip().split("/")[-1]
            if f and f != "NA":
                leitura[f] = r["Posicao do medidor lida"].strip()
div = [(r["arquivo"], r["conjunto"]) for r in csv.DictReader(
    open(RAIZ / "experiments/piloto_anotacao/divisao_v1.csv", encoding="utf-8")) if r["conjunto"] in CONJUNTOS]

for c in CONJUNTOS:
    (SAIDA / "recortes" / c).mkdir(parents=True, exist_ok=True)
saida_csv = SAIDA / "recortes.csv"
feitos = set()
if saida_csv.exists():  # retoma de onde parou
    feitos = {r["arquivo"] for r in csv.DictReader(open(saida_csv, encoding="utf-8"))}
fh = open(saida_csv, "a", newline="", encoding="utf-8")
w = csv.writer(fh)
if not feitos:
    w.writerow(["arquivo", "conjunto", "leitura", "prob_legivel", "conf_visor", "altura", "largura"])

t0, n, sem_visor = time.time(), 0, 0
for i, (f, conj) in enumerate(div, 1):
    if f in feitos or f not in leitura:
        continue
    img = cv2.imdecode(np.frombuffer(z.read(caminho[f]), np.uint8), cv2.IMREAD_COLOR)
    melhor = ex.detectar(img)
    if "visor" not in melhor:
        sem_visor += 1
        continue
    p = ex.prob_legivel(ex.sinais_legibilidade(img, melhor))
    x0, y0, x1, y1 = melhor["visor"][0]
    mx, my = MARGEM * (x1 - x0), MARGEM * (y1 - y0)
    h, wd = img.shape[:2]
    X0, Y0, X1, Y1 = int(max(0, x0 - mx)), int(max(0, y0 - my)), int(min(wd, x1 + mx)), int(min(h, y1 + my))
    rec = img[Y0:Y1, X0:X1]
    cv2.imwrite(str(SAIDA / "recortes" / conj / f.replace(".jpg", ".png")), rec)
    w.writerow([f, conj, leitura[f], f"{p:.3f}", f"{melhor['visor'][1]:.3f}", rec.shape[0], rec.shape[1]])
    n += 1
    if n % 500 == 0:
        fh.flush()
        print(f"{i}/{len(div)} fotos vistas, {n} recortes, {sem_visor} sem visor, {time.time() - t0:.0f}s", flush=True)
fh.close()
print(f"fim: {n} recortes novos, {sem_visor} sem visor, {time.time() - t0:.0f}s")
