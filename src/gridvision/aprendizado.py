# -*- coding: utf-8 -*-
"""
Aprendizado com as decisões do analista: retreino periódico com trava (06/11/2026).

Por que periódico e não a cada clique: o erro tolerado nas leituras resolvidas sozinhas é zero. Uma decisão errada
ou um lote atípico não pode mudar o modelo na hora. Aqui o retreino roda quando o analista pede (botão no Histórico
ou script) e o modelo novo só entra se não piorar.

O que aprende:
1. Classificador de legibilidade v1: cada decisão "Ilegível" (não legível), "Corrigido" ou "Confirmado" (legível)
   do histórico vira gabarito, somada às 100 fotos de validação anotadas à mão.
2. Banco de transcrições do visor: cada "Corrigido" ou "Confirmado" traz a leitura verdadeira; o recorte do visor e o
   valor vão para <dados>/aprendizado/visor/, que é o que o leitor de dígitos próprio precisa (retreino na F4).

Fotos do teste e do teste temporal (divisao_v1) nunca entram: ficam reservadas para a medida final.

Trava: a comparação é feita nas fotos que o modelo atual nunca viu (decididas depois do último treino). Nelas, o
modelo atual é avaliado direto e o novo por validação cruzada (5 partes, previsões fora da parte de treino). O novo só
substitui o atual se a AUC não cair mais de 0,02 e a fração de legíveis entre as negadas (no limiar em uso) não subir
mais de 2 pontos. A lista de fotos de cada treino fica em <dados>/aprendizado/treino_legibilidade.txt e o modelo
anterior em <dados>/aprendizado/ (e no histórico do Git). Tudo fora do Git, menos os coeficientes
(src/gridvision/legibilidade_v1.json), que não têm dado do cliente.
"""
import csv, json, math
from datetime import datetime
from pathlib import Path

from gridvision import extracao as ex

RAIZ = Path(__file__).resolve().parents[2]
ARQ_MODELO = Path(__file__).with_name("legibilidade_v1.json")
TOLERANCIA_AUC = 0.02
TOLERANCIA_LEGIVEIS = 0.02
MIN_NOVAS = 20   # fotos nunca vistas pelo modelo atual necessárias para comparar


def reservadas():
    """Fotos que nunca entram no aprendizado: teste e teste temporal da divisão oficial."""
    arq = RAIZ / "experiments" / "piloto_anotacao" / "divisao_v1.csv"
    return {r["arquivo"] for r in csv.DictReader(open(arq, encoding="utf-8"))
            if r["conjunto"] in ("teste", "teste_temporal")}


def gabarito(dados, historico):
    """{arquivo: (caminho, legível?, origem)}: validação anotada + decisões do histórico (a mais recente vale)."""
    dados = Path(dados)
    fora = reservadas()
    saida = {}
    conj = {r["arquivo"]: r["conjunto"] for r in
            csv.DictReader(open(RAIZ / "experiments" / "avaliacao_detector" / "avaliacao_v1.csv", encoding="utf-8"))}
    anot = dados / "avaliacao" / "avaliacao.json"
    if anot.exists():
        caminhos = {p.name: p for p in (dados / "avaliacao" / "fotos").rglob("*.jpg")}
        for t in json.load(open(anot, encoding="utf-8")):
            f = t["data"]["image"].rsplit("/", 1)[-1].split("-", 1)[-1]
            if conj.get(f) != "validacao" or f not in caminhos:
                continue
            a = [x for x in t["annotations"] if not x.get("was_cancelled")][-1]
            resp = {r["from_name"]: r["value"]["choices"][0] for r in a["result"] if r["type"] == "choices"}
            if resp.get("tem_medidor") == "sim":
                saida[f] = (caminhos[f], resp["leitura_legivel"] == "sim", "anotação")
    for r in historico:   # carregar_historico devolve só a decisão mais recente de cada foto
        if r.decisao in ("Ilegível", "Corrigido", "Confirmado") and r.arquivo not in fora and r.arquivo not in saida \
                and Path(r.caminho).exists():
            saida[r.arquivo] = (Path(r.caminho), r.decisao != "Ilegível", "analista")
    return saida


def treino_atual(dados, historico):
    """Fotos usadas no treino do modelo em uso. Sem a lista gravada, reconstrói a do v1 de 06/11/2026: validação
    anotada + decisões do lote_demo2."""
    dados = Path(dados)
    arq = dados / "aprendizado" / "treino_legibilidade.txt"
    if arq.exists():
        return set(arq.read_text(encoding="utf-8").split())
    lote2 = {p.name for p in (dados / "lote_demo2" / "fotos").glob("*.jpg")}
    return set(gabarito(dados, [])) | {r.arquivo for r in historico if r.arquivo in lote2}


def sinais(dados, gab, progresso=print):
    """Sinais do v1 por foto, com cache em <dados>/aprendizado/sinais.json (fora do Git)."""
    import cv2
    dados = Path(dados)
    arq = dados / "aprendizado" / "sinais.json"
    antigo = dados / "legibilidade_v1_sinais.json"
    cache = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else \
        json.loads(antigo.read_text(encoding="utf-8")) if antigo.exists() else {}
    faltam = [f for f in gab if f not in cache]
    if faltam:
        ex._carregar()
    for i, f in enumerate(faltam, 1):
        img = cv2.imread(str(gab[f][0]))
        if img is None:
            continue
        melhor = ex.detectar(img)
        s = ex.sinais_legibilidade(img, melhor)
        visor = melhor.get("visor", (None, 0))[0]; placa = melhor.get("placa", (None, 0))[0]
        s.update(ex.sinais_ocr(ex._passes(img, visor, placa), visor, placa))
        cache[f] = s
        if i % 20 == 0:
            progresso(f"sinais: {i} de {len(faltam)} fotos novas")
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(cache), encoding="utf-8")
    return cache


