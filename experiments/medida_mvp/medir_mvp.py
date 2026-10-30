# -*- coding: utf-8 -*-
"""Mede o MVP (a mesma regra do app) nas 100 fotos de validação anotadas e varre o limiar de confiança.

Uso (ambiente do app, a partir da raiz do repositório):
    python experiments/medida_mvp/medir_mvp.py <gridvision_dados> <zip da base>

1. Roda a extração (detector v0 + PaddleOCR + fiscal) uma vez por foto e guarda a saída bruta em
   <gridvision_dados>/medida_mvp/extracoes_validacao.json (fora do Git: tem leituras e números).
   Rodar de novo reaproveita esse cache; apague-o para extrair outra vez.
2. Aplica `decidir` do app com o limiar atual e compara com a verdade anotada (tem medidor,
   número legível, leitura legível).
3. Varre o limiar de confiança: quantos "Confere" e quantos erros em cada valor.

Erro = "Confere" numa foto em que a leitura ou o número não estão legíveis (bateu por coincidência).
Sem transcrição do visor, um "Confere" em foto legível conta como certo: o OCR leu o mesmo valor do CSV.
O conjunto de teste não é usado (reservado para a medida final).
"""
import csv, io, json, os, sys, time, zipfile
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
import pipeline as pl

DADOS, ZIP = Path(sys.argv[1]), Path(sys.argv[2])
AVAL = DADOS / "avaliacao"
OCR = os.environ.get("GRIDVISION_OCR", "v6_medium")
# um cache por modelo de OCR; o do padrão mantém o nome original
CACHE = DADOS / "medida_mvp" / ("extracoes_validacao.json" if OCR == "v6_medium" else f"extracoes_validacao_{OCR}.json")


def verdade():
    """{arquivo: respostas da anotação} só das fotos de validação."""
    conj = {r["arquivo"]: r["conjunto"] for r in
            csv.DictReader(open(RAIZ / "experiments" / "avaliacao_detector" / "avaliacao_v1.csv", encoding="utf-8"))}
    saida = {}
    for t in json.load(open(AVAL / "avaliacao.json", encoding="utf-8")):
        f = t["data"]["image"].rsplit("/", 1)[-1].split("-", 1)[-1]
        if conj.get(f) != "validacao":
            continue
        a = [x for x in t["annotations"] if not x.get("was_cancelled")][-1]
        saida[f] = {r["from_name"]: r["value"]["choices"][0] for r in a["result"] if r["type"] == "choices"}
    return saida


def informado_da_base():
    """Mesmo formato de pl.carregar_informado, lido dos 4 CSVs do zip em memória."""
    inf = {}
    with zipfile.ZipFile(ZIP) as z:
        for nome in z.namelist():
            if nome.lower().endswith(".csv"):
                texto = z.read(nome).decode("utf-8-sig")
                for l in csv.DictReader(io.StringIO(texto), delimiter=";"):
                    foto = (l.get("Foto do medidor") or "").strip()
                    if foto and foto != "NA":
                        inf[foto] = ((l.get("Numero do medidor") or "").strip(),
                                     (l.get("Posicao do medidor lida") or "").strip())
    return inf


def extrair_tudo(fotos, informado):
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    caminhos = {p.name: p for p in (AVAL / "fotos").rglob("*.jpg")}
    for i, f in enumerate(fotos, 1):
        if f in cache:
            continue
        p = caminhos[f]
        t0 = time.perf_counter()
        nit = pl.nitidez(p)
        e = pl.extrair(p, informado.get(f), nitida=nit >= pl.LIMIAR_NITIDEZ)
        cache[f] = dict(tem_medidor=e.tem_medidor, numero=e.numero, leitura=e.leitura, confianca=e.confianca,
                        detalhe=e.detalhe, prob_legivel=e.prob_legivel, nitidez=nit,
                        segundos=round(time.perf_counter() - t0, 2))
        print(f"{i}/{len(fotos)}", flush=True)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache


