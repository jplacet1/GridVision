# -*- coding: utf-8 -*-
"""
Baseline de OCR do GridVision (SR1, 02/10/2026).

Roda um OCR pronto (PaddleOCR, PP-OCRv5) na foto inteira, sem recorte e sem treino,
e compara os textos reconhecidos com o nº do medidor e a leitura registrados no CSV.

Uso, de dentro desta pasta (baseline_ocr/):

    python baseline_ocr.py ocr        # roda o PaddleOCR nas 100 fotos de fotos/ e grava a saída bruta
    python baseline_ocr.py avaliar    # compara com o CSV e imprime o resumo
    python baseline_ocr.py amostrar   # (opcional) refaz o sorteio; exige a base e os CSVs da EDA, ver abaixo

A pasta já traz a amostra sorteada (amostra_100_nitidas.csv + fotos/), a saída bruta do PaddleOCR de 02/10
e o resultado. Para reproduzir só a avaliação, basta `python baseline_ocr.py avaliar`.

Dependências: ver requirements.txt. A primeira execução do `ocr` baixa os modelos do PaddleOCR (~100 MB).
Em CPU leva ~5 s por foto, ~9 min no total.

Para `amostrar`, a pasta precisa estar dentro de "Projeto 4", ao lado de:
    Entregaveis/tabela_mestre.csv        registros do CSV + verificação de existência da foto (saída do eda_projeto4.py)
    Entregaveis/qualidade_amostra.csv    brilho, contraste e nitidez de 1.200 fotos sorteadas (idem)
    Classroom/Base de Dados Neoenergia PE/<lote>/*.jpg

Saídas, nesta pasta:
    amostra_100_nitidas.csv        as 100 fotos sorteadas, com nº do medidor e leitura do CSV
    fotos/                         cópia das 100 fotos
    paddleocr_saida_bruta.json     textos e confianças reconhecidos por foto
    resultado_baseline_ocr.csv     uma linha por foto com os acertos
"""
import argparse, csv, json, os, re, shutil, sys, time, warnings
from pathlib import Path

OUT = Path(__file__).resolve().parent             # esta pasta (baseline_ocr/)
FOTOS = OUT / "fotos"
RAIZ = OUT.parent                                 # pasta "Projeto 4", só usada em `amostrar`
BASE = RAIZ / "Classroom" / "Base de Dados Neoenergia PE"
ENT = RAIZ / "Entregaveis"
SEED = 1
N_AMOSTRA = 100
LIMIAR_NITIDEZ = 100.0   # variância do Laplaciano; mesmo limiar da EDA


def amostrar():
    import pandas as pd
    for p in (ENT / "qualidade_amostra.csv", ENT / "tabela_mestre.csv", BASE):
        if not p.exists():
            sys.exit(f"não encontrei {p}. A etapa `amostrar` precisa da base e dos CSVs da EDA; "
                     f"para reproduzir só o OCR e a avaliação, use `ocr` e `avaliar`.")
    q = pd.read_csv(ENT / "qualidade_amostra.csv")
    # keep_default_na=False: os CSVs usam o texto "NA" como valor, não como vazio
    m = pd.read_csv(ENT / "tabela_mestre.csv", keep_default_na=False)
    m = m[m["arquivo_existe"] == True]
    df = q.merge(m, left_on="arquivo", right_on="Foto do medidor")
    df = df[df["nitidez_lapvar"] >= LIMIAR_NITIDEZ]
    print(f"fotos nítidas com registro no CSV: {len(df)}")
    s = df.sample(N_AMOSTRA, random_state=SEED)
    out = s[["lote_x", "arquivo", "Numero do medidor", "Posicao do medidor lida", "nitidez_lapvar", "brilho"]]
    out = out.rename(columns={"lote_x": "lote"})
    OUT.mkdir(exist_ok=True); FOTOS.mkdir(exist_ok=True)
    out.to_csv(OUT / "amostra_100_nitidas.csv", index=False)
    for _, r in out.iterrows():
        shutil.copy(BASE / r.lote / r.arquivo, FOTOS / r.arquivo)
    print(f"{len(out)} fotos copiadas para {FOTOS}")


