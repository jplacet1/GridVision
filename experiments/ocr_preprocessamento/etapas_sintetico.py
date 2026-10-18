# Gera as imagens das etapas da V1 numa imagem SINTÉTICA (sem dado da Neoenergia).
import base64, json, warnings
from pathlib import Path
import cv2, numpy as np
warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
OUT = AQUI / "etapas"; OUT.mkdir(exist_ok=True)

img = cv2.imread(r"C:\Users\joaop\triagem-medidor-bentoml\examples\medidor_01.png").astype(np.float32)
h, w = img.shape[:2]
# foto de campo: pouco contraste, sombra forte à esquerda, reflexo, desfoque e ruído
img = img * 0.45 + 70
grad = np.tile(np.linspace(0.30, 1.0, w, dtype=np.float32), (h, 1))[..., None]
img = img * grad
yy, xx = np.mgrid[0:h, 0:w]
glare = np.exp(-(((xx - 250) / 60.0) ** 2 + ((yy - 230) / 28.0) ** 2))[..., None] * 90
img = img + glare
img = cv2.GaussianBlur(img, (0, 0), 1.3)
img = img + np.random.default_rng(1).normal(0, 6, img.shape).astype(np.float32)
deg = np.clip(img, 0, 255).astype(np.uint8)

big = cv2.resize(deg, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
lab = cv2.cvtColor(big, cv2.COLOR_BGR2LAB)
lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[:, :, 0])
clahe = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

from paddleocr import PaddleOCR
motor = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                  use_textline_orientation=False, lang="en", enable_mkldnn=False)

def ler(im, nome):
    p = OUT / f"{nome}_in.png"; cv2.imwrite(str(p), im)
    r = motor.predict(str(p))[0]
    vis = im.copy()
    esc = im.shape[1] / 360
    for poly, t, s in zip(r["rec_polys"], r["rec_texts"], r["rec_scores"]):
        pts = np.array(poly, dtype=np.int32)
        cv2.polylines(vis, [pts], True, (211, 91, 10), max(2, int(2 * esc)))
    return vis, [(t, round(float(s), 2)) for t, s in zip(r["rec_texts"], r["rec_scores"])]

ocr_deg, txt_deg = ler(deg, "deg")
ocr_v1, txt_v1 = ler(clahe, "v1")

def uri(im, largura=360):
    im = cv2.resize(im, (largura, int(im.shape[0] * largura / im.shape[1])), interpolation=cv2.INTER_AREA)
    ok, b = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return "data:image/jpeg;base64," + base64.b64encode(b).decode()

# a ampliada é mostrada como recorte do visor em tamanho real, para a diferença de pixels aparecer
def recorte(im, fator):
    y0, y1, x0, x1 = [int(v * fator) for v in (195, 295, 45, 315)]
    return im[y0:y1, x0:x1]

dados = dict(
    original=uri(deg), ampliada=uri(big), clahe=uri(clahe),
    ocr_deg=uri(ocr_deg), ocr_v1=uri(ocr_v1),
    zoom_deg=uri(cv2.resize(recorte(deg, 1), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST), 360),
    zoom_big=uri(recorte(big, 2), 360), zoom_clahe=uri(recorte(clahe, 2), 360),
    txt_deg=txt_deg, txt_v1=txt_v1,
)
json.dump(dados, open(AQUI / "etapas.json", "w", encoding="utf-8"), ensure_ascii=False)
print("deg:", txt_deg); print("v1:", txt_v1)
print("tamanho total KB:", sum(len(v) for v in dados.values() if isinstance(v, str)) // 1024)
