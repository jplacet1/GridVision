# -*- coding: utf-8 -*-
"""
Testes funcionais do MVP (item 16): o lote inteiro passando pelo pipeline, a exportação, o CLI e a interface.
Rodar da raiz do repositório: python -m unittest discover app

- Fotos sintéticas (geradas aqui, sem dado do cliente): rodam em qualquer máquina, com extração simulada.
- Com o modelo real instalado: uma foto sintética passa pelo modelo sem erro.
- Regressão no lote_demo3 (30 fotos da validação, fora do Git): só roda onde a pasta existe e o modelo real
  carrega. Compara a contagem por status com a medida de 20/11/2026 (motor ONNX, classificador v1, limiar 0,40).
"""
import csv, io, os, tempfile, unittest
from collections import Counter
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw, ImageFilter

import pipeline as pl
import processar

LOTE_REGRESSAO = Path(os.environ.get("GRIDVISION_LOTE_REGRESSAO",
                                     Path.home() / "gridvision_dados" / "lote_demo3"))
ESPERADO_REGRESSAO = {pl.CONFERE: 8, pl.DIVERGE: 4, pl.REVISAO: 6, pl.ILEGIVEL: 3, pl.ILEGIVEL_CERTO: 8,
                      pl.SEM_MEDIDOR: 1}


def foto_sintetica(caminho, texto="042884", borrar=False):
    """Retrato 360 x 480, como as fotos da base, com um "visor" escuro e dígitos claros."""
    im = Image.new("RGB", (360, 480), (120, 125, 130))
    d = ImageDraw.Draw(im)
    d.rectangle((60, 180, 300, 260), fill=(20, 30, 20))
    d.text((90, 210), texto, fill=(200, 255, 200))
    if borrar:
        im = im.filter(ImageFilter.GaussianBlur(6))
    im.save(caminho, quality=90)


