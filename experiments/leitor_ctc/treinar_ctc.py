# -*- coding: utf-8 -*-
"""Leitor do visor CRNN + CTC, treinado em CPU com pseudo-rótulos e displays sintéticos (06/11/2026).

Por que CTC: o leitor anterior (treinar_cnn.py, 6 posições fixas) aprendia com o rótulo do CSV, que não
bate com o visor em pelo menos 10% dos recortes, e precisava adivinhar onde cada dígito estava. Aqui:
- rótulo = sequência visível confirmada pelo OCR (pseudo_rotulos.py), de qualquer comprimento;
- CTC alinha sozinho os dígitos ao longo da largura do recorte;
- displays sintéticos de 7 segmentos (gerados aqui, sem dado do cliente) completam o treino.

Uso (ambiente do app, com PyTorch):
    python experiments/leitor_ctc/treinar_ctc.py <pasta leitor_digitos> [minutos=40]

Treino: pseudo_treino.csv (conjunto `treino`), 10% separados por arquivo para checagem; metade de cada lote
é sintética. Validação e teste não entram aqui. Grava <pasta>/ctc_v0.pt (fora do Git).
"""
import csv, math, random, sys, time
from pathlib import Path
import cv2, numpy as np
import torch, torch.nn as nn, torch.nn.functional as F

H, W = 32, 128
ALFABETO = "0123456789"
SEMENTE = 42


# ---------- modelo ----------

class CRNN(nn.Module):
    def __init__(self):
        super().__init__()
        def bloco(i, o, pool):
            return [nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True)] + ([nn.MaxPool2d(pool)] if pool else [])
        self.cnn = nn.Sequential(*bloco(1, 32, 2), *bloco(32, 64, 2), *bloco(64, 128, None), *bloco(128, 128, (2, 1)),
                                 *bloco(128, 192, None), *bloco(192, 192, (2, 1)), nn.Dropout2d(0.1))
        self.rnn = nn.LSTM(192 * 2, 128, num_layers=2, bidirectional=True, batch_first=True, dropout=0.2)
        self.saida = nn.Linear(256, len(ALFABETO) + 1)   # 0 = branco do CTC

    def forward(self, x):                      # x: (N, 1, 32, 128)
        f = self.cnn(x)                        # (N, 192, 2, 32)
        f = f.permute(0, 3, 1, 2).flatten(2)   # (N, 32, 384)
        return self.saida(self.rnn(f)[0])      # (N, 32, 11)


def preparar(cinza):
    """Recorte em cinza -> tensor 1x32x128, mantendo a proporção (preenche com a cor da borda)."""
    h, w = cinza.shape
    nw = max(1, min(W, int(round(w * H / h))))
    r = cv2.resize(cinza, (nw, H), interpolation=cv2.INTER_AREA if h > H else cv2.INTER_CUBIC)
    if nw < W:
        r = cv2.copyMakeBorder(r, 0, 0, 0, W - nw, cv2.BORDER_REPLICATE)
    r = r.astype(np.float32) / 255.0
    return torch.from_numpy((r - r.mean()) / (r.std() + 1e-6))[None]


def decodificar(logits):
    """Greedy CTC. Devolve [(dígitos, confiança)], confiança = produto das probabilidades dos dígitos emitidos."""
    p = logits.softmax(-1)
    best, idx = p.max(-1)
    saida = []
    for b, i in zip(best, idx):
        s, conf, ant = "", 1.0, 0
        for pb, k in zip(b.tolist(), i.tolist()):
            if k != ant and k != 0:
                s += ALFABETO[k - 1]; conf *= pb
            ant = k
        saida.append((s, conf if s else 0.0))
    return saida


class Leitor:
    """Uso no app e nas avaliações: Leitor(caminho).ler(recorte_bgr) -> (dígitos, confiança)."""
    def __init__(self, caminho):
        self.m = CRNN(); self.m.load_state_dict(torch.load(caminho, map_location="cpu")); self.m.eval()

    @torch.no_grad()
    def ler(self, bgr):
        return decodificar(self.m(preparar(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))[None]))[0]


# ---------- displays sintéticos de 7 segmentos ----------

SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
       "7": "abc", "8": "abcdefg", "9": "abcdfg"}


