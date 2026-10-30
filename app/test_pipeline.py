# -*- coding: utf-8 -*-
"""Testes da regra de decisão. Rodar da raiz do repositório: python -m unittest discover app"""
import unittest

import pipeline as pl


class TestDecidir(unittest.TestCase):
    def ext(self, leitura="42884", numero="A123", confianca=0.95, tem_medidor=True):
        return pl.Extracao(tem_medidor, numero, leitura, confianca)

    def test_sem_medidor(self):
        self.assertEqual(pl.decidir(self.ext(tem_medidor=False), None)[0], pl.SEM_MEDIDOR)

    def test_ilegivel(self):
        self.assertEqual(pl.decidir(self.ext(leitura=""), ("A123", "42884"))[0], pl.ILEGIVEL)

    def test_confianca_baixa_vai_para_revisao(self):
        self.assertEqual(pl.decidir(self.ext(confianca=0.5), ("A123", "42884"))[0], pl.REVISAO)

    def test_confere_ignora_zeros_a_esquerda(self):
        self.assertEqual(pl.decidir(self.ext(leitura="042884"), ("A123", "42884"))[0], pl.CONFERE)

    def test_diverge(self):
        self.assertEqual(pl.decidir(self.ext(leitura="42885"), ("A123", "42884"))[0], pl.DIVERGE)

    def test_sem_informado_vai_ao_analista(self):
        status = pl.decidir(self.ext(), None)[0]
        self.assertEqual(status, pl.LIDO)
        self.assertNotIn(status, pl.AUTOMATICOS)


    def test_sem_medidor_sai_da_revisao(self):
        r = pl.Resultado("f.jpg", "f.jpg", 200, "", "", 1.0, "", "", pl.SEM_MEDIDOR, "")
        self.assertTrue(r.excluido)
        self.assertFalse(r.precisa_analista)
        self.assertFalse(r.pendente)


@unittest.skipIf(pl._modelo is None, "módulo do modelo indisponível")
class TestCertezaDeIlegivel(unittest.TestCase):
    def ext(self, prob, leitura="", numero=""):
        return pl.Extracao(True, numero, leitura, 0.95 if leitura and numero else 0.0, "", prob)

    def test_limiar_escolhido(self):
        self.assertAlmostEqual(pl.limiar_ilegivel(), 0.20)

    def test_chance_baixa_sai_da_fila(self):
        st = pl.decidir(self.ext(0.05), ("A1", "10"))[0]
        self.assertEqual(st, pl.ILEGIVEL_CERTO)
        self.assertIn(st, pl.EXCLUIDOS)

    def test_chance_alta_vai_ao_analista(self):
        self.assertEqual(pl.decidir(self.ext(0.60), ("A1", "10"))[0], pl.ILEGIVEL)

    def test_confere_vence_a_chance_baixa(self):
        self.assertEqual(pl.decidir(self.ext(0.05, "10", "A1"), ("A1", "10"))[0], pl.CONFERE)

    def test_sem_classificador_nao_muda_nada(self):
        self.assertEqual(pl.decidir(self.ext(-1.0), ("A1", "10"))[0], pl.ILEGIVEL)


class TestProblemasEHistorico(unittest.TestCase):
    def test_problemas(self):
        e = pl.Extracao(True, "", "", 0.0, "sem visor, sem placa")
        p = pl.classificar_problemas(e, pl.ILEGIVEL, 50, ("A1", "10"))
        self.assertEqual(p, [pl.P_SEM_VISOR, pl.P_SEM_PLACA, pl.P_NUMERO, pl.P_BORRADA])
        e = pl.Extracao(True, "123", "", 0.0, "visor 0.9, placa 0.8, display não mostra o consumo (função 03)")
        self.assertIn(pl.P_FUNCAO, pl.classificar_problemas(e, pl.ILEGIVEL, 300, None))
        self.assertEqual(pl.classificar_problemas(pl.Extracao(False, "", "", 1.0), pl.SEM_MEDIDOR, 300, None),
                         [pl.P_SEM_MEDIDOR])

    def test_historico_grava_e_le_a_decisao_mais_recente(self):
        import tempfile
        from pathlib import Path
        antigo = pl.HISTORICO
        with tempfile.TemporaryDirectory() as d:
            pl.HISTORICO = Path(d) / "h.csv"
            try:
                r = pl.Resultado("f.jpg", "f.jpg", 200, "1", "10", 0.95, "1", "10", pl.DIVERGE, "m",
                                 problemas=pl.P_DIVERGE, lote="lote1")
                r.decisao = "Ilegível"; pl.registrar_decisao(r)
                import time; time.sleep(1.1)
                r.decisao, r.leitura_final = "Corrigido", "11"; pl.registrar_decisao(r)
                h = pl.carregar_historico()
                self.assertEqual(len(h), 1)
                self.assertEqual((h[0].decisao, h[0].leitura_final), ("Corrigido", "11"))
                self.assertEqual(h[0].lista_problemas, [pl.P_DIVERGE])
            finally:
                pl.HISTORICO = antigo


@unittest.skipIf(pl._modelo is None, "módulo do modelo indisponível")
class TestFuncaoDoDisplay(unittest.TestCase):
    """O display mostra o código da função (03 = consumo) à esquerda da leitura."""
    def textos(self, *pares):
        return [{"texto": t, "conf": 0.99, "x": x} for x, t in pares]

    def test_funcao_separada_pelo_ocr(self):
        c = pl._modelo._leituras_do_visor(self.textos((10, "03"), (40, "007237")))
        self.assertIn(("007237", 0.99, "03"), c)
        self.assertNotIn("03007237", [d for d, _, _ in c])

    def test_funcao_grudada_no_numero(self):
        c = pl._modelo._leituras_do_visor(self.textos((10, "03007237")))
        self.assertIn(("007237", 0.99, "03"), c)

    def test_leitura_sem_zeros_a_esquerda(self):
        n = pl._modelo.normalizar_leitura
        self.assertEqual(n("007237"), "7237")
        self.assertEqual(n("000000"), "0")
        self.assertEqual(n("42884"), "42884")
        self.assertEqual(n(""), "")

    def test_leitura_curta_nao_e_cortada(self):
        c = pl._modelo._leituras_do_visor(self.textos((10, "042884")))
        self.assertEqual(c, [("042884", 0.99, None)])


if __name__ == "__main__":
    unittest.main()
