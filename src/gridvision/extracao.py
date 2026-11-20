# -*- coding: utf-8 -*-
"""
Extração do GridVision: da foto ao número do medidor e à leitura, com o fiscal do detector.

Uma função pública, `extrair(caminho, informado=None)`, usada tanto pelo app quanto pelas avaliações,
para que o número medido seja o comportamento real do MVP.

Fluxo (decidido em 18/10/2026, ver docs/contexto.md):
1. Detector v0 (YOLO11n): tem medidor? onde estão visor e placa?
2. PaddleOCR 3.7 na foto inteira ampliada 2x (melhor variante dos experimentos), guardando a posição
   de cada texto.
3. Fiscal:
   - leitura: só valem textos com o centro DENTRO da caixa do visor. Sem visor, não há leitura
     (evita coincidência com 240V, 15(100)A, ano de fabricação etc.).
   - número do medidor: vale dentro da caixa da placa; fora dela, só se o número informado tiver
     6 dígitos ou mais e aparecer inteiro (coincidência improvável).
4. Função do display: medidores digitais mostram o código da função à esquerda do valor (03 = consumo,
   ex.: "03 007237"). O código é separado da leitura; se a função não for de consumo, a leitura não é
   aceita (o display mostra outra coisa, como data ou hora) e a foto vai ao analista.
5. Confiança: a menor entre a confiança do OCR na leitura e no número. O limiar fica no app.

Motor ONNX (06/11/2026, experiments/ensemble_ocr): os modelos PP-OCRv6 medium e PP-OCRv5 mobile convertidos
para ONNX, no ONNX Runtime (GPU via DirectML, ou CPU), com três passes por motor: foto inteira, recorte do
visor e recorte da placa. O fiscal junta os candidatos de todos os passes (é verificação: o valor do CSV
aparece em algum?). Nas 100 fotos de validação: 18 Confere contra 10 do PaddleOCR v6 só na foto, sem erro de
leitura, e cerca de 1 s de OCR por foto na GPU contra 7,5 s.

Configuração por variável de ambiente:
- GRIDVISION_DETECTOR: caminho dos pesos do detector
  (padrão: ~/gridvision_dados/detector_v0/runs/v0/weights/best.pt, fora do Git).
- GRIDVISION_OCR: "onnx" (padrão quando os modelos ONNX e o onnxruntime existem), "v6_medium" ou "v5_mobile".
- GRIDVISION_ONNX: pasta dos modelos ONNX (padrão: ~/gridvision_dados/onnx, fora do Git).
- GRIDVISION_GPU=0: força o ONNX na CPU.
"""
import os, re
from dataclasses import dataclass
from pathlib import Path

PESOS_PADRAO = Path.home() / "gridvision_dados" / "detector_v0" / "runs" / "v0" / "weights" / "best.pt"
CONF_DETECTOR = 0.25
FATOR_AMPLIACAO = 2.0
MARGEM_CAIXA = 0.10          # folga ao checar se um texto está dentro da caixa
MIN_DIGITOS_FORA_PLACA = 6   # número informado achado fora da placa só conta se for longo
# Códigos de função do display que mostram o consumo (leitura). Informado pelo grupo em 18/10/2026:
# "geralmente a 03". Outros códigos podem ser acrescentados por GRIDVISION_FUNCOES_LEITURA="03,..."
FUNCOES_LEITURA = {c.strip().zfill(2) for c in os.environ.get("GRIDVISION_FUNCOES_LEITURA", "03").split(",") if c.strip()}
MIN_DIGITOS_COM_FUNCAO = 7   # "03" + leitura de 5 ou mais dígitos; abaixo disso não separa
# Modelos do OCR por GRIDVISION_OCR. v6_medium é o padrão do PaddleOCR 3.7 (lang="en"), o dos experimentos.
MODELOS_OCR = {
    "v6_medium": {},
    "v5_mobile": dict(text_detection_model_name="PP-OCRv5_mobile_det",
                      text_recognition_model_name="en_PP-OCRv5_mobile_rec"),
    "v6_det_v5_rec": dict(text_recognition_model_name="en_PP-OCRv5_mobile_rec"),
}

