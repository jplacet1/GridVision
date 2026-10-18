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

Configuração por variável de ambiente:
- GRIDVISION_DETECTOR: caminho dos pesos do detector
  (padrão: ~/gridvision_dados/detector_v0/runs/v0/weights/best.pt, fora do Git).
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

_detector = None
_ocr = None


@dataclass
class ResultadoExtracao:
    tem_medidor: bool
    numero: str        # vazio se não achou
    leitura: str       # vazio se não achou
    confianca: float   # 0 a 1
    detalhe: str       # texto curto para o analista e para depuração


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
    global _detector, _ocr
    if _detector is None:
        from ultralytics import YOLO
        _detector = YOLO(str(caminho_pesos()))
    if _ocr is None:
        import warnings; warnings.filterwarnings("ignore")
        from paddleocr import PaddleOCR
        # enable_mkldnn=False: com o PaddlePaddle 3.3 em CPU, sem isso a inferência falha em silêncio
        _ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                         use_textline_orientation=False, lang="en", enable_mkldnn=False)


def _digitos(s):
    return re.sub(r"\D", "", s or "")


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


def extrair(caminho, informado=None):
    """`informado` = (numero, leitura) do CSV, ou None. Nunca lança erro por foto ruim: devolve vazio."""
    import cv2
    _carregar()
    img = cv2.imread(str(caminho))
    if img is None:
        return ResultadoExtracao(False, "", "", 0.0, "não consegui abrir a imagem")

    # 1. detector: melhor caixa de cada classe
    r = _detector.predict(img, imgsz=480, conf=CONF_DETECTOR, device="cpu", verbose=False)[0]
    nomes = r.names
    melhor = {}
    for caixa, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
        n = nomes[int(c)]
        if n not in melhor or s > melhor[n][1]:
            melhor[n] = (caixa, s)
    if "medidor" not in melhor and "visor" not in melhor:
        return ResultadoExtracao(False, "", "", 1.0, "detector não achou medidor")
    visor = melhor.get("visor", (None, 0))[0]
    placa = melhor.get("placa", (None, 0))[0]

    # 2. OCR na foto inteira ampliada, com a posição de cada texto (de volta à escala original)
    grande = cv2.resize(img, None, fx=FATOR_AMPLIACAO, fy=FATOR_AMPLIACAO, interpolation=cv2.INTER_CUBIC)
    o = _ocr.predict(grande)[0]
    textos = []
    for t, s, poly in zip(o["rec_texts"], o["rec_scores"], o["rec_polys"]):
        xs = [p[0] / FATOR_AMPLIACAO for p in poly]; ys = [p[1] / FATOR_AMPLIACAO for p in poly]
        textos.append({"texto": t, "conf": float(s), "x": min(xs),
                       "centro": (sum(xs) / len(xs), sum(ys) / len(ys))})

    num_inf, leit_inf = informado or ("", "")
    partes = [f"visor {melhor['visor'][1]:.2f}" if visor else "sem visor",
              f"placa {melhor['placa'][1]:.2f}" if placa else "sem placa"]

    # 3a. leitura: só dentro do visor
    leitura, conf_l = "", 0.0
    if visor is not None:
        cands = _leituras_do_visor([t for t in textos if _dentro(t["centro"], visor)])
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

    # 3b. número do medidor: na placa; fora dela só se longo e inteiro
    numero, conf_n = "", 0.0
    alvos = [_digitos(m) for m in (num_inf or "").split("/") if _digitos(m)]
    na_placa = _candidatos([t for t in textos if _dentro(t["centro"], placa)]) if placa is not None else []
    for d, c in na_placa:
        if d in alvos and c > conf_n:
            numero, conf_n = num_inf, c
    if not numero:
        for t in textos:
            d = _digitos(t["texto"])
            if any(a and len(a) >= MIN_DIGITOS_FORA_PLACA and a in d for a in alvos) and t["conf"] > conf_n:
                numero, conf_n = num_inf, t["conf"]
                partes.append("número achado fora da placa")
    if not numero and na_placa:
        numero, conf_n = max(na_placa, key=lambda x: (len(x[0]), x[1]))

    confianca = min(conf_l, conf_n) if leitura and numero else 0.0
    return ResultadoExtracao(True, numero, leitura, round(confianca, 3), ", ".join(partes))
