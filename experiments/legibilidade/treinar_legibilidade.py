# -*- coding: utf-8 -*-
"""Classificador de legibilidade da leitura (opção A, 18/10/2026).

Uso (ambiente com ultralytics, opencv e scikit-learn):
    python treinar_legibilidade.py <pasta gridvision_dados>

Alvo: a leitura do visor é legível? (resposta "leitura_legivel" das anotações do piloto e da avaliação).
Sinais: os de `sinais_legibilidade` em src/gridvision/extracao.py (detector + qualidade do recorte do
visor, sem OCR), os mesmos que o app calcula.

Dados (só fotos com medidor):
- treino do classificador: 60 fotos de checagem do piloto + 100 de validação. As 240 fotos que treinaram
  o detector ficam de fora: nelas as confianças do detector são otimistas.
- medida final: 100 fotos de teste, uma vez só.
Limiar de "ilegível com certeza alta": 0,20, escolhido pelo grupo em 18/10/2026 a partir da tabela de
troca impressa abaixo (com a regra de no máximo 2% de legíveis entre as excluídas, nenhuma foto era
excluída: uma foto legível aparece mesmo nos limiares mais baixos).
Grava src/gridvision/legibilidade_v0.json (coeficientes, padronização, limiar).
"""
import csv, json, math, re, sys
from pathlib import Path
import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from gridvision import extracao as ex
import cv2
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score

DADOS = Path(sys.argv[1])
LIMIAR_ESCOLHIDO = 0.20


def respostas(caminho_json):
    out = {}
    for t in json.load(open(caminho_json, encoding="utf-8")):
        f = re.search(r"(PSP_EXTRATLEITIMPL_\d+_\d+_\d{20}_\d{3}\.jpg)", t.get("file_upload") or t["data"]["image"]).group(1)
        anns = sorted([a for a in t["annotations"] if not a.get("was_cancelled")], key=lambda a: a["created_at"])
        if f not in out and anns:
            out[f] = {r["from_name"]: r["value"]["choices"][0] for r in anns[0]["result"] if r["type"] == "choices"}
    return out


interna = {r["arquivo"]: r["parte"] for r in csv.DictReader(open(RAIZ / "experiments/detector_v0/divisao_interna_piloto.csv", encoding="utf-8"))}
aval = {r["arquivo"]: r["conjunto"] for r in csv.DictReader(open(RAIZ / "experiments/avaliacao_detector/avaliacao_v1.csv", encoding="utf-8"))}
amostras = []
for f, resp in respostas(DADOS / "piloto/anotacoes/piloto_final.json").items():
    if interna.get(f) == "val":
        amostras.append((f, "ajuste", DADOS / "piloto/fotos" / f, resp))
for f, resp in respostas(DADOS / "avaliacao/avaliacao.json").items():
    p = next((q for q in (DADOS / "avaliacao/fotos").glob(f"*/{f}")), None)
    amostras.append((f, "ajuste" if aval[f] == "validacao" else "teste", p, resp))
amostras = [a for a in amostras if a[3].get("tem_medidor") != "não"]

X, y, grupo = [], [], []
for f, g, p, resp in amostras:
    img = cv2.imread(str(p))
    s = ex.sinais_legibilidade(img, ex.detectar(img))
    X.append([s[k] for k in ex.SINAIS]); y.append(resp["leitura_legivel"] == "sim"); grupo.append(g)
X, y, grupo = np.array(X, float), np.array(y), np.array(grupo)
# escalas muito diferentes (nitidez em centenas, confiança 0 a 1): log nas de nitidez, área e altura
LOG = [i for i, k in enumerate(ex.SINAIS) if k in ("visor_nitidez", "foto_nitidez", "visor_altura", "visor_area")]
def transformar(M):
    M = M.copy(); M[:, LOG] = np.log1p(M[:, LOG]); return M
Xt = transformar(X)
aj, te = grupo == "ajuste", grupo == "teste"
print(f"fotos com medidor: ajuste {aj.sum()} (legíveis {y[aj].sum()}), teste {te.sum()} (legíveis {y[te].sum()})")

media, desvio = Xt[aj].mean(0), Xt[aj].std(0) + 1e-9
Z = (Xt - media) / desvio
cv = StratifiedKFold(5, shuffle=True, random_state=42)
modelos = {"logistica": LogisticRegression(C=1.0, max_iter=2000),
           "arvores": GradientBoostingClassifier(n_estimators=150, max_depth=2, random_state=42)}
prob_cv = {}
for nome, m in modelos.items():
    prob_cv[nome] = cross_val_predict(m, Z[aj], y[aj], cv=cv, method="predict_proba")[:, 1]
    print(f"{nome}: AUC na validação cruzada {roc_auc_score(y[aj], prob_cv[nome]):.3f}")

escolhido = max(prob_cv, key=lambda n: roc_auc_score(y[aj], prob_cv[n]))
p_aj, y_aj = prob_cv[escolhido], y[aj]
limiar = LIMIAR_ESCOLHIDO
exc = p_aj < limiar
print(f"modelo: {escolhido} | limiar {limiar:.3f} | na validação cruzada exclui {exc.sum()} de {len(p_aj)} "
      f"fotos ({y_aj[exc].sum()} legíveis entre elas); ilegíveis no ajuste: {(~y_aj).sum()}")

final = modelos[escolhido].fit(Z[aj], y[aj])
p_te = final.predict_proba(Z[te])[:, 1]
print("troca por limiar (excluídas / legíveis entre elas / ilegíveis pegas):")
for t in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
    a, b = p_aj < t, p_te < t
    print(f"  P(legível) < {t:.2f} | ajuste (validação cruzada): {a.sum():3d} / {y_aj[a].sum():2d} / {(~y_aj)[a].sum():2d}"
          f" | teste: {b.sum():3d} / {y[te][b].sum():2d} / {(~y[te])[b].sum():2d}")
exc_te = p_te < limiar
print(f"TESTE: AUC {roc_auc_score(y[te], p_te):.3f} | exclui {exc_te.sum()} de {te.sum()} fotos com medidor | "
      f"legíveis entre as excluídas: {y[te][exc_te].sum()} | ilegíveis no teste: {(~y[te]).sum()} | "
      f"ilegíveis pegas: {(~y[te])[exc_te].sum()}")

saida = {"versao": "v0", "modelo": escolhido, "sinais": ex.SINAIS, "log": [ex.SINAIS[i] for i in LOG],
         "media": media.tolist(), "desvio": desvio.tolist(), "limiar_ilegivel": limiar,
         "treinado_com": "60 fotos de checagem do piloto + 100 de validação (com medidor)",
         "teste": {"fotos": int(te.sum()), "auc": round(float(roc_auc_score(y[te], p_te)), 3),
                   "excluidas": int(exc_te.sum()), "legiveis_excluidas": int(y[te][exc_te].sum())}}
if escolhido == "logistica":
    saida.update(coef=final.coef_[0].tolist(), intercepto=float(final.intercept_[0]))
    json.dump(saida, open(RAIZ / "src/gridvision/legibilidade_v0.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("gravado src/gridvision/legibilidade_v0.json")
else:
    import pickle
    (DADOS / "legibilidade_v0").mkdir(exist_ok=True)
    pickle.dump({"modelo": final, **saida}, open(DADOS / "legibilidade_v0/modelo.pkl", "wb"))
    json.dump(saida, open(RAIZ / "src/gridvision/legibilidade_v0.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("gravado gridvision_dados/legibilidade_v0/modelo.pkl e o resumo em src/gridvision/legibilidade_v0.json")
