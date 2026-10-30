# -*- coding: utf-8 -*-
"""Compara motores de OCR no recorte do visor e da placa (PaddleOCR, EasyOCR, Tesseract).

Recorte pelas caixas CORRIGIDAS À MÃO da avaliação (validação, 100 fotos): isola a qualidade do OCR,
sem o erro do detector. Acerto contra o CSV, só nas fotos anotadas como legíveis.

Uso:
    python comparar_ocr.py ler <motor> <gridvision_dados>        motor: paddle | easyocr | tesseract
    python comparar_ocr.py avaliar <gridvision_dados> <zip da base>

`ler` grava os textos brutos em <gridvision_dados>/comparar_ocr/<motor>.json (fora do Git).
PaddleOCR roda no venv_app; EasyOCR e Tesseract no venv_ocr_comparar (ambiente separado, para não
mexer nas dependências do app). Tesseract: instalador do UB Mannheim (winget UB-Mannheim.TesseractOCR).
`avaliar` também lê o cache do medir_mvp.py (pipeline atual do app) para comparação.
"""
import csv, io, json, re, sys, time, zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AMPLIACAO = 3   # recortes do visor têm ~30 a 60 px de altura; Tesseract e EasyOCR preferem letras maiores


def digitos(s):
    return re.sub(r"\D", "", s or "")


def anotacoes(dados):
    """{arquivo: (respostas, {classe: caixa em %})} das fotos de validação."""
    conj = {r["arquivo"]: r["conjunto"] for r in
            csv.DictReader(open(RAIZ / "experiments" / "avaliacao_detector" / "avaliacao_v1.csv", encoding="utf-8"))}
    saida = {}
    for t in json.load(open(dados / "avaliacao" / "avaliacao.json", encoding="utf-8")):
        f = t["data"]["image"].rsplit("/", 1)[-1].split("-", 1)[-1]
        if conj.get(f) != "validacao":
            continue
        a = [x for x in t["annotations"] if not x.get("was_cancelled")][-1]
        resp = {r["from_name"]: r["value"]["choices"][0] for r in a["result"] if r["type"] == "choices"}
        caixas = {}
        for r in a["result"]:
            if r["type"] == "rectanglelabels":
                v = r["value"]
                caixas.setdefault(v["rectanglelabels"][0], (v["x"], v["y"], v["width"], v["height"]))
        saida[f] = (resp, caixas)
    return saida


def recortes(dados):
    """Gera (arquivo, classe, imagem PIL ampliada) para visor e placa."""
    from PIL import Image
    caminhos = {p.name: p for p in (dados / "avaliacao" / "fotos").rglob("*.jpg")}
    for f, (resp, caixas) in sorted(anotacoes(dados).items()):
        img = Image.open(caminhos[f]).convert("RGB")
        W, H = img.size
        for classe in ("visor", "placa"):
            if classe not in caixas:
                continue
            x, y, w, h = caixas[classe]
            r = img.crop((int(x * W / 100), int(y * H / 100), int((x + w) * W / 100), int((y + h) * H / 100)))
            yield f, classe, r.resize((r.width * AMPLIACAO, r.height * AMPLIACAO), Image.BICUBIC)


def ler(motor, dados):
    import numpy as np
    if motor == "paddle":
        sys.path.insert(0, str(RAIZ / "src"))
        from gridvision import extracao
        extracao._carregar()
        def rodar(img):
            o = extracao._ocr.predict(np.array(img)[:, :, ::-1])[0]
            return [(t, float(s)) for t, s in zip(o["rec_texts"], o["rec_scores"])]
    elif motor == "easyocr":
        import easyocr
        leitor = easyocr.Reader(["en"], gpu=False, verbose=False)
        def rodar(img):
            return [(t, float(s)) for _, t, s in leitor.readtext(np.array(img), allowlist="0123456789")]
    elif motor == "tesseract":
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        def rodar(img):
            # psm 7 = uma linha (visor); psm 6 = bloco (placa com várias linhas). Os dois, só dígitos.
            saida = []
            for psm in (7, 6):
                d = pytesseract.image_to_data(img.convert("L"), config=f"--psm {psm} -c tessedit_char_whitelist=0123456789",
                                              output_type=pytesseract.Output.DICT)
                saida += [(t, max(float(c), 0) / 100) for t, c in zip(d["text"], d["conf"]) if t.strip()]
            return saida
    else:
        raise SystemExit(f"motor desconhecido: {motor}")
    out, tempos = {}, []
    for f, classe, img in recortes(dados):
        t0 = time.perf_counter()
        out.setdefault(f, {})[classe] = rodar(img)
        tempos.append(time.perf_counter() - t0)
    destino = dados / "comparar_ocr" / f"{motor}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps({"segundos_por_recorte": sorted(tempos)[len(tempos) // 2], "textos": out},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{motor}: {len(tempos)} recortes, mediana {sorted(tempos)[len(tempos) // 2]:.2f} s por recorte -> {destino}")


