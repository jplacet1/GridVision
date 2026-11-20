# -*- coding: utf-8 -*-
"""Conjunto de passes de OCR para o Confere: mais candidatos de leitura e número por foto.

Hipótese (06/11/2026): PP-OCRv6 medium e PP-OCRv5 mobile acertam fotos diferentes (na validação, 10 Confere
cada, só 5 em comum, união 15 sem erro). Como o Confere é verificação (o valor do CSV aparece entre os
candidatos?), juntar candidatos de vários passes aumenta a cobertura; a proteção contra coincidência é exigir
leitura E número batendo.

Passes por motor (v6_medium, v5_mobile): foto inteira ampliada 2x, recorte do visor 2x e recorte da placa 2x
(caixas do detector v0, com folga). Tudo grava os textos brutos em
<gridvision_dados>/ensemble_ocr/<conjunto>.json (fora do Git: tem leituras e números).

Uso (ambiente do app, a partir da raiz do repositório):
    python experiments/ensemble_ocr/ensemble_ocr.py extrair <gridvision_dados> <conjunto>     conjunto: validacao | teste
    python experiments/ensemble_ocr/ensemble_ocr.py extras <gridvision_dados> <conjunto>      (passes extras nos recortes)
    python experiments/ensemble_ocr/ensemble_ocr.py ctc <gridvision_dados> <conjunto> <pesos ctc_v0.pt>   (leitor próprio)
    python experiments/ensemble_ocr/ensemble_ocr.py avaliar <gridvision_dados> <zip da base> <conjunto>

O teste só deve ser avaliado uma vez, com a regra escolhida na validação.
"""
import csv, io, json, sys, time, zipfile
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from gridvision import extracao as ex

MOTORES = ["v6_medium", "v5_mobile"]
AMPLIACAO = 2.0
FOLGA_RECORTE = 0.15
LIMIAR_CONFIANCA = 0.90   # o mesmo do app
LIMIAR_ILEGIVEL = 0.20    # o mesmo do app


def verdade(dados, conjunto):
    conj = {r["arquivo"]: r["conjunto"] for r in
            csv.DictReader(open(RAIZ / "experiments" / "avaliacao_detector" / "avaliacao_v1.csv", encoding="utf-8"))}
    saida = {}
    for t in json.load(open(dados / "avaliacao" / "avaliacao.json", encoding="utf-8")):
        f = t["data"]["image"].rsplit("/", 1)[-1].split("-", 1)[-1]
        if conj.get(f) != conjunto:
            continue
        a = [x for x in t["annotations"] if not x.get("was_cancelled")][-1]
        saida[f] = {r["from_name"]: r["value"]["choices"][0] for r in a["result"] if r["type"] == "choices"}
    return saida


def informado_da_base(zip_base):
    inf = {}
    with zipfile.ZipFile(zip_base) as z:
        for nome in z.namelist():
            if nome.lower().endswith(".csv"):
                for l in csv.DictReader(io.StringIO(z.read(nome).decode("utf-8-sig")), delimiter=";"):
                    foto = (l.get("Foto do medidor") or "").strip()
                    if foto and foto != "NA":
                        inf[foto] = ((l.get("Numero do medidor") or "").strip(),
                                     (l.get("Posicao do medidor lida") or "").strip())
    return inf


def _ocr(motor):
    import warnings; warnings.filterwarnings("ignore")
    from paddleocr import PaddleOCR
    return PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False,
                     lang="en", enable_mkldnn=False, **ex.MODELOS_OCR[motor])


def _variante(img, nome):
    """Pré-processamento do recorte: 'bin' = Otsu em cinza; 'inv' = cinza invertido (display de fundo escuro)."""
    import cv2
    if nome == "normal":
        return img
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if nome == "bin":
        cinza = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    elif nome == "inv":
        cinza = 255 - cinza
    return cv2.cvtColor(cinza, cv2.COLOR_GRAY2BGR)


def _ler(ocr, img, x0=0.0, y0=0.0, fator=AMPLIACAO, variante="normal"):
    """OCR na imagem ampliada; posições de volta à escala da foto original."""
    import cv2
    g = cv2.resize(_variante(img, variante), None, fx=fator, fy=fator, interpolation=cv2.INTER_CUBIC)
    o = ocr.predict(g)[0]
    saida = []
    for t, s, poly in zip(o["rec_texts"], o["rec_scores"], o["rec_polys"]):
        xs = [x0 + p[0] / fator for p in poly]; ys = [y0 + p[1] / fator for p in poly]
        saida.append({"texto": t, "conf": float(s), "x": min(xs), "centro": (sum(xs) / len(xs), sum(ys) / len(ys))})
    return saida