def _matriz(lista, nomes, log):
    import numpy as np
    return np.array([[math.log1p(s[k]) if k in log else s[k] for k in nomes] for s in lista], dtype=float)


def _metricas(y, p, limiar):
    from sklearn.metrics import roc_auc_score
    neg = p < limiar
    return {"auc": float(roc_auc_score(y, p)), "legiveis_entre_negadas": float(y[neg].mean()) if neg.any() else 0.0,
            "negadas": int(neg.sum()), "fotos": int(len(y)), "ilegiveis": int((~y).sum())}


def retreinar(dados, historico, progresso=print, gravar=True):
    """Retreina o v1 com o gabarito atual. Devolve um relatório (dict) com 'promovido' e o motivo."""
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    dados = Path(dados)
    atual = json.load(open(ARQ_MODELO, encoding="utf-8"))
    limiar = atual.get("limiar_ilegivel", 0.40)
    gab = gabarito(dados, historico)
    s = sinais(dados, gab, progresso)
    fotos = [f for f in gab if f in s]
    y = np.array([gab[f][1] for f in fotos])
    vistas = treino_atual(dados, historico)
    novas = np.array([f not in vistas for f in fotos])
    rel = {"limiar": limiar, "fotos": len(fotos), "novas": int(novas.sum()),
           "do_analista": sum(gab[f][2] == "analista" for f in fotos)}
    if novas.sum() < MIN_NOVAS or y[novas].all() or not y[novas].any():
        rel.update(promovido=False,
                   motivo=f"poucas fotos novas desde o último treino ({int(novas.sum())}; mínimo {MIN_NOVAS})")
        rel["visor"] = exportar_visor(dados, historico)
        return rel
    nomes, log = atual["sinais"], set(atual["log"])
    X = _matriz([s[f] for f in fotos], nomes, log)
    media, desvio = X.mean(0), X.std(0) + 1e-9
    Z = (X - media) / desvio
    modelo = LogisticRegression(C=0.5, max_iter=2000)
    p_novo = cross_val_predict(modelo, Z, y, cv=StratifiedKFold(5, shuffle=True, random_state=42),
                               method="predict_proba")[:, 1]
    p_atual = np.array([ex.prob_legivel(s[f], "v1") for f in fotos])
    antes, depois = _metricas(y[novas], p_atual[novas], limiar), _metricas(y[novas], p_novo[novas], limiar)
    rel.update(antes=antes, depois=depois)
    if depois["auc"] < antes["auc"] - TOLERANCIA_AUC:
        rel.update(promovido=False, motivo="nas fotos novas, a AUC do modelo novo caiu além da tolerância")
    elif depois["legiveis_entre_negadas"] > antes["legiveis_entre_negadas"] + TOLERANCIA_LEGIVEIS:
        rel.update(promovido=False, motivo="nas fotos novas, o modelo novo negaria mais fotos legíveis")
    else:
        rel.update(promovido=True, motivo="nas fotos novas, o modelo novo não piorou")
    if rel["promovido"] and gravar:
        modelo.fit(Z, y)
        copia = dados / "aprendizado" / f"legibilidade_v1_{datetime.now():%Y%m%d_%H%M%S}_anterior.json"
        copia.write_text(json.dumps(atual, indent=1), encoding="utf-8")
        novo = dict(atual, media=media.tolist(), desvio=desvio.tolist(), coef=modelo.coef_[0].tolist(),
                    intercepto=float(modelo.intercept_[0]), metricas_fotos_novas=depois, fotos_treino=len(fotos),
                    rodada=atual.get("rodada", 1) + 1, treinado_em=f"{datetime.now():%Y-%m-%d %H:%M}")
        ARQ_MODELO.write_text(json.dumps(novo, indent=1), encoding="utf-8")
        (dados / "aprendizado" / "treino_legibilidade.txt").write_text("\n".join(sorted(fotos)), encoding="utf-8")
        ex._LEGIB.clear()   # o processo atual passa a usar o modelo novo
        rel["anterior_guardado_em"] = str(copia)
    rel["visor"] = exportar_visor(dados, historico)
    return rel


def exportar_visor(dados, historico):
    """Banco de transcrições: recorte do visor + leitura verdadeira de cada foto corrigida ou confirmada.
    Grava <dados>/aprendizado/visor/<arquivo>.png e transcricoes.csv. Devolve quantas transcrições há."""
    import cv2
    pasta = Path(dados) / "aprendizado" / "visor"
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / "transcricoes.csv"
    feitas = {}
    if arq.exists():
        feitas = {r["arquivo"]: r for r in csv.DictReader(open(arq, encoding="utf-8"))}
    fora = reservadas()
    novas = [r for r in historico if r.decisao in ("Corrigido", "Confirmado") and r.leitura_final
             and r.arquivo not in fora and Path(r.caminho).exists()
             and feitas.get(r.arquivo, {}).get("leitura") != r.leitura_final]
    if novas:
        ex._carregar()
    for r in novas:
        img = cv2.imread(r.caminho)
        visor = ex.detectar(img).get("visor") if img is not None else None
        if visor is None:
            continue
        rec, _, _ = ex._recorte(img, visor[0])
        cv2.imwrite(str(pasta / (Path(r.arquivo).stem + ".png")), rec)
        feitas[r.arquivo] = {"arquivo": r.arquivo, "leitura": r.leitura_final, "decisao": r.decisao,
                             "analisado_em": r.analisado_em}
    with open(arq, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["arquivo", "leitura", "decisao", "analisado_em"])
        w.writeheader(); w.writerows(feitas.values())
    return len(feitas)