def ocr():
    warnings.filterwarnings("ignore")
    from paddleocr import PaddleOCR
    # enable_mkldnn=False evita um erro do PaddlePaddle 3.3 em CPU
    motor = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                      use_textline_orientation=False, lang="en", enable_mkldnn=False)
    saida = {}
    t0 = time.time()
    arquivos = sorted(f for f in os.listdir(FOTOS) if f.lower().endswith(".jpg"))
    for i, f in enumerate(arquivos, 1):
        try:
            r = motor.predict(str(FOTOS / f))[0]
            saida[f] = {"texts": list(r["rec_texts"]), "scores": [float(x) for x in r["rec_scores"]]}
        except Exception as e:
            saida[f] = {"error": str(e)}
        print(f"{i:3d}/{len(arquivos)} {f} -> {len(saida[f].get('texts', []))} textos", flush=True)
    json.dump(saida, open(OUT / "paddleocr_saida_bruta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"tempo total: {time.time() - t0:.0f} s")


def _digitos(s):
    return re.sub(r"\D", "", s)


def _lev(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def avaliar():
    raw = json.load(open(OUT / "paddleocr_saida_bruta.json", encoding="utf-8"))
    linhas = list(csv.DictReader(open(OUT / "amostra_100_nitidas.csv", encoding="utf-8")))
    res = []
    for r in linhas:
        f = r["arquivo"]; o = raw.get(f, {})
        textos = o.get("texts", []); erro = "error" in o
        toks = [_digitos(t) for t in textos]
        junto = "".join(toks)
        leit = r["Posicao do medidor lida"].strip()
        # o campo pode trazer mais de um medidor separado por "/" e letras (ex.: B67717)
        meds = [_digitos(m) for m in r["Numero do medidor"].split("/")]
        toks3 = [t.lstrip("0") for t in toks if len(t) >= 3]
        l0 = leit.lstrip("0") or "0"
        res.append(dict(
            arquivo=f, leitura=leit, medidor=r["Numero do medidor"], n_textos=len(textos), erro=erro,
            leitura_exata=any(t == leit for t in toks),
            # o display mostra zeros à esquerda (042884) que o CSV não tem (42884)
            leitura_sem_zeros=any(t and t.lstrip("0") == leit.lstrip("0") for t in toks),
            leitura_substring=(len(leit) >= 3 and leit in junto),
            leitura_erro_1_digito=any(_lev(t, l0) == 1 for t in toks3 if abs(len(t) - len(l0)) <= 1),
            medidor_exato=any(t == m for t in toks for m in meds),
            medidor_substring=any(m in junto for m in meds if len(m) >= 6),
            textos="|".join(textos),
        ))
    # "errou por 1 dígito" só conta quando não acertou
    for x in res:
        if x["leitura_sem_zeros"]:
            x["leitura_erro_1_digito"] = False
    with open(OUT / "resultado_baseline_ocr.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)

    n = len(res)
    def c(k): return sum(1 for x in res if x[k])
    print(f"\nfotos: {n} | com erro de execução: {c('erro')} | sem nenhum texto detectado: "
          f"{sum(1 for x in res if x['n_textos'] == 0 and not x['erro'])}")
    for k in ["leitura_exata", "leitura_sem_zeros", "leitura_substring", "leitura_erro_1_digito",
              "medidor_exato", "medidor_substring"]:
        print(f"  {k:24s} {c(k):3d} / {n}")
    print(f"resultado gravado em {OUT / 'resultado_baseline_ocr.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("etapa", choices=["amostrar", "ocr", "avaliar", "tudo"])
    etapa = ap.parse_args().etapa
    if etapa in ("amostrar", "tudo"): amostrar()
    if etapa in ("ocr", "tudo"): ocr()
    if etapa in ("avaliar", "tudo"): avaliar()