PASTA_ONNX = Path(os.environ.get("GRIDVISION_ONNX", Path.home() / "gridvision_dados" / "onnx"))
# Modelos ONNX e parâmetros do detector de texto (DB), tirados do inference.yml de cada modelo
MODELOS_ONNX = {
    "v6onnx": dict(det="PP-OCRv6_medium_det", rec="PP-OCRv6_medium_rec"),
    "v5onnx": dict(det="PP-OCRv5_mobile_det", rec="en_PP-OCRv5_mobile_rec"),
}
FOLGA_RECORTE = 0.15   # folga dos recortes de visor e placa lidos à parte

_detector = None
_ocr = None
_ocrs_onnx = None


def motor_ocr():
    pedido = os.environ.get("GRIDVISION_OCR")
    if pedido:
        return pedido
    import importlib.util
    tem = importlib.util.find_spec("onnxruntime") and importlib.util.find_spec("rapidocr") and \
        all((PASTA_ONNX / f"{m}.onnx").exists() for c in MODELOS_ONNX.values() for m in (c["det"], c["rec"]))
    return "onnx" if tem else "v6_medium"


def usa_gpu():
    if os.environ.get("GRIDVISION_GPU") == "0":
        return False
    try:
        import onnxruntime
        return "DmlExecutionProvider" in onnxruntime.get_available_providers()
    except ImportError:
        return False


def _criar_onnx(nome):
    from rapidocr import RapidOCR
    c = MODELOS_ONNX[nome]
    return RapidOCR(params={
        "Global.use_cls": False, "Global.text_score": 0.0, "Global.use_preprocess_img": False,
        "Global.use_vertical_padding": False, "Global.log_level": "error",
        "EngineConfig.onnxruntime.use_dml": usa_gpu(),
        "Det.model_path": str(PASTA_ONNX / f"{c['det']}.onnx"),
        "Det.limit_type": "min", "Det.limit_side_len": 64,
        "Det.mean": [0.485, 0.456, 0.406], "Det.std": [0.229, 0.224, 0.225],
        "Det.thresh": 0.3, "Det.box_thresh": 0.6, "Det.unclip_ratio": 1.5,
        "Det.use_dilation": False, "Det.score_mode": "fast",
        "Rec.model_path": str(PASTA_ONNX / f"{c['rec']}.onnx"),
        "Rec.rec_keys_path": str(PASTA_ONNX / f"{c['rec']}_dict.txt"),
    })


@dataclass
class ResultadoExtracao:
    tem_medidor: bool
    numero: str        # vazio se não achou
    leitura: str       # vazio se não achou
    confianca: float   # 0 a 1
    detalhe: str       # texto curto para o analista e para depuração
    prob_legivel: float = -1.0   # chance de a leitura ser legível (classificador v0 ou v1); -1 se não calculada


# Classificador de legibilidade (experiments/legibilidade): regressão logística.
# v0 (18/10/2026): sinais do detector e do recorte do visor; limiar de "ilegível com certeza alta" 0,20.
# v1 (06/11/2026): v0 + sinais do OCR (passes com dígitos no visor, confiança, concordância entre motores, dígitos
# na placa). Só vale com o motor ONNX, cujos passes geram esses sinais. Outro limiar com GRIDVISION_LIMIAR_ILEGIVEL.
_LEGIB = {}


def _legibilidade(versao=None):
    versao = versao or ("v1" if usa_legibilidade_v1() else "v0")
    if versao not in _LEGIB:
        import json
        arq = Path(__file__).with_name(f"legibilidade_{versao}.json")
        _LEGIB[versao] = json.load(open(arq, encoding="utf-8")) if arq.exists() else {}
    return _LEGIB[versao]


