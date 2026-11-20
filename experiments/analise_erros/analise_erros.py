# -*- coding: utf-8 -*-
"""
Análise de erros do pipeline atual do app (item 12): por que uma foto com a leitura legível não vira "Confere"?

Gabarito: as decisões do analista gravadas no histórico do app (`Corrigido` ou `Confirmado`, com a leitura
verdadeira digitada ou confirmada). Só fotos da validação (teste e teste temporal ficam de fora). As fotos
marcadas "Ilegível" pelo analista não entram: não têm leitura verdadeira.

Para cada foto, roda o pipeline do app (mesmo status do app) e reabre os passes do OCR para ver todos os
candidatos de leitura dentro do visor, e classifica a causa na primeira regra que se aplica:

  sem leitura informada        a foto não tem leitura no CSV: vai ao analista como "Lido" (comportamento certo)
  CSV difere da leitura real   o informado não é o que o visor mostra: não pode conferir (comportamento certo)
  detector sem visor           o detector não achou o visor
  OCR sem dígitos no visor     nenhum passe leu dígitos dentro do visor
  OCR leu outro valor          há candidatos, mas nenhum igual à leitura verdadeira
  função recusada              a leitura certa só aparece com código de função que não é de consumo
  leitura certa descartada     a leitura certa estava entre os candidatos, mas a extração escolheu outra ou nenhuma
  negada pelo classificador    a leitura certa estava entre os candidatos, mas a foto saiu como ilegível
  confiança abaixo de 0,90     leitura certa escolhida, mas a confiança (menor entre leitura e número) não basta
  número do medidor não lido   leitura certa, mas o número não foi achado (Só a leitura confere ou Ilegível)
  número lido diferente        o número lido não bate com o informado

Uso (ambiente do app, raiz do repositório):
    python experiments/analise_erros/analise_erros.py [<gridvision_dados>]

Curva do limiar de confiança: inclui também as fotos que o analista marcou "Ilegível". Um "Confere" numa
delas conta como erro (bateu por coincidência, não dá para provar o valor), a mesma regra de medir_mvp.py.
O app não muda: a escolha do limiar é do grupo.

Saída por foto em <gridvision_dados>/analise_erros/detalhe.csv (fora do Git: tem nomes e leituras).
No terminal, só contagens.
"""
import csv, sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
import pipeline as pl

m = pl._modelo
DADOS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "gridvision_dados"
CAUSAS = ["sem leitura informada", "CSV difere da leitura real", "detector sem visor", "OCR sem dígitos no visor", "OCR leu outro valor",
          "função recusada", "leitura certa descartada", "negada pelo classificador", "confiança abaixo de 0,90", "número do medidor não lido",
          "número lido diferente", "outra"]


LIMIARES = [0.0, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]


def historico_validacao():
    """Decisões do analista (a mais recente de cada foto) só em fotos da validação que ainda estão no disco."""
    conj = {l["arquivo"]: l["conjunto"] for l in
            csv.DictReader(open(RAIZ / "experiments" / "piloto_anotacao" / "divisao_v1.csv", encoding="utf-8"))}
    return [r for r in pl.carregar_historico()
            if conj.get(r.arquivo) == "validacao" and Path(r.caminho).exists()]


def legivel(h):
    return h.decisao in ("Corrigido", "Confirmado") and bool(h.leitura_final)


def candidatos_leitura(caminho):
    """(tem visor, [(leitura normalizada, confiança, função)]) com os mesmos passes e regras de extracao.py."""
    import cv2
    img = cv2.imread(str(caminho))
    melhor = m.detectar(img)
    visor = melhor.get("visor", (None, 0))[0]
    placa = melhor.get("placa", (None, 0))[0]
    if visor is None:
        return False, []
    passes = m._passes(img, visor, placa)
    cands = [c for regiao, ts in passes if regiao != "placa"
             for c in m._leituras_do_visor(ts if regiao == "visor" else [t for t in ts if m._dentro(t["centro"], visor)])]
    return True, [(m.normalizar_leitura(d), c, f) for d, c, f in cands]


def causa(r, verdade, tem_visor, cands):
    if not r.leitura_informada:
        return "sem leitura informada"
    if r.leitura_informada and m.normalizar_leitura(r.leitura_informada) != verdade:
        return "CSV difere da leitura real"
    if not tem_visor:
        return "detector sem visor"
    if not cands:
        return "OCR sem dígitos no visor"
    certos = [c for c in cands if c[0] == verdade]
    if not certos:
        return "OCR leu outro valor"
    if all(f is not None and f not in m.FUNCOES_LEITURA for _, _, f in certos):
        return "função recusada"
    if r.leitura_lida != verdade:
        return "leitura certa descartada"
    if r.status == pl.ILEGIVEL_CERTO:
        return "negada pelo classificador"
    if r.status == pl.REVISAO:
        return "confiança abaixo de 0,90"
    if not r.numero_lido or r.status == pl.SO_LEITURA:
        return "número do medidor não lido"
    if r.status == pl.DIVERGE:
        return "número lido diferente"
    return "outra"


