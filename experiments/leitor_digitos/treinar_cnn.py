# -*- coding: utf-8 -*-
"""Leitor de dígitos do visor: CNN de vários dígitos (18/10/2026).

Uso (ambiente do app, com PyTorch):
    python treinar_cnn.py <pasta leitor_digitos> [épocas] [arquitetura: v0 | v1]

v0: CNN pequena do zero, uma fatia do recorte por posição (acerto exato 20% na validação).
v1: ResNet18 pré-treinada no ImageNet (transfer learning) e 6 cabeças independentes que olham o
    recorte inteiro (cada posição aprende onde está o seu dígito).

Entrada: recorte do visor (montar_recortes.py), cinza, 64 x 192 px.
Saída: 6 posições, cada uma um dígito de 0 a 9; o rótulo é a leitura do CSV completada com zeros
à esquerda (o display mostra "007237", o CSV traz "7237"). O código de função ("03") à esquerda é
ignorado: o modelo aprende só as 6 posições da direita.
Treino: conjunto `treino`, chance de legível >= 0,6 e leitura diferente de "0".
Validação: conjunto `validacao`, mesmo filtro (rótulo fraco: o informado pelo leiturista).
O conjunto `teste` não é usado aqui.
Grava <pasta>/modelo_<arquitetura>.pt (pesos fora do Git) e imprime acerto exato e acerto por confiança.
"""
import csv, random, sys, time
from pathlib import Path
import cv2, numpy as np
import torch, torch.nn as nn, torch.nn.functional as F

PASTA = Path(sys.argv[1])
EPOCAS = int(sys.argv[2]) if len(sys.argv) > 2 else 40
ARQ = sys.argv[3] if len(sys.argv) > 3 else "v1"
N_POS, H, W = 6, 64, 192
MIN_LEGIVEL = 0.6
torch.manual_seed(42); random.seed(42); np.random.seed(42)
torch.set_num_threads(8)


def carregar(conj):
    xs, ys, nomes = [], [], []
    for r in csv.DictReader(open(PASTA / "recortes.csv", encoding="utf-8")):
        if r["conjunto"] != conj or float(r["prob_legivel"]) < MIN_LEGIVEL:
            continue
        d = "".join(ch for ch in r["leitura"] if ch.isdigit()).lstrip("0")
        if not d or len(d) > N_POS:
            continue
        img = cv2.imread(str(PASTA / "recortes" / conj / r["arquivo"].replace(".jpg", ".png")), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        xs.append(cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA))
        ys.append([int(c) for c in d.zfill(N_POS)])
        nomes.append(r["arquivo"])
    return np.array(xs, np.uint8), np.array(ys, np.int64), nomes


def aumentar(img):
    """Variações de foto de campo: brilho, contraste, desfoque, deslocamento e leve rotação."""
    img = img.astype(np.float32)
    img = img * random.uniform(0.6, 1.4) + random.uniform(-40, 40)
    if random.random() < 0.3:
        img = cv2.GaussianBlur(img, (0, 0), random.uniform(0.5, 1.5))
    M = cv2.getRotationMatrix2D((W / 2, H / 2), random.uniform(-4, 4), random.uniform(0.9, 1.1))
    M[:, 2] += (random.uniform(-8, 8), random.uniform(-4, 4))
    img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
    return np.clip(img, 0, 255)


class LeitorDigitos(nn.Module):
    def __init__(self):
        super().__init__()
        def bloco(a, b):
            return nn.Sequential(nn.Conv2d(a, b, 3, padding=1), nn.BatchNorm2d(b), nn.ReLU(),
                                 nn.Conv2d(b, b, 3, padding=1), nn.BatchNorm2d(b), nn.ReLU())
        self.f = nn.ModuleList([bloco(1, 32), bloco(32, 64), bloco(64, 128), bloco(128, 192)])
        self.drop = nn.Dropout(0.3)
        # depois de 4 poolings: 4 x 12; uma coluna-resumo por posição via pooling adaptativo
        self.cabecas = nn.Linear(192 * 2, 10)
        self.n = N_POS

    def forward(self, x):
        for b in self.f:
            x = F.max_pool2d(b(x), 2)
        x = F.adaptive_avg_pool2d(x, (2, self.n))            # (B, 192, 2, 6): uma fatia por posição
        x = x.permute(0, 3, 1, 2).flatten(2)                  # (B, 6, 384)
        return self.cabecas(self.drop(x))                     # (B, 6, 10)


