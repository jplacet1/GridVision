# -*- coding: utf-8 -*-
"""Cria o projeto de transcrição do visor no Label Studio, importa os recortes e pré-preenche o texto
e as caixas de função e leitura. Rodar de novo atualiza o template e troca o pré-preenchimento antigo
(só texto) nas tarefas ainda sem anotação.

Uso: python criar_projeto_transcricao.py <pasta transcricao> <token> [url]
O token (Account & Settings) não é gravado em lugar nenhum.
"""
import json, re, sys
from pathlib import Path
import requests

PASTA, TOKEN = Path(sys.argv[1]), sys.argv[2]
URL = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8080"
TITULO = "GridVision transcrição do visor"

s = requests.Session()
s.headers["Authorization"] = f"Token {TOKEN}"
if s.get(f"{URL}/api/projects").status_code == 401:
    r = requests.post(f"{URL}/api/token/refresh", json={"refresh": TOKEN}); r.raise_for_status()
    s.headers["Authorization"] = f"Bearer {r.json()['access']}"

cfg = Path(__file__).with_name("label_studio_transcricao.xml").read_text(encoding="utf-8")
projetos = s.get(f"{URL}/api/projects", params={"page_size": 100}).json()
projetos = projetos.get("results", projetos)
proj = next((p for p in projetos if p["title"] == TITULO), None)
if proj is None:
    proj = s.post(f"{URL}/api/projects", json={"title": TITULO, "label_config": cfg,
                                               "show_collab_predictions": True, "model_version": "ocr"}).json()
elif proj["label_config"] != cfg:
    # Template mudou (caixas de função e leitura, 24/10/2026): atualiza o projeto existente.
    s.patch(f"{URL}/api/projects/{proj['id']}", json={"label_config": cfg}).raise_for_status()
pid = proj["id"]


def tarefas():
    ts, pg = [], 1
    while True:
        r = s.get(f"{URL}/api/tasks", params={"project": pid, "page": pg, "page_size": 100})
        if r.status_code != 200:
            break
        lote = r.json()["tasks"]
        if not lote:
            break
        ts += lote; pg += 1
    return ts


def nome(t):
    m = re.search(r"(PSP_EXTRATLEITIMPL_\d+_\d+_\d{20}_\d{3}\.png)", t["data"]["image"])
    return m.group(1) if m else None


ja = {nome(t) for t in tarefas()}
fotos = sorted(PASTA.glob("fotos/parte*/*.png"))
for f in fotos:
    if f.name not in ja:
        with open(f, "rb") as fh:
            s.post(f"{URL}/api/projects/{pid}/import", files={"file": (f.name, fh, "image/png")}).raise_for_status()

pred = json.load(open(PASTA / "predicoes.json", encoding="utf-8"))
feitas = 0
for t in tarefas():
    n = nome(t)
    if n not in pred or t.get("total_annotations"):
        continue
    p = pred[n] if isinstance(pred[n], dict) else {"texto": pred[n], "caixas": []}
    if t.get("total_predictions"):
        antigas = s.get(f"{URL}/api/predictions", params={"task": t["id"]}).json()
        if any(r["type"] == "rectanglelabels" for a in antigas for r in a["result"]) or not p["caixas"]:
            continue
        for a in antigas:  # pré-preenchimento antigo, só com o texto: troca pelo que tem as caixas
            s.delete(f"{URL}/api/predictions/{a['id']}").raise_for_status()
    res = [{"id": "ocr", "from_name": "texto", "to_name": "foto", "type": "textarea",
            "value": {"text": [p["texto"]]}}] if p["texto"] else []
    res += [{"id": f"caixa{i}", "from_name": "regiao", "to_name": "foto", "type": "rectanglelabels",
             "value": {"x": x, "y": y, "width": w, "height": h, "rotation": 0, "rectanglelabels": [rotulo]}}
            for i, (rotulo, x, y, w, h) in enumerate(p["caixas"])]
    s.post(f"{URL}/api/predictions", json={"task": t["id"], "result": res, "score": 0.5,
                                          "model_version": "ocr"}).raise_for_status()
    feitas += 1
print(f"projeto {pid} '{TITULO}': {len(tarefas())} tarefas, {feitas} pré-preenchidas agora")
