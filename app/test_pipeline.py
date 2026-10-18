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

    def test_leitura_curta_nao_e_cortada(self):
        c = pl._modelo._leituras_do_visor(self.textos((10, "042884")))
        self.assertEqual(c, [("042884", 0.99, None)])


if __name__ == "__main__":
    unittest.main()
