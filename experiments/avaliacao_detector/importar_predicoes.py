# -*- coding: utf-8 -*-
"""Envia as caixas previstas pelo detector como pré-anotação para um projeto do Label Studio.

Uso: python importar_predicoes.py <predicoes.json> <id do projeto> <token de acesso> [url]
O token fica em Account & Settings > Access Token (ou Personal Access Token). Ele não é gravado.
As fotos precisam já ter sido importadas no projeto. Cada tarefa recebe uma predição
"detector_v0"; ao abrir a tarefa, as caixas aparecem prontas para corrigir.
"""
import json, re, sys
import requests

PRED, PROJETO, TOKEN = sys.argv[1], sys.argv[2], sys.argv[3]
URL = sys.argv[4] if len(sys.argv) > 4 else "http://localhost:8080"
pred = json.load(open(PRED, encoding="utf-8"))

def sessao():
    s = requests.Session()
    s.headers["Authorization"] = f"Token {TOKEN}"
    if s.get(f"{URL}/api/projects/{PROJETO}").status_code == 401:
        # token pessoal (JWT): troca o refresh token por um access token
        r = requests.post(f"{URL}/api/token/refresh", json={"refresh": TOKEN})
        r.raise_for_status()
        s.headers["Authorization"] = f"Bearer {r.json()['access']}"
    return s

s = sessao()
tarefas, pagina = [], 1
while True:
    r = s.get(f"{URL}/api/tasks", params={"project": PROJETO, "page": pagina, "page_size": 100})
    if r.status_code == 404: break
    r.raise_for_status()
    lote = r.json()["tasks"] if isinstance(r.json(), dict) else r.json()
    if not lote: break
    tarefas += lote; pagina += 1

feitas = sem = 0
for t in tarefas:
    nome = t.get("file_upload") or str(t["data"].get("image", ""))
    m = re.search(r"(PSP_EXTRATLEITIMPL_\d+_\d+_\d{20}_\d{3}\.jpg)", nome)
    if not m or m.group(1) not in pred:
        sem += 1; continue
    res = pred[m.group(1)]
    score = max([x["score"] for x in res], default=0.0)
    s.post(f"{URL}/api/predictions", json={"task": t["id"], "result": res, "score": score,
                                          "model_version": "detector_v0"}).raise_for_status()
    feitas += 1
print("tarefas no projeto", len(tarefas), "| com pré-anotação", feitas, "| sem correspondência", sem)
