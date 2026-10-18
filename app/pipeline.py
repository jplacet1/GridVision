# -*- coding: utf-8 -*-
"""
Pipeline da interface do GridVision: carrega o lote, mede a nitidez, extrai número do medidor e leitura,
e decide o que vai para o analista.

A extração (`extrair`) usa o modelo real de src/gridvision/extracao.py (detector v0 + PaddleOCR 3.7 com o
fiscal) quando as bibliotecas e os pesos estão disponíveis. Sem eles, ou com GRIDVISION_SIMULADO=1,
volta à extração simulada, para quem só mexe na interface. A regra de decisão (`decidir`) e a nitidez são reais.
"""
import csv, hashlib, os, random, sys
from dataclasses import dataclass, asdict
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
try:
    from gridvision import extracao as _modelo
    MOTIVO_SEM_MODELO = _modelo.motivo_indisponivel()
except Exception as e:  # import quebrado não pode derrubar a interface
    _modelo, MOTIVO_SEM_MODELO = None, f"módulo do modelo não carregou ({e})"
if os.environ.get("GRIDVISION_SIMULADO") == "1":
    MOTIVO_SEM_MODELO = "GRIDVISION_SIMULADO=1"
MODELO_REAL = MOTIVO_SEM_MODELO is None

EXTENSOES = {".jpg", ".jpeg", ".png"}
LIMIAR_NITIDEZ = 100.0     # variância do Laplaciano, mesmo limiar da EDA
LIMIAR_CONFIANCA = 0.90    # provisório: abaixo disso o sistema não decide sozinho (erro tolerado é zero)

CONFERE = "Confere"
DIVERGE = "Diverge"
LIDO = "Lido"
REVISAO = "Revisão manual"
ILEGIVEL = "Ilegível"
SEM_MEDIDOR = "Sem medidor"
STATUS = [CONFERE, DIVERGE, LIDO, REVISAO, ILEGIVEL, SEM_MEDIDOR]

# Só "Confere" sai sem analista. "Lido" (sem leitura informada) volta ao analista com o valor lido.
AUTOMATICOS = {CONFERE}
# Fora da fila de revisão (decisão do grupo, 18/10/2026): sem medidor na foto não há o que revisar.
# Continuam na tabela de resultados e na exportação, marcadas como excluídas.
EXCLUIDOS = {SEM_MEDIDOR}

# Tipos de problema, para filtrar resultados e histórico. Uma foto pode ter mais de um.
P_SEM_MEDIDOR = "Sem medidor"
P_SEM_VISOR = "Visor não encontrado"
P_SEM_PLACA = "Placa não encontrada"
P_LEITURA = "Leitura não lida"
P_NUMERO = "Número não lido"
P_FUNCAO = "Display em outra função"
P_DIVERGE = "Leitura diferente da informada"
P_CONFIANCA = "Confiança baixa"
P_BORRADA = "Foto borrada"
P_SEM_INFORMADO = "Sem leitura informada"
PROBLEMAS = [P_SEM_MEDIDOR, P_SEM_VISOR, P_SEM_PLACA, P_LEITURA, P_NUMERO, P_FUNCAO, P_DIVERGE,
             P_CONFIANCA, P_BORRADA, P_SEM_INFORMADO]

# Histórico das decisões do analista: arquivo local, fora do Git (tem nomes de fotos e leituras).
HISTORICO = Path(os.environ.get("GRIDVISION_HISTORICO", Path.home() / "gridvision_dados" / "historico" / "historico.csv"))
CAMPOS_HISTORICO = ["analisado_em", "lote", "arquivo", "caminho", "status", "problemas", "numero_lido", "leitura_lida",
                    "numero_informado", "leitura_informada", "decisao", "numero_final", "leitura_final",
                    "confianca", "nitidez", "motivo"]


@dataclass
class Extracao:
    tem_medidor: bool
    numero: str        # vazio se ilegível
    leitura: str       # vazio se ilegível
    confianca: float   # 0 a 1
    detalhe: str = ""  # o que o modelo achou (caixas, fiscal); vai para o motivo


