# -*- coding: utf-8 -*-
"""
Interface desktop do GridVision (protótipo em ttkbootstrap).

Fluxo: 1 Lote (pasta de fotos e CSV opcional) > 2 Processamento > 3 Resultados > 4 Revisão > 5 Exportação.

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


def familia(preferidas, reserva="Segoe UI"):
    instaladas = set(tkfont.families())
    return next((f for f in preferidas if f in instaladas), reserva)


class App(ttk.Window):
    def __init__(self):
        super().__init__(title="GridVision", size=(1180, 760), minsize=(980, 640))
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
        self.fila_revisao = []
        self.pos_revisao = 0
        self._cancelar = threading.Event()
        self._fila = queue.Queue()

        self._cabecalho()
        self.corpo = ttk.Frame(self, padding=(24, 16))
        self.corpo.pack(fill=BOTH, expand=YES)
        self.telas = {n: ttk.Frame(self.corpo) for n in ETAPAS}
        self._tela_lote(self.telas["Lote"])
        self._tela_processamento(self.telas["Processamento"])
        self._tela_resultados(self.telas["Resultados"])
        self._tela_revisao(self.telas["Revisão"])
        self._tela_exportacao(self.telas["Exportação"])
        self.ir("Lote")

    # ---------- estrutura ----------
    def _cabecalho(self):
        topo = ttk.Frame(self, padding=(24, 16, 24, 8))
        topo.pack(fill=X)
        ttk.Label(topo, text="GridVision", font=(self.f_display, 20, "bold")).pack(side=LEFT)
        ttk.Label(topo, text="Leitura de medidores por foto", foreground=COR["ink-muted"],
                  font=(self.f_sans, 10)).pack(side=LEFT, padx=(12, 0), pady=(8, 0))
        self.passos = ttk.Frame(topo)
        self.passos.pack(side=RIGHT)
        self.rotulos_passo = {}
        for i, n in enumerate(ETAPAS, 1):
            lb = ttk.Label(self.passos, text=f"{i}  {n.upper()}", font=(self.f_sans, 9, "bold"), padding=(10, 4))
            lb.pack(side=LEFT)
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
        aviso = ttk.Label(self, text=texto_aviso, foreground=cor_aviso, font=(self.f_sans, 9), padding=(24, 6))
        aviso.pack(fill=X)

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

    def ir(self, nome):
        for t in self.telas.values():
            t.pack_forget()
        self.telas[nome].pack(fill=BOTH, expand=YES)
        for n, lb in self.rotulos_passo.items():
            lb.configure(foreground=COR["action"] if n == nome else COR["ink-muted"])

    def titulo(self, pai, texto, sub=None):
        ttk.Label(pai, text=texto, font=(self.f_display, 16, "bold")).pack(anchor=W)
        if sub:
            ttk.Label(pai, text=sub, foreground=COR["ink-muted"], wraplength=900,
                      justify=LEFT).pack(anchor=W, pady=(4, 16))

    # ---------- 1. Lote ----------
    def _tela_lote(self, t):
        self.titulo(t, "Novo lote", "Escolha a pasta com as fotos do lote. O CSV com a leitura informada pelo "
                                    "leiturista é opcional: com ele o sistema compara as leituras; sem ele, "
                                    "devolve o valor lido para o analista confirmar.")
        form = ttk.Frame(t)
        form.pack(fill=X)
        self._campo_arquivo(form, 0, "Pasta de fotos", self.pasta, self._escolher_pasta)
        self._campo_arquivo(form, 1, "CSV informado (opcional)", self.csv, self._escolher_csv)
        form.columnconfigure(1, weight=1)
        self.info_lote = ttk.Label(t, text="", foreground=COR["ink-muted"])
        self.info_lote.pack(anchor=W, pady=(12, 0))
        ttk.Label(t, text="Os dados ficam só nesta máquina, fora do repositório (LGPD).",
                  foreground=COR["ink-muted"], font=(self.f_sans, 9)).pack(anchor=W, pady=(4, 0))
        ttk.Button(t, text="Processar lote", bootstyle=PRIMARY, command=self.iniciar,
                   padding=(16, 8)).pack(anchor=W, pady=(24, 0))

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

    # ---------- 2. Processamento ----------
    def _tela_processamento(self, t):
        self.titulo(t, "Processando lote", "Para cada foto: nitidez, extração do número do medidor e da "
                                           "leitura, e decisão.")
        self.progresso = ttk.Progressbar(t, bootstyle=PRIMARY, length=600)
        self.progresso.pack(fill=X, pady=(8, 8))
        self.txt_progresso = ttk.Label(t, text="", font=(self.f_mono, 10))
        self.txt_progresso.pack(anchor=W)
        self.txt_atual = ttk.Label(t, text="", foreground=COR["ink-muted"], font=(self.f_mono, 9))
        self.txt_atual.pack(anchor=W, pady=(4, 0))
        ttk.Button(t, text="Cancelar", bootstyle=(DANGER, OUTLINE),
                   command=self._cancelar.set).pack(anchor=W, pady=(24, 0))

    def iniciar(self):
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
        self.resultados = []
        self._cancelar.clear()
        self.progresso.configure(maximum=len(fotos), value=0)
        self.ir("Processamento")
        threading.Thread(target=self._trabalhar, args=(fotos, informado), daemon=True).start()
        self.after(50, self._acompanhar)

    def _trabalhar(self, fotos, informado):
        for i, f in enumerate(fotos, 1):
            if self._cancelar.is_set():
                break
            try:
                r = pl.processar(f, informado.get(f.name))
            except OSError as e:
                r = pl.Resultado(f.name, str(f), 0.0, "", "", 0.0, "", "", pl.REVISAO, f"erro ao abrir: {e}")
            self._fila.put(("item", i, len(fotos), r))
        self._fila.put(("fim",))

    def _acompanhar(self):
        try:
            while True:
                msg = self._fila.get_nowait()
                if msg[0] == "fim":
                    self.mostrar_resultados()
                    return
                _, i, n, r = msg
                self.resultados.append(r)
                self.progresso.configure(value=i)
                self.txt_progresso.configure(text=f"{i} de {n} fotos")
                self.txt_atual.configure(text=r.arquivo)
        except queue.Empty:
            pass
        self.after(50, self._acompanhar)

    # ---------- 3. Resultados ----------
    def _tela_resultados(self, t):
        self.titulo(t, "Resultados do lote")
        self.cartoes = ttk.Frame(t)
        self.cartoes.pack(fill=X, pady=(8, 16))
        barra = ttk.Frame(t)
        barra.pack(fill=X, pady=(0, 8))
        ttk.Label(barra, text="FILTRO", font=(self.f_sans, 9, "bold"),
                  foreground=COR["ink-muted"]).pack(side=LEFT, padx=(0, 8))
        self.filtro = ttk.Combobox(barra, state="readonly", width=24,
                                   values=["Todos", "Pendentes do analista"] + pl.STATUS)
        self.filtro.set("Pendentes do analista")
        self.filtro.pack(side=LEFT)
        self.filtro.bind("<<ComboboxSelected>>", lambda e: self._preencher_tabela())
        ttk.Button(barra, text="Exportar", bootstyle=(SECONDARY, OUTLINE),
                   command=lambda: self.ir_exportacao()).pack(side=RIGHT)
        ttk.Button(barra, text="Revisar pendentes", bootstyle=PRIMARY,
                   command=self.revisar_pendentes).pack(side=RIGHT, padx=(0, 8))

        cols = ("arquivo", "status", "numero", "leitura", "informado", "confianca", "decisao", "motivo")
        nomes = ("Foto", "Status", "Nº lido", "Leitura lida", "Leitura informada", "Confiança", "Decisão", "Motivo")
        larguras = (230, 120, 110, 100, 120, 80, 100, 320)
        quadro = ttk.Frame(t)
        quadro.pack(fill=BOTH, expand=YES)
        self.tabela = ttk.Treeview(quadro, columns=cols, show=HEADINGS, bootstyle=PRIMARY)
        for c, n, w in zip(cols, nomes, larguras):
            self.tabela.heading(c, text=n, anchor=W)
            self.tabela.column(c, width=w, anchor=W, stretch=(c == "motivo"))
        for s, c in COR_STATUS.items():
            self.tabela.tag_configure(s, foreground=COR[c])
        rolagem = ttk.Scrollbar(quadro, orient=VERTICAL, command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=rolagem.set)
        self.tabela.pack(side=LEFT, fill=BOTH, expand=YES)
        rolagem.pack(side=RIGHT, fill=Y)
        self.tabela.bind("<Double-1>", self._abrir_linha)

    def mostrar_resultados(self):
        for w in self.cartoes.winfo_children():
            w.destroy()
        n = len(self.resultados)
        auto = sum(1 for r in self.resultados if r.status in pl.AUTOMATICOS)
        pend = sum(1 for r in self.resultados if r.pendente)
        self._cartao("Fotos", str(n), "ink")
        self._cartao("Confere automático", f"{auto / n:.0%}" if n else "-", "action")
        self._cartao("Pendentes", str(pend), "warn" if pend else "ok")
        for s in pl.STATUS:
            self._cartao(s, str(sum(1 for r in self.resultados if r.status == s)), COR_STATUS[s])
        self._preencher_tabela()
        self.ir("Resultados")

    def _cartao(self, rotulo, valor, cor):
        c = ttk.Frame(self.cartoes, bootstyle=DARK, padding=(16, 10))
        c.pack(side=LEFT, padx=(0, 8), fill=Y)
        ttk.Label(c, text=rotulo.upper(), font=(self.f_sans, 8, "bold"), foreground=COR["ink-muted"],
                  bootstyle=(INVERSE, DARK)).pack(anchor=W)
        ttk.Label(c, text=valor, font=(self.f_mono, 18), foreground=COR[cor],
                  bootstyle=(INVERSE, DARK)).pack(anchor=W)

    def _visiveis(self):
        f = self.filtro.get()
        if f == "Todos":
            return list(self.resultados)
        if f == "Pendentes do analista":
            return [r for r in self.resultados if r.pendente]
        return [r for r in self.resultados if r.status == f]

    def _preencher_tabela(self):
        self.tabela.delete(*self.tabela.get_children())
        visiveis = {id(r) for r in self._visiveis()}
        for i, r in enumerate(self.resultados):
            if id(r) in visiveis:
                self.tabela.insert("", END, iid=str(i), tags=(r.status,), values=(
                    r.arquivo, r.status, r.numero_final or r.numero_lido or "-",
                    r.leitura_final or r.leitura_lida or "-", r.leitura_informada or "-",
                    f"{r.confianca:.2f}",
                    r.decisao or ("Excluída" if r.excluido else "-" if r.precisa_analista else "Automático"),
                    r.motivo))

    def _abrir_linha(self, ev):
        sel = self.tabela.focus()
        if sel:
            self.fila_revisao = [self.resultados[int(i)] for i in self.tabela.get_children()]
            self.pos_revisao = self.fila_revisao.index(self.resultados[int(sel)])
            self._mostrar_revisao()

    def revisar_pendentes(self):
        self.fila_revisao = [r for r in self.resultados if r.pendente]
        if not self.fila_revisao:
            Messagebox.show_info("Nenhuma foto pendente.", "GridVision", parent=self)
            return
        self.pos_revisao = 0
        self._mostrar_revisao()

    # ---------- 4. Revisão ----------
    def _tela_revisao(self, t):
        topo = ttk.Frame(t)
        topo.pack(fill=X)
        ttk.Label(topo, text="Revisão do analista", font=(self.f_display, 16, "bold")).pack(side=LEFT)
        self.txt_pos = ttk.Label(topo, text="", font=(self.f_mono, 10), foreground=COR["ink-muted"])
        self.txt_pos.pack(side=RIGHT)

        corpo = ttk.Frame(t)
        corpo.pack(fill=BOTH, expand=YES, pady=(16, 0))
        self.foto = ttk.Label(corpo, background=COR["surface-raised"], anchor=CENTER)
        self.foto.pack(side=LEFT, fill=Y)
        lado = ttk.Frame(corpo, padding=(24, 0, 0, 0))
        lado.pack(side=LEFT, fill=BOTH, expand=YES)

        self.txt_arquivo = ttk.Label(lado, font=(self.f_mono, 10), foreground=COR["ink-muted"])
        self.txt_arquivo.pack(anchor=W)
        self.txt_status = ttk.Label(lado, font=(self.f_display, 14, "bold"))
        self.txt_status.pack(anchor=W, pady=(8, 0))
        self.txt_motivo = ttk.Label(lado, foreground=COR["ink-muted"], wraplength=420, justify=LEFT)
        self.txt_motivo.pack(anchor=W, pady=(2, 16))

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
        acoes.pack(fill=X, pady=(20, 0))
        ttk.Button(acoes, text="Confirmar (Enter)", bootstyle=SUCCESS,
                   command=lambda: self._decidir("Confirmado")).pack(side=LEFT)
        ttk.Button(acoes, text="Ilegível", bootstyle=(WARNING, OUTLINE),
                   command=lambda: self._decidir("Ilegível")).pack(side=LEFT, padx=8)
        nav = ttk.Frame(lado)
        nav.pack(fill=X, pady=(12, 0))
        ttk.Button(nav, text="Anterior", bootstyle=(SECONDARY, OUTLINE),
                   command=lambda: self._mover(-1)).pack(side=LEFT)
        ttk.Button(nav, text="Pular", bootstyle=(SECONDARY, OUTLINE),
                   command=lambda: self._mover(1)).pack(side=LEFT, padx=8)
        ttk.Button(nav, text="Voltar aos resultados", bootstyle=(SECONDARY, LINK),
                   command=self.mostrar_resultados).pack(side=RIGHT)
        ttk.Label(lado, text="Se editar o número ou a leitura, a decisão fica como Corrigido.",
                  foreground=COR["ink-muted"], font=(self.f_sans, 9)).pack(anchor=W, pady=(16, 0))
        self.bind("<Return>", lambda e: self._decidir("Confirmado") if self.telas["Revisão"].winfo_ismapped() else None)

    def _mostrar_revisao(self):
        r = self.fila_revisao[self.pos_revisao]
        self.txt_pos.configure(text=f"{self.pos_revisao + 1} de {len(self.fila_revisao)}")
        self.txt_arquivo.configure(text=r.arquivo)
        self.txt_status.configure(text=r.status + (f"  ·  {r.decisao}" if r.decisao else ""),
                                  foreground=COR[COR_STATUS[r.status]])
        self.txt_motivo.configure(text=r.motivo)
        self.v_numero.set(r.numero_final or r.numero_lido)
        self.v_leitura.set(r.leitura_final or r.leitura_lida)
        self.v_num_inf.set(r.numero_informado or "-")
        self.v_leit_inf.set(r.leitura_informada or "-")
        self.v_conf.set(f"{r.confianca:.2f}  ·  nitidez {r.nitidez:.0f}")
        try:
            img = Image.open(r.caminho)
            img.thumbnail((420, 560))
            self._img = ImageTk.PhotoImage(img)
            self.foto.configure(image=self._img, text="")
        except OSError:
            self._img = None
            self.foto.configure(image="", text="Não foi possível abrir a foto", width=40)
        self.ir("Revisão")
        self.campo_leitura.focus_set()
        self.campo_leitura.select_range(0, END)

    def _decidir(self, decisao):
        r = self.fila_revisao[self.pos_revisao]
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
        self._mover(1)

    def _mover(self, passo):
        novo = self.pos_revisao + passo
        if 0 <= novo < len(self.fila_revisao):
            self.pos_revisao = novo
            self._mostrar_revisao()
        elif novo >= len(self.fila_revisao):
            self.mostrar_resultados()

    # ---------- 5. Exportação ----------
    def _tela_exportacao(self, t):
        self.titulo(t, "Exportar resultado", "Gera um CSV (separador ;) com o status, o valor lido, o informado "
                                             "e a decisão do analista de cada foto. Salve fora do repositório.")
        self.txt_export = ttk.Label(t, text="", font=(self.f_mono, 10))
        self.txt_export.pack(anchor=W, pady=(0, 16))
        linha = ttk.Frame(t)
        linha.pack(anchor=W)
        ttk.Button(linha, text="Salvar CSV", bootstyle=PRIMARY, padding=(16, 8),
                   command=self._salvar).pack(side=LEFT)
        ttk.Button(linha, text="Voltar aos resultados", bootstyle=(SECONDARY, LINK),
                   command=self.mostrar_resultados).pack(side=LEFT, padx=8)
        ttk.Button(linha, text="Novo lote", bootstyle=(SECONDARY, LINK),
                   command=lambda: self.ir("Lote")).pack(side=LEFT)

    def ir_exportacao(self):
        pend = sum(1 for r in self.resultados if r.pendente)
        self.txt_export.configure(text=f"{len(self.resultados)} fotos · {pend} ainda pendentes do analista")
        self.ir("Exportação")

    def _salvar(self):
        p = filedialog.asksaveasfilename(title="Salvar resultado", defaultextension=".csv",
                                         initialfile="resultado_gridvision.csv", filetypes=[("CSV", "*.csv")])
        if p:
            pl.exportar(self.resultados, p)
            Messagebox.show_info(f"Resultado salvo em\n{p}", "GridVision", parent=self)


if __name__ == "__main__":
    App().mainloop()