def usa_legibilidade_v1():
    return motor_ocr() == "onnx" and Path(__file__).with_name("legibilidade_v1.json").exists()         and os.environ.get("GRIDVISION_LEGIBILIDADE") != "v0"


def limiar_ilegivel():
    return float(os.environ.get("GRIDVISION_LIMIAR_ILEGIVEL", _legibilidade().get("limiar_ilegivel", 0.0)))


def sinais_ocr(passes, visor, placa):
    """Sinais do classificador v1, a partir dos passes de `_passes`: no visor, quantos passes acharam dígitos,
    a sequência mais longa, a maior confiança e se dois passes leram a mesma sequência; na placa, a sequência
    mais longa."""
    melhores, n_passes, max_dig, max_conf, placa_dig = [], 0, 0, 0.0, 0
    for regiao, ts in passes:
        if regiao != "placa" and visor is not None:
            no_visor = ts if regiao == "visor" else [t for t in ts if _dentro(t["centro"], visor)]
            toks = [(_digitos(t["texto"]), t["conf"]) for t in no_visor if _digitos(t["texto"])]
            if toks:
                n_passes += 1
                d, c = max(toks, key=lambda x: (len(x[0]), x[1]))
                max_dig, max_conf = max(max_dig, len(d)), max(max_conf, c)
                melhores.append(d.lstrip("0"))
        if regiao != "visor" and placa is not None:
            na = ts if regiao == "placa" else [t for t in ts if _dentro(t["centro"], placa)]
            placa_dig = max([placa_dig] + [len(_digitos(t["texto"])) for t in na])
    concordam = int(len(melhores) >= 2 and any(melhores.count(m) >= 2 and len(m) >= 3 for m in melhores))
    return {"ocr_passes_digitos": n_passes, "ocr_max_digitos": max_dig, "ocr_max_conf": max_conf,
            "ocr_concordam": concordam, "ocr_placa_digitos": placa_dig}


def prob_legivel(sinais, versao=None):
    """P(leitura legível) pelos coeficientes gravados; -1 se o classificador não estiver disponível."""
    import math
    m = _legibilidade(versao)
    if m.get("modelo") != "logistica":
        return -1.0
    z = m["intercepto"]
    for k, media, desvio, coef in zip(m["sinais"], m["media"], m["desvio"], m["coef"]):
        v = sinais[k]
        if k in m["log"]:
            v = math.log1p(v)
        z += coef * (v - media) / desvio
    return 1 / (1 + math.exp(-z))


def caminho_pesos():
    return Path(os.environ.get("GRIDVISION_DETECTOR", PESOS_PADRAO))


def motivo_indisponivel():
    """None se o modelo pode rodar; senão, o motivo (sem carregar os modelos)."""
    import importlib.util
    for mod in ("ultralytics", "paddleocr", "cv2"):
        if importlib.util.find_spec(mod) is None:
            return f"biblioteca {mod} não instalada"
    if not caminho_pesos().exists():
        return f"pesos do detector não encontrados em {caminho_pesos()}"
    return None


def _carregar():
    global _detector, _ocr, _ocrs_onnx
    # Números com ponto decimal para o código em C (OpenCV, ONNX Runtime, Paddle). O ttkbootstrap troca o locale
    # do processo para pt-BR (vírgula decimal) ao ser importado, e com isso o OCR do app perdia Confere (06/11/2026:
    # 6 contra 8 no lote_demo3).
    import locale
    locale.setlocale(locale.LC_NUMERIC, "C")
    if _detector is None:
        from ultralytics import YOLO
        _detector = YOLO(str(caminho_pesos()))
    if motor_ocr() == "onnx":
        if _ocrs_onnx is None:
            _ocrs_onnx = {m: _criar_onnx(m) for m in MODELOS_ONNX}
        return
    if _ocr is None:
        import warnings; warnings.filterwarnings("ignore")
        from paddleocr import PaddleOCR
        # enable_mkldnn=False: com o PaddlePaddle 3.3 em CPU, sem isso a inferência falha em silêncio
        # GRIDVISION_THREADS_OCR: threads de CPU do OCR (o app divide as threads entre os processos paralelos)
        threads = {"cpu_threads": int(os.environ["GRIDVISION_THREADS_OCR"])} if os.environ.get("GRIDVISION_THREADS_OCR") else {}
        _ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                         use_textline_orientation=False, lang="en", enable_mkldnn=False, **threads,
                         **MODELOS_OCR.get(os.environ.get("GRIDVISION_OCR", "v6_medium"), {}))


