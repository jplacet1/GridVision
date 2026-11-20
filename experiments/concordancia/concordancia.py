# -*- coding: utf-8 -*-
"""
Regra de concordância (item 12, 20/11/2026): aceitar a leitura com confiança baixa quando vários passes
independentes leem o mesmo valor, e esse valor é o do CSV?

Hoje o Confere exige confiança de 0,90 ou mais (a menor entre leitura e número). Na análise de erros, os leitores
acertam leituras com confiança menor (o ctc_v1 acertou 6 das 22 fotos em que só a leitura falhava, todas abaixo
de 0,90). A ideia: um único passe pode coincidir com o CSV por acaso; vários passes diferentes coincidirem numa
foto ilegível é muito menos provável.

Regra medida (fora do app, nada muda nele):
  Confere se o número do medidor bate com o CSV com confiança >= 0,90 (como hoje), e a leitura do CSV aparece
  em pelo menos k passes distintos (OCR v6 e v5 na foto e no recorte do visor; opcionalmente o leitor CTC),
  com qualquer confiança, fora de função que não seja de consumo.
Os passes do OCR olham a mesma imagem, então não são independentes de verdade: por isso o critério é o erro
medido nas fotos ilegíveis do gabarito, não um cálculo de probabilidade.

Gabarito: o de experiments/passes_extras (162 decisões do histórico + 228 fotos da revisão cega, validação).
Erro = Confere em foto cuja leitura é ilegível pelo gabarito, ou com leitura diferente da verdadeira.

Uso (venv_app, raiz do repositório):
    python experiments/concordancia/concordancia.py <export_revisao_cega.json> [ctc.json]
"""
import json, sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "experiments" / "passes_extras"))
import passes_extras as pe  # gabarito e o pipeline do app (os passes extras ficam desligados aqui)

pl, m = pe.pl, pe.m


def fontes_da_leitura(img, visor, placa, alvo, ctc):
    """Passes distintos em que a leitura do CSV aparece entre os candidatos do visor."""
    passes = pe._passes_app(img, visor, placa)
    achou = set()
    for i, (regiao, ts) in enumerate(passes):
        if regiao == "placa" or visor is None:
            continue
        no_visor = ts if regiao == "visor" else [t for t in ts if m._dentro(t["centro"], visor)]
        for d, c, f in m._leituras_do_visor(no_visor):
            if (f is None or f in m.FUNCOES_LEITURA) and m.normalizar_leitura(d) == alvo:
                achou.add(i)
    for t, c in ctc:
        d = m._digitos(t.split()[-1]) if " " in t else m._digitos(t)
        cands = {m.normalizar_leitura(d)}
        if " " not in t:
            cands |= {m.normalizar_leitura(d[2:]), m.normalizar_leitura(d[3:])}
        if alvo in cands:
            achou.add("ctc")
    return achou


def main():
    if not pl.MODELO_REAL or m.motor_ocr() != "onnx":
        sys.exit("precisa do modelo real com o motor ONNX")
    import cv2
    gab = pe.gabarito(sys.argv[1])
    ctc = {}
    if len(sys.argv) > 2:
        ctc = {k.replace(".png", ".jpg"): v for k, v in json.load(open(sys.argv[2], encoding="utf-8")).items()}
    pe.VARIANTES_ATIVAS.clear()
    linhas, novos_perfil = [], []
    for caminho, inf, leg, verdade, fonte in gab:
        nome = Path(caminho).name
        ext = pl.extrair(caminho, inf)
        st = pl.decidir(ext, inf)[0]
        num_inf, leit_inf = inf or ("", "")
        alvo = m.normalizar_leitura(leit_inf)
        n_fontes, num_ok = 0, False
        if ext.tem_medidor and alvo and ext.numero and pl.mesmo_numero(ext.numero, num_inf):
            img = cv2.imread(caminho)
            det = m.detectar(img)
            visor, placa = det.get("visor", (None, 0))[0], det.get("placa", (None, 0))[0]
            # confiança do número: a maior entre os textos fora do visor que contêm o número lido (aproxima a do app,
            # que olha a placa primeiro) e o código de barras
            textos = [t for r, ts in pe._passes_app(img, visor, placa) if r != "visor" for t in ts]
            conf_n = max([t["conf"] for t in textos if ext.numero in m._digitos(t["texto"])] + [0.0])
            from gridvision import codigo_barras
            if any(ext.numero in m._digitos(c) for c in codigo_barras.ler(img)):
                conf_n = max(conf_n, m.CONF_CODIGO_BARRAS)
            num_ok = conf_n >= pl.LIMIAR_CONFIANCA
            n_fontes = len(fontes_da_leitura(img, visor, placa, alvo, ctc.get(nome, [])))
        linhas.append((nome, st, leg, verdade, alvo, num_ok, n_fontes))
        if num_ok and n_fontes and st != pl.CONFERE:
            so_ctc = fontes_da_leitura(img, visor, placa, alvo, []) == set()
            novos_perfil.append((len(alvo), so_ctc, leg))

    def erro(l, confere):
        nome, st, leg, verdade, alvo, *_ = l
        return confere and (not leg or bool(verdade and alvo != verdade))

    print(f"{len(linhas)} fotos ({sum(l[2] for l in linhas)} legíveis); fonte CTC: {'sim' if ctc else 'não'}")
    base = {l[0] for l in linhas if l[1] == pl.CONFERE}
    print(f"app atual: {len(base)} Confere, {sum(erro(l, True) for l in linhas if l[0] in base)} erro(s)")
    for k in (1, 2, 3, 4):
        novo = {l[0] for l in linhas if l[5] and l[6] >= k}
        total = base | novo
        err = sum(erro(l, True) for l in linhas if l[0] in total)
        print(f"  app + concordância em >= {k} passes: {len(total)} Confere (novos {len(total - base)}), {err} erro(s)")
    print("Novos com >= 1 passe (dígitos da leitura, só o CTC achou, legível):", sorted(novos_perfil))
    print("Fontes da leitura nas fotos com número ok, por gabarito:",
          dict(Counter((l[2], min(l[6], 4)) for l in linhas if l[5])))


if __name__ == "__main__":
    main()