def _digito(img, x, y, w, h, t, d, cor, inclina):
    pts = {"a": [(0, 0), (1, 0)], "b": [(1, 0), (1, .5)], "c": [(1, .5), (1, 1)], "d": [(0, 1), (1, 1)],
           "e": [(0, .5), (0, 1)], "f": [(0, 0), (0, .5)], "g": [(0, .5), (1, .5)]}
    for s in SEG[d]:
        (x0, y0), (x1, y1) = pts[s]
        p0 = (int(x + x0 * w + inclina * (1 - y0) * h), int(y + y0 * h))
        p1 = (int(x + x1 * w + inclina * (1 - y1) * h), int(y + y1 * h))
        cv2.line(img, p0, p1, cor, t, cv2.LINE_AA)


def sintetico(rnd):
    """Um visor sintético e o rótulo visível (função opcional + leitura com zeros à esquerda)."""
    n = rnd.randint(4, 8)
    leitura = "".join(rnd.choice(ALFABETO) for _ in range(n))
    if rnd.random() < 0.5:
        z = rnd.randint(1, n - 1); leitura = "0" * z + leitura[z:]
    funcao = rnd.choice(["03", "03", "03", "01", "02", "24", "88"]) if rnd.random() < 0.45 else ""
    rotulo = funcao + leitura
    dh = rnd.randint(28, 48); dw = int(dh * rnd.uniform(0.45, 0.62)); esp = int(dw * rnd.uniform(0.25, 0.5))
    gap = int(dw * rnd.uniform(0.8, 2.0)) if funcao else 0
    largura = len(rotulo) * (dw + esp) + gap + 40
    fundo = rnd.randint(120, 230) if rnd.random() < 0.7 else rnd.randint(10, 60)
    cor = max(0, fundo - rnd.randint(70, 140)) if fundo > 100 else min(255, fundo + rnd.randint(90, 200))
    img = np.full((dh + 30, largura), fundo, np.uint8)
    t = max(2, int(dw * rnd.uniform(0.12, 0.22))); inc = rnd.uniform(0, 0.15)
    xs, x = [], 20 + rnd.randint(-5, 5)
    for i in range(len(rotulo)):
        xs.append(x)
        x += dw + esp + (gap if funcao and i == len(funcao) - 1 else 0)
    if rnd.random() < 0.5:   # segmentos apagados ("fantasma") dos displays LCD: um "8" quase da cor do fundo
        fantasma = int(fundo + (cor - fundo) * rnd.uniform(0.04, 0.12))
        for xi in xs:
            _digito(img, xi, 15, dw, dh, t, "8", fantasma, inc)
    for xi, ch in zip(xs, rotulo):
        _digito(img, xi, 15, dw, dh, t, ch, int(cor), inc)
    return _sujar(img, rnd), rotulo


def _sujar(img, rnd):
    h, w = img.shape
    # gradiente de luz e reflexo
    g = np.linspace(rnd.uniform(-40, 40), rnd.uniform(-40, 40), w)[None].repeat(h, 0)
    img = np.clip(img + g, 0, 255).astype(np.uint8)
    # perspectiva leve
    d = 0.06
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[rnd.uniform(0, d) * w, rnd.uniform(0, d) * h], [w - rnd.uniform(0, d) * w, rnd.uniform(0, d) * h],
                      [w - rnd.uniform(0, d) * w, h - rnd.uniform(0, d) * h], [rnd.uniform(0, d) * w, h - rnd.uniform(0, d) * h]])
    img = cv2.warpPerspective(img, cv2.getPerspectiveTransform(src, dst), (w, h), borderMode=cv2.BORDER_REPLICATE)
    # baixa resolução (os recortes reais têm 30 a 60 px de altura), desfoque, ruído, JPEG
    esc = rnd.uniform(0.35, 0.9)
    img = cv2.resize(img, (max(8, int(w * esc)), max(8, int(h * esc))), interpolation=cv2.INTER_AREA)
    if rnd.random() < 0.7:
        k = rnd.choice([3, 3, 5]); img = cv2.GaussianBlur(img, (k, k), 0)
    img = np.clip(img + np.random.normal(0, rnd.uniform(2, 14), img.shape), 0, 255).astype(np.uint8)
    q = rnd.randint(25, 85)
    return cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])[1], cv2.IMREAD_GRAYSCALE)


# ---------- dados reais ----------

