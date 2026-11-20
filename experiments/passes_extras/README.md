# Experimentos baratos de melhoria (20/11/2026)

Depois da [análise de erros](../analise_erros/README.md), três ideias de baixo custo foram medidas no pipeline real do app, sem alterar o app. Os passes extras entram como passes de OCR adicionais. A decisão (`extrair` + `decidir`) é a mesma do app, e a chance de legível não muda.

Gabarito (só validação): 162 decisões do analista no histórico do app e as 228 fotos da revisão cega do `lote_demo6` (11/11). Erro = Confere em foto cuja leitura o gabarito diz ilegível, ou com leitura diferente da verdadeira. Esse gabarito é enviesado para fotos difíceis (198 das 228 foram negadas pelo v1). Por isso, o ganho também foi medido no `lote_demo6` inteiro (500 fotos aleatórias da validação, sem rótulo de legibilidade para todas).

As medidas usaram o `extracao.py` que já aceita a função 103 como consumo (mudança feita em paralelo em 20/11/2026). No `lote_demo6`, o app atual deu os mesmos números de 11/11 (63 Confere, 198 negadas).

## 1. Passes extras na placa (número do medidor)

Script: [passes_extras.py](passes_extras.py). Variantes: recorte com folga de 40%, ampliação 3x e CLAHE em cinza.

| Variante | Confere (390 fotos) | Novos | Erros |
|---|---|---|---|
| App atual | 16 | - | 1 |
| Folga de 40% | 16 | 0 | 1 |
| Ampliação 3x | 16 | 0 | 1 |
| CLAHE | 17 | 1 | 1 |
| As três | 17 | 1 | 1 |

O único erro é o mesmo caso da análise de erros: 10 dígitos no histórico, provável erro de digitação. Esse caso ainda espera a conferência à mão. **Pré-processar a placa não resolve o número.** O gargalo é legibilidade ou resolução (360 x 480), não contraste nem recorte.

## 2. Código de barras da placa

Script: [codigo_barras.py](codigo_barras.py). Normas de distribuidoras (ex.: Celesc E-321.0013) pedem na placa um código de barras Code 128 com a parte numérica do número do medidor. Se decodifica, o valor é exato: o código tem verificação embutida. O zxing-cpp procura códigos na foto inteira, ampliada 1x, 2x e 3x (cerca de 0,05 s por foto, em CPU).

- Lotes demo 2 a 6 (780 fotos): código decodificado em 51 (7%), igual ao número do CSV em 36.
- Como passe extra, com confiança 0,99 no número lido do código:

| `lote_demo6` (500 fotos) | Confere | Novos | Perdidos |
|---|---|---|---|
| App atual | 63 | - | - |
| + código de barras | 67 | 4 | 0 |
| + código de barras + CLAHE na placa | 68 | 5 | 0 |

No gabarito rotulado (390 fotos): +1 e +2 Confere, nenhum erro novo. **É o ganho barato mais claro: +8% de Confere no lote aleatório.** O número sai exato, mas a leitura continua vindo do OCR. Os 5 novos Confere precisam da conferência à mão junto com os 63 do item 10d. A lista fica em `gridvision_dados/passes_extras/`, fora do Git. Para entrar no app falta: a dependência `zxing-cpp` (wheel pequena, sem dependências) e a decisão do grupo.

## 3. PARSeq no recorte do visor (não rodou)

Script pronto: [parseq_visor.py](parseq_visor.py). Num estudo de 2026 com medidores da Copel (ENIAC, UFPR-AMR e Copel-AMR), o PARSeq sem ajuste fino foi o melhor equilíbrio entre acerto e custo: 84% em contadores limpos, 38% nos degradados, 4,5 GFLOPs. VLMs como Qwen2.5-VL e DeepSeek-VL2 foram mais lentos (0,15 a 4 imagens por segundo), não acertaram mais e inventam leitura em foto ilegível. Modelos treinados no domínio chegam a 96% (Fast-OCR).

A execução foi barrada pela proteção automática do Claude Code. O `torch.hub` com `trust_repo=True` baixa e executa código do repositório `baudm/parseq` no GitHub. Para rodar, alguém do grupo precisa autorizar ou executar à mão, em ambiente separado (`venv_parseq`):

```
python experiments/passes_extras/parseq_visor.py <gridvision_dados>/passes_extras/visor <gridvision_dados>/passes_extras/visor_parseq.json
python experiments/passes_extras/passes_extras.py <export_revisao_cega.json> --parseq=<gridvision_dados>/passes_extras/visor_parseq.json
```

Expectativa realista: pelo estudo, sem ajuste fino o PARSeq fica longe do necessário em displays degradados. O caminho que funciona é o **ajuste fino com os 500 recortes transcritos (item 12a)**: PARSeq ou o leitor CTC já existente.

## Fontes

- Laroca et al., *Towards Image-based Automatic Meter Reading in Unconstrained Scenarios* (Copel-AMR, Fast-OCR), https://arxiv.org/abs/2009.10181
- Laroca et al., *Convolutional Neural Networks for Automatic Meter Reading* (UFPR-AMR), https://arxiv.org/abs/1902.09600
- Avaliação zero-shot de OCR e VLMs em medidores (ENIAC 2026), https://sol.sbc.org.br/index.php/eniac/article/download/46816/46573/
- PaddleOCR (DBNet) e PARSeq em displays de 7 segmentos (ITM Web of Conferences, 2024), https://www.itm-conferences.org/articles/itmconf/abs/2024/06/itmconf_amict2023_01007/itmconf_amict2023_01007.html
- Norma Celesc E-321.0013 (código de barras Code 128 na placa), https://celesc.com.br/arquivos/normas-tecnicas/equipamentos-medicao/E-321.0013-MEDIDOR-ELETRONICO-ENERGIA-ELETRICA-PARA-REDE-MONOFASICA-3-FIOS.pdf