@dataclass
class Resultado:
    arquivo: str
    caminho: str
    nitidez: float
    numero_lido: str
    leitura_lida: str
    confianca: float
    numero_informado: str
    leitura_informada: str
    status: str
    motivo: str
    decisao: str = ""          # preenchido na revisão: Confirmado, Corrigido, Ilegível
    numero_final: str = ""
    leitura_final: str = ""
    problemas: str = ""        # tipos de problema separados por " | " (ver PROBLEMAS)
    lote: str = ""             # nome da pasta do lote
    analisado_em: str = ""     # data e hora da decisão do analista

    @property
    def lista_problemas(self):
        return [p for p in self.problemas.split(" | ") if p]

    @property
    def precisa_analista(self):
        return self.status not in AUTOMATICOS | EXCLUIDOS

    @property
    def excluido(self):
        return self.status in EXCLUIDOS

    @property
    def pendente(self):
        return self.precisa_analista and not self.decisao


def listar_fotos(pasta):
    return sorted(p for p in Path(pasta).iterdir() if p.suffix.lower() in EXTENSOES)


def carregar_informado(caminho_csv):
    """CSV no formato da base: separador `;`, colunas `Foto do medidor`, `Numero do medidor`,
    `Posicao do medidor lida`. "NA" é texto, não vazio. Devolve {arquivo: (numero, leitura)}."""
    informado = {}
    with open(caminho_csv, encoding="utf-8-sig", newline="") as f:
        for linha in csv.DictReader(f, delimiter=";"):
            foto = (linha.get("Foto do medidor") or "").strip()
            if foto and foto != "NA":
                informado[foto] = ((linha.get("Numero do medidor") or "").strip(),
                                   (linha.get("Posicao do medidor lida") or "").strip())
    return informado


def nitidez(caminho):
    """Variância do Laplaciano em tons de cinza. Aproximação em Pillow (o kernel satura em 0..255),
    então o valor pode diferir um pouco do OpenCV usado na EDA."""
    cinza = Image.open(caminho).convert("L")
    lap = cinza.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128))
    return ImageStat.Stat(lap).var[0]


def conjuntos_do_lote(fotos):
    """Quantas fotos do lote estão em cada conjunto da divisão (experiments/piloto_anotacao/divisao_v1.csv).
    Rodar o app não ensina nada ao modelo, mas: fotos de treino não servem para medir, e teste e teste
    temporal ficam reservados para a medida final (não ajustar regras olhando para eles)."""
    divisao = RAIZ / "experiments" / "piloto_anotacao" / "divisao_v1.csv"
    if not divisao.exists():
        return {}
    with open(divisao, encoding="utf-8") as f:
        conj = {l["arquivo"]: l["conjunto"] for l in csv.DictReader(f)}
    cont = {}
    for p in fotos:
        c = conj.get(Path(p).name)
        if c:
            cont[c] = cont.get(c, 0) + 1
    return cont


def extrair(caminho, informado=None, nitida=True):
    if MODELO_REAL:
        r = _modelo.extrair(caminho, informado)
        return Extracao(r.tem_medidor, r.numero, r.leitura, r.confianca, r.detalhe)
    return _extrair_simulado(caminho, informado, nitida)


def _extrair_simulado(caminho, informado=None, nitida=True):
    """SIMULADO. Gera um resultado determinístico por nome de arquivo para exercitar o fluxo da interface."""
    rnd = random.Random(hashlib.md5(Path(caminho).name.encode()).hexdigest())
    if rnd.random() < 0.11:
        return Extracao(False, "", "", rnd.uniform(0.6, 0.99))
    if rnd.random() < (0.25 if nitida else 0.7):
        return Extracao(True, "", "", rnd.uniform(0.1, 0.5))
    numero, leitura = informado or ("", "")
    numero = numero or "".join(rnd.choice("0123456789") for _ in range(8))
    leitura = leitura or str(rnd.randint(100, 99999))
    if rnd.random() < 0.15 and leitura:
        i = rnd.randrange(len(leitura))
        leitura = leitura[:i] + str((int(leitura[i]) + 1) % 10 if leitura[i].isdigit() else 0) + leitura[i + 1:]
    return Extracao(True, numero, leitura, rnd.uniform(0.7, 0.999) if nitida else rnd.uniform(0.4, 0.95))


def mesma_leitura(a, b):
    # o visor mostra zeros à esquerda (042884) que o CSV não tem (42884)
    return a.lstrip("0") == b.lstrip("0")