def status(c, inf):
    e = pl.Extracao(c["tem_medidor"], c["numero"], c["leitura"], c["confianca"], c["detalhe"], c["prob_legivel"])
    return pl.decidir(e, inf)[0]


def main():
    assert pl.MODELO_REAL, pl.MOTIVO_SEM_MODELO
    gt = verdade()
    informado = informado_da_base()
    fotos = sorted(gt)
    cache = extrair_tudo(fotos, informado)

    def legivel(f): return gt[f]["leitura_legivel"] == "sim" and gt[f]["numero_legivel"] == "sim"
    def tem_medidor(f): return gt[f]["tem_medidor"] == "sim"
    n = len(fotos)
    com_csv = [f for f in fotos if f in informado]
    tempos = sorted(c["segundos"] for c in cache.values() if "segundos" in c)
    if tempos:  # a primeira foto inclui carregar os modelos
        print(f"\nOCR {OCR}: mediana {tempos[len(tempos) // 2]:.1f} s por foto ({len(tempos)} medidas)")
    print(f"\n{n} fotos de validação; {len(com_csv)} com registro no CSV; "
          f"leitura e número legíveis em {sum(map(legivel, fotos))}; sem medidor em {n - sum(map(tem_medidor, fotos))}")

    # 1. regra atual do app
    lim_atual = pl.LIMIAR_CONFIANCA
    st = {f: status(cache[f], informado.get(f)) for f in fotos}
    print(f"\n== Regra do app (limiar de confiança {lim_atual:.2f}, ilegível com certeza alta < {pl.limiar_ilegivel():.2f}) ==")
    for s, k in Counter(st.values()).most_common():
        print(f"  {s:26} {k:3}")
    confere = [f for f in fotos if st[f] == pl.CONFERE]
    neg = [f for f in fotos if st[f] == pl.ILEGIVEL_CERTO]
    sem = [f for f in fotos if st[f] == pl.SEM_MEDIDOR]
    print(f"  Resolvidas sem analista: {len(confere) + len(neg)} de {n} ({100 * (len(confere) + len(neg)) / n:.0f}%): "
          f"{len(confere)} Confere + {len(neg)} ilegível com certeza alta")
    print(f"  Erros no Confere (foto sem leitura e número legíveis): {sum(not legivel(f) for f in confere)}")
    print(f"  Ilegível com certeza alta em foto com leitura legível: "
          f"{sum(gt[f]['leitura_legivel'] == 'sim' for f in neg)} de {len(neg)}")
    print(f"  Sem medidor em foto com medidor: {sum(tem_medidor(f) for f in sem)} de {len(sem)}")
    leg = [f for f in fotos if legivel(f) and f in informado]
    print(f"  Legíveis com CSV: {len(leg)}; viraram Confere: {sum(st[f] == pl.CONFERE for f in leg)}; "
          f"onde pararam as outras: {dict(Counter(st[f] for f in leg if st[f] != pl.CONFERE))}")

    # 2. varredura do limiar de confiança (só muda o que seria Confere)
    pl.LIMIAR_CONFIANCA = 0.0
    candidatas = [f for f in fotos if status(cache[f], informado.get(f)) == pl.CONFERE]
    pl.LIMIAR_CONFIANCA = lim_atual
    print(f"\n== Limiar de confiança: {len(candidatas)} fotos seriam Confere sem limiar ==")
    print("  limiar  Confere  erros  confianças dos erros")
    erros_conf = sorted(round(cache[f]["confianca"], 3) for f in candidatas if not legivel(f))
    for t in [0.0, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.97, 0.99]:
        ok = [f for f in candidatas if cache[f]["confianca"] >= t]
        er = [f for f in ok if not legivel(f)]
        print(f"  {t:5.2f}  {len(ok):7}  {len(er):5}")
    print(f"  confianças dos Confere errados: {erros_conf or 'nenhum'}")
    print(f"  confianças dos Confere certos (menores): {sorted(round(cache[f]['confianca'], 3) for f in candidatas if legivel(f))[:8]}")


if __name__ == "__main__":
    main()
