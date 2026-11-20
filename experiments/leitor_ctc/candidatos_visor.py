# -*- coding: utf-8 -*-
"""
Candidatos de leitura do leitor CTC nos recortes do visor, para a variante `visor_externo` de
experiments/passes_extras/passes_extras.py (item 12, 20/11/2026): o leitor treinado com a transcrição
traz Confere novos sem erro quando entra como mais um passe do app?

Recortes: os de passes_extras.py --recortes (mesma caixa e folga do app), ampliados 3x como na transcrição.
Confiança: produto das probabilidades dos símbolos emitidos (como o ctc_v0).

Uso (venv_app, raiz do repositório):
    python experiments/leitor_ctc/candidatos_visor.py <pasta dos recortes> <pasta leitor_digitos> <modelo: ctc_v0|ctc_v1> <saida.json>
"""
import json, sys
from pathlib import Path

import cv2
import torch

sys.path.insert(0, str(Path(__file__).parent))
import treinar_ctc as v0
import treinar_transcricao as v1


def decodificar(logits, alfabeto):
    p = logits.softmax(-1)
    best, idx = p.max(-1)
    saida = []
    for b, i in zip(best, idx):
        s, conf, ant = "", 1.0, 0
        for pb, k in zip(b.tolist(), i.tolist()):
            if k != ant and k != 0:
                s += alfabeto[k - 1]; conf *= pb
            ant = k
        s = " ".join(s.split())
        saida.append((s, conf if s else 0.0))
    return saida


def main():
    pasta, pasta_ld, nome, saida = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
    alfabeto = v0.ALFABETO if nome == "ctc_v0" else v1.ALFABETO
    m = v0.CRNN(classes=len(alfabeto) + 1)
    m.load_state_dict(torch.load(pasta_ld / f"{nome}.pt", map_location="cpu"))
    m.eval()
    res = {}
    with torch.no_grad():
        for p in sorted(pasta.glob("*.png")):
            cinza = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2GRAY)
            cinza = cv2.resize(cinza, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            texto, conf = decodificar(m(v0.preparar(cinza)[None]), alfabeto)[0]
            res[p.name] = [(texto, conf)] if texto else []
    saida.write_text(json.dumps(res), encoding="utf-8")
    print(f"{nome}: {len(res)} recortes, {sum(bool(v) for v in res.values())} com leitura")


if __name__ == "__main__":
    main()