def main():
    if not pl.MODELO_REAL:
        sys.exit(f"precisa do modelo real ({pl.MOTIVO_SEM_MODELO})")
    hist = historico_validacao()
    gab = [h for h in hist if legivel(h)]
    ilegiveis = [h for h in hist if h.decisao == "Ilegível"]
    linhas, causas, status, curva = [], Counter(), Counter(), []
    for h in hist:
        inf = (h.numero_informado, h.leitura_informada) if h.leitura_informada or h.numero_informado else None
        ext = pl.extrair(h.caminho, inf)
        st = pl.decidir(ext, inf)[0]
        limiar_app = pl.LIMIAR_CONFIANCA
        pl.LIMIAR_CONFIANCA = 0.0  # status sem a trava de confiança, para a curva
        try:
            st0 = pl.decidir(ext, inf)[0]
        finally:
            pl.LIMIAR_CONFIANCA = limiar_app
        if st0 == pl.CONFERE:
            certo = legivel(h) and ext.leitura == m.normalizar_leitura(h.leitura_final)
            curva.append((ext.confianca, certo))
        if not legivel(h):
            continue
        r = pl.Resultado(h.arquivo, h.caminho, 0, ext.numero, ext.leitura, ext.confianca, *(inf or ("", "")), st, "")
        verdade = m.normalizar_leitura(h.leitura_final)
        tem_visor, cands = candidatos_leitura(h.caminho)
        status[st] += 1
        c = "" if st == pl.CONFERE else causa(r, verdade, tem_visor, cands)
        if c:
            causas[c] += 1
        conf_certa = max((cf for d, cf, _ in cands if d == verdade), default=None)
        linhas.append({"arquivo": h.arquivo, "decisao_analista": h.decisao, "status_atual": st, "causa": c,
                       "leitura_verdadeira": verdade, "leitura_lida": ext.leitura,
                       "leitura_informada": r.leitura_informada, "numero_lido": ext.numero,
                       "numero_informado": r.numero_informado, "confianca": f"{ext.confianca:.3f}",
                       "conf_leitura_certa": "" if conf_certa is None else f"{conf_certa:.3f}",
                       "prob_legivel": f"{ext.prob_legivel:.3f}", "n_candidatos": len(cands)})
    saida = DADOS / "analise_erros" / "detalhe.csv"
    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]), delimiter=";")
        w.writeheader()
        w.writerows(linhas)

    n = len(gab)
    print(f"{n} fotos com leitura verdadeira (analista: {dict(Counter(h.decisao for h in gab))}); "
          f"{len(ilegiveis)} marcadas ilegíveis")
    print("Status atual:", dict(status.most_common()))
    print(f"Confere: {status[pl.CONFERE]} de {n}. Causas nas outras {n - status[pl.CONFERE]}:")
    for c in CAUSAS:
        if causas[c]:
            print(f"  {c}: {causas[c]}")
    csv_dif = Counter(l["status_atual"] for l in linhas if l["causa"] == "CSV difere da leitura real")
    print(f"  (CSV difere, status: {dict(csv_dif)})")
    # Confere errado: conferiu, mas a leitura verdadeira é outra (o que o erro zero proíbe)
    errados = sum(1 for l in linhas if l["status_atual"] == pl.CONFERE and l["leitura_lida"] != l["leitura_verdadeira"])
    print(f"Confere com leitura diferente da do analista: {errados}")
    confs = sorted(float(l["confianca"]) for l in linhas if l["causa"] == "confiança abaixo de 0,90")
    if confs:
        print(f"Confiança nas paradas por confiança: mín {confs[0]:.2f}, mediana {confs[len(confs) // 2]:.2f}, "
              f"máx {confs[-1]:.2f}")
    # gargalo nas fotos que podem conferir: com leitura informada igual à verdadeira
    podem = [l for l in linhas if l["leitura_informada"] and m.normalizar_leitura(l["leitura_informada"]) == l["leitura_verdadeira"]]
    leit = [l["leitura_lida"] == l["leitura_verdadeira"] for l in podem]
    num = [pl.mesmo_numero(l["numero_lido"], l["numero_informado"]) for l in podem]
    print(f"Podem conferir (CSV = leitura real): {len(podem)}. Leitura certa {sum(leit)}, número igual ao informado "
          f"{sum(num)}, os dois {sum(a and b for a, b in zip(leit, num))}; leitura certa entre os candidatos "
          f"{sum(bool(l['conf_leitura_certa']) for l in podem)}; número vazio {sum(not l['numero_lido'] for l in podem)}, "
          f"diferente {sum(bool(l['numero_lido']) and not b for l, b in zip(podem, num))}")
    sem_inf = Counter(l["status_atual"] for l in linhas if l["causa"] == "sem leitura informada")
    print(f"  (sem leitura informada, status: {dict(sem_inf)})")
    print(f"Curva do limiar ({len(hist)} fotos; erro = Confere em foto ilegível ou com outra leitura):")
    for t in LIMIARES:
        ok = [certo for c, certo in curva if c >= t]
        print(f"  {t:.2f}: {len(ok)} Confere, {len(ok) - sum(ok)} erro(s)")
    print(f"Detalhe por foto em {saida}")


if __name__ == "__main__":
    main()
