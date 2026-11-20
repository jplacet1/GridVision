# -*- coding: utf-8 -*-
"""Leitor CTC v1: ajuste fino do ctc_v0 com a transcrição manual do visor (item 12a, 20/11/2026).

Rótulo = texto transcrito no projeto 7 do Label Studio ("03 007237" ou só "007237"), com o espaço como
símbolo: o leitor separa sozinho a função da leitura, sem precisar da caixa na hora de usar. Só entram as
tarefas com situação "legível, é o consumo" (nas outras, o texto pré-preenchido é ignorado; ver README do
leitor_digitos) e texto no formato "dígitos" ou "dígitos espaço dígitos".

Entrada: o recorte do visor da transcrição (o mesmo do detector, ampliado 3x), como no app.
Escolha do modelo: 10% do treino (checagem). A validação só é medida no fim, uma vez, contra:
- o OCR atual no mesmo recorte (o texto que pré-preencheu a tarefa, predicoes.json);
- o ctc_v0.

Uso (ambiente do app): python experiments/leitor_ctc/treinar_transcricao.py <pasta transcricao> <pasta leitor_digitos> [minutos=20]
Grava <pasta leitor_digitos>/ctc_v1.pt (fora do Git). Só imprime contagens.
"""
import json, math, random, re, sys, time
from pathlib import Path
import cv2, numpy as np
import torch, torch.nn as nn

sys.path.insert(0, str(Path(__file__).parent))
import treinar_ctc as v0

ALFABETO = "0123456789 "
SEMENTE = 42


def rotulo(texto):
    """Texto transcrito -> rótulo, ou None fora do formato aceito."""
    g = texto.split()
    if not (1 <= len(g) <= 2) or not all(x.isdigit() for x in g):
        return None
    return " ".join(g)


def leitura(r):
    return r.split()[-1] if r else ""


def carregar(pasta):
    ex = json.load(open(pasta / "export_20261120.json", encoding="utf-8"))
    pred = json.load(open(pasta / "predicoes.json", encoding="utf-8"))
    fotos = {f.stem: f for f in pasta.glob("fotos/parte*/*.png")}
    dados, fora = {"treino": [], "validacao": []}, 0
    for o in ex:
        res = o["result"]
        sit = next((x["value"]["choices"][0] for x in res if x["from_name"] == "situacao"), "")
        if not sit.startswith("leg"):
            continue
        r = rotulo(next((x["value"]["text"][0] for x in res if x["from_name"] == "texto"), ""))
        img = cv2.imread(str(fotos[o["nome"]]), cv2.IMREAD_GRAYSCALE)
        if r is None or img is None:
            fora += 1; continue
        p = pred.get(o["nome"] + ".png", "")
        dados[o["conjunto"]].append((img, r, p["texto"] if isinstance(p, dict) else p))
    return dados, fora


def lote(itens):
    x = torch.stack([v0.preparar(i) for i, _ in itens])
    alvo = torch.tensor([ALFABETO.index(c) + 1 for _, r in itens for c in r], dtype=torch.long)
    comp = torch.tensor([len(r) for _, r in itens], dtype=torch.long)
    return x, alvo, comp


def decodificar(logits):
    p = logits.softmax(-1)
    out = []
    for i in p.argmax(-1):
        s, ant = "", 0
        for k in i.tolist():
            if k != ant and k != 0:
                s += ALFABETO[k - 1]
            ant = k
        out.append(" ".join(s.split()))
    return out


@torch.no_grad()
def ler(m, imgs, alfabeto_v0=False):
    m.eval(); out = []
    for i in range(0, len(imgs), 128):
        lg = m(torch.stack([v0.preparar(x) for x in imgs[i:i + 128]]))
        out += [s for s, _ in v0.decodificar(lg)] if alfabeto_v0 else decodificar(lg)
    m.train()
    return out


def placar(preds, rotulos):
    """Acerto exato do texto todo e da leitura (último grupo; sem o espaço, a leitura tem que ser o fim)."""
    tudo = sum(" ".join(p.split()) == r for p, r in zip(preds, rotulos))
    return tudo, sum(acerta_leitura(p, r) for p, r in zip(preds, rotulos))


def acerta_leitura(p, r):
    # sem espaço (ctc_v0, OCR que juntou tudo) a leitura só precisa ser o fim do texto: critério a favor deles
    return leitura(p) == leitura(r) if " " in p else bool(p) and p.endswith(leitura(r))


