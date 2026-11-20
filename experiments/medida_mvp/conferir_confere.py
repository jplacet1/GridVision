# -*- coding: utf-8 -*-
"""Conferência manual dos Confere de um lote (item 10d: prova do erro zero com amostra maior), 20/11/2026.

Uso (ambiente do app; Label Studio local rodando):
    python conferir_confere.py criar <pasta do lote> <email> <senha>
    python conferir_confere.py resultado <pasta do lote> <email> <senha>

criar: cria o projeto "GridVision conferência dos Confere (<lote>)" com cada foto em Confere de
resultados_app.csv e, ao lado, a leitura e o número que o app conferiu. Nada vem pré-marcado: é uma prova.
resultado: conta as respostas. Só imprime contagens (os valores ficam no Label Studio local, fora do Git).
"""
import csv, collections, sys
from pathlib import Path
import requests

URL = "http://localhost:8080"
CONFIG = """<View style="display: flex; gap: 24px; align-items: flex-start;">
  <View style="flex: 0 0 65%;">
    <Image name="foto" value="$image" zoom="true" zoomControl="true"/>
  </View>
  <View style="flex: 1; min-width: 260px;">
    <Header value="O app conferiu estes valores com a foto:"/>
    <Text name="lidos" value="Leitura: $leitura | Número do medidor: $numero"/>
    <Header value="A foto mostra esses valores?"/>
    <Choices name="conferencia" toName="foto" choice="single-radio" required="true">
      <Choice value="os dois certos" hotkey="q"/>
      <Choice value="leitura errada" hotkey="w"/>
      <Choice value="número errado" hotkey="e"/>
      <Choice value="os dois errados" hotkey="r"/>
      <Choice value="não dá para confirmar" hotkey="t"/>
    </Choices>
    <TextArea name="obs" toName="foto" rows="2" placeholder="Observação (opcional)"/>
  </View>
</View>"""


# o upload de imagem solta só é aceito com um campo de dados: importa com este e troca pelo CONFIG depois
SO_IMAGEM = '<View><Image name="foto" value="$image"/><Choices name="conferencia" toName="foto"><Choice value="x"/></Choices></View>'


def sessao(email, senha):
    s = requests.Session()
    s.get(f"{URL}/user/login/")
    s.post(f"{URL}/user/login/", data={"email": email, "password": senha, "csrfmiddlewaretoken": s.cookies.get("csrftoken")},
           headers={"Referer": f"{URL}/user/login/"})
    s.headers.update({"X-CSRFToken": s.cookies.get("csrftoken"), "Referer": URL})
    if s.get(f"{URL}/api/projects").status_code != 200:
        sys.exit("login recusado")
    return s


def tarefas(s, pid):
    ts, pg = [], 1
    while True:
        r = s.get(f"{URL}/api/tasks", params={"project": pid, "page": pg, "page_size": 100})
        if r.status_code != 200 or not r.json()["tasks"]:
            return ts
        ts += r.json()["tasks"]; pg += 1


def main():
    modo, lote, email, senha = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4]
    titulo = f"GridVision conferência dos Confere ({lote.name})"
    s = sessao(email, senha)
    ps = s.get(f"{URL}/api/projects", params={"page_size": 100}).json()
    proj = next((p for p in ps.get("results", ps) if p["title"] == titulo), None)
    if modo == "criar":
        conf = [r for r in csv.DictReader(open(lote / "resultados_app.csv", encoding="utf-8"), delimiter=";")
                if r["status"] == "Confere"]
        if proj is None:
            proj = s.post(f"{URL}/api/projects", json={"title": titulo, "label_config": SO_IMAGEM}).json()
        # o upload devolve a tarefa sem id; o nome do arquivo fica no fim da URL da imagem
        def nome(t):
            return next((r["arquivo"] for r in conf if t["data"]["image"].endswith(r["arquivo"])), None)
        ja = {nome(t) for t in tarefas(s, proj["id"])}
        s.patch(f"{URL}/api/projects/{proj['id']}", json={"label_config": SO_IMAGEM})
        for r in conf:
            if r["arquivo"] not in ja:
                with open(lote / "fotos" / r["arquivo"], "rb") as fh:
                    s.post(f"{URL}/api/projects/{proj['id']}/import",
                           files={"file": (r["arquivo"], fh, "image/jpeg")}).raise_for_status()
        por = {r["arquivo"]: r for r in conf}
        for t in tarefas(s, proj["id"]):
            r = por.get(nome(t))
            if r and "leitura" not in t["data"]:
                s.patch(f"{URL}/api/tasks/{t['id']}", json={"data": {**t["data"], "arquivo": r["arquivo"],
                        "leitura": r["leitura_lida"], "numero": r["numero_lido"]}}).raise_for_status()
        s.patch(f"{URL}/api/projects/{proj['id']}", json={"label_config": CONFIG}).raise_for_status()
        print(f"projeto {proj['id']}: {len(tarefas(s, proj['id']))} tarefas ({len(conf)} Confere no lote)")
    else:
        c = collections.Counter()
        for t in tarefas(s, proj["id"]):
            if not t.get("total_annotations"):
                c["sem resposta"] += 1; continue
            a = s.get(f"{URL}/api/tasks/{t['id']}/annotations").json()[-1]
            c[next((x["value"]["choices"][0] for x in a["result"] if x["from_name"] == "conferencia"), "sem resposta")] += 1
        for k, v in c.most_common():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