def _digitos(s):
    return re.sub(r"\D", "", s or "")


def normalizar_leitura(s):
    """Leitura no formato do CSV: sem zeros à esquerda (o display mostra 007237, o CSV traz 7237;
    nenhuma das 13.669 leituras da base começa com 0, fora o próprio "0"). Não vale para o número
    do medidor, em que o zero à esquerda faz parte do identificador (32 casos na base)."""
    d = _digitos(s)
    return d.lstrip("0") or ("0" if d else "")


def _dentro(centro, caixa):
    if caixa is None:
        return False
    x0, y0, x1, y1 = caixa
    mx, my = MARGEM_CAIXA * (x1 - x0), MARGEM_CAIXA * (y1 - y0)
    return x0 - mx <= centro[0] <= x1 + mx and y0 - my <= centro[1] <= y1 + my


def _candidatos(textos):
    """Sequências de dígitos de uma região: cada texto e, se houver mais de um, a junção da esquerda
    para a direita (o OCR às vezes parte a leitura do display). Devolve [(dígitos, confiança)]."""
    toks = [(t["x"], _digitos(t["texto"]), t["conf"]) for t in textos if _digitos(t["texto"])]
    cands = [(d, c) for _, d, c in toks]
    if len(toks) > 1:
        toks.sort()
        cands.append(("".join(d for _, d, _ in toks), min(c for _, _, c in toks)))
    return cands


def _leituras_do_visor(textos):
    """Candidatos de leitura do visor, já separando o código de função do display.
    Devolve [(leitura, confiança, função ou None)]."""
    toks = sorted((t["x"], _digitos(t["texto"]), t["conf"]) for t in textos if _digitos(t["texto"]))
    funcao = None
    # função lida como texto separado: 1 ou 2 dígitos à esquerda de um número maior
    if len(toks) > 1 and len(toks[0][1]) <= 2 and max(len(d) for _, d, _ in toks[1:]) >= 3:
        funcao = toks[0][1].zfill(2)
        toks = toks[1:]
    cands = [(d, c, funcao) for _, d, c in toks]
    if len(toks) > 1:
        cands.append(("".join(d for _, d, _ in toks), min(c for _, _, c in toks), funcao))
    # função grudada no número pelo OCR: "03007237" -> função 03, leitura 007237
    for d, c, f in list(cands):
        if f is None and len(d) >= MIN_DIGITOS_COM_FUNCAO:
            cands.append((d[2:], c, d[:2]))
    return cands


def detectar(img):
    """Detector v0: melhor caixa de cada classe. Devolve {classe: ([x0, y0, x1, y1], confiança)}."""
    _carregar()
    r = _detector.predict(img, imgsz=480, conf=CONF_DETECTOR, device="cpu", verbose=False)[0]
    melhor = {}
    for caixa, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
        n = r.names[int(c)]
        if n not in melhor or s > melhor[n][1]:
            melhor[n] = (caixa, s)
    return melhor


SINAIS = ["conf_medidor", "conf_visor", "conf_placa", "visor_nitidez", "visor_contraste", "visor_brilho",
          "visor_altura", "visor_area", "foto_nitidez", "foto_brilho"]


