# -*- coding: utf-8 -*-
"""Leitor CTC v2 (item 12, 20/11/2026): transcrição manual + pseudo-rótulos reais + sintéticos.

O ctc_v1 (treinar_transcricao.py) usou só ~290 recortes transcritos e escolheu o modelo por uma checagem de 29:
leu a leitura certa em 56% da validação, mas, como passe extra do app, não trouxe nenhum Confere, porque a
confiança ficou abaixo de 0,90 em todos os acertos. O v2 acrescenta os 1.316 pseudo-rótulos reais do treino
(recortes em que o OCR leu exatamente a leitura do CSV, os mesmos do ctc_v0) e escolhe o modelo por uma
checagem maior (15% da transcrição de treino), pela leitura exata.

Lote: 16 transcritos + 16 pseudo-rótulos + 16 sintéticos. Começa do ctc_v0 (mesma inicialização do v1).
Validação (100 recortes da transcrição, 64 legíveis) medida uma vez no fim, contra o OCR, o ctc_v0 e o ctc_v1.

Uso (venv_app): python experiments/leitor_ctc/treinar_v2.py <pasta transcricao> <pasta leitor_digitos> [minutos=25]
Grava <pasta leitor_digitos>/ctc_v2.pt (fora do Git). Só imprime contagens.
"""
import math, random, re, sys, time
from pathlib import Path

import numpy as np
import torch, torch.nn as nn

sys.path.insert(0, str(Path(__file__).parent))
import treinar_ctc as v0
import treinar_transcricao as v1

SEMENTE = 7


def acerto_leitura(m, itens):
    return v1.placar(v1.ler(m, [i for i, _ in itens]), [r for _, r in itens])[1]


def main():
    pasta, pasta_ld = Path(sys.argv[1]), Path(sys.argv[2])
    minutos = float(sys.argv[3]) if len(sys.argv) > 3 else 25
    rnd = random.Random(SEMENTE); np.random.seed(SEMENTE); torch.manual_seed(SEMENTE)
    dados, fora = v1.carregar(pasta)
    tr = [(img, r) for img, r, _ in dados["treino"]]; rnd.shuffle(tr)
    n_chk = max(40, len(tr) * 15 // 100)
    chk, tr = tr[:n_chk], tr[n_chk:]
    pseudo = [(img, r) for _, img, r in v0.carregar_reais(pasta_ld)]
    print(f"transcritos: treino {len(tr)}, checagem {len(chk)}; pseudo-rótulos {len(pseudo)}; "
          f"validação {len(dados['validacao'])}; fora do formato {fora}", flush=True)

    m = v1.modelo_inicial(pasta_ld)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-4, weight_decay=1e-4)
    ctc = nn.CTCLoss(blank=0, zero_infinity=True)
    t0, passo, melhor = time.time(), 0, -1
    saida = pasta_ld / "ctc_v2.pt"
    while time.time() < t0 + minutos * 60:
        itens = ([(v0.aumentar(i, rnd), r) for i, r in rnd.sample(tr, 16)]
                 + [(v0.aumentar(i, rnd), r) for i, r in rnd.sample(pseudo, 16)]
                 + [v0.sintetico(rnd, espaco=True) for _ in range(16)])
        x, alvo, comp = v1.lote(itens)
        logp = m(x).log_softmax(-1).permute(1, 0, 2)
        perda = ctc(logp, alvo, torch.full((len(itens),), logp.shape[0], dtype=torch.long), comp)
        opt.zero_grad(); perda.backward(); nn.utils.clip_grad_norm_(m.parameters(), 5.0); opt.step()
        frac = min(1.0, (time.time() - t0) / (minutos * 60))
        for g in opt.param_groups:
            g["lr"] = 5e-4 * (0.05 + 0.95 * 0.5 * (1 + math.cos(math.pi * frac)))
        passo += 1
        if passo % 100 == 0:
            ac = acerto_leitura(m, chk)
            if ac > melhor:
                melhor = ac; torch.save(m.state_dict(), saida)
            print(f"passo {passo}  {time.time() - t0:.0f}s  perda {perda.item():.3f}  checagem {ac}/{len(chk)}  "
                  f"melhor {melhor}", flush=True)
    ac = acerto_leitura(m, chk)
    if ac > melhor:
        melhor = ac; torch.save(m.state_dict(), saida)
    print(f"fim: {passo} passos, melhor checagem {melhor}/{len(chk)} -> {saida}", flush=True)

    val = dados["validacao"]; imgs, rots = [i for i, _, _ in val], [r for _, r, _ in val]
    m.load_state_dict(torch.load(saida, map_location="cpu"))
    m0 = v0.CRNN(); m0.load_state_dict(torch.load(pasta_ld / "ctc_v0.pt", map_location="cpu"))
    m1 = v0.CRNN(classes=len(v1.ALFABETO) + 1); m1.load_state_dict(torch.load(pasta_ld / "ctc_v1.pt", map_location="cpu"))
    linhas = [("OCR atual (pré-preenchimento)", [" ".join(re.sub(r"[^\d ]", "", p).split()) for _, _, p in val]),
              ("ctc_v0", v1.ler(m0, imgs, alfabeto_v0=True)),
              ("ctc_v1 (só transcrição)", v1.ler(m1, imgs)),
              ("ctc_v2 (transcrição + pseudo)", v1.ler(m, imgs))]
    print(f"\nValidação: {len(val)} recortes legíveis")
    for nome, preds in linhas:
        tudo, so = v1.placar(preds, rots)
        print(f"  {nome:32s} texto exato {tudo:3d} ({tudo / len(val):.0%})   leitura exata {so:3d} ({so / len(val):.0%})")


if __name__ == "__main__":
    main()
