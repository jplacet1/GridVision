# -*- coding: utf-8 -*-
"""
Legibilidade pelo recorte do visor com uma CNN pequena (20/11/2026). Pergunta do item 12h: dá para negar menos
fotos com salvação do que o classificador v1?

Motivo: na revisão cega de 11/11, 46 das 198 fotos negadas pelo v1 (limiar 0,40) tinham a leitura legível. O v1
usa sinais do detector e do OCR; quando o OCR falha numa foto boa, ele nega. No Copel-AMR (Laroca et al., 2021),
uma rede olhando o próprio recorte do contador recusou 98,9% dos ilegíveis e aceitou 99,8% dos legíveis.

Modelo: MobileNetV3-small pré-treinada no ImageNet (pesos do torchvision, já no cache local), última camada
trocada por 1 saída, ajuste fino no recorte do visor (detector v0, mesma folga do app). 5 sementes, média.

Treino (nada do lote_demo6, nada do teste nem do teste temporal):
  piloto (300, treino), avaliação de validação (100), decisões do analista no histórico (validação).
  Alvo: a leitura do visor é legível? Sem visor detectado, entra a foto inteira.
Prova: as 228 fotos da revisão cega do lote_demo6 (198 negadas pelo v1 e 30 de controle), que nem o v1 nem a CNN
viram. Legível = "Legível" ou "Legível com esforço" (critério de 11/11). "Sem medidor ou visor" fica de fora.

Uso (venv_app, raiz do repositório):
    python experiments/legibilidade_cnn/legibilidade_cnn.py <export_revisao_cega.json>
Só contagens no terminal; nada de foto sai da pasta local.
"""
import csv, json, re, sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from torch import nn

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
import pipeline as pl
import cv2

m = pl._modelo
DADOS = Path.home() / "gridvision_dados"
LOTE6 = DADOS / "lote_demo6"
ALTURA, LARGURA = 96, 224
SEMENTES, EPOCAS = 5, 12


def respostas(caminho_json):
    out = {}
    for t in json.load(open(caminho_json, encoding="utf-8")):
        f = re.search(r"(PSP_EXTRATLEITIMPL_\d+_\d+_\d{20}_\d{3}\.jpg)", t.get("file_upload") or t["data"]["image"]).group(1)
        anns = sorted([a for a in t["annotations"] if not a.get("was_cancelled")], key=lambda a: a["created_at"])
        if f not in out and anns:
            out[f] = {r["from_name"]: r["value"]["choices"][0] for r in anns[0]["result"] if r["type"] == "choices"}
    return out


def treino():
    """[(caminho, legível)] sem lote_demo6, teste nem teste temporal."""
    conj = {l["arquivo"]: l["conjunto"] for l in
            csv.DictReader(open(RAIZ / "experiments/piloto_anotacao/divisao_v1.csv", encoding="utf-8"))}
    lote6 = {p.name for p in (LOTE6 / "fotos").iterdir()}
    itens = {}
    for f, r in respostas(DADOS / "piloto/anotacoes/piloto_final.json").items():
        if r.get("tem_medidor") != "não":
            itens[f] = (DADOS / "piloto/fotos" / f, r.get("leitura_legivel") == "sim")
    for f, r in respostas(DADOS / "avaliacao/avaliacao.json").items():
        p = next((q for q in (DADOS / "avaliacao/fotos").glob(f"*/{f}")), None)
        if p and conj.get(f) == "validacao" and r.get("tem_medidor") != "não":
            itens[f] = (p, r.get("leitura_legivel") == "sim")
    for h in pl.carregar_historico():
        if conj.get(h.arquivo) == "validacao" and Path(h.caminho).exists():
            itens[h.arquivo] = (Path(h.caminho), h.decisao in ("Corrigido", "Confirmado") and bool(h.leitura_final))
    return [v for f, v in itens.items() if f not in lote6 and conj.get(f) in ("treino", "validacao")]


def prova(export_json):
    """[(caminho, legível, chance v1)] da revisão cega."""
    chave = {l["id"]: l for l in csv.DictReader(open(LOTE6 / "revisao_cega_chave.csv", encoding="utf-8"), delimiter=";")}
    saida = []
    for t in json.load(open(export_json, encoding="utf-8")):
        anot = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
        if not anot or not anot[-1]["result"]:
            continue
        resp = anot[-1]["result"][0]["value"]["choices"][0]
        if resp.startswith("Sem medidor"):
            continue
        c = chave[Path(t["data"]["image"]).name[-7:-4]]
        saida.append((LOTE6 / "fotos" / c["arquivo"], resp.startswith("Legível"), float(c["prob_legivel"])))
    return saida


