# -*- coding: utf-8 -*-
"""
Dá para ler o número do medidor pelo código de barras da placa? (20/11/2026)

Normas de distribuidoras (ex.: Celesc E-321.0013) pedem um código de barras Code 128 com a parte numérica do
número do medidor. Código de barras tem verificação embutida: se decodifica, o valor é exato. Aqui o zxing-cpp
procura códigos de barras na foto inteira, ampliada 1x, 2x e 3x, e conta quantos batem com o número do CSV.

Uso (ambiente com zxing-cpp e Pillow, fora do venv_app):
    python experiments/passes_extras/codigo_barras.py <saida.json> <pasta do lote>...
Cada pasta de lote tem `fotos/` e `informado.csv`. Grava {foto: [códigos lidos]} (fora do Git), para a variante
`placa_barras` de passes_extras.py. Só contagens no terminal.
"""
import csv, sys
from pathlib import Path

import zxingcpp
from PIL import Image


def ler(im):
    lidos = set()
    for f in (1, 2, 3):
        g = im.resize((im.width * f, im.height * f), Image.BICUBIC) if f > 1 else im
        lidos |= {r.text for r in zxingcpp.read_barcodes(g)}
    return lidos


def main():
    saida, lotes = Path(sys.argv[1]), [Path(a) for a in sys.argv[2:]]
    todos = {}
    for lote in lotes:
        numero = {}
        with open(lote / "informado.csv", encoding="utf-8-sig", newline="") as f:
            for l in csv.DictReader(f, delimiter=";"):
                if l.get("Foto do medidor") and l["Foto do medidor"] != "NA":
                    numero[l["Foto do medidor"]] = ["".join(c for c in n if c.isdigit()) for n in l["Numero do medidor"].split("/")]
        fotos = sorted((lote / "fotos").glob("*.jpg"))
        com_codigo = bate = 0
        for p in fotos:
            lidos = ler(Image.open(p).convert("L"))
            if lidos:
                todos[p.name] = sorted(lidos)
                com_codigo += 1
                alvos = [a for a in numero.get(p.name, []) if a]
                if any(a in "".join(c for c in t if c.isdigit()) for t in lidos for a in alvos):
                    bate += 1
        print(f"{lote.name}: {len(fotos)} fotos, código de barras em {com_codigo}, com o número do CSV em {bate}")
    import json
    saida.write_text(json.dumps(todos), encoding="utf-8")


if __name__ == "__main__":
    main()