def sinais_legibilidade(img, melhor):
    """Sinais rápidos (sem OCR) para estimar se a leitura é legível: confianças do detector e
    qualidade do recorte do visor. Mesma função no treino do classificador e no app."""
    import cv2
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = cinza.shape
    s = {"conf_medidor": melhor.get("medidor", (None, 0.0))[1], "conf_visor": melhor.get("visor", (None, 0.0))[1],
         "conf_placa": melhor.get("placa", (None, 0.0))[1],
         "foto_nitidez": float(cv2.Laplacian(cinza, cv2.CV_64F).var()), "foto_brilho": float(cinza.mean()),
         "visor_nitidez": 0.0, "visor_contraste": 0.0, "visor_brilho": 0.0, "visor_altura": 0.0, "visor_area": 0.0}
    if "visor" in melhor:
        x0, y0, x1, y1 = [int(round(v)) for v in melhor["visor"][0]]
        rec = cinza[max(0, y0):min(h, y1), max(0, x0):min(w, x1)]
        if rec.size:
            s.update(visor_nitidez=float(cv2.Laplacian(rec, cv2.CV_64F).var()), visor_contraste=float(rec.std()),
                     visor_brilho=float(rec.mean()), visor_altura=float(rec.shape[0]),
                     visor_area=float(rec.size) / (h * w))
    return s


def _ler_textos(img, x0=0.0, y0=0.0, ocr=None):
    """OCR na imagem ampliada, com a posição de cada texto de volta à escala da foto original."""
    import cv2
    grande = cv2.resize(img, None, fx=FATOR_AMPLIACAO, fy=FATOR_AMPLIACAO, interpolation=cv2.INTER_CUBIC)
    if ocr is not None:   # ONNX (RapidOCR)
        r = ocr(grande)
        trios = [] if r.boxes is None else zip(r.txts, r.scores, r.boxes)
    else:
        o = _ocr.predict(grande)[0]
        trios = zip(o["rec_texts"], o["rec_scores"], o["rec_polys"])
    textos = []
    for t, s, poly in trios:
        xs = [x0 + p[0] / FATOR_AMPLIACAO for p in poly]; ys = [y0 + p[1] / FATOR_AMPLIACAO for p in poly]
        textos.append({"texto": t, "conf": float(s), "x": float(min(xs)),
                       "centro": (sum(xs) / len(xs), sum(ys) / len(ys))})
    return textos


def _recorte(img, caixa):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = caixa
    fx, fy = FOLGA_RECORTE * (x1 - x0), FOLGA_RECORTE * (y1 - y0)
    x0, y0 = max(0, int(x0 - fx)), max(0, int(y0 - fy))
    return img[y0:min(h, int(y1 + fy)), x0:min(w, int(x1 + fx))], x0, y0


def _passes(img, visor, placa):
    """[(região, textos)]: 'foto' (foto inteira, textos com posição) e, no ONNX, 'visor' e 'placa'
    (recortes lidos à parte: tudo o que sair deles pertence à região)."""
    if _ocrs_onnx is None:
        return [("foto", _ler_textos(img))]
    saida = []
    for ocr in _ocrs_onnx.values():
        saida.append(("foto", _ler_textos(img, ocr=ocr)))
        for regiao, caixa in (("visor", visor), ("placa", placa)):
            if caixa is not None:
                r, x0, y0 = _recorte(img, caixa)
                if r.size:
                    saida.append((regiao, _ler_textos(r, x0, y0, ocr=ocr)))
    return saida