class LeitorResnet(nn.Module):
    """v1: ResNet18 pré-treinada; 64 x 192 vira um mapa 512 x 2 x 6; 6 cabeças sobre o mapa inteiro."""
    def __init__(self):
        super().__init__()
        import torchvision
        r = torchvision.models.resnet18(weights=torchvision.models.ResNet18_Weights.IMAGENET1K_V1)
        self.base = nn.Sequential(r.conv1, r.bn1, r.relu, r.maxpool, r.layer1, r.layer2, r.layer3, r.layer4)
        self.drop = nn.Dropout(0.4)
        self.cabecas = nn.ModuleList([nn.Linear(512 * 2 * 6, 10) for _ in range(N_POS)])
        self.register_buffer("media", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer("desvio_px", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def forward(self, x):
        x = (x.repeat(1, 3, 1, 1) - self.media) / self.desvio_px
        f = self.drop(self.base(x).flatten(1))
        return torch.stack([c(f) for c in self.cabecas], 1)   # (B, 6, 10)


def tensor(imgs):
    return torch.from_numpy(np.stack(imgs).astype(np.float32) / 255.0).unsqueeze(1)


def avaliar(modelo, X, Y):
    modelo.eval()
    with torch.no_grad():
        prob = torch.cat([F.softmax(modelo(tensor(X[i:i + 256])), -1) for i in range(0, len(X), 256)])
    pred = prob.argmax(-1).numpy()
    conf = prob.max(-1).values.prod(-1).numpy()
    exato = (pred == Y).all(1)
    avaliar.por_digito = (pred == Y).mean()
    return exato, conf, pred


if __name__ == "__main__":
    Xtr, Ytr, _ = carregar("treino")
    Xva, Yva, nomes_va = carregar("validacao")
    print(f"treino {len(Xtr)} recortes | validação {len(Xva)} recortes")
    modelo = LeitorResnet() if ARQ == "v1" else LeitorDigitos()
    lr = 1e-3 if ARQ == "v1" else 2e-3
    otim = torch.optim.AdamW(modelo.parameters(), lr=lr, weight_decay=1e-4)
    passos = EPOCAS * ((len(Xtr) + 63) // 64)
    sched = torch.optim.lr_scheduler.OneCycleLR(otim, max_lr=lr, total_steps=passos)
    ARQUIVO = PASTA / f"modelo_{ARQ}.pt"
    melhor, t0 = -1, time.time()
    for ep in range(1, EPOCAS + 1):
        modelo.train()
        ordem = np.random.permutation(len(Xtr))
        perda_tot = 0.0
        for i in range(0, len(ordem), 64):
            idx = ordem[i:i + 64]
            x = tensor([aumentar(Xtr[j]) for j in idx])
            y = torch.from_numpy(Ytr[idx])
            perda = F.cross_entropy(modelo(x).reshape(-1, 10), y.reshape(-1))
            otim.zero_grad(); perda.backward(); otim.step(); sched.step()
            perda_tot += perda.item() * len(idx)
        exato, conf, _ = avaliar(modelo, Xva, Yva)
        if exato.mean() > melhor:
            melhor = exato.mean()
            torch.save(modelo.state_dict(), ARQUIVO)
        print(f"época {ep:2d} | perda {perda_tot / len(Xtr):.3f} | acerto exato na validação {exato.mean():.1%} | por dígito {avaliar.por_digito:.1%} | "
              f"{time.time() - t0:.0f}s", flush=True)

    modelo.load_state_dict(torch.load(ARQUIVO))
    exato, conf, _ = avaliar(modelo, Xva, Yva)
    print(f"\nmelhor época ({ARQ}): acerto exato {exato.mean():.1%}, por dígito {avaliar.por_digito:.1%}, "
          f"em {len(Xva)} recortes de validação")
    print("acerto por limiar de confiança (validação): limiar | aceitas | acerto entre as aceitas")
    for t in (0.5, 0.8, 0.9, 0.95, 0.98, 0.99):
        a = conf >= t
        if a.sum():
            print(f"  {t:.2f} | {a.sum():4d} ({a.mean():.0%}) | {exato[a].mean():.1%}")
