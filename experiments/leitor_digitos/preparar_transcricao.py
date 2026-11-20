# -*- coding: utf-8 -*-
"""Prepara a transcrição manual do visor (rótulos limpos para o leitor), 18/10/2026.

Uso (ambiente do app): python preparar_transcricao.py <pasta leitor_digitos> <pasta de saída fora do Git>

- Sorteia 400 recortes de treino e 100 de validação (o teste fica de fora), com chance de legível >= 0,4.
- Amplia cada recorte 3x e salva em <saída>/fotos/parteN (100 por parte, limite do Label Studio).
- Lê cada recorte com o PaddleOCR (ampliado 2x) e grava <saída>/predicoes.json com o texto lido e as
  caixas sugeridas de função e leitura, para pré-preencher a tarefa: o anotador só corrige.
- Grava transcricao_v1.csv (só nomes de arquivo e conjunto) no repositório.
"""
import csv, json, random, sys
from pathlib import Path
import cv2

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from gridvision import extracao as ex

P, SAIDA = Path(sys.argv[1]), Path(sys.argv[2])
rs = [r for r in csv.DictReader(open(P / "recortes.csv", encoding="utf-8")) if float(r["prob_legivel"]) >= 0.4]
rng = random.Random(42)
sel = []
for conj, n in (("treino", 400), ("validacao", 100)):
    c = [r for r in rs if r["conjunto"] == conj]
    sel += rng.sample(c, n)



def caixas(toks, h, w):
    """Sugere as caixas de função e leitura a partir dos textos do OCR (em % do recorte, como o Label Studio).
    A função fica à esquerda da leitura e tem até 2 dígitos; a leitura é o texto mais longo do resto."""
    def pct(poly):
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        return [100 * min(xs) / w, 100 * min(ys) / h, 100 * (max(xs) - min(xs)) / w, 100 * (max(ys) - min(ys)) / h]
    if not toks:
        return []
    out = []
    if len(toks) >= 2 and len(toks[0][1]) <= 2:
        out.append(["função", *pct(toks[0][2])])
        toks = toks[1:]
    out.append(["leitura", *pct(max(toks, key=lambda t: len(t[1]))[2])])
    return out


ex._carregar()
pred = {}
for i, r in enumerate(sel):
    rec = cv2.imread(str(P / "recortes" / r["conjunto"] / r["arquivo"].replace(".jpg", ".png")))
    nome = r["arquivo"].replace(".jpg", ".png")
    destino = SAIDA / "fotos" / f"parte{i // 100 + 1}"
    destino.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destino / nome), cv2.resize(rec, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
    rec2 = cv2.resize(rec, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    o = ex._ocr.predict(rec2)[0]
    toks = sorted((min(p[0] for p in poly), ex._digitos(t), poly) for t, poly in zip(o["rec_texts"], o["rec_polys"])
                  if ex._digitos(t))
    pred[nome] = {"texto": " ".join(d for _, d, _ in toks), "caixas": caixas(toks, *rec2.shape[:2])}
    if (i + 1) % 100 == 0:
        print(f"{i + 1}/{len(sel)}", flush=True)
json.dump(pred, open(SAIDA / "predicoes.json", "w", encoding="utf-8"))
with open(Path(__file__).with_name("transcricao_v1.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["arquivo", "conjunto"])
    for r in sel:
        w.writerow([r["arquivo"], r["conjunto"]])
print("recortes:", len(sel), "| com texto pré-preenchido:", sum(1 for v in pred.values() if v["texto"]),
      "| com caixa de função sugerida:", sum(1 for v in pred.values() if any(c[0] == "função" for c in v["caixas"])))
