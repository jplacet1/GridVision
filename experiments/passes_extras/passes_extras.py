# -*- coding: utf-8 -*-
"""
Passes extras de OCR no pipeline do app (20/11/2026): ganham Confere sem criar erro?

A análise de erros (experiments/analise_erros) mostrou que o número da placa falha em 25 de 59 fotos que podiam
conferir. Aqui cada variante acrescenta passes de OCR aos do app, sem trocar nada do que já existe, e o pipeline
real (`extrair` + `decidir`) decide. Os passes extras não entram nos sinais do classificador de legibilidade
(para medir só o efeito no Confere, com a mesma chance de legível do app).

Variantes:
  placa_folga   recorte da placa com folga de 40% (o app usa 15%): número cortado na borda
  placa_3x      recorte da placa ampliado 3x (o app amplia 2x)
  placa_clahe   recorte da placa em cinza com CLAHE (contraste local)
  visor_externo candidatos de leitura de um leitor externo nos recortes do visor (JSON de parseq_visor.py ou de
                experiments/leitor_ctc/candidatos_visor.py)
  placa_barras  número lido do código de barras da foto (JSON de codigo_barras.py, zxing-cpp)

Gabarito (só validação; teste e teste temporal ficam de fora):
  historico      decisões do analista no app: leitura verdadeira (Corrigido/Confirmado) ou Ilegível
  revisao_cega   228 fotos do lote_demo6 rotuladas às cegas em 11/11 (a leitura dá para ler?)
Erro = Confere em foto cuja leitura o gabarito diz ilegível, ou com leitura diferente da verdadeira.

Uso (ambiente do app, raiz do repositório):
    python experiments/passes_extras/passes_extras.py <export_revisao_cega.json> [--visor=candidatos.json] [--barras=barras.json]
    python experiments/passes_extras/passes_extras.py --recortes   # grava os recortes do visor para o parseq
Saídas por foto ficam em gridvision_dados/passes_extras/ (fora do Git). No terminal, só contagens.
"""
import csv, hashlib, json, sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
import pipeline as pl

m = pl._modelo
DADOS = Path.home() / "gridvision_dados"
SAIDA = DADOS / "passes_extras"
LOTE6 = DADOS / "lote_demo6"


def conjuntos():
    return {l["arquivo"]: l["conjunto"] for l in
            csv.DictReader(open(RAIZ / "experiments" / "piloto_anotacao" / "divisao_v1.csv", encoding="utf-8"))}


def gabarito(export_json):
    """[(caminho, informado, legivel, leitura verdadeira ou "")]"""
    conj, itens = conjuntos(), {}
    for h in pl.carregar_historico():
        if conj.get(h.arquivo) != "validacao" or not Path(h.caminho).exists():
            continue
        inf = (h.numero_informado, h.leitura_informada) if h.numero_informado or h.leitura_informada else None
        leg = h.decisao in ("Corrigido", "Confirmado") and bool(h.leitura_final)
        itens[h.arquivo] = (h.caminho, inf, leg, m.normalizar_leitura(h.leitura_final) if leg else "", "historico")
    if export_json:
        chave = {l["id"]: l["arquivo"] for l in
                 csv.DictReader(open(LOTE6 / "revisao_cega_chave.csv", encoding="utf-8"), delimiter=";")}
        inf6 = pl.carregar_informado(LOTE6 / "informado.csv")
        for t in json.load(open(export_json, encoding="utf-8")):
            anot = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
            if not anot or not anot[-1]["result"]:
                continue
            arq = chave[Path(t["data"]["image"]).name[-7:-4]]
            resp = anot[-1]["result"][0]["value"]["choices"][0]
            if arq not in itens and conj.get(arq) == "validacao":
                itens[arq] = (str(LOTE6 / "fotos" / arq), inf6.get(arq), resp.startswith("Legível"), "", "revisao_cega")
    return list(itens.values())


# ---------- passes extras, guardados por foto (o OCR é o que custa) ----------
_cache, _extras_ids = {}, set()
_passes_app, _sinais_app = m._passes, m.sinais_ocr
VARIANTES_ATIVAS = set()
EXTERNO = {}      # nome do arquivo: [(texto, confiança)] do leitor externo do visor
BARRAS = {}       # nome do arquivo: [códigos de barras lidos]
_foto_atual = [""]


def _ocr_em(img):
    """Textos de todos os motores ONNX numa imagem (posição irrelevante: tudo pertence à região)."""
    m._carregar()
    return [t for ocr in m._ocrs_onnx.values() for t in m._ler_textos(img, ocr=ocr)]


def _recorte(img, caixa, folga):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = caixa
    fx, fy = folga * (x1 - x0), folga * (y1 - y0)
    return img[max(0, int(y0 - fy)):min(h, int(y1 + fy)), max(0, int(x0 - fx)):min(w, int(x1 + fx))]