def lote_sintetico(pasta, n=8):
    """n fotos (metade borradas), uma foto corrompida e o CSV informado de todas menos a última boa."""
    pasta = Path(pasta)
    nomes = [f"foto_{i:02d}_000.jpg" for i in range(n)]
    for i, nome in enumerate(nomes):
        foto_sintetica(pasta / nome, f"{1000 + i:06d}", borrar=i % 2 == 1)
    (pasta / "corrompida_000.jpg").write_bytes(b"isto nao e um jpeg")
    csv_inf = pasta / "informado.csv"
    with open(csv_inf, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Numero do medidor", "Posicao do medidor lida", "Nota de Leitura Atual", "Foto do medidor"])
        for i, nome in enumerate(nomes[:-1]):
            w.writerow([f"{12345678 + i}", str(1000 + i), "NA", nome])
        w.writerow(["999", "1", "NA", "NA"])  # registro sem foto, como na base
    return nomes, csv_inf


def rodar_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        codigo = processar.main([str(a) for a in args])
    return codigo, out.getvalue(), err.getvalue()


class TestLoteSimulado(unittest.TestCase):
    """Fluxo completo com extração simulada: lote, decisão, exportação e CLI."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.tmp.name) / "lote"
        self.pasta.mkdir()
        self.nomes, self.csv = lote_sintetico(self.pasta)
        self.simulado = mock.patch.object(pl, "MODELO_REAL", False)
        self.simulado.start()

    def tearDown(self):
        self.simulado.stop()
        self.tmp.cleanup()

    def test_lote_inteiro_e_exportacao(self):
        fotos = pl.listar_fotos(self.pasta)
        self.assertEqual(len(fotos), len(self.nomes) + 1)  # o CSV não entra como foto
        informado = pl.carregar_informado(self.csv)
        self.assertEqual(len(informado), len(self.nomes) - 1)  # "NA" na coluna da foto não vira chave
        res = list(pl.processar_lote(fotos, informado))
        self.assertEqual(len(res), len(fotos))
        self.assertTrue(all(r.status in pl.STATUS for r in res))
        ruim = next(r for r in res if r.arquivo == "corrompida_000.jpg")
        self.assertEqual(ruim.status, pl.REVISAO)  # foto que não abre vai ao analista, não derruba o lote
        self.assertIn("erro ao processar", ruim.motivo)
        sem_inf = next(r for r in res if r.arquivo == self.nomes[-1])
        self.assertEqual(sem_inf.leitura_informada, "")
        self.assertNotEqual(sem_inf.status, pl.CONFERE)  # sem informado nunca confere sozinho

        saida = Path(self.tmp.name) / "exp.csv"
        pl.exportar(res, saida)
        with open(saida, encoding="utf-8-sig", newline="") as f:
            linhas = list(csv.DictReader(f, delimiter=";"))
        self.assertEqual(len(linhas), len(res))
        self.assertNotIn("caminho", linhas[0])  # caminho local não sai na exportação
        for l in linhas:
            if l["status"] in pl.EXCLUIDOS:
                self.assertTrue(l["decisao"].startswith("Excluída"))

    def test_cli_grava_resultados_e_resumo(self):
        saida = Path(self.tmp.name) / "saida" / "resultados.csv"
        codigo, out, _ = rodar_cli(self.pasta, "--csv", self.csv, "--saida", saida, "--processos", "1")
        self.assertEqual(codigo, 0)
        self.assertIn("SIMULADA", out)
        self.assertIn(f"{len(self.nomes) + 1} fotos", out)
        with open(saida, encoding="utf-8-sig", newline="") as f:
            status = Counter(l["status"] for l in csv.DictReader(f, delimiter=";"))
        self.assertEqual(sum(status.values()), len(self.nomes) + 1)
        s = processar.resumo([pl.Resultado("a", "a", 0, "", "", 0, "", "", st, "") for st in status.elements()])
        self.assertIn(f"Sem analista: {s['confere'] + s['excluidas']} de {s['total']}", out)

    def test_cli_recusa_entrada_invalida(self):
        self.assertEqual(rodar_cli(Path(self.tmp.name) / "nao_existe")[0], 2)
        self.assertEqual(rodar_cli(self.pasta, "--csv", Path(self.tmp.name) / "nao_existe.csv")[0], 2)
        vazia = Path(self.tmp.name) / "vazia"
        vazia.mkdir()
        self.assertEqual(rodar_cli(vazia, "--saida", Path(self.tmp.name) / "x.csv")[0], 2)
        self.assertEqual(rodar_cli(self.pasta, "--saida", vazia)[0], 2)  # saída é uma pasta
        self.assertEqual(rodar_cli(self.pasta, "--processos", "0", "--saida", Path(self.tmp.name) / "x.csv")[0], 2)

    def test_cli_nao_grava_no_repositorio(self):
        destino = pl.RAIZ / "resultados_teste.csv"
        codigo, _, err = rodar_cli(self.pasta, "--saida", destino)
        self.assertEqual(codigo, 2)
        self.assertIn("LGPD", err)
        self.assertFalse(destino.exists())


@unittest.skipUnless(pl.MODELO_REAL, f"modelo real indisponível ({pl.MOTIVO_SEM_MODELO})")
class TestModeloReal(unittest.TestCase):
    def test_foto_sintetica_passa_pelo_modelo(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "sintetica_000.jpg"
            foto_sintetica(p)
            r = pl.processar(p, ("12345678", "42884"))
        self.assertIn(r.status, pl.STATUS)
        self.assertNotIn("erro ao processar", r.motivo)
        self.assertNotEqual(r.status, pl.CONFERE)  # foto sem medidor de verdade não pode conferir


@unittest.skipUnless(pl.MODELO_REAL and (LOTE_REGRESSAO / "fotos").is_dir(),
                     "regressão só roda com o modelo real e o lote_demo3 local")
class TestRegressaoLoteDemo3(unittest.TestCase):
    def test_contagem_por_status(self):
        fotos = pl.listar_fotos(LOTE_REGRESSAO / "fotos")
        informado = pl.carregar_informado(LOTE_REGRESSAO / "informado.csv")
        res = list(pl.processar_lote(fotos, informado))  # em paralelo, como no app
        self.assertEqual(len(res), 30)
        self.assertEqual(dict(Counter(r.status for r in res)), ESPERADO_REGRESSAO)


class TestInterface(unittest.TestCase):
    """Abre a janela de verdade, passa por todas as telas e confere ícones de status e miniaturas (12c)."""

    @classmethod
    def setUpClass(cls):
        try:
            import main
        except Exception as e:  # sem Tk ou sem ttkbootstrap
            raise unittest.SkipTest(f"interface indisponível: {e}")
        cls.main = main

    def test_telas_icones_e_miniaturas(self):
        main = self.main
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            fotos = []
            for i in range(3):
                fotos.append(d / f"f{i}.jpg")
                foto_sintetica(fotos[-1])
            status = [pl.CONFERE, pl.SEM_MEDIDOR, pl.DIVERGE]
            res = [pl.Resultado(f.name, str(f), 200, "1", "10", 0.95, "1", "10", s, "m", lote="l")
                   for f, s in zip(fotos, status)]
            res.append(pl.Resultado("sumiu.jpg", str(d / "sumiu.jpg"), 200, "", "", 0, "", "", pl.CONFERE, "m"))
            with mock.patch.object(pl, "HISTORICO", d / "historico.csv"), \
                    mock.patch.object(main, "PREFERENCIAS", d / "interface.json"):
                app = main.App()
                try:
                    app.withdraw()
                    app.resultados, app.total_lote = res, len(res)
                    for tela in main.ETAPAS + ["Histórico"]:
                        app.ir(tela)
                        app.update_idletasks()
                    app.ir("Resultados")
                    tv = app.res_tabela
                    itens = {tv.item(i, "values")[0]: tv.item(i) for i in tv.get_children()}
                    # pendente (Diverge sem decisão) não aparece em Resultados
                    self.assertEqual(set(itens), {"f0.jpg", "f1.jpg", "sumiu.jpg"})
                    self.assertTrue(itens["f0.jpg"]["image"])     # miniatura da foto
                    self.assertFalse(itens["sumiu.jpg"]["image"])  # foto que não abre fica sem miniatura
                    self.assertEqual(itens["f0.jpg"]["values"][2], "✔ Confere")
                    self.assertEqual(itens["f1.jpg"]["values"][2], "— Sem medidor")
                    app.ir("Revisão")
                    fila = [app.fila_tv.item(i, "values") for i in app.fila_tv.get_children()]
                    self.assertEqual([tuple(v) for v in fila], [("f2.jpg", "✖ Diverge")])
                    self.assertTrue(app.txt_status.cget("text").startswith("✖ Diverge"))
                    self.assertEqual(set(main.ICONE_STATUS), set(pl.STATUS))  # todo status tem ícone
                finally:
                    app.destroy()
            self.assertFalse((d / "historico.csv").exists())  # navegar não grava decisão


if __name__ == "__main__":
    unittest.main()