def _recorte(img, caixa):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = caixa
    fx, fy = FOLGA_RECORTE * (x1 - x0), FOLGA_RECORTE * (y1 - y0)
    x0, y0 = max(0, int(x0 - fx)), max(0, int(y0 - fy))
    x1, y1 = min(w, int(x1 + fx)), min(h, int(y1 + fy))
    return img[y0:y1, x0:x1], x0, y0


def extrair(dados, conjunto):
    import cv2
    ex._carregar()   # detector (e o OCR padrão, não usado aqui)
    ocrs = {m: _ocr(m) for m in MOTORES}
    fotos = sorted(verdade(dados, conjunto))
    caminhos = {p.name: p for p in (dados / "avaliacao" / "fotos").rglob("*.jpg")}
    arq = dados / "ensemble_ocr" / f"{conjunto}.json"
    cache = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}
    for i, f in enumerate(fotos, 1):
        if f in cache:
            continue
        img = cv2.imread(str(caminhos[f]))
        melhor = ex.detectar(img)
        reg = {"caixas": {k: v[0] for k, v in melhor.items()},
               "prob_legivel": ex.prob_legivel(ex.sinais_legibilidade(img, melhor)), "passes": {}}
        for m, ocr in ocrs.items():
            t0 = time.perf_counter()
            reg["passes"][f"{m}/foto"] = _ler(ocr, img)
            reg[f"segundos_{m}"] = round(time.perf_counter() - t0, 2)
            t0 = time.perf_counter()
            for classe in ("visor", "placa"):
                if classe in melhor:
                    r, x0, y0 = _recorte(img, melhor[classe][0])
                    if r.size:
                        reg["passes"][f"{m}/{classe}"] = _ler(ocr, r, x0, y0)
            reg[f"segundos_{m}_recortes"] = round(time.perf_counter() - t0, 2)
        cache[f] = reg
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        print(f"{i}/{len(fotos)}", flush=True)


EXTRAS = [(1.5, "normal"), (3.0, "normal"), (2.0, "bin"), (2.0, "inv")]


def extrair_extras(dados, conjunto):
    """Passes extras nos recortes (visor e placa) das fotos já extraídas, gravados no mesmo cache."""
    import cv2
    ocrs = {m: _ocr(m) for m in MOTORES}
    arq = dados / "ensemble_ocr" / f"{conjunto}.json"
    cache = json.loads(arq.read_text(encoding="utf-8"))
    caminhos = {p.name: p for p in (dados / "avaliacao" / "fotos").rglob("*.jpg")}
    for i, f in enumerate(sorted(cache), 1):
        reg = cache[f]
        if reg.get("extras_ok"):
            continue
        img = cv2.imread(str(caminhos[f]))
        for m, ocr in ocrs.items():
            t0 = time.perf_counter()
            for classe in ("visor", "placa"):
                if classe in reg["caixas"]:
                    r, x0, y0 = _recorte(img, reg["caixas"][classe])
                    if r.size:
                        for fator, var in EXTRAS:
                            reg["passes"][f"{m}/{classe}/{var}{fator:g}x"] = _ler(ocr, r, x0, y0, fator, var)
            reg[f"segundos_{m}_extras"] = round(time.perf_counter() - t0, 2)
        reg["extras_ok"] = True
        arq.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        print(f"{i}/{len(cache)}", flush=True)


def passe_ctc(dados, conjunto, pesos):
    """Leitor CTC próprio (experiments/leitor_ctc) no recorte do visor, como o passe 'ctc/visor' do cache.
    Mesmo recorte do treino (montar_recortes.py: margem de 8%)."""
    import cv2
    sys.path.insert(0, str(RAIZ / "experiments" / "leitor_ctc"))
    from treinar_ctc import Leitor
    leitor = Leitor(pesos)
    arq = dados / "ensemble_ocr" / f"{conjunto}.json"
    cache = json.loads(arq.read_text(encoding="utf-8"))
    caminhos = {p.name: p for p in (dados / "avaliacao" / "fotos").rglob("*.jpg")}
    t0 = time.perf_counter()
    for f, reg in cache.items():
        reg["passes"].pop("ctc/visor", None)
        if "visor" not in reg["caixas"]:
            continue
        img = cv2.imread(str(caminhos[f]))
        h, w = img.shape[:2]
        x0, y0, x1, y1 = reg["caixas"]["visor"]
        mx, my = 0.08 * (x1 - x0), 0.08 * (y1 - y0)
        X0, Y0 = int(max(0, x0 - mx)), int(max(0, y0 - my))
        rec = img[Y0:int(min(h, y1 + my)), X0:int(min(w, x1 + mx))]
        if rec.size:
            d, c = leitor.ler(rec)
            reg["passes"]["ctc/visor"] = [{"texto": d, "conf": c, "x": X0, "centro": ((x0 + x1) / 2, (y0 + y1) / 2)}] if d else []
    arq.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    print(f"passe CTC em {len(cache)} fotos, {time.perf_counter() - t0:.1f}s no total")