def decidir(ext, informado):
    """Devolve (status, motivo). O sistema só decide sozinho quando tem certeza; o resto vai ao analista."""
    if not ext.tem_medidor:
        return SEM_MEDIDOR, "nenhum medidor encontrado na foto"
    if not ext.leitura or not ext.numero:
        return ILEGIVEL, "número ou leitura não legível na foto"
    if ext.confianca < LIMIAR_CONFIANCA:
        return REVISAO, f"confiança {ext.confianca:.2f} abaixo de {LIMIAR_CONFIANCA:.2f}"
    if not informado or not informado[1]:
        return LIDO, "sem leitura informada; confirmar o valor lido"
    if mesma_leitura(ext.leitura, informado[1]):
        return CONFERE, "leitura da foto igual à informada"
    return DIVERGE, f"foto {ext.leitura}, informado {informado[1]}"


def classificar_problemas(ext, status, nit, informado):
    """Tipos de problema de uma foto, a partir do que o modelo achou e da decisão."""
    p = []
    if status == SEM_MEDIDOR:
        return [P_SEM_MEDIDOR]
    det = ext.detalhe or ""
    if "sem visor" in det: p.append(P_SEM_VISOR)
    if "sem placa" in det: p.append(P_SEM_PLACA)
    if "display não mostra o consumo" in det: p.append(P_FUNCAO)
    elif not ext.leitura and "sem visor" not in det: p.append(P_LEITURA)
    if not ext.numero: p.append(P_NUMERO)
    if status == DIVERGE: p.append(P_DIVERGE)
    if status == REVISAO: p.append(P_CONFIANCA)
    if status == LIDO: p.append(P_SEM_INFORMADO)
    if nit < LIMIAR_NITIDEZ: p.append(P_BORRADA)
    return p


def processar(caminho, informado=None):
    caminho = Path(caminho)
    nit = nitidez(caminho)
    ext = extrair(caminho, informado, nitida=nit >= LIMIAR_NITIDEZ)
    status, motivo = decidir(ext, informado)
    if ext.detalhe:
        motivo += f" [{ext.detalhe}]"
    if nit < LIMIAR_NITIDEZ and status != CONFERE:
        motivo += f" (foto borrada, nitidez {nit:.0f})"
    num_inf, leit_inf = informado or ("", "")
    return Resultado(caminho.name, str(caminho), nit, ext.numero, ext.leitura, ext.confianca,
                     num_inf, leit_inf, status, motivo,
                     problemas=" | ".join(classificar_problemas(ext, status, nit, informado)),
                     lote=caminho.parent.name)


def registrar_decisao(r):
    """Acrescenta a decisão do analista ao histórico (uma linha por decisão; revisar de novo
    acrescenta outra linha, e a mais recente vale)."""
    from datetime import datetime
    r.analisado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    HISTORICO.parent.mkdir(parents=True, exist_ok=True)
    novo = not HISTORICO.exists()
    linha = asdict(r)
    linha["confianca"], linha["nitidez"] = f"{r.confianca:.3f}", f"{r.nitidez:.1f}"
    with open(HISTORICO, "a", encoding="utf-8-sig" if novo else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_HISTORICO, delimiter=";", extrasaction="ignore")
        if novo:
            w.writeheader()
        w.writerow(linha)


def carregar_historico():
    """Decisões do histórico, a mais recente de cada foto primeiro. Devolve [Resultado]."""
    if not HISTORICO.exists():
        return []
    with open(HISTORICO, encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    vistos, saida = set(), []
    for l in sorted(linhas, key=lambda l: l["analisado_em"], reverse=True):
        chave = (l["lote"], l["arquivo"])
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append(Resultado(l["arquivo"], l["caminho"], float(l["nitidez"] or 0), l["numero_lido"],
                               l["leitura_lida"], float(l["confianca"] or 0), l["numero_informado"],
                               l["leitura_informada"], l["status"], l["motivo"], l["decisao"],
                               l["numero_final"], l["leitura_final"], l["problemas"], l["lote"], l["analisado_em"]))
    return saida


def exportar(resultados, destino):
    campos = [k for k in asdict(resultados[0]) if k != "caminho"] if resultados else []
    with open(destino, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        for r in resultados:
            linha = asdict(r)
            linha.pop("caminho")
            if r.excluido and not r.decisao:
                linha["decisao"] = "Excluída (sem medidor)"
            linha["confianca"] = f"{r.confianca:.3f}"
            linha["nitidez"] = f"{r.nitidez:.1f}"
            w.writerow(linha)
