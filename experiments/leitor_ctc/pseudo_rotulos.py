# -*- coding: utf-8 -*-
"""Pseudo-rótulos do visor para o leitor CTC (06/11/2026).

O rótulo do CSV não bate com o visor em pelo menos 10% dos recortes (diagnóstico de 18/10). Aqui só fica
o recorte em que algum passe de OCR (PP-OCRv5 mobile e PP-OCRv6 medium, recorte ampliado 2x) lê
exatamente a leitura do CSV: OCR e leiturista concordam, então o rótulo é confiável. O rótulo gravado é a
sequência de dígitos VISÍVEL no visor, da esquerda para a direita (zeros à esquerda e código de função
incluídos), que é o que o leitor CTC precisa transcrever.

Uso (a partir da raiz do repositório):
    python experiments/leitor_ctc/pseudo_rotulos.py <pasta leitor_digitos> [conjunto=treino] [processos=4] [paddle|onnx]

paddle (padrão, ambiente do app): PaddleOCR em CPU, vários processos.
onnx (ambiente venv_dml): os mesmos modelos em ONNX na GPU (ensemble_ocr/ocr_onnx.py), um processo, 10 a 24x
mais rápido. O cache bruto é o mesmo, então dá para começar num motor e terminar no outro.

Entrada: <pasta>/recortes.csv e <pasta>/recortes/<conjunto>/*.png (montar_recortes.py, fora do Git).
Saída: <pasta>/pseudo_<conjunto>.csv (arquivo, rótulo, passe, confiança) e um cache bruto
<pasta>/pseudo_<conjunto>_ocr.jsonl, que permite retomar. Nada vai para o Git.
"""
import csv, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

MOTORES = ["v5_mobile", "v6_medium"]
AMPLIACAO = 2.0
MAX_DIGITOS = 12
_ocrs = None


def _iniciar(threads, motor="paddle"):
    os.environ["OMP_NUM_THREADS"] = str(threads)
    global _ocrs
    if motor == "onnx":
        sys.path.insert(0, str(RAIZ / "experiments" / "ensemble_ocr"))
        import ocr_onnx
        pasta = Path(os.environ.get("GRIDVISION_ONNX", Path.home() / "gridvision_dados" / "onnx"))
        _ocrs = {m: ocr_onnx.criar(pasta, m, True) for m in ("v5onnx", "v6onnx")}
        return
    import warnings; warnings.filterwarnings("ignore")
    from paddleocr import PaddleOCR
    from gridvision import extracao as ex
    _ocrs = {m: PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False,
                          lang="en", enable_mkldnn=False, cpu_threads=threads, **ex.MODELOS_OCR[m]) for m in MOTORES}


def _ler(caminho):
    import cv2
    img = cv2.imread(str(caminho))
    g = cv2.resize(img, None, fx=AMPLIACAO, fy=AMPLIACAO, interpolation=cv2.INTER_CUBIC)
    saida = {}
    for m, ocr in _ocrs.items():
        if m.endswith("onnx"):
            r = ocr(g)
            saida[m] = [] if r.boxes is None else [{"texto": t, "conf": float(s), "x": float(min(p[0] for p in poly))}
                                                   for poly, t, s in zip(r.boxes, r.txts, r.scores)]
            continue
        o = ocr.predict(g)[0]
        saida[m] = [{"texto": t, "conf": float(s), "x": float(min(p[0] for p in poly))}
                    for t, s, poly in zip(o["rec_texts"], o["rec_scores"], o["rec_polys"])]
    return caminho.name, saida


def rotular(textos_por_motor, leitura_csv):
    """(rótulo visível, passe, confiança) se algum passe confirma a leitura do CSV; senão None."""
    from gridvision import extracao as ex
    alvo = ex._digitos(leitura_csv).lstrip("0")
    if not alvo or alvo == "0":
        return None
    melhor = None
    for m, textos in textos_por_motor.items():
        cands = ex._leituras_do_visor(textos)
        conf = max((c for d, c, f in cands if d.lstrip("0") == alvo and (f is None or f in ex.FUNCOES_LEITURA)), default=0)
        if not conf:
            continue
        visivel = "".join(ex._digitos(t["texto"]) for t in sorted(textos, key=lambda t: t["x"]))
        if len(visivel) > MAX_DIGITOS or alvo not in visivel:
            continue
        if melhor is None or conf > melhor[2]:
            melhor = (visivel, m, conf)
    return melhor


def _linhas(bruto):
    """Linhas do cache bruto; uma linha cortada (processo interrompido) é ignorada."""
    for l in open(bruto, encoding="utf-8"):
        try:
            yield json.loads(l)
        except json.JSONDecodeError:
            pass


def main():
    pasta = Path(sys.argv[1])
    conj = sys.argv[2] if len(sys.argv) > 2 else "treino"
    proc = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    motor = sys.argv[4] if len(sys.argv) > 4 else "paddle"
    linhas = [r for r in csv.DictReader(open(pasta / "recortes.csv", encoding="utf-8")) if r["conjunto"] == conj]
    leitura = {r["arquivo"].replace(".jpg", ".png"): r["leitura"] for r in linhas}
    bruto = pasta / f"pseudo_{conj}_ocr.jsonl"
    feitos = {r["arquivo"] for r in _linhas(bruto)} if bruto.exists() else set()
    faltam = [pasta / "recortes" / conj / a for a in leitura if a not in feitos]
    print(f"{conj}: {len(leitura)} recortes, {len(feitos)} já lidos, {len(faltam)} a ler, {proc} processos", flush=True)
    t0 = time.time()
    threads = max(1, (os.cpu_count() or proc) // proc)
    exe = None
    if motor == "onnx":   # GPU: um processo só
        _iniciar(threads, "onnx")
        leituras = map(_ler, faltam)
    else:
        exe = ProcessPoolExecutor(proc, initializer=_iniciar, initargs=(threads,))
        leituras = exe.map(_ler, faltam, chunksize=8)
    with open(bruto, "a", encoding="utf-8") as fh:
        for i, (nome, saida) in enumerate(leituras, 1):
            fh.write(json.dumps({"arquivo": nome, "ocr": saida}, ensure_ascii=False) + "\n")
            if i % 200 == 0:
                fh.flush()
                print(f"{i}/{len(faltam)} em {time.time() - t0:.0f}s", flush=True)
    if exe is not None:
        exe.shutdown()
    n = 0
    with open(pasta / f"pseudo_{conj}.csv", "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["arquivo", "rotulo", "passe", "conf"])
        for r in _linhas(bruto):
            rot = rotular(r["ocr"], leitura.get(r["arquivo"], ""))
            if rot:
                w.writerow([r["arquivo"], rot[0], rot[1], f"{rot[2]:.3f}"])
                n += 1
    print(f"fim: {n} pseudo-rótulos de {len(leitura)} recortes ({100 * n / max(1, len(leitura)):.0f}%), "
          f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
