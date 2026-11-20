# -*- coding: utf-8 -*-
"""
Pipeline de inferência do GridVision sem interface: processa a pasta de fotos de um lote com o mesmo
código do app (app/pipeline.py), grava o CSV de resultados no formato da exportação e imprime o resumo.

Uso, da raiz do repositório:
    python app/processar.py PASTA_DAS_FOTOS [--csv INFORMADO.csv] [--saida RESULTADOS.csv] [--processos N]

Sem --saida, grava `resultados.csv` dentro da pasta das fotos. A saída tem nomes de fotos e leituras
(LGPD): o script recusa gravar dentro do repositório. Nenhuma decisão do analista é gravada no histórico.
Código de saída: 0 ok, 2 entrada inválida.
"""
import argparse, sys, time
from collections import Counter
from pathlib import Path

import pipeline as pl


def resumo(resultados):
    """Contagem por status e por destino (sem analista, excluídas, ao analista)."""
    status = Counter(r.status for r in resultados)
    auto = sum(status[s] for s in pl.AUTOMATICOS)
    excl = sum(status[s] for s in pl.EXCLUIDOS)
    return {"total": len(resultados), "status": dict(status), "confere": auto, "excluidas": excl,
            "analista": len(resultados) - auto - excl}


def _dentro_do_repositorio(caminho):
    try:
        Path(caminho).resolve().relative_to(pl.RAIZ)
        return True
    except ValueError:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="Processa um lote de fotos com o pipeline do GridVision.")
    ap.add_argument("pasta", type=Path, help="pasta com as fotos (.jpg, .jpeg, .png)")
    ap.add_argument("--csv", type=Path, help="CSV informado no formato da base (opcional)")
    ap.add_argument("--saida", type=Path, help="CSV de resultados (padrão: PASTA/resultados.csv)")
    ap.add_argument("--processos", type=int, default=None, help=f"processos em paralelo (padrão {pl.PROCESSOS})")
    a = ap.parse_args(argv)

    if not a.pasta.is_dir():
        print(f"erro: pasta não encontrada: {a.pasta}", file=sys.stderr)
        return 2
    if a.csv is not None and not a.csv.is_file():
        print(f"erro: CSV não encontrado: {a.csv}", file=sys.stderr)
        return 2
    if a.processos is not None and a.processos < 1:
        print("erro: --processos precisa ser 1 ou mais", file=sys.stderr)
        return 2
    saida = a.saida or a.pasta / "resultados.csv"
    if saida.is_dir():
        print(f"erro: --saida é uma pasta; indique o arquivo CSV: {saida}", file=sys.stderr)
        return 2
    if _dentro_do_repositorio(saida):
        print("erro: a saída tem nomes de fotos e leituras (LGPD); grave fora do repositório", file=sys.stderr)
        return 2
    fotos = pl.listar_fotos(a.pasta)
    if not fotos:
        print(f"erro: nenhuma foto em {a.pasta}", file=sys.stderr)
        return 2
    informado = pl.carregar_informado(a.csv) if a.csv else {}

    print(f"{len(fotos)} fotos, {sum(1 for f in fotos if f.name in informado)} com informado. "
          + ("Modelo real." if pl.MODELO_REAL else f"Extração SIMULADA ({pl.MOTIVO_SEM_MODELO})."))
    conj = pl.conjuntos_do_lote(fotos)
    if conj.get("treino"):
        print(f"atenção: {conj['treino']} fotos do treino (servem para demonstrar, não para medir)")
    if conj.get("teste", 0) + conj.get("teste_temporal", 0):
        print(f"atenção: {conj.get('teste', 0) + conj.get('teste_temporal', 0)} fotos do teste ou teste temporal "
              "(reservadas para a medida final)")

    t0 = time.monotonic()
    resultados = sorted(pl.processar_lote(fotos, informado, processos=a.processos), key=lambda r: r.arquivo)
    dt = time.monotonic() - t0
    saida.parent.mkdir(parents=True, exist_ok=True)
    pl.exportar(resultados, saida)

    s = resumo(resultados)
    n = s["total"]
    print(f"Processado em {dt:.1f} s ({dt / n:.2f} s por foto).")
    for st in pl.STATUS:
        if s["status"].get(st):
            print(f"  {st}: {s['status'][st]}")
    print(f"Sem analista: {s['confere'] + s['excluidas']} de {n} ({(s['confere'] + s['excluidas']) / n:.0%}): "
          f"{s['confere']} Confere, {s['excluidas']} excluídas. Ao analista: {s['analista']}.")
    print(f"Resultados em {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