def informado_da_base(zip_):
    inf = {}
    with zipfile.ZipFile(zip_) as z:
        for nome in z.namelist():
            if nome.lower().endswith(".csv"):
                for l in csv.DictReader(io.StringIO(z.read(nome).decode("utf-8-sig")), delimiter=";"):
                    foto = (l.get("Foto do medidor") or "").strip()
                    if foto and foto != "NA":
                        inf[foto] = ((l.get("Numero do medidor") or "").strip(),
                                     (l.get("Posicao do medidor lida") or "").strip())
    return inf


def leitura_certa(textos, alvo):
    """Alvo (CSV, sem zeros à esquerda) igual a algum texto, ou ao texto todo sem a função na frente (03...)."""
    alvo = alvo.lstrip("0") or "0"
    toks = [digitos(t) for t, _ in textos if digitos(t)]
    if any(t.lstrip("0") == alvo for t in toks):
        return True
    junto = "".join(toks)
    return any(junto[k:].lstrip("0") == alvo for k in range(0, min(3, len(junto))))


def numero_certo(textos, informado):
    alvos = [digitos(m) for m in informado.split("/") if digitos(m)]
    toks = [digitos(t) for t, _ in textos]
    junto = "".join(toks)
    return any(a in toks or (len(a) >= 6 and a in junto) for a in alvos)


def avaliar(dados, zip_):
    an = anotacoes(dados)
    inf = informado_da_base(zip_)
    leg_l = [f for f, (r, c) in an.items() if r.get("leitura_legivel") == "sim" and f in inf and "visor" in c]
    leg_n = [f for f, (r, c) in an.items() if r.get("numero_legivel") == "sim" and f in inf and "placa" in c]
    print(f"Validação: {len(an)} fotos; leitura legível com CSV e visor anotado: {len(leg_l)}; "
          f"número legível com CSV e placa anotada: {len(leg_n)}\n")
    print(f"{'motor':28} {'leitura':>12} {'número':>12} {'s/recorte':>10}")
    for motor in ("paddle", "easyocr", "tesseract"):
        arq = dados / "comparar_ocr" / f"{motor}.json"
        if not arq.exists():
            print(f"{motor:28} (não rodado)")
            continue
        d = json.loads(arq.read_text(encoding="utf-8"))
        tx = d["textos"]
        ok_l = sum(leitura_certa(tx.get(f, {}).get("visor", []), inf[f][1]) for f in leg_l)
        ok_n = sum(numero_certo(tx.get(f, {}).get("placa", []), inf[f][0]) for f in leg_n)
        print(f"{motor + ' (recorte manual 3x)':28} {ok_l:>5} de {len(leg_l):<4} {ok_n:>5} de {len(leg_n):<4} "
              f"{d['segundos_por_recorte']:>10.2f}")
    cache = dados / "medida_mvp" / "extracoes_validacao.json"
    if cache.exists():
        c = json.loads(cache.read_text(encoding="utf-8"))
        ok_l = sum(c[f]["leitura"] != "" and c[f]["leitura"].lstrip("0") == (inf[f][1].lstrip("0") or "0") for f in leg_l if f in c)
        ok_n = sum(c[f]["numero"] != "" and c[f]["numero"] in [digitos(m) for m in inf[f][0].split("/")] for f in leg_n if f in c)
        print(f"{'app atual (detector + fiscal)':28} {ok_l:>5} de {len(leg_l):<4} {ok_n:>5} de {len(leg_n):<4}")
    print("\nObs.: 'app atual' usa a caixa do detector e escolhe um valor; os motores no recorte manual contam acerto"
          " se algum texto bater (mais brando).")


if __name__ == "__main__":
    if sys.argv[1] == "ler":
        ler(sys.argv[2], Path(sys.argv[3]))
    else:
        avaliar(Path(sys.argv[2]), Path(sys.argv[3]))
