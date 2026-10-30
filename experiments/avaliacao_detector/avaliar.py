# -*- coding: utf-8 -*-
"""Avalia o detector v0 contra as caixas corrigidas à mão (validação + teste).

Uso: python avaliar.py <avaliacao.json exportado> <predicoes.json>
- Casa previsão e caixa corrigida da mesma classe por IoU (guloso, por confiança).
- AP50 por classe (área sob a curva precisão x revocação, interpolada), precisão e revocação
  com confiança >= 0,25 e IoU >= 0,5, e "tem medidor?".
- Conta quantas caixas foram aceitas sem mudança, ajustadas, apagadas ou desenhadas do zero
  (a anotação partiu das previsões, o que puxa o resultado para cima: viés de ancoragem).
- Legibilidade numa amostra aleatória de validação + teste (proporção real da base).
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
anot = json.load(open(sys.argv[1], encoding="utf-8"))
pred = json.load(open(sys.argv[2], encoding="utf-8"))
conj = {r["arquivo"]: r["conjunto"] for r in csv.DictReader(open(AQUI / "avaliacao_v1.csv", encoding="utf-8"))}
CL = ["medidor", "placa", "visor"]

def caixa(v): return (v["x"], v["y"], v["x"] + v["width"], v["y"] + v["height"])
def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy; u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u else 0

gt, pr, resp = {}, {}, {}
for t in anot:
    f = re.search(r"(PSP_EXTRATLEITIMPL_\d+_\d+_\d{20}_\d{3}\.jpg)", t["data"]["image"]).group(1)
    a = [x for x in t["annotations"] if not x.get("was_cancelled")][-1]
    gt[f] = [(r["value"]["rectanglelabels"][0], caixa(r["value"])) for r in a["result"] if r["type"] == "rectanglelabels"]
    resp[f] = {r["from_name"]: r["value"]["choices"][0] for r in a["result"] if r["type"] == "choices"}
    pr[f] = [(r["value"]["rectanglelabels"][0], caixa(r["value"]), r["score"]) for r in pred[f]]

def ap50(c, fotos):
    dets, ngt = [], 0
    for f in fotos:
        g = [b for l, b in gt[f] if l == c]; ngt += len(g); usado = [False] * len(g)
        for l, b, s in sorted([p for p in pr[f] if p[0] == c], key=lambda p: -p[2]):
            ious = [iou(b, x) for x in g]; j = max(range(len(g)), key=lambda k: ious[k]) if g else -1
            ok = j >= 0 and ious[j] >= 0.5 and not usado[j]
            if ok: usado[j] = True
            dets.append((s, ok))
    dets.sort(key=lambda d: -d[0]); tp = fp = 0; pts = []
    for s, ok in dets:
        tp += ok; fp += not ok; pts.append((tp / ngt if ngt else 0, tp / (tp + fp)))
    ap = 0;
    for k in range(101):
        r = k / 100; ps = [p for rr, p in pts if rr >= r]; ap += max(ps) if ps else 0
    tp25 = sum(ok for s, ok in dets if s >= 0.25); n25 = sum(1 for s, ok in dets if s >= 0.25)
    return dict(ap50=round(ap / 101, 3), precisao=round(tp25 / n25, 3) if n25 else None,
                revocacao=round(tp25 / ngt, 3) if ngt else None, caixas_reais=ngt)

for nome, fotos in (("todas", list(gt)), ("validacao", [f for f in gt if conj[f] == "validacao"]), ("teste", [f for f in gt if conj[f] == "teste"])):
    res = {c: ap50(c, fotos) for c in CL}
    print(nome, len(fotos), "fotos | mAP50", round(sum(r["ap50"] for r in res.values()) / 3, 3), json.dumps(res, ensure_ascii=False))

# o que foi mudado nas caixas
mud = Counter()
for f in gt:
    usadas = set()
    for l, b, s in pr[f]:
        cands = [(iou(b, x), k) for k, (ll, x) in enumerate(gt[f]) if ll == l and k not in usadas]
        best = max(cands) if cands else (0, None)
        if best[0] >= 0.98: mud[(l, "aceita sem mudança")] += 1; usadas.add(best[1])
        elif best[0] >= 0.3: mud[(l, "ajustada")] += 1; usadas.add(best[1])
        else: mud[(l, "apagada")] += 1
    for k, (l, x) in enumerate(gt[f]):
        if k not in usadas: mud[(l, "desenhada do zero")] += 1
for c in CL: print(c, {k[1]: v for k, v in mud.items() if k[0] == c})

# tem medidor?
m = Counter()
for f in gt:
    real = any(l == "medidor" for l, b in gt[f]); prev = any(l == "medidor" and s >= 0.25 for l, b, s in pr[f])
    m["certo" if real == prev else ("falso positivo" if prev else "falso negativo")] += 1
print("tem medidor?", dict(m))

# legibilidade (amostra aleatória, proporção real)
n = len(resp); L = Counter()
for r in resp.values():
    L["leitura legível"] += r["leitura_legivel"] == "sim"; L["número legível"] += r["numero_legivel"] == "sim"
    L["os dois legíveis"] += r["leitura_legivel"] == "sim" and r["numero_legivel"] == "sim"
    L["sem medidor"] += r["tem_medidor"] == "não"
print("legibilidade em", n, "fotos:", {k: f"{v} ({100 * v / n:.0f}%)" for k, v in L.items()})
