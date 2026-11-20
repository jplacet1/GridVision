# -*- coding: utf-8 -*-
"""
Revisão cega das fotos negadas pelo classificador de legibilidade v1 (limiar 0,40), pedida pelo
professor em 07/11/2026: mostrar que nenhuma foto com salvação é eliminada.

  preparar  junta todas as negadas do lote e 30 não negadas como controle, embaralha, copia com
            nomes neutros (001.jpg...) e grava a chave.
  avaliar   lê a exportação JSON do Label Studio e conta as legíveis por estrato.

Entrada: resultados_app.csv do lote (pipeline do app, colunas de app/pipeline.Resultado).
Tudo fica na pasta do lote, fora do Git (LGPD).
"""
import csv, json, random, shutil, sys
from collections import Counter
from pathlib import Path

LIMIAR, CORTE_ANTIGO = 0.40, 0.20
N_CONTROLE, SEED = 30, 1111


def estrato(r):
    if r["status"] != "Ilegível (certeza alta)":
        return "controle"
    return "negada 0,20-0,40" if float(r["prob_legivel"]) >= CORTE_ANTIGO else "negada <0,20"


def preparar(lote):
    res = list(csv.DictReader(open(lote / "resultados_app.csv", encoding="utf-8"), delimiter=";"))
    grupos = {}
    for r in res:
        if r["status"] != "Sem medidor":  # sem medidor não tem leitura a julgar
            grupos.setdefault(estrato(r), []).append(r)
    rng = random.Random(SEED)
    amostra = (grupos["negada 0,20-0,40"] + grupos["negada <0,20"]
               + rng.sample(grupos["controle"], N_CONTROLE))
    rng.shuffle(amostra)
    pasta = lote / "revisao_cega"
    pasta.mkdir(exist_ok=False)  # não sobrescreve uma revisão já feita
    with open(lote / "revisao_cega_chave.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "arquivo", "estrato", "prob_legivel", "status"])
        for i, r in enumerate(amostra, 1):
            shutil.copy(r["caminho"], pasta / f"{i:03d}.jpg")
            w.writerow([f"{i:03d}", r["arquivo"], estrato(r), r["prob_legivel"], r["status"]])
    print(len(amostra), "fotos em", pasta, Counter(estrato(r) for r in amostra))


def avaliar(lote, export_json):
    chave = {l["id"]: l for l in csv.DictReader(open(lote / "revisao_cega_chave.csv", encoding="utf-8"), delimiter=";")}
    total = Counter(estrato(r) for r in csv.DictReader(open(lote / "resultados_app.csv", encoding="utf-8"), delimiter=";")
                    if r["status"] != "Sem medidor")
    resposta = {}
    for t in json.load(open(export_json, encoding="utf-8")):
        anot = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
        if anot and anot[-1]["result"]:
            nome = Path(t["data"]["image"]).name[-7:-4]  # o upload prefixa o nome com um hash
            resposta[nome] = anot[-1]["result"][0]["value"]["choices"][0]
    faltam = sorted(set(chave) - set(resposta))
    print("respondidas", len(resposta), "de", len(chave), "faltam", faltam[:10])
    por = {}
    for i, v in resposta.items():
        por.setdefault(chave[i]["estrato"], Counter())[v] += 1
    for e in ("negada 0,20-0,40", "negada <0,20", "controle"):
        print(e, f"(no lote: {total[e]})", dict(por.get(e, {})))
    for i, v in sorted(resposta.items()):
        if chave[i]["estrato"] != "controle" and v.startswith("Legível"):
            print("salvável:", i, chave[i]["prob_legivel"], v)


if __name__ == "__main__":
    lote = Path(sys.argv[2])
    preparar(lote) if sys.argv[1] == "preparar" else avaliar(lote, sys.argv[3])