def _passes_usados(reg, regra):
    """Chaves 'motor/classe' (passe principal) ou 'motor/classe/extra' (passes extras dos recortes)."""
    saida = {}
    for k, v in reg["passes"].items():
        motor, classe, *extra = k.split("/")
        if motor not in regra["motores"] or (extra and not regra.get("extras")):
            continue
        if classe == "foto" and regra.get("foto", True) or classe != "foto" and regra["recortes"]:
            saida[k] = v
    return saida


def decidir(reg, informado, regra):
    """Confere só se leitura E número batem com o CSV, com confiança mínima e função de consumo.
    Devolve 'confere', 'so_leitura', 'sem_medidor', 'negada' (ilegível com certeza alta) ou 'analista'."""
    cx = reg["caixas"]
    if "medidor" not in cx and "visor" not in cx:
        return "sem_medidor"
    num_inf, leit_inf = informado or ("", "")
    alvo_l = ex._digitos(leit_inf).lstrip("0")
    alvos_n = [ex._digitos(m) for m in num_inf.split("/") if ex._digitos(m)]
    conf_l = conf_n = 0.0
    for k, textos in _passes_usados(reg, regra).items():
        classe = k.split("/")[1]
        if "visor" in cx and classe != "placa":
            no_visor = textos if classe == "visor" else [t for t in textos if ex._dentro(t["centro"], cx["visor"])]
            for d, c, func in ex._leituras_do_visor(no_visor):
                if alvo_l and d.lstrip("0") == alvo_l and (func is None or func in ex.FUNCOES_LEITURA):
                    conf_l = max(conf_l, c)
        if classe != "visor":
            na_placa = textos if classe == "placa" else \
                [t for t in textos if "placa" in cx and ex._dentro(t["centro"], cx["placa"])]
            for d, c in ex._candidatos(na_placa):
                if d in alvos_n or (regra["contido"] and any(len(a) >= ex.MIN_DIGITOS_FORA_PLACA and a in d for a in alvos_n)):
                    conf_n = max(conf_n, c)
            if classe == "foto":   # fora da placa, como no app: só número longo e inteiro
                for t in textos:
                    d = ex._digitos(t["texto"])
                    if any(len(a) >= ex.MIN_DIGITOS_FORA_PLACA and a in d for a in alvos_n):
                        conf_n = max(conf_n, t["conf"])
    if conf_l and conf_n and min(conf_l, conf_n) >= regra.get("limiar", LIMIAR_CONFIANCA):
        return "confere"
    if conf_l >= regra.get("limiar", LIMIAR_CONFIANCA):
        return "so_leitura"
    if 0 <= reg["prob_legivel"] < regra.get("limiar_ilegivel", LIMIAR_ILEGIVEL):
        return "negada"
    return "analista"


