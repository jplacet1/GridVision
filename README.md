# GridVision

> **Integrantes do grupo:** comecem por [docs/guia-do-grupo.md](docs/guia-do-grupo.md), que explica como usar este repositório como workspace (com o Claude Code, dados fora do Git e fluxo de branches).

O **GridVision** é um projeto de visão computacional desenvolvido como parte da disciplina de Projeto 4 (Dados) da CESAR School, em parceria com a Neoenergia Pernambuco.

O objetivo é diminuir o trabalho manual dos analistas que conferem as leituras de medidores de energia a partir das fotos de campo.

## O que o sistema faz

Para cada foto do lote, o sistema lê o **número do medidor** e a **leitura do visor** e compara com o que o leiturista informou:

- **Confere:** leitura e número batem com o informado, com confiança alta. Sai sem analista.
- **Ilegível com certeza alta** ou **sem medidor:** sai da fila (pedir nova foto).
- **Todo o resto** (diverge, confiança baixa, ilegível, sem leitura informada) vai ao analista, com o motivo e o valor lido preenchido.

O erro tolerado nas leituras resolvidas sozinhas é zero: na dúvida, a foto vai ao analista.

## Como funciona

1. **Detector** (YOLO11n treinado pelo grupo): acha medidor, visor e placa.
2. **OCR** (PP-OCRv6 e PP-OCRv5 em ONNX, na GPU ou na CPU): lê a foto inteira e os recortes do visor e da placa.
3. **Fiscal:** a leitura só vale dentro do visor; o código de função do display é separado da leitura.
4. **Classificador de legibilidade:** estima a chance de a leitura ser legível e tira da fila as fotos sem salvação.
5. **App desktop** (ttkbootstrap): processamento do lote, revisão do analista, histórico e exportação.

Detalhes, números e decisões: [docs/contexto.md](docs/contexto.md). Como rodar o app: [app/README.md](app/README.md).

## Estrutura

```text
GridVision/
├── app/            interface desktop, pipeline do lote, processamento sem interface e testes
├── src/gridvision/ extração (detector, OCR, fiscal, legibilidade) e aprendizado com as decisões
├── experiments/    experimentos, cada um com script e README de resultados agregados
└── docs/           contexto do projeto, checklist, fontes e sessões
```

As fotos e os CSVs da Neoenergia têm dados pessoais (LGPD) e nunca entram no repositório. Pesos dos modelos também ficam fora do Git.
