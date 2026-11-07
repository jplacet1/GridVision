# -*- coding: utf-8 -*-
"""Os mesmos modelos do PaddleOCR, convertidos para ONNX, rodando no ONNX Runtime (CPU ou GPU via DirectML).

Por que: a GPU da máquina (AMD Radeon RX 6600) não acelera o PaddlePaddle no Windows, mas o DirectML do
ONNX Runtime usa qualquer GPU DirectX 12. Conversão (06/11/2026): paddle2onnx 2.1.0 com paddlepaddle 3.1.0 num
ambiente separado (venv_conv), opset 14. O pré e o pós-processamento são os do RapidOCR, com os parâmetros
dos próprios modelos (inference.yml): normalização ImageNet, limiares do DB e dicionário do reconhecedor.

Uso (ambiente venv_dml: onnxruntime-directml + rapidocr + opencv):
    python experiments/ensemble_ocr/ocr_onnx.py <gridvision_dados> <conjunto> <dml|cpu>

Lê as caixas do cache do ensemble_ocr.py (<gridvision_dados>/ensemble_ocr/<conjunto>.json) e grava os passes
'v5onnx/...' e 'v6onnx/...' (foto inteira 2x, recorte do visor 2x, recorte da placa 2x) em
<gridvision_dados>/ensemble_ocr/<conjunto>_onnx_<dml|cpu>.json, que o `avaliar` junta ao cache principal.
Modelos ONNX em <gridvision_dados>/onnx (fora do Git).
"""
import json, sys, time
from pathlib import Path

import cv2

AMPLIACAO = 2.0
FOLGA_RECORTE = 0.15
MODELOS = {
    "v5onnx": dict(det="PP-OCRv5_mobile_det", rec="en_PP-OCRv5_mobile_rec", thresh=0.3, box_thresh=0.6, unclip=1.5),
    "v6onnx": dict(det="PP-OCRv6_medium_det", rec="PP-OCRv6_medium_rec", thresh=0.3, box_thresh=0.6, unclip=1.5),
}


def criar(pasta_onnx, m, dml):
    from rapidocr import RapidOCR
    c = MODELOS[m]
    return RapidOCR(params={
        "Global.use_cls": False, "Global.text_score": 0.0, "Global.use_preprocess_img": False,
        "Global.use_vertical_padding": False, "Global.log_level": "error",
        "EngineConfig.onnxruntime.use_dml": dml,
        "Det.model_path": str(pasta_onnx / f"{c['det']}.onnx"),
        "Det.limit_type": "min", "Det.limit_side_len": 64,
        "Det.mean": [0.485, 0.456, 0.406], "Det.std": [0.229, 0.224, 0.225],
        "Det.thresh": c["thresh"], "Det.box_thresh": c["box_thresh"], "Det.unclip_ratio": c["unclip"],
        "Det.use_dilation": False, "Det.score_mode": "fast",
        "Rec.model_path": str(pasta_onnx / f"{c['rec']}.onnx"),
        "Rec.rec_keys_path": str(pasta_onnx / f"{c['rec']}_dict.txt"),
    })


def ler(ocr, img, x0=0.0, y0=0.0):
    g = cv2.resize(img, None, fx=AMPLIACAO, fy=AMPLIACAO, interpolation=cv2.INTER_CUBIC)
    r = ocr(g)
    if r.boxes is None:
        return []
    saida = []
    for poly, t, s in zip(r.boxes, r.txts, r.scores):
        xs = [x0 + p[0] / AMPLIACAO for p in poly]; ys = [y0 + p[1] / AMPLIACAO for p in poly]
        saida.append({"texto": t, "conf": float(s), "x": float(min(xs)),
                      "centro": (float(sum(xs) / len(xs)), float(sum(ys) / len(ys)))})
    return saida


def recorte(img, caixa):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = caixa
    fx, fy = FOLGA_RECORTE * (x1 - x0), FOLGA_RECORTE * (y1 - y0)
    x0, y0 = max(0, int(x0 - fx)), max(0, int(y0 - fy))
    return img[y0:min(h, int(y1 + fy)), x0:min(w, int(x1 + fx))], x0, y0


def main():
    dados, conj, disp = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    principal = json.loads((dados / "ensemble_ocr" / f"{conj}.json").read_text(encoding="utf-8"))
    ocrs = {m: criar(dados / "onnx", m, disp == "dml") for m in MODELOS}
    caminhos = {p.name: p for p in (dados / "avaliacao" / "fotos").rglob("*.jpg")}
    saida = {}
    for i, (f, reg) in enumerate(sorted(principal.items()), 1):
        img = cv2.imread(str(caminhos[f]))
        novo = {"passes": {}}
        for m, ocr in ocrs.items():
            t0 = time.perf_counter()
            novo["passes"][f"{m}/foto"] = ler(ocr, img)
            novo[f"segundos_{m}"] = round(time.perf_counter() - t0, 3)
            t0 = time.perf_counter()
            for classe in ("visor", "placa"):
                if classe in reg["caixas"]:
                    r, x0, y0 = recorte(img, reg["caixas"][classe])
                    if r.size:
                        novo["passes"][f"{m}/{classe}"] = ler(ocr, r, x0, y0)
            novo[f"segundos_{m}_recortes"] = round(time.perf_counter() - t0, 3)
        saida[f] = novo
        if i % 20 == 0:
            print(f"{i}/{len(principal)}", flush=True)
    (dados / "ensemble_ocr" / f"{conj}_onnx_{disp}.json").write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
    for m in MODELOS:
        for k in (f"segundos_{m}", f"segundos_{m}_recortes"):
            s = sorted(v[k] for v in list(saida.values())[1:])   # a primeira foto inclui aquecer o modelo
            print(f"{disp} {k}: mediana {s[len(s) // 2]:.3f} s")


if __name__ == "__main__":
    main()