REGRAS = {
    "v5 só recortes":           dict(motores={"v5_mobile"}, recortes=True, contido=False, foto=False),
    "v5 só recortes+cont":      dict(motores={"v5_mobile"}, recortes=True, contido=True, foto=False),
    "v6 só recortes":           dict(motores={"v6_medium"}, recortes=True, contido=False, foto=False),
    "v6+v5 só recortes+cont":   dict(motores={"v6_medium", "v5_mobile"}, recortes=True, contido=True, foto=False),
    "v5 foto+recortes+extras":  dict(motores={"v5_mobile"}, recortes=True, contido=True, extras=True),
    "v6+v5 tudo+extras":        dict(motores={"v6_medium", "v5_mobile"}, recortes=True, contido=True, extras=True),
    "ctc visor + v5 placa":     dict(motores={"ctc", "v5_mobile"}, recortes=True, contido=True, foto=False),
    "ctc + v5 foto+recortes":   dict(motores={"ctc", "v5_mobile"}, recortes=True, contido=True),
    "ctc + v6+v5 foto+recortes": dict(motores={"ctc", "v6_medium", "v5_mobile"}, recortes=True, contido=True),
    "v5onnx foto (GPU)":        dict(motores={"v5onnx"}, recortes=False, contido=False),
    "v6onnx foto (GPU)":        dict(motores={"v6onnx"}, recortes=False, contido=False),
    "v5onnx foto+recortes":     dict(motores={"v5onnx"}, recortes=True, contido=True),
    "v6onnx foto+recortes":     dict(motores={"v6onnx"}, recortes=True, contido=True),
    "v6onnx+v5onnx foto+rec":   dict(motores={"v6onnx", "v5onnx"}, recortes=True, contido=True),
    "todos (Paddle+ONNX)":      dict(motores={"v6_medium", "v5_mobile", "v6onnx", "v5onnx"}, recortes=True, contido=True),
    "v6 foto (app)":            dict(motores={"v6_medium"}, recortes=False, contido=False),
    "v5 foto":                  dict(motores={"v5_mobile"}, recortes=False, contido=False),
    "v6+v5 foto":               dict(motores={"v6_medium", "v5_mobile"}, recortes=False, contido=False),
    "v5 foto+recortes":         dict(motores={"v5_mobile"}, recortes=True, contido=False),
    "v5 foto+recortes+cont":    dict(motores={"v5_mobile"}, recortes=True, contido=True),
    "v6 foto+recortes":         dict(motores={"v6_medium"}, recortes=True, contido=False),
    "v6+v5 foto+recortes":      dict(motores={"v6_medium", "v5_mobile"}, recortes=True, contido=False),
    "v6+v5 foto+recortes+cont": dict(motores={"v6_medium", "v5_mobile"}, recortes=True, contido=True),
}


def avaliar(dados, zip_base, conjunto):
    gt = verdade(dados, conjunto)
    inf = informado_da_base(zip_base)
    cache = json.loads((dados / "ensemble_ocr" / f"{conjunto}.json").read_text(encoding="utf-8"))
    onnx = dados / "ensemble_ocr" / f"{conjunto}_onnx_dml.json"   # passes do ocr_onnx.py (GPU)
    if onnx.exists():
        for f, reg in json.loads(onnx.read_text(encoding="utf-8")).items():
            if f in cache:
                cache[f]["passes"].update(reg["passes"])
    fotos = sorted(f for f in gt if f in cache)
    ambos = lambda f: gt[f]["leitura_legivel"] == "sim" and gt[f]["numero_legivel"] == "sim"
    leit = lambda f: gt[f]["leitura_legivel"] == "sim"
    print(f"{conjunto}: {len(fotos)} fotos; leitura e número legíveis em {sum(map(ambos, fotos))}; "
          f"com CSV e legíveis: {sum(ambos(f) and f in inf for f in fotos)}")
    for m in MOTORES:
        s = sorted(cache[f][f"segundos_{m}"] for f in fotos)
        print(f"  OCR {m}: mediana {s[len(s) // 2]:.1f} s por foto (foto inteira)")
        r = sorted(cache[f][f"segundos_{m}_recortes"] for f in fotos if f"segundos_{m}_recortes" in cache[f])
        if r:
            print(f"  OCR {m}: mediana {r[len(r) // 2]:.1f} s por foto (recortes de visor e placa)")
    print(f"\n{'regra':28} {'confere':>7} {'erros':>5} {'negadas':>7} {'neg. legíveis':>13} {'resolvidas':>10}")
    for nome, regra in REGRAS.items():
        st = {f: decidir(cache[f], inf.get(f), regra) for f in fotos}
        c = [f for f in fotos if st[f] == "confere"]; n = [f for f in fotos if st[f] == "negada"]
        print(f"{nome:28} {len(c):7} {sum(not ambos(f) for f in c):5} {len(n):7} {sum(map(leit, n)):13} "
              f"{100 * (len(c) + len(n)) / len(fotos):9.0f}%")
    melhor = REGRAS["v6+v5 foto+recortes+cont"]
    print("\nLimiar de confiança (v6+v5 foto+recortes+cont): limiar / confere / erros")
    for t in [0.0, 0.5, 0.7, 0.8, 0.85, 0.9, 0.95]:
        st = {f: decidir(cache[f], inf.get(f), dict(melhor, limiar=t)) for f in fotos}
        c = [f for f in fotos if st[f] == "confere"]
        print(f"  {t:4.2f} {len(c):4} {sum(not ambos(f) for f in c):4}")


if __name__ == "__main__":
    if sys.argv[1] == "extrair":
        extrair(Path(sys.argv[2]), sys.argv[3])
    elif sys.argv[1] == "ctc":
        passe_ctc(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
    elif sys.argv[1] == "extras":
        extrair_extras(Path(sys.argv[2]), sys.argv[3])
    else:
        avaliar(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