def recorte(caminho):
    img = cv2.imread(str(caminho))
    visor = m.detectar(img).get("visor", (None, 0))[0]
    if visor is not None:
        x0, y0, x1, y1 = visor
        fx, fy = m.FOLGA_RECORTE * (x1 - x0), m.FOLGA_RECORTE * (y1 - y0)
        h, w = img.shape[:2]
        r = img[max(0, int(y0 - fy)):min(h, int(y1 + fy)), max(0, int(x0 - fx)):min(w, int(x1 + fx))]
        if r.size:
            img = r
    img = cv2.cvtColor(cv2.resize(img, (LARGURA, ALTURA), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
    x = torch.from_numpy(img).permute(2, 0, 1).float() / 255
    return (x - torch.tensor([0.485, 0.456, 0.406])[:, None, None]) / torch.tensor([0.229, 0.224, 0.225])[:, None, None]


def aumentar(x, g):
    """Brilho, contraste e deslocamento pequenos; o espelhamento trocaria a ordem dos dígitos e fica de fora."""
    x = x * (0.8 + 0.4 * torch.rand(len(x), 1, 1, 1, generator=g)) + 0.3 * (torch.rand(len(x), 1, 1, 1, generator=g) - 0.5)
    dx, dy = [int(v) for v in torch.randint(-8, 9, (2,), generator=g)]
    return torch.roll(x, (dy // 2, dx), dims=(2, 3))


def modelo():
    from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
    net = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.IMAGENET1K_V1)
    net.classifier[-1] = nn.Linear(net.classifier[-1].in_features, 1)
    return net


def treinar(X, y, semente):
    torch.manual_seed(semente)
    g = torch.Generator().manual_seed(semente)
    net = modelo()
    opt = torch.optim.AdamW(net.parameters(), lr=3e-4, weight_decay=1e-4)
    peso = torch.tensor([(len(y) - y.sum()) / max(1, y.sum())])  # equilibra legíveis e ilegíveis
    perda = nn.BCEWithLogitsLoss(pos_weight=peso)
    for _ in range(EPOCAS):
        net.train()
        for i in torch.randperm(len(X), generator=g).split(32):
            opt.zero_grad()
            perda(net(aumentar(X[i], g)).squeeze(1), y[i]).backward()
            opt.step()
    return net.eval()


def auc(p, y):
    from sklearn.metrics import roc_auc_score
    return roc_auc_score(y, p)


def main():
    if not pl.MODELO_REAL:
        sys.exit("precisa do modelo real (detector)")
    torch.set_num_threads(8)
    tr, pv = treino(), prova(sys.argv[1])
    print(f"treino {len(tr)} ({sum(l for _, l in tr)} legíveis); prova {len(pv)} ({sum(l for _, l, _ in pv)} legíveis)")
    Xt = torch.stack([recorte(c) for c, _ in tr]); yt = torch.tensor([float(l) for _, l in tr])
    Xp = torch.stack([recorte(c) for c, _, _ in pv]); yp = np.array([l for _, l, _ in pv])
    v1 = np.array([p for _, _, p in pv])
    redes = [treinar(Xt, yt, s) for s in range(SEMENTES)]
    with torch.inference_mode():
        cnn = np.mean([torch.sigmoid(r(Xp)).squeeze(1).numpy() for r in redes], axis=0)
    print(f"AUC na revisão cega: v1 {auc(v1, yp):.3f}, CNN {auc(cnn, yp):.3f}, média {auc((v1 + cnn) / 2, yp):.3f}")
    negadas = v1 < 0.40
    print(f"Negadas pelo v1 (0,40): {negadas.sum()}, com salvação {int((negadas & yp).sum())}")
    print(f"AUC só entre as negadas pelo v1: CNN {auc(cnn[negadas], yp[negadas]):.3f}")
    print("Regra: nega se v1 < 0,40 E CNN < t  (negadas, com salvação)")
    for t in (0.05, 0.10, 0.20, 0.30, 0.40, 0.50):
        n = negadas & (cnn < t)
        print(f"  t={t:.2f}: {int(n.sum())} negadas, {int((n & yp).sum())} com salvação")
    print("Comparação no mesmo número de negadas (v1 sozinho, limiar mais baixo):")
    for t in (0.05, 0.10, 0.20, 0.30):
        n = negadas & (cnn < t)
        k = int(n.sum())
        ordem = np.argsort(v1)[:k]
        print(f"  {k} negadas: v1 sozinho {int(yp[ordem].sum())} com salvação, v1 + CNN {int((n & yp).sum())}")
    json.dump({"cnn": cnn.tolist(), "v1": v1.tolist(), "legivel": yp.tolist()},
              open(DADOS / "passes_extras" / "legibilidade_cnn_prova.json", "w"))


if __name__ == "__main__":
    main()