assert rotulo(" 03  007237 ") == "03 007237" and rotulo("03 0072 37") is None and rotulo("03x") is None
assert acerta_leitura("03 007237", "007237") and acerta_leitura("03007237", "03 007237") and not acerta_leitura("", "1")


def modelo_inicial(pasta_ld):
    m = v0.CRNN(classes=len(ALFABETO) + 1)
    sd = torch.load(pasta_ld / "ctc_v0.pt", map_location="cpu")
    w, b = sd.pop("saida.weight"), sd.pop("saida.bias")
    m.load_state_dict(sd, strict=False)
    with torch.no_grad():  # branco e dígitos herdam a saída do v0; o espaço começa do zero
        m.saida.weight[:11] = w; m.saida.bias[:11] = b
    return m


def main():
    pasta, pasta_ld = Path(sys.argv[1]), Path(sys.argv[2])
    minutos = float(sys.argv[3]) if len(sys.argv) > 3 else 20
    rnd = random.Random(SEMENTE); np.random.seed(SEMENTE); torch.manual_seed(SEMENTE)
    dados, fora = carregar(pasta)
    tr = dados["treino"][:]; rnd.shuffle(tr)
    n_chk = max(25, len(tr) // 10)
    chk, tr = tr[:n_chk], tr[n_chk:]
    print(f"treino {len(tr)}, checagem {len(chk)}, validação {len(dados['validacao'])}, fora do formato {fora}", flush=True)

    m = modelo_inicial(pasta_ld)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-4, weight_decay=1e-4)
    ctc = nn.CTCLoss(blank=0, zero_infinity=True)
    t0, passo, melhor = time.time(), 0, -1
    saida = pasta_ld / "ctc_v1.pt"
    while time.time() < t0 + minutos * 60:
        itens = [(v0.aumentar(img, rnd), r) for img, r, _ in rnd.sample(tr, min(32, len(tr)))] + \
                [v0.sintetico(rnd, espaco=True) for _ in range(16)]
        x, alvo, comp = lote(itens)
        logp = m(x).log_softmax(-1).permute(1, 0, 2)
        perda = ctc(logp, alvo, torch.full((len(itens),), logp.shape[0], dtype=torch.long), comp)
        opt.zero_grad(); perda.backward(); nn.utils.clip_grad_norm_(m.parameters(), 5.0); opt.step()
        frac = min(1.0, (time.time() - t0) / (minutos * 60))
        for g in opt.param_groups:
            g["lr"] = 5e-4 * (0.05 + 0.95 * 0.5 * (1 + math.cos(math.pi * frac)))
        passo += 1
        if passo % 100 == 0:
            ac = placar(ler(m, [i for i, _, _ in chk]), [r for _, r, _ in chk])[0]
            if ac > melhor:
                melhor = ac; torch.save(m.state_dict(), saida)
            print(f"passo {passo}  {time.time() - t0:.0f}s  perda {perda.item():.3f}  checagem {ac}/{len(chk)}  melhor {melhor}", flush=True)

    ac = placar(ler(m, [i for i, _, _ in chk]), [r for _, r, _ in chk])[0]
    if ac > melhor:
        melhor = ac; torch.save(m.state_dict(), saida)
    print(f"fim: {passo} passos, melhor checagem {melhor}/{len(chk)} -> {saida}", flush=True)

    # medida única na validação
    val = dados["validacao"]; imgs, rots = [i for i, _, _ in val], [r for _, r, _ in val]
    m.load_state_dict(torch.load(saida, map_location="cpu"))
    m0 = v0.CRNN(); m0.load_state_dict(torch.load(pasta_ld / "ctc_v0.pt", map_location="cpu"))
    linhas = [("OCR atual (pré-preenchimento)", [" ".join(re.sub(r"[^\d ]", "", p).split()) for _, _, p in val]),
              ("ctc_v0", ler(m0, imgs, alfabeto_v0=True)),
              ("ctc_v1 (transcrição)", ler(m, imgs))]
    print(f"\nValidação: {len(val)} recortes legíveis")
    for nome, preds in linhas:
        tudo, so = placar(preds, rots)
        print(f"  {nome:32s} texto exato {tudo:3d} ({tudo / len(val):.0%})   leitura exata {so:3d} ({so / len(val):.0%})")


if __name__ == "__main__":
    main()