def aumentar(cinza, rnd):
    h, w = cinza.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rnd.uniform(-4, 4), rnd.uniform(0.92, 1.06))
    M[:, 2] += (rnd.uniform(-0.04, 0.04) * w, rnd.uniform(-0.06, 0.06) * h)
    r = cv2.warpAffine(cinza, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    r = cv2.convertScaleAbs(r, alpha=rnd.uniform(0.7, 1.3), beta=rnd.uniform(-30, 30))
    if rnd.random() < 0.3:
        r = cv2.GaussianBlur(r, (3, 3), 0)
    return r


def carregar_reais(pasta):
    linhas = list(csv.DictReader(open(pasta / "pseudo_treino.csv", encoding="utf-8")))
    dados = []
    for l in linhas:
        img = cv2.imread(str(pasta / "recortes" / "treino" / l["arquivo"]), cv2.IMREAD_GRAYSCALE)
        if img is not None and img.size:
            dados.append((l["arquivo"], img, l["rotulo"]))
    return dados


def lote(itens):
    x = torch.stack([preparar(i) for i, _ in itens])
    alvo = torch.tensor([ALFABETO.index(c) + 1 for _, r in itens for c in r], dtype=torch.long)
    comp = torch.tensor([len(r) for _, r in itens], dtype=torch.long)
    return x, alvo, comp


def avaliar(m, itens):
    m.eval()
    certos = 0
    with torch.no_grad():
        for i in range(0, len(itens), 128):
            parte = itens[i:i + 128]
            pred = decodificar(m(torch.stack([preparar(img) for img, _ in parte])))
            certos += sum(p == r for (p, _), (_, r) in zip(pred, parte))
    m.train()
    return certos / max(1, len(itens))


def main():
    pasta = Path(sys.argv[1])
    minutos = float(sys.argv[2]) if len(sys.argv) > 2 else 40
    rnd = random.Random(SEMENTE); np.random.seed(SEMENTE); torch.manual_seed(SEMENTE)
    torch.set_num_threads(max(1, torch.get_num_threads()))
    reais = carregar_reais(pasta)
    rnd.shuffle(reais)
    n_chk = max(50, len(reais) // 10)
    checagem = [(img, r) for _, img, r in reais[:n_chk]]
    treino = [(img, r) for _, img, r in reais[n_chk:]]
    sint_chk = [sintetico(random.Random(i)) for i in range(300)]
    print(f"{len(treino)} reais de treino, {len(checagem)} reais de checagem, sintéticos sob demanda", flush=True)

    m = CRNN()
    opt = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=1e-4)
    ctc = nn.CTCLoss(blank=0, zero_infinity=True)
    t0, passo, melhor = time.time(), 0, -1.0
    fim = t0 + minutos * 60
    total_passos = None
    while time.time() < fim:
        itens = [(aumentar(img, rnd), r) for img, r in rnd.sample(treino, min(32, len(treino)))] + \
                [sintetico(rnd) for _ in range(32)]
        x, alvo, comp = lote(itens)
        logp = m(x).log_softmax(-1).permute(1, 0, 2)    # (T, N, C)
        perda = ctc(logp, alvo, torch.full((len(itens),), logp.shape[0], dtype=torch.long), comp)
        opt.zero_grad(); perda.backward(); nn.utils.clip_grad_norm_(m.parameters(), 5.0); opt.step()
        # cosseno pelo tempo: lr cai até 5% no fim
        frac = min(1.0, (time.time() - t0) / (minutos * 60))
        for g in opt.param_groups:
            g["lr"] = 2e-3 * (0.05 + 0.95 * 0.5 * (1 + math.cos(math.pi * frac)))
        passo += 1
        if passo % 200 == 0:
            ac_r, ac_s = avaliar(m, checagem), avaliar(m, sint_chk)
            if ac_r > melhor:
                melhor = ac_r
                torch.save(m.state_dict(), pasta / "ctc_v0.pt")
            print(f"passo {passo}  {time.time() - t0:.0f}s  perda {perda.item():.3f}  "
                  f"checagem real {ac_r:.1%}  sintético {ac_s:.1%}  melhor real {melhor:.1%}", flush=True)
    ac_r = avaliar(m, checagem)
    if ac_r > melhor:
        melhor = ac_r; torch.save(m.state_dict(), pasta / "ctc_v0.pt")
    print(f"fim: {passo} passos, melhor acerto exato na checagem real {melhor:.1%} -> {pasta / 'ctc_v0.pt'}", flush=True)


if __name__ == "__main__":
    main()