def _variante(nome, img, visor, placa):
    import cv2
    if nome == "placa_barras":
        lidos = [{"texto": t, "conf": 0.99, "x": 0.0, "centro": (-1e6, -1e6)} for t in BARRAS.get(_foto_atual[0], [])]
        # sem placa detectada, entra como texto da foto fora de qualquer caixa (vale o número longo, >= 6 dígitos)
        return [("placa" if placa is not None else "foto", lidos)] if lidos else []
    if nome.startswith("placa") and placa is None:
        return []
    if nome == "placa_folga":
        r = _recorte(img, placa, 0.40)
    elif nome == "placa_3x":
        r = cv2.resize(_recorte(img, placa, m.FOLGA_RECORTE), None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    elif nome == "placa_clahe":
        cinza = cv2.cvtColor(_recorte(img, placa, m.FOLGA_RECORTE), cv2.COLOR_BGR2GRAY)
        r = cv2.cvtColor(cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(cinza), cv2.COLOR_GRAY2BGR)
    elif nome == "visor_externo":
        if visor is None:
            return []
        cx, cy = (visor[0] + visor[2]) / 2, (visor[1] + visor[3]) / 2
        return [("visor", [{"texto": t, "conf": c, "x": visor[0], "centro": (cx, cy)}
                           for t, c in EXTERNO.get(_foto_atual[0], [])])]
    else:
        raise ValueError(nome)
    return [("placa", _ocr_em(r))] if r.size else []


def _passes_com_extras(img, visor, placa):
    k = hashlib.md5(img.tobytes()).hexdigest()
    if k not in _cache:
        _cache[k] = {"app": _passes_app(img, visor, placa)}
    c = _cache[k]
    extras = []
    for v in sorted(VARIANTES_ATIVAS):
        if v not in c:
            c[v] = _variante(v, img, visor, placa)
        extras += c[v]
    _extras_ids.update(id(p) for p in extras)
    return c["app"] + extras


def _sinais_sem_extras(passes, visor, placa):
    return _sinais_app([p for p in passes if id(p) not in _extras_ids], visor, placa)


m._passes, m.sinais_ocr = _passes_com_extras, _sinais_sem_extras


def rodar(gab, variantes):
    VARIANTES_ATIVAS.clear()
    VARIANTES_ATIVAS.update(variantes)
    st, linhas = Counter(), []
    for caminho, inf, leg, verdade, fonte in gab:
        _foto_atual[0] = Path(caminho).name
        ext = pl.extrair(caminho, inf)
        s = pl.decidir(ext, inf)[0]
        st[s] += 1
        erro = s == pl.CONFERE and (not leg or bool(verdade and ext.leitura != verdade))
        linhas.append((Path(caminho).name, s, erro, leg))
    return st, linhas


def gravar_recortes(gab):
    """Recortes do visor (mesma caixa e folga do app) para o reconhecedor externo, fora do Git."""
    import cv2
    pasta = SAIDA / "visor"
    pasta.mkdir(parents=True, exist_ok=True)
    n = 0
    for caminho, *_ in gab:
        img = cv2.imread(caminho)
        visor = m.detectar(img).get("visor", (None, 0))[0]
        if visor is not None:
            r = _recorte(img, visor, m.FOLGA_RECORTE)
            if r.size:
                cv2.imwrite(str(pasta / Path(caminho).name.replace(".jpg", ".png")), r)
                n += 1
    print(n, "recortes do visor em", pasta)


def main():
    if not pl.MODELO_REAL or m.motor_ocr() != "onnx":
        sys.exit("precisa do modelo real com o motor ONNX")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opc = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    gab = gabarito(args[0] if args else None)
    print(f"{len(gab)} fotos: {dict(Counter(g[4] for g in gab))}; legíveis {sum(g[2] for g in gab)}")
    if "--recortes" in sys.argv:
        gravar_recortes(gab)
        return
    configs = [(), ("placa_folga",), ("placa_3x",), ("placa_clahe",), ("placa_folga", "placa_3x", "placa_clahe")]
    if "visor" in opc:
        EXTERNO.update({k.replace(".png", ".jpg"): v for k, v in json.load(open(opc["visor"], encoding="utf-8")).items()})
        configs = [(), ("visor_externo",)]
    if "barras" in opc:
        BARRAS.update(json.load(open(opc["barras"], encoding="utf-8")))
        configs += [("placa_barras",), ("placa_barras", "placa_clahe")]
    SAIDA.mkdir(parents=True, exist_ok=True)
    base = None
    for cfg in configs:
        st, linhas = rodar(gab, cfg)
        conf = {l[0] for l in linhas if l[1] == pl.CONFERE}
        base = base if base is not None else conf
        resolv = st[pl.CONFERE] + st[pl.ILEGIVEL_CERTO] + st[pl.SEM_MEDIDOR]
        print(f"{'+'.join(cfg) or 'app atual':52s} Confere {st[pl.CONFERE]:3d} (novos {len(conf - base)}, "
              f"perdidos {len(base - conf)}), erros {sum(l[2] for l in linhas)}, sem analista {resolv}")
        with open(SAIDA / f"{'+'.join(cfg) or 'app'}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["arquivo", "status", "erro", "legivel"])
            w.writerows(linhas)


if __name__ == "__main__":
    main()
