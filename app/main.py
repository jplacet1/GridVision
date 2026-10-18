# -*- coding: utf-8 -*-
"""
Interface desktop do GridVision (protótipo em ttkbootstrap).

Etapas, todas clicáveis no topo:
1 Lote          importar a pasta de fotos e o CSV informado (opcional)
2 Processamento abre ao começar o lote; progresso e contadores ao vivo
3 Resultados    o que já está resolvido: "Confere" automático (entra enquanto processa), revisadas e excluídas
4 Revisão       fila do que está pendente (cresce enquanto processa), com filtro por problema
5 Exportação    exportar tudo, só o filtrado ou as linhas selecionadas
Histórico (botão no topo): todas as decisões já gravadas, de todos os lotes.

Uso:  python app/main.py

As fotos e o CSV ficam fora do Git (LGPD). A interface só lê da pasta local que o analista escolhe.
"""
import queue, threading
import tkinter as tk
from tkinter import filedialog, font as tkfont

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.style import ThemeDefinition
from ttkbootstrap.dialogs import Messagebox
from PIL import Image, ImageTk

import pipeline as pl

# Tokens do design system do GridVision, tema escuro (plataforma e demonstrações)
COR = {
    "surface": "#0a0f18", "surface-raised": "#121926", "ink": "#eef2f7", "ink-muted": "#a3aec2",
    "border": "#263044", "border-strong": "#5b6780", "action": "#4da3ff", "on-action": "#06101f",
    "ok": "#4ade80", "warn": "#f5b53d", "danger": "#ff7a6b",
    "grid-blue": "#007afb", "grid-cyan": "#00abfd", "grid-teal": "#02d3b2", "grid-green": "#40f837",
}
TEMA = ThemeDefinition(name="gridvision", themetype="dark", colors={
    "primary": COR["action"], "secondary": COR["border-strong"], "success": COR["ok"],
    "info": COR["grid-teal"], "warning": COR["warn"], "danger": COR["danger"],
    "light": COR["ink"], "dark": COR["surface-raised"], "bg": COR["surface"], "fg": COR["ink"],
    "selectbg": COR["action"], "selectfg": COR["on-action"], "border": COR["border-strong"],
    "inputfg": COR["ink"], "inputbg": COR["surface-raised"], "active": "#1b2434",
})
# Cor de cada status na tabela e nos cartões (sempre junto da palavra, nunca só a cor)
COR_STATUS = {pl.CONFERE: "ok", pl.DIVERGE: "danger", pl.LIDO: "action", pl.REVISAO: "warn",
              pl.ILEGIVEL: "warn", pl.SEM_MEDIDOR: "ink-muted"}
ETAPAS = ["Lote", "Processamento", "Resultados", "Revisão", "Exportação"]

# Situação de cada foto no lote
AUTOMATICA, REVISADA, EXCLUIDA, PENDENTE = "Automática", "Revisada", "Excluída", "Pendente"
SITUACOES = [AUTOMATICA, REVISADA, EXCLUIDA, PENDENTE]


def situacao(r):
    if r.decisao:
        return REVISADA
    if r.excluido:
        return EXCLUIDA
    if r.status in pl.AUTOMATICOS:
        return AUTOMATICA
    return PENDENTE


def familia(preferidas, reserva="Segoe UI"):
    instaladas = set(tkfont.families())
    return next((f for f in preferidas if f in instaladas), reserva)


