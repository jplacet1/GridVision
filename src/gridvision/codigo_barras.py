# -*- coding: utf-8 -*-
"""
Número do medidor pelo código de barras da placa (camada da extração desde 20/11/2026).

Normas de distribuidoras pedem na placa um código de barras (Code 128) com a parte numérica do número do medidor.
O código tem verificação embutida: quando decodifica, o valor é exato. Medido em experiments/passes_extras:
decodifica em cerca de 7% das fotos (360 x 480 é pouco para barras finas) e, no lote_demo6, levou o Confere
de 63 para 67 sem perder nenhum. Só ajuda o número; a leitura continua vindo do OCR.

Sem o pacote `zxing-cpp`, devolve vazio e a extração segue como antes.
"""


def ler(img):
    """Textos dos códigos de barras achados na foto (BGR do OpenCV), procurando em 1x, 2x e 3x."""
    try:
        import zxingcpp
        from PIL import Image
    except ImportError:
        return []
    # ampliação bicúbica do Pillow, a mesma do experimento (a do OpenCV achou 1 código a menos no lote_demo6)
    cinza = Image.fromarray(img[:, :, ::-1]).convert("L")
    lidos = set()
    for f in (1, 2, 3):
        g = cinza if f == 1 else cinza.resize((cinza.width * f, cinza.height * f), Image.BICUBIC)
        lidos |= {r.text for r in zxingcpp.read_barcodes(g)}
    return sorted(lidos)
