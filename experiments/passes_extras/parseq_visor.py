# -*- coding: utf-8 -*-
"""
PARSeq pré-treinado (sem ajuste fino) nos recortes do visor, para a variante `visor_parseq` de passes_extras.py.

Por que PARSeq: num estudo de 2026 (ENIAC, UFPR-AMR e Copel-AMR), foi o melhor equilíbrio entre acerto e custo entre
os modelos sem treino no domínio (84% em contadores limpos, 38% nos degradados, 4,5 GFLOPs), à frente de
EasyOCR e Tesseract, que também perdem aqui. Num display de 7 segmentos, também foi o melhor reconhecedor em
outro estudo (ITM Web of Conferences, 2024).

Ambiente separado (não mexe no venv_app): torch CPU, timm, pytorch-lightning, nltk; o código e os pesos vêm do
torch.hub (baudm/parseq).

Uso:  python experiments/passes_extras/parseq_visor.py <pasta dos recortes> <saida.json>
Grava {recorte: [(texto, confiança)]}: a leitura do recorte original e a do recorte ampliado com borda.
"""
import json, sys
from pathlib import Path

import torch
from PIL import Image, ImageOps
from torchvision import transforms as T


def main():
    pasta, saida = Path(sys.argv[1]), Path(sys.argv[2])
    modelo = torch.hub.load("baudm/parseq", "parseq", pretrained=True, trust_repo=True).eval()
    prep = T.Compose([T.Resize(modelo.hparams.img_size, T.InterpolationMode.BICUBIC), T.ToTensor(),
                      T.Normalize(0.5, 0.5)])
    res = {}
    with torch.inference_mode():
        for p in sorted(pasta.glob("*.png")):
            im = Image.open(p).convert("RGB")
            variantes = [im, ImageOps.expand(im, border=max(4, im.height // 6), fill=(0, 0, 0))]
            x = torch.stack([prep(v) for v in variantes])
            probs = modelo(x).softmax(-1)
            textos, confs = modelo.tokenizer.decode(probs)
            res[p.name] = [(t, float(c.prod())) for t, c in zip(textos, confs)]
    saida.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    print(len(res), "recortes lidos")


if __name__ == "__main__":
    main()