def extrair(caminho, informado=None):
    """`informado` = (numero, leitura) do CSV, ou None. Nunca lança erro por foto ruim: devolve vazio."""
    import cv2
    _carregar()
    img = cv2.imread(str(caminho))
    if img is None:
        return ResultadoExtracao(False, "", "", 0.0, "não consegui abrir a imagem")

    # 1. detector: melhor caixa de cada classe; chance de a leitura ser legível
    melhor = detectar(img)
    if "medidor" not in melhor and "visor" not in melhor:
        return ResultadoExtracao(False, "", "", 1.0, "detector não achou medidor")
    sinais = sinais_legibilidade(img, melhor)
    visor = melhor.get("visor", (None, 0))[0]
    placa = melhor.get("placa", (None, 0))[0]

    # 2. OCR: um ou mais passes, cada um com a posição dos textos na foto original
    passes = _passes(img, visor, placa)
    if usa_legibilidade_v1():
        sinais.update(sinais_ocr(passes, visor, placa))
    p_leg = prob_legivel(sinais)
    textos = [t for regiao, ts in passes if regiao == "foto" for t in ts]

    num_inf, leit_inf = informado or ("", "")
    partes = [f"visor {melhor['visor'][1]:.2f}" if visor else "sem visor",
              f"placa {melhor['placa'][1]:.2f}" if placa else "sem placa"]

    # 3a. leitura: só dentro do visor (candidatos de cada passe separados: não se juntam textos de passes diferentes)
    leitura, conf_l = "", 0.0
    if visor is not None:
        cands = [c for regiao, ts in passes if regiao != "placa"
                 for c in _leituras_do_visor(ts if regiao == "visor" else [t for t in ts if _dentro(t["centro"], visor)])]
        alvo = _digitos(leit_inf).lstrip("0")
        iguais = [x for x in cands if alvo and x[0].lstrip("0") == alvo]
        # preferências: igual ao informado; função de consumo explícita; sequência mais longa
        if iguais:
            escolha = max(iguais, key=lambda x: (x[2] in FUNCOES_LEITURA, x[1]))
        elif cands:
            escolha = max(cands, key=lambda x: (x[2] in FUNCOES_LEITURA, x[2] is None, len(x[0]), x[1]))
        else:
            escolha = None
        if escolha:
            leitura, conf_l, funcao = escolha
            if funcao is not None:
                partes.append(f"função {funcao}")
                if funcao not in FUNCOES_LEITURA:
                    partes.append(f"display não mostra o consumo (função {', '.join(sorted(FUNCOES_LEITURA))})")
                    leitura, conf_l = "", 0.0
            if leitura and leitura != normalizar_leitura(leitura):
                partes.append(f"no visor: {leitura}")
            leitura = normalizar_leitura(leitura)

    # 3b. número do medidor: na placa; fora dela só se longo e inteiro
    numero, conf_n = "", 0.0
    alvos = [_digitos(m) for m in (num_inf or "").split("/") if _digitos(m)]
    na_placa = [c for regiao, ts in passes if regiao != "visor" and placa is not None
                for c in _candidatos(ts if regiao == "placa" else [t for t in ts if _dentro(t["centro"], placa)])]
    # devolve o número que foi LIDO, não o texto informado (que pode trazer vários medidores "a/b/c")
    for d, c in na_placa:
        if d in alvos and c > conf_n:
            numero, conf_n = d, c
    # na placa, um número informado longo contido num texto maior também vale (o OCR grudou outro texto nele)
    if not numero:
        for d, c in na_placa:
            achado = next((a for a in alvos if len(a) >= MIN_DIGITOS_FORA_PLACA and a in d), None)
            if achado and c > conf_n:
                numero, conf_n = achado, c
    if not numero:
        for t in textos:
            d = _digitos(t["texto"])
            achado = next((a for a in alvos if len(a) >= MIN_DIGITOS_FORA_PLACA and a in d), None)
            if achado and t["conf"] > conf_n:
                numero, conf_n = achado, t["conf"]
        if numero:
            partes.append("número achado fora da placa")
    if numero and len(alvos) > 1:
        partes.append(f"conferido 1 de {len(alvos)} números informados")
    if not numero and na_placa:
        numero, conf_n = max(na_placa, key=lambda x: (len(x[0]), x[1]))

    # sem número, vale a confiança da leitura: leitura que confere vai ao analista já preenchida
    confianca = min(conf_l, conf_n) if leitura and numero else conf_l if leitura else 0.0
    if p_leg >= 0:
        partes.append(f"chance de legível {p_leg:.0%}")
    return ResultadoExtracao(True, numero, leitura, round(confianca, 3), ", ".join(partes), round(p_leg, 3))
