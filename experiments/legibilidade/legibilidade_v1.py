# -*- coding: utf-8 -*-
"""Classificador de legibilidade v1: sinais do OCR somados aos do v0 (06/11/2026).

Motivo: no ensaio de 06/11, fotos praticamente impossíveis de ler continuavam pendentes porque o v0 (só
confiança do detector e qualidade do recorte) dava mais de 50% de chance de legível. O OCR sabe mais: se algum
passe achou dígitos no visor, quantos, com que confiança e se os dois motores concordam.

Gabarito ("a leitura é legível?"):
- validação (100 fotos anotadas à mão, avaliacao.json): leitura_legivel;
- lote_demo2 e lote_demo3: decisão do analista no histórico do app (Ilegível = não; Corrigido/Confirmado = sim).
Treino e escolha do limiar: validação + lote_demo2, com validação cruzada. Prova cega: lote_demo3. O conjunto de
teste não é usado.

Uso (ambiente do app, a partir da raiz do repositório):
    python experiments/legibilidade/legibilidade_v1.py <gridvision_dados>

Grava src/gridvision/legibilidade_v1.json (coeficientes, sem dado do cliente) e imprime a curva
negadas x legíveis negadas por limiar. Sinais por foto ficam em <gridvision_dados>/legibilidade_v1_sinais.json.
"""
import json, math, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src")); sys.path.insert(0, str(RAIZ / "app"))
from gridvision import extracao as ex

LIMIAR = 0.40   # escolhido pelo João Pedro em 06/11/2026 (lote_demo3: 18 para 13 pendentes, nenhuma legível negada)
SINAIS_OCR = ["ocr_passes_digitos", "ocr_max_digitos", "ocr_max_conf", "ocr_concordam", "ocr_placa_digitos"]


sinais_ocr = ex.sinais_ocr   # a mesma função do app


def gabarito(dados):
    """{arquivo: (caminho, legível?, origem)}."""
    import csv
    import pipeline as pl
    saida = {}
    conj = {r["arquivo"]: r["conjunto"] for r in
            csv.DictReader(open(RAIZ / "experiments" / "avaliacao_detector" / "avaliacao_v1.csv", encoding="utf-8"))}
    caminhos = {p.name: p for p in (dados / "avaliacao" / "fotos").rglob("*.jpg")}
    for t in json.load(open(dados / "avaliacao" / "avaliacao.json", encoding="utf-8")):
        f = t["data"]["image"].rsplit("/", 1)[-1].split("-", 1)[-1]
        if conj.get(f) != "validacao":
            continue
        a = [x for x in t["annotations"] if not x.get("was_cancelled")][-1]
        resp = {r["from_name"]: r["value"]["choices"][0] for r in a["result"] if r["type"] == "choices"}
        if resp.get("tem_medidor") == "sim":
            saida[f] = (caminhos[f], resp["leitura_legivel"] == "sim", "validacao")
    hist = {r.arquivo: r.decisao for r in pl.carregar_historico()}
    for lote in ("lote_demo2", "lote_demo3"):
        for p in (dados / lote / "fotos").glob("*.jpg"):
            dec = hist.get(p.name)
            if dec in ("Ilegível", "Corrigido", "Confirmado"):
                saida[p.name] = (p, dec != "Ilegível", lote)
    return saida


def extrair_sinais(dados, gab):
    import cv2
    arq = dados / "legibilidade_v1_sinais.json"
    cache = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}
    ex._carregar()
    for f, (caminho, _, _) in gab.items():
        if f in cache:
            continue
        img = cv2.imread(str(caminho))
        melhor = ex.detectar(img)
        s = ex.sinais_legibilidade(img, melhor)
        visor = melhor.get("visor", (None, 0))[0]; placa = melhor.get("placa", (None, 0))[0]
        s.update(sinais_ocr(ex._passes(img, visor, placa), visor, placa))
        cache[f] = s
    arq.write_text(json.dumps(cache), encoding="utf-8")
    return cache


def matriz(sinais, nomes, log):
    import numpy as np
    X = np.array([[math.log1p(s[k]) if k in log else s[k] for k in nomes] for s in sinais], dtype=float)
    return X


def main():
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.metrics import roc_auc_score
    dados = Path(sys.argv[1])
    gab = gabarito(dados)
    sinais = extrair_sinais(dados, gab)
    v0 = json.load(open(RAIZ / "src" / "gridvision" / "legibilidade_v0.json", encoding="utf-8"))
    nomes = list(v0["sinais"]) + SINAIS_OCR
    log = set(v0["log"]) | {"ocr_max_digitos", "ocr_placa_digitos"}
    treino = [f for f in gab if gab[f][2] != "lote_demo3"]
    prova = [f for f in gab if gab[f][2] == "lote_demo3"]
    Xt = matriz([sinais[f] for f in treino], nomes, log); yt = np.array([gab[f][1] for f in treino])
    Xp = matriz([sinais[f] for f in prova], nomes, log); yp = np.array([gab[f][1] for f in prova])
    media, desvio = Xt.mean(0), Xt.std(0) + 1e-9
    modelo = LogisticRegression(C=0.5, max_iter=2000)
    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    p_cv = cross_val_predict(modelo, (Xt - media) / desvio, yt, cv=cv, method="predict_proba")[:, 1]
    p_v0 = np.array([ex.prob_legivel({k: sinais[f][k] for k in v0["sinais"]}) for f in treino])
    print(f"treino: {len(treino)} fotos ({int(yt.sum())} legíveis); prova cega lote_demo3: {len(prova)} ({int(yp.sum())} legíveis)")
    print(f"AUC validação cruzada: v1 {roc_auc_score(yt, p_cv):.3f}  |  v0 nas mesmas fotos {roc_auc_score(yt, p_v0):.3f}")
    modelo.fit((Xt - media) / desvio, yt)
    p_prova = modelo.predict_proba((Xp - media) / desvio)[:, 1]
    print(f"AUC prova cega: v1 {roc_auc_score(yp, p_prova):.3f}")
    print("\nlimiar | validação cruzada: negadas / legíveis entre elas (de ilegíveis) | prova cega: negadas / legíveis")
    n_il, n_il_p = int((~yt).sum()), int((~yp).sum())
    for t in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
        neg, negp = p_cv < t, p_prova < t
        print(f"  {t:.2f} | {neg.sum():3} / {int(yt[neg].sum()):2}  ({int((~yt[neg]).sum())} de {n_il}) | "
              f"{negp.sum():3} / {int(yp[negp].sum()):2}  ({int((~yp[negp]).sum())} de {n_il_p})")
    coef = {"modelo": "logistica", "versao": "v1", "sinais": nomes, "log": sorted(log), "media": media.tolist(),
            "desvio": desvio.tolist(), "coef": modelo.coef_[0].tolist(), "intercepto": float(modelo.intercept_[0]),
            "limiar_ilegivel": LIMIAR}
    (RAIZ / "src" / "gridvision" / "legibilidade_v1.json").write_text(json.dumps(coef, indent=1), encoding="utf-8")
    print("\ncoeficientes:", {k: round(c, 2) for k, c in zip(nomes, modelo.coef_[0])})


if __name__ == "__main__":
    main()