class App(ttk.Window):
    def __init__(self):
        super().__init__(title="GridVision", size=(1240, 800), minsize=(1040, 660))
        self.style.register_theme(TEMA)
        self.style.theme_use("gridvision")
        self.f_display = familia(["Oxanium", "Eurostile"])
        self.f_sans = familia(["IBM Plex Sans"])
        self.f_mono = familia(["IBM Plex Mono", "Consolas"], "Courier New")
        self.style.configure(".", font=(self.f_sans, 10))
        self.style.configure("Treeview", rowheight=26, font=(self.f_mono, 10))
        self.style.configure("Treeview.Heading", font=(self.f_sans, 9, "bold"))

        self.pasta = tk.StringVar()
        self.csv = tk.StringVar()
        self.resultados = []
        self.total_lote = 0
        self.processando = False
        self.atual = None              # foto aberta no painel de revisão
        self.origem_revisao = "Revisão"
        self.tela_atual = None
        self._cancelar = threading.Event()
        self._fila = queue.Queue()

        self._cabecalho()
        self.corpo = ttk.Frame(self, padding=(24, 12))
        self.corpo.pack(fill=BOTH, expand=YES)
        self.telas = {n: ttk.Frame(self.corpo) for n in ETAPAS + ["Histórico"]}
        self._tela_lote(self.telas["Lote"])
        self._tela_processamento(self.telas["Processamento"])
        self._tela_resultados(self.telas["Resultados"])
        self._tela_revisao(self.telas["Revisão"])
        self._tela_exportacao(self.telas["Exportação"])
        self._tela_historico(self.telas["Histórico"])
        self.bind("<Return>", self._enter)
        self.ir("Lote")

    # ================= estrutura =================
    def _cabecalho(self):
        topo = ttk.Frame(self, padding=(24, 14, 24, 8))
        topo.pack(fill=X)
        ttk.Label(topo, text="GridVision", font=(self.f_display, 20, "bold")).pack(side=LEFT)
        ttk.Label(topo, text="Leitura de medidores por foto", foreground=COR["ink-muted"],
                  font=(self.f_sans, 10)).pack(side=LEFT, padx=(12, 0), pady=(8, 0))
        self.bt_hist = ttk.Label(topo, text="HISTÓRICO", font=(self.f_sans, 9, "bold"), padding=(12, 6),
                                 cursor="hand2", foreground=COR["ink-muted"])
        self.bt_hist.pack(side=RIGHT, padx=(12, 0))
        self.bt_hist.bind("<Button-1>", lambda e: self.ir("Histórico"))
        self.passos = ttk.Frame(topo)
        self.passos.pack(side=RIGHT)
        self.rotulos_passo = {}
        for i, n in enumerate(ETAPAS, 1):
            lb = ttk.Label(self.passos, text=f"{i}  {n.upper()}", font=(self.f_sans, 9, "bold"),
                           padding=(10, 6), cursor="hand2")
            lb.pack(side=LEFT)
            lb.bind("<Button-1>", lambda e, nome=n: self.ir(nome))
            lb.bind("<Enter>", lambda e, w=lb: w.configure(foreground=COR["ink"]))
            lb.bind("<Leave>", lambda e: self._pintar_passos())
            self.rotulos_passo[n] = lb
        # único acento da tela: linha de 3px com o gradiente da marca
        self.linha = tk.Canvas(self, height=3, highlightthickness=0, bg=COR["surface"])
        self.linha.pack(fill=X)
        self.linha.bind("<Configure>", self._gradiente)
        if pl.MODELO_REAL:
            texto_aviso, cor_aviso = ("Modelo: detector v0 + PaddleOCR 3.7 com fiscal. Cerca de 10 s por foto em CPU; "
                                      "só \"Confere\" sai sem analista."), COR["ink-muted"]
        else:
            texto_aviso, cor_aviso = (f"Extração simulada ({pl.MOTIVO_SEM_MODELO}). "
                                      "Nitidez e regra de decisão são reais."), COR["warn"]
        ttk.Label(self, text=texto_aviso, foreground=cor_aviso, font=(self.f_sans, 9), padding=(24, 6)).pack(fill=X)

    def _gradiente(self, ev):
        self.linha.delete("all")
        paradas = [COR[c] for c in ("grid-blue", "grid-cyan", "grid-teal", "grid-green")]
        rgb = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in paradas]
        w = max(ev.width, 1)
        for x in range(0, w, 2):
            t = x / w * (len(rgb) - 1)
            i = min(int(t), len(rgb) - 2)
            a, b, f = rgb[i], rgb[i + 1], t - i
            cor = "#%02x%02x%02x" % tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))
            self.linha.create_line(x, 0, x, 3, fill=cor, width=2)

    def _pintar_passos(self):
        cont = {s: 0 for s in SITUACOES}
        for r in self.resultados:
            cont[situacao(r)] += 1
        extras = {"Processamento": f"  {len(self.resultados)}/{self.total_lote}" if self.processando else "",
                  "Resultados": f"  ({cont[AUTOMATICA] + cont[REVISADA] + cont[EXCLUIDA]})" if self.resultados else "",
                  "Revisão": f"  ({cont[PENDENTE]})" if self.resultados else ""}
        for i, (n, lb) in enumerate(self.rotulos_passo.items(), 1):
            lb.configure(text=f"{i}  {n.upper()}{extras.get(n, '')}",
                         foreground=COR["action"] if n == self.tela_atual else COR["ink-muted"])
        self.bt_hist.configure(foreground=COR["action"] if self.tela_atual == "Histórico" else COR["ink-muted"])

    def ir(self, nome):
        for t in self.telas.values():
            t.pack_forget()
        self.tela_atual = nome
        self.telas[nome].pack(fill=BOTH, expand=YES)
        {"Processamento": self._atualizar_processamento, "Resultados": self._preencher_resultados,
         "Revisão": self._atualizar_revisao, "Exportação": self._preencher_exportacao,
         "Histórico": self._carregar_historico}.get(nome, lambda: None)()
        self._pintar_passos()

    def titulo(self, pai, texto, sub=None):
        ttk.Label(pai, text=texto, font=(self.f_display, 16, "bold")).pack(anchor=W)
        if sub:
            ttk.Label(pai, text=sub, foreground=COR["ink-muted"], wraplength=1000,
                      justify=LEFT).pack(anchor=W, pady=(4, 12))

    def _rotulo(self, pai, texto, **pack):
        lb = ttk.Label(pai, text=texto, font=(self.f_sans, 9, "bold"), foreground=COR["ink-muted"])
        lb.pack(side=LEFT, **pack)
        return lb

    def _combo(self, pai, valores, largura, cmd):
        cb = ttk.Combobox(pai, state="readonly", width=largura, values=valores)
        cb.set(valores[0])
        cb.pack(side=LEFT, padx=(8, 16))
        cb.bind("<<ComboboxSelected>>", lambda e: cmd())
        return cb

    def _tabela(self, pai, cols, nomes, larguras, estica, selecao="browse"):
        quadro = ttk.Frame(pai)
        quadro.pack(fill=BOTH, expand=YES)
        tv = ttk.Treeview(quadro, columns=cols, show=HEADINGS, bootstyle=PRIMARY, selectmode=selecao)
        for c, n, w in zip(cols, nomes, larguras):
            tv.heading(c, text=n, anchor=W)
            tv.column(c, width=w, anchor=W, stretch=(c == estica))
        for s, c in COR_STATUS.items():
            tv.tag_configure(s, foreground=COR[c])
        rolagem = ttk.Scrollbar(quadro, orient=VERTICAL, command=tv.yview)
        tv.configure(yscrollcommand=rolagem.set)
        tv.pack(side=LEFT, fill=BOTH, expand=YES)
        rolagem.pack(side=RIGHT, fill=Y)
        return tv

    def _cartoes(self, quadro, itens):
        for w in quadro.winfo_children():
            w.destroy()
        for rotulo, valor, cor in itens:
            c = ttk.Frame(quadro, bootstyle=DARK, padding=(16, 10))
            c.pack(side=LEFT, padx=(0, 8), fill=Y)
            ttk.Label(c, text=rotulo.upper(), font=(self.f_sans, 8, "bold"), foreground=COR["ink-muted"],
                      bootstyle=(INVERSE, DARK)).pack(anchor=W)
            ttk.Label(c, text=valor, font=(self.f_mono, 18), foreground=COR[cor],
                      bootstyle=(INVERSE, DARK)).pack(anchor=W)

    @staticmethod
    def _valores(r):
        return (r.arquivo, situacao(r), r.status, ", ".join(r.lista_problemas) or "-",
                r.numero_final or r.numero_lido or "-", r.leitura_final or r.leitura_lida or "-",
                r.leitura_informada or "-", f"{r.confianca:.2f}", r.decisao or "-", r.motivo)

    # ================= 1. Lote =================
    def _tela_lote(self, t):
        self.titulo(t, "Novo lote", "Escolha a pasta com as fotos do lote. O CSV com a leitura informada pelo "
                                    "leiturista é opcional: com ele o sistema compara as leituras; sem ele, "
                                    "devolve o valor lido para o analista confirmar.")
        form = ttk.Frame(t)
        form.pack(fill=X)
        self._campo_arquivo(form, 0, "Pasta de fotos", self.pasta, self._escolher_pasta)
        self._campo_arquivo(form, 1, "CSV informado (opcional)", self.csv, self._escolher_csv)
        form.columnconfigure(1, weight=1)
        self.info_lote = ttk.Label(t, text="", foreground=COR["ink-muted"], wraplength=1000, justify=LEFT)
        self.info_lote.pack(anchor=W, pady=(12, 0))
        ttk.Label(t, text="Os dados ficam só nesta máquina, fora do repositório (LGPD).",
                  foreground=COR["ink-muted"], font=(self.f_sans, 9)).pack(anchor=W, pady=(4, 0))
        self.bt_processar = ttk.Button(t, text="Processar lote", bootstyle=PRIMARY, command=self.iniciar,
                                       padding=(16, 8))
        self.bt_processar.pack(anchor=W, pady=(24, 0))

    def _campo_arquivo(self, pai, linha, rotulo, var, cmd):
        ttk.Label(pai, text=rotulo.upper(), font=(self.f_sans, 9, "bold"),
                  foreground=COR["ink-muted"]).grid(row=linha, column=0, sticky=W, pady=6, padx=(0, 16))
        ttk.Entry(pai, textvariable=var).grid(row=linha, column=1, sticky=EW, pady=6)
        ttk.Button(pai, text="Procurar", bootstyle=(SECONDARY, OUTLINE), command=cmd).grid(
            row=linha, column=2, padx=(8, 0), pady=6)

    def _escolher_pasta(self):
        p = filedialog.askdirectory(title="Pasta de fotos do lote")
        if p:
            self.pasta.set(p)
            fotos = pl.listar_fotos(p)
            conj = pl.conjuntos_do_lote(fotos)
            texto = f"{len(fotos)} fotos encontradas"
            avisos = []
            if conj.get("treino"):
                avisos.append(f"{conj['treino']} do treino (servem para demonstrar, não para medir)")
            reservadas = conj.get("teste", 0) + conj.get("teste_temporal", 0)
            if reservadas:
                avisos.append(f"{reservadas} do teste ou teste temporal (reservadas para a medida final; "
                              "não ajuste regras olhando para elas)")
            if avisos:
                texto += ". Atenção: " + "; ".join(avisos) + "."
            self.info_lote.configure(text=texto, foreground=COR["warn"] if avisos else COR["ink-muted"])

    def _escolher_csv(self):
        p = filedialog.askopenfilename(title="CSV do lote", filetypes=[("CSV", "*.csv")])
        if p:
            self.csv.set(p)

    # ================= 2. Processamento =================
    def _tela_processamento(self, t):
        self.titulo(t, "Processamento", "Para cada foto: nitidez, extração do número do medidor e da leitura, e "
                                        "decisão. Enquanto processa, as fotos com \"Confere\" já aparecem em "
                                        "Resultados e as pendentes já podem ser revisadas em Revisão.")
        self.txt_proc_estado = ttk.Label(t, text="", font=(self.f_display, 13, "bold"))
        self.txt_proc_estado.pack(anchor=W, pady=(4, 8))
        self.progresso = ttk.Progressbar(t, bootstyle=PRIMARY, length=600)
        self.progresso.pack(fill=X, pady=(0, 8))
        self.txt_progresso = ttk.Label(t, text="", font=(self.f_mono, 10))
        self.txt_progresso.pack(anchor=W)
        self.txt_atual = ttk.Label(t, text="", foreground=COR["ink-muted"], font=(self.f_mono, 9))
        self.txt_atual.pack(anchor=W, pady=(4, 12))
        self.cartoes_proc = ttk.Frame(t)
        self.cartoes_proc.pack(fill=X, pady=(4, 16))
        acoes = ttk.Frame(t)
        acoes.pack(anchor=W)
        self.bt_cancelar = ttk.Button(acoes, text="Cancelar", bootstyle=(DANGER, OUTLINE), command=self._cancelar.set)
        self.bt_cancelar.pack(side=LEFT)
        ttk.Button(acoes, text="Ver resultados", bootstyle=(SECONDARY, OUTLINE),
                   command=lambda: self.ir("Resultados")).pack(side=LEFT, padx=8)
        ttk.Button(acoes, text="Revisar pendentes", bootstyle=PRIMARY,
                   command=lambda: self.ir("Revisão")).pack(side=LEFT)

    def _atualizar_processamento(self):
        n = len(self.resultados)
        if self.processando:
            self.txt_proc_estado.configure(text="Processando lote…", foreground=COR["ink"])
        elif self.total_lote:
            fim = "Lote concluído" if n == self.total_lote else f"Processamento interrompido em {n} fotos"
            self.txt_proc_estado.configure(text=fim, foreground=COR["ok"] if n == self.total_lote else COR["warn"])
        else:
            self.txt_proc_estado.configure(text="Nenhum lote processado ainda. Comece em 1 Lote.",
                                           foreground=COR["ink-muted"])
        self.progresso.configure(maximum=max(self.total_lote, 1), value=n)
        self.txt_progresso.configure(text=f"{n} de {self.total_lote} fotos" if self.total_lote else "")
        if self.processando:
            self.bt_cancelar.state(["!disabled"])
        else:
            self.bt_cancelar.state(["disabled"])
            self.txt_atual.configure(text="")
        cont = {s: sum(1 for r in self.resultados if situacao(r) == s) for s in SITUACOES}
        self._cartoes(self.cartoes_proc, [("Processadas", str(n), "ink"),
                                          ("Confere automático", str(cont[AUTOMATICA]), "ok"),
                                          ("Pendentes", str(cont[PENDENTE]), "warn"),
                                          ("Excluídas (sem medidor)", str(cont[EXCLUIDA]), "ink-muted"),
                                          ("Revisadas", str(cont[REVISADA]), "action")])

    def iniciar(self):
        if self.processando:
            Messagebox.show_warning("Já há um lote em processamento.", "GridVision", parent=self)
            return
        pasta = self.pasta.get().strip()
        if not pasta:
            Messagebox.show_warning("Escolha a pasta de fotos.", "GridVision", parent=self)
            return
        try:
            fotos = pl.listar_fotos(pasta)
            informado = pl.carregar_informado(self.csv.get().strip()) if self.csv.get().strip() else {}
        except (OSError, UnicodeDecodeError) as e:
            Messagebox.show_error(f"Não consegui ler o lote:\n{e}", "GridVision", parent=self)
            return
        if not fotos:
            Messagebox.show_warning("Nenhuma foto .jpg ou .png na pasta.", "GridVision", parent=self)
            return
        self.resultados, self.atual = [], None
        self.total_lote, self.processando = len(fotos), True
        self._cancelar.clear()
        self.ir("Processamento")
        threading.Thread(target=self._trabalhar, args=(fotos, informado), daemon=True).start()
        self.after(50, self._acompanhar)

    def _trabalhar(self, fotos, informado):
        for i, f in enumerate(fotos, 1):
            if self._cancelar.is_set():
                break
            self._fila.put(("atual", f.name))
            try:
                r = pl.processar(f, informado.get(f.name))
            except Exception as e:  # uma foto ruim não derruba o lote
                r = pl.Resultado(f.name, str(f), 0.0, "", "", 0.0, "", "", pl.REVISAO, f"erro ao processar: {e}",
                                 problemas=pl.P_CONFIANCA, lote=f.parent.name)
            self._fila.put(("item", r))
        self._fila.put(("fim",))

    def _acompanhar(self):
        novos = False
        try:
            while True:
                msg = self._fila.get_nowait()
                if msg[0] == "atual":
                    self.txt_atual.configure(text=f"lendo {msg[1]}")
                elif msg[0] == "item":
                    self.resultados.append(msg[1])
                    novos = True
                else:  # fim
                    self.processando = False
                    self._ao_mudar()
                    return
        except queue.Empty:
            pass
        if novos:
            self._ao_mudar()
        self.after(100, self._acompanhar)

    def _ao_mudar(self):
        """Atualiza a tela aberta e os contadores do topo quando chegam fotos ou decisões."""
        tela = self.tela_atual
        if tela == "Processamento":
            self._atualizar_processamento()
        elif tela == "Resultados":
            self._preencher_resultados()
        elif tela == "Revisão":
            self._preencher_fila()
            if self.atual is None:
                self._abrir_proximo()
        elif tela == "Exportação":
            self._preencher_exportacao()
        self._pintar_passos()

    # ================= 3. Resultados =================
    def _tela_resultados(self, t):
        self.titulo(t, "Resultados", "O que já está resolvido: \"Confere\" automático (entra enquanto o lote "
                                     "processa), fotos revisadas pelo analista e fotos excluídas por não terem "
                                     "medidor. Duplo clique abre a foto para revisar ou corrigir.")
        self.cartoes_res = ttk.Frame(t)
        self.cartoes_res.pack(fill=X, pady=(0, 12))
        barra = ttk.Frame(t)
        barra.pack(fill=X, pady=(0, 8))
        self._rotulo(barra, "SITUAÇÃO")
        self.r_sit = self._combo(barra, ["Todas", AUTOMATICA, REVISADA, EXCLUIDA], 14, self._preencher_resultados)
        self._rotulo(barra, "PROBLEMA")
        self.r_prob = self._combo(barra, ["Todos"] + pl.PROBLEMAS, 28, self._preencher_resultados)
        self.res_tabela = self._tabela(
            t, ("arquivo", "situacao", "status", "problemas", "numero", "leitura", "informado", "confianca",
                "decisao", "motivo"),
            ("Foto", "Situação", "Status", "Problemas", "Nº", "Leitura", "Leitura informada", "Confiança",
             "Decisão", "Motivo"),
            (230, 90, 110, 200, 100, 80, 110, 70, 90, 260), "motivo")
        self.res_tabela.bind("<Double-1>", lambda e: self._abrir_da_tabela(self.res_tabela, "Resultados"))
        self.res_vazio = ttk.Label(t, text="", foreground=COR["ink-muted"])

    def _preencher_resultados(self):
        cont = {s: sum(1 for r in self.resultados if situacao(r) == s) for s in SITUACOES}
        n = len(self.resultados)
        self._cartoes(self.cartoes_res, [
            ("Processadas", f"{n}/{self.total_lote}" if self.total_lote else "0", "ink"),
            ("Confere automático", f"{cont[AUTOMATICA]}  ({cont[AUTOMATICA] / n:.0%})" if n else "0", "ok"),
            ("Revisadas", str(cont[REVISADA]), "action"),
            ("Excluídas (sem medidor)", str(cont[EXCLUIDA]), "ink-muted"),
            ("Pendentes de revisão", str(cont[PENDENTE]), "warn" if cont[PENDENTE] else "ok")])
        sit, prob = self.r_sit.get(), self.r_prob.get()
        tv = self.res_tabela
        tv.delete(*tv.get_children())
        for i, r in enumerate(self.resultados):
            s = situacao(r)
            if s == PENDENTE or (sit != "Todas" and s != sit) or (prob != "Todos" and prob not in r.lista_problemas):
                continue
            tv.insert("", END, iid=str(i), tags=(r.status,), values=self._valores(r))

    def _abrir_da_tabela(self, tv, origem):
        sel = tv.focus()
        if sel:
            self.origem_revisao = origem
            self.atual = self.resultados[int(sel)] if origem != "Histórico" else self.historico[int(sel)]
            self.ir("Revisão")

    # ================= 4. Revisão =================
    def _tela_revisao(self, t):
        topo = ttk.Frame(t)
        topo.pack(fill=X)
        ttk.Label(topo, text="Revisão", font=(self.f_display, 16, "bold")).pack(side=LEFT)
        self.txt_fila = ttk.Label(topo, text="", font=(self.f_mono, 10), foreground=COR["ink-muted"])
        self.txt_fila.pack(side=RIGHT)

        corpo = ttk.Frame(t)
        corpo.pack(fill=BOTH, expand=YES, pady=(10, 0))

        # fila de pendentes, à esquerda
        esq = ttk.Frame(corpo, width=330)
        esq.pack(side=LEFT, fill=Y)
        esq.pack_propagate(False)
        f = ttk.Frame(esq)
        f.pack(fill=X, pady=(0, 6))
        ttk.Label(f, text="PROBLEMA", font=(self.f_sans, 9, "bold"), foreground=COR["ink-muted"]).pack(side=LEFT)
        self.v_prob = ttk.Combobox(f, state="readonly", width=26, values=["Todos"] + pl.PROBLEMAS)
        self.v_prob.set("Todos")
        self.v_prob.pack(side=LEFT, padx=(8, 0))
        self.v_prob.bind("<<ComboboxSelected>>", lambda e: (self._preencher_fila(), self._abrir_proximo()))
        quadro = ttk.Frame(esq)
        quadro.pack(fill=BOTH, expand=YES)
        self.fila_tv = ttk.Treeview(quadro, columns=("arquivo", "status"), show=HEADINGS, bootstyle=PRIMARY,
                                    selectmode="browse")
        self.fila_tv.heading("arquivo", text="Foto pendente", anchor=W)
        self.fila_tv.heading("status", text="Status", anchor=W)
        self.fila_tv.column("arquivo", width=200, anchor=W)
        self.fila_tv.column("status", width=100, anchor=W, stretch=False)
        for s, c in COR_STATUS.items():
            self.fila_tv.tag_configure(s, foreground=COR[c])
        rol = ttk.Scrollbar(quadro, orient=VERTICAL, command=self.fila_tv.yview)
        self.fila_tv.configure(yscrollcommand=rol.set)
        self.fila_tv.pack(side=LEFT, fill=BOTH, expand=YES)
        rol.pack(side=RIGHT, fill=Y)
        self.fila_tv.bind("<<TreeviewSelect>>", self._selecionar_na_fila)

        # painel da foto, à direita
        self.painel = ttk.Frame(corpo, padding=(20, 0, 0, 0))
        self.painel.pack(side=LEFT, fill=BOTH, expand=YES)
        self.vazio = ttk.Label(corpo, text="", foreground=COR["ink-muted"], font=(self.f_sans, 11),
                               wraplength=600, justify=LEFT, padding=(20, 20))

        self.foto = ttk.Label(self.painel, background=COR["surface-raised"], anchor=CENTER)
        self.foto.pack(side=LEFT, fill=Y)
        lado = ttk.Frame(self.painel, padding=(20, 0, 0, 0))
        lado.pack(side=LEFT, fill=BOTH, expand=YES)
        self.txt_arquivo = ttk.Label(lado, font=(self.f_mono, 9), foreground=COR["ink-muted"], wraplength=380)
        self.txt_arquivo.pack(anchor=W)
        self.txt_status = ttk.Label(lado, font=(self.f_display, 14, "bold"))
        self.txt_status.pack(anchor=W, pady=(8, 0))
        self.txt_problemas = ttk.Label(lado, foreground=COR["warn"], wraplength=380, justify=LEFT)
        self.txt_problemas.pack(anchor=W, pady=(2, 0))
        self.txt_motivo = ttk.Label(lado, foreground=COR["ink-muted"], wraplength=380, justify=LEFT)
        self.txt_motivo.pack(anchor=W, pady=(2, 12))

        form = ttk.Frame(lado)
        form.pack(fill=X)
        self.v_numero, self.v_leitura = tk.StringVar(), tk.StringVar()
        self.v_num_inf, self.v_leit_inf, self.v_conf = tk.StringVar(), tk.StringVar(), tk.StringVar()
        linhas = [("Nº do medidor", self.v_numero, True), ("Leitura", self.v_leitura, True),
                  ("Nº informado", self.v_num_inf, False), ("Leitura informada", self.v_leit_inf, False),
                  ("Confiança e nitidez", self.v_conf, False)]
        for i, (rot, var, editavel) in enumerate(linhas):
            ttk.Label(form, text=rot.upper(), font=(self.f_sans, 9, "bold"),
                      foreground=COR["ink-muted"]).grid(row=i, column=0, sticky=W, pady=5, padx=(0, 16))
            if editavel:
                e = ttk.Entry(form, textvariable=var, font=(self.f_mono, 12))
                e.grid(row=i, column=1, sticky=EW, pady=5)
                if i == 1:
                    self.campo_leitura = e
            else:
                ttk.Label(form, textvariable=var, font=(self.f_mono, 12)).grid(
                    row=i, column=1, sticky=W, pady=5, padx=(6, 0))
        form.columnconfigure(1, weight=1)

        acoes = ttk.Frame(lado)
        acoes.pack(fill=X, pady=(16, 0))
        ttk.Button(acoes, text="Confirmar (Enter)", bootstyle=SUCCESS,
                   command=lambda: self._decidir("Confirmado")).pack(side=LEFT)
        ttk.Button(acoes, text="Ilegível", bootstyle=(WARNING, OUTLINE),
                   command=lambda: self._decidir("Ilegível")).pack(side=LEFT, padx=8)
        ttk.Button(acoes, text="Pular", bootstyle=(SECONDARY, OUTLINE),
                   command=self._pular).pack(side=LEFT)
        self.bt_voltar = ttk.Button(acoes, text="Voltar", bootstyle=(SECONDARY, LINK),
                                    command=lambda: self.ir(self.origem_revisao))
        ttk.Label(lado, text="Se editar o número ou a leitura, a decisão fica como Corrigido. "
                             "Cada decisão é gravada no Histórico.",
                  foreground=COR["ink-muted"], font=(self.f_sans, 9), wraplength=380,
                  justify=LEFT).pack(anchor=W, pady=(14, 0))

    def _pendentes(self):
        prob = self.v_prob.get()
        return [(i, r) for i, r in enumerate(self.resultados)
                if situacao(r) == PENDENTE and (prob == "Todos" or prob in r.lista_problemas)]

    def _preencher_fila(self):
        pend = self._pendentes()
        tv = self.fila_tv
        sel = tv.selection()
        tv.delete(*tv.get_children())
        for i, r in pend:
            tv.insert("", END, iid=str(i), tags=(r.status,), values=(r.arquivo, r.status))
        # marca na lista a foto aberta (só se for uma pendente deste lote)
        if self.atual is not None and any(r is self.atual for _, r in pend):
            iid = str(next(i for i, r in pend if r is self.atual))
            tv.selection_set(iid)
            tv.see(iid)
        total_pend = sum(1 for r in self.resultados if situacao(r) == PENDENTE)
        mais = "  ·  o lote ainda está processando" if self.processando else ""
        self.txt_fila.configure(text=f"{total_pend} pendentes{mais}")

    def _atualizar_revisao(self):
        self._preencher_fila()
        if self.atual is None:
            self._abrir_proximo()
        else:
            self._mostrar(self.atual)

    def _abrir_proximo(self):
        pend = self._pendentes()
        if pend:
            self._mostrar(pend[0][1])
        else:
            self.atual = None
            self._mostrar_vazio()

    def _mostrar_vazio(self):
        self.painel.pack_forget()
        if not self.resultados and not self.processando:
            texto = "Nenhum lote processado ainda. Comece em 1 Lote."
        elif self.processando:
            texto = "Nada pendente por enquanto. As fotos que precisarem de revisão aparecem aqui enquanto o lote processa."
        else:
            texto = "Nada pendente neste lote. Veja o que foi resolvido em 3 Resultados ou exporte em 5 Exportação."
        self.vazio.configure(text=texto)
        self.vazio.pack(side=LEFT, fill=BOTH, expand=YES)

    def _selecionar_na_fila(self, ev):
        sel = self.fila_tv.selection()
        if sel:
            r = self.resultados[int(sel[0])]
            if r is not self.atual:
                self.origem_revisao = "Revisão"
                self._mostrar(r)

    def _mostrar(self, r):
        self.atual = r
        self.vazio.pack_forget()
        self.painel.pack(side=LEFT, fill=BOTH, expand=YES)
        if self.origem_revisao != "Revisão":
            self.bt_voltar.pack(side=RIGHT)
        else:
            self.bt_voltar.pack_forget()
        self.txt_arquivo.configure(text=f"{r.lote} / {r.arquivo}" if r.lote else r.arquivo)
        self.txt_status.configure(text=r.status + (f"  ·  {r.decisao}" if r.decisao else ""),
                                  foreground=COR[COR_STATUS.get(r.status, "ink")])
        self.txt_problemas.configure(text=" · ".join(r.lista_problemas))
        self.txt_motivo.configure(text=r.motivo)
        self.v_numero.set(r.numero_final or r.numero_lido)
        self.v_leitura.set(r.leitura_final or r.leitura_lida)
        self.v_num_inf.set(r.numero_informado or "-")
        self.v_leit_inf.set(r.leitura_informada or "-")
        self.v_conf.set(f"{r.confianca:.2f}  ·  nitidez {r.nitidez:.0f}")
        try:
            img = Image.open(r.caminho)
            img.thumbnail((400, 540))
            self._img = ImageTk.PhotoImage(img)
            self.foto.configure(image=self._img, text="")
        except OSError:
            self._img = None
            self.foto.configure(image="", text="Não foi possível abrir a foto", width=40)
        self.campo_leitura.focus_set()
        self.campo_leitura.select_range(0, END)

    def _enter(self, ev):
        if self.tela_atual == "Revisão" and self.atual is not None:
            self._decidir("Confirmado")

    def _decidir(self, decisao):
        r = self.atual
        if r is None:
            return
        num, leit = self.v_numero.get().strip(), self.v_leitura.get().strip()
        if decisao == "Confirmado":
            if not leit or not num:
                Messagebox.show_warning("Preencha número e leitura, ou marque como Ilegível.",
                                        "GridVision", parent=self)
                return
            if (num, leit) != (r.numero_lido, r.leitura_lida):
                decisao = "Corrigido"
            r.numero_final, r.leitura_final = num, leit
        else:
            r.numero_final = r.leitura_final = ""
        r.decisao = decisao
        try:
            pl.registrar_decisao(r)
        except OSError as e:
            Messagebox.show_error(f"A decisão foi aplicada, mas não consegui gravar o histórico:\n{e}",
                                  "GridVision", parent=self)
        if self.origem_revisao != "Revisão":
            origem, self.origem_revisao, self.atual = self.origem_revisao, "Revisão", None
            self.ir(origem)
            return
        self.atual = None
        self._preencher_fila()
        self._abrir_proximo()
        self._pintar_passos()

    def _pular(self):
        pend = [r for _, r in self._pendentes()]
        if self.atual in pend and len(pend) > 1:
            self._mostrar(pend[(pend.index(self.atual) + 1) % len(pend)])
            self._preencher_fila()

    # ================= 5. Exportação =================
    def _tela_exportacao(self, t):
        self.titulo(t, "Exportação", "Gera um CSV (separador ;) com status, problemas, valor lido, informado e a "
                                     "decisão do analista. Exporte tudo, só o que estiver filtrado, ou selecione "
                                     "as linhas (Ctrl e Shift para várias). Salve fora do repositório.")
        barra = ttk.Frame(t)
        barra.pack(fill=X, pady=(0, 8))
        self._rotulo(barra, "SITUAÇÃO")
        self.e_sit = self._combo(barra, ["Todas"] + SITUACOES, 14, self._preencher_exportacao)
        self._rotulo(barra, "STATUS")
        self.e_st = self._combo(barra, ["Todos"] + pl.STATUS, 16, self._preencher_exportacao)
        self._rotulo(barra, "PROBLEMA")
        self.e_prob = self._combo(barra, ["Todos"] + pl.PROBLEMAS, 28, self._preencher_exportacao)
        acoes = ttk.Frame(t)
        acoes.pack(fill=X, pady=(0, 8))
        self.bt_exp_todos = ttk.Button(acoes, text="Exportar todos", bootstyle=PRIMARY,
                                       command=lambda: self._exportar("todos"))
        self.bt_exp_todos.pack(side=LEFT)
        self.bt_exp_filtro = ttk.Button(acoes, text="Exportar filtrados", bootstyle=(PRIMARY, OUTLINE),
                                        command=lambda: self._exportar("filtrados"))
        self.bt_exp_filtro.pack(side=LEFT, padx=8)
        self.bt_exp_sel = ttk.Button(acoes, text="Exportar selecionados", bootstyle=(PRIMARY, OUTLINE),
                                     command=lambda: self._exportar("selecionados"))
        self.bt_exp_sel.pack(side=LEFT)
        ttk.Button(acoes, text="Selecionar todos", bootstyle=(SECONDARY, LINK),
                   command=lambda: (self.exp_tabela.selection_set(self.exp_tabela.get_children()),)).pack(side=LEFT, padx=(16, 0))
        ttk.Button(acoes, text="Limpar seleção", bootstyle=(SECONDARY, LINK),
                   command=lambda: self.exp_tabela.selection_remove(self.exp_tabela.selection())).pack(side=LEFT)
        self.exp_tabela = self._tabela(
            t, ("arquivo", "situacao", "status", "problemas", "numero", "leitura", "informado", "confianca",
                "decisao", "motivo"),
            ("Foto", "Situação", "Status", "Problemas", "Nº", "Leitura", "Leitura informada", "Confiança",
             "Decisão", "Motivo"),
            (230, 90, 110, 200, 100, 80, 110, 70, 90, 260), "motivo", selecao="extended")
        self.exp_tabela.bind("<<TreeviewSelect>>", lambda e: self._contar_exportacao())

    def _filtrados_exportacao(self):
        sit, st, prob = self.e_sit.get(), self.e_st.get(), self.e_prob.get()
        return [(i, r) for i, r in enumerate(self.resultados)
                if (sit == "Todas" or situacao(r) == sit) and (st == "Todos" or r.status == st)
                and (prob == "Todos" or prob in r.lista_problemas)]

    def _preencher_exportacao(self):
        tv = self.exp_tabela
        sel = set(tv.selection())
        tv.delete(*tv.get_children())
        for i, r in self._filtrados_exportacao():
            tv.insert("", END, iid=str(i), tags=(r.status,), values=self._valores(r))
        tv.selection_set([s for s in sel if tv.exists(s)])
        self._contar_exportacao()

    def _contar_exportacao(self):
        self.bt_exp_todos.configure(text=f"Exportar todos ({len(self.resultados)})")
        self.bt_exp_filtro.configure(text=f"Exportar filtrados ({len(self.exp_tabela.get_children())})")
        self.bt_exp_sel.configure(text=f"Exportar selecionados ({len(self.exp_tabela.selection())})")

    def _exportar(self, modo):
        if modo == "todos":
            itens = list(self.resultados)
        elif modo == "filtrados":
            itens = [r for _, r in self._filtrados_exportacao()]
        else:
            itens = [self.resultados[int(i)] for i in self.exp_tabela.selection()]
        if not itens:
            Messagebox.show_warning("Nada para exportar com essa escolha.", "GridVision", parent=self)
            return
        pend = sum(1 for r in itens if situacao(r) == PENDENTE)
        p = filedialog.asksaveasfilename(title="Salvar resultado", defaultextension=".csv",
                                         initialfile=f"resultado_gridvision_{modo}.csv", filetypes=[("CSV", "*.csv")])
        if p:
            pl.exportar(itens, p)
            aviso = f"\n{pend} delas ainda estão pendentes de revisão." if pend else ""
            Messagebox.show_info(f"{len(itens)} fotos salvas em\n{p}{aviso}", "GridVision", parent=self)

    # ================= Histórico =================
    def _tela_historico(self, t):
        self.titulo(t, "Histórico de análises",
                    "Todas as decisões do analista, de todos os lotes, gravadas só nesta máquina "
                    f"({pl.HISTORICO}). Vale a decisão mais recente de cada foto. "
                    "Duplo clique abre a foto para revisar de novo.")
        barra = ttk.Frame(t)
        barra.pack(fill=X, pady=(0, 8))
        self._rotulo(barra, "DECISÃO")
        self.h_dec = self._combo(barra, ["Todas", "Confirmado", "Corrigido", "Ilegível"], 12, self._preencher_historico)
        self._rotulo(barra, "STATUS")
        self.h_st = self._combo(barra, ["Todos"] + pl.STATUS, 16, self._preencher_historico)
        self._rotulo(barra, "PROBLEMA")
        self.h_prob = self._combo(barra, ["Todos"] + pl.PROBLEMAS, 28, self._preencher_historico)
        self._rotulo(barra, "BUSCAR")
        self.h_busca = tk.StringVar()
        ttk.Entry(barra, textvariable=self.h_busca, width=22).pack(side=LEFT, padx=(8, 0))
        self.h_busca.trace_add("write", lambda *a: self._preencher_historico())
        self.h_resumo = ttk.Label(t, text="", foreground=COR["ink-muted"], font=(self.f_mono, 10))
        self.h_resumo.pack(anchor=W, pady=(0, 8))
        self.h_tabela = self._tabela(
            t, ("quando", "lote", "arquivo", "status", "problemas", "decisao", "leitura", "informado", "motivo"),
            ("Analisado em", "Lote", "Foto", "Status", "Problemas", "Decisão", "Leitura final", "Leitura informada",
             "Motivo"),
            (140, 100, 220, 110, 200, 90, 90, 110, 260), "motivo")
        self.h_tabela.bind("<Double-1>", lambda e: self._abrir_da_tabela(self.h_tabela, "Histórico"))
        self.historico = []

    def _carregar_historico(self):
        try:
            self.historico = pl.carregar_historico()
        except (OSError, ValueError, KeyError) as e:
            Messagebox.show_error(f"Não consegui ler o histórico:\n{e}", "GridVision", parent=self)
            self.historico = []
        self._preencher_historico()

    def _preencher_historico(self):
        dec, st, prob = self.h_dec.get(), self.h_st.get(), self.h_prob.get()
        busca = self.h_busca.get().strip().lower()
        tv = self.h_tabela
        tv.delete(*tv.get_children())
        vis = []
        for i, r in enumerate(self.historico):
            if ((dec == "Todas" or r.decisao == dec) and (st == "Todos" or r.status == st)
                    and (prob == "Todos" or prob in r.lista_problemas)
                    and (not busca or busca in r.arquivo.lower() or busca in r.lote.lower())):
                vis.append(r)
                tv.insert("", END, iid=str(i), tags=(r.status,), values=(
                    r.analisado_em, r.lote, r.arquivo, r.status, ", ".join(r.lista_problemas) or "-", r.decisao,
                    r.leitura_final or "-", r.leitura_informada or "-", r.motivo))
        cont = {d: sum(1 for r in vis if r.decisao == d) for d in ("Confirmado", "Corrigido", "Ilegível")}
        self.h_resumo.configure(text=f"{len(vis)} de {len(self.historico)} fotos  ·  "
                                     + "  ·  ".join(f"{k} {v}" for k, v in cont.items()))


if __name__ == "__main__":
    App().mainloop()
