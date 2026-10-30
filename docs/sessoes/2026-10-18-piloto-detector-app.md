# Sessão de 05 a 18/10/2026: baseline, piloto, detector e app com modelo

Conversa longa do João Pedro com o Claude Code. Números e decisões estão em [../contexto.md](../contexto.md) (seções Dados e "17 e 18/10/2026"); aqui só o fio da meada.

**Feito**
- Guia do grupo ([../guia-do-grupo.md](../guia-do-grupo.md)) e skill `/salvar-contexto` versionada.
- Baseline do Henrique recebido e reconferido (05/10): leitura 20%, número do medidor 38% igual / 42% contido.
- Atendimento de 17/10 (notas do Granola): professor gostou do SR1; interface obrigatória; pauta de 24/10 = cronograma revisado + proposta de front-end.
- Experimento de OCR 1: ampliar a foto 2x leva a leitura de 20 para 28 (mesmo modelo, p = 0,02). CLAHE não ajuda no PaddleOCR 3.7. Os modelos do 3.7 são PP-OCRv6 medium (o baseline usou v5).
- Divisão treino/validação/teste por medidor e piloto de 300 fotos anotadas no Label Studio.
- Detector v0 (YOLO11n): mAP50 0,942 em 200 fotos de validação + teste, pré-anotadas e corrigidas à mão.
- Teto de legibilidade medido: leitura 56%, leitura e número juntos 46%, abaixo da meta de 50%.
- Recorte do visor + OCR pronto: 23 de 100 com ampliação 2x (contra 28 da foto inteira); o gargalo é o OCR genérico lendo display.
- Protótipo desktop (`app/`, ttkbootstrap) ligado ao modelo real (`src/gridvision/extracao.py`), com fiscal, função 03, leitura sem zeros, sem medidor fora da revisão, histórico, filtro por problema, etapas clicáveis e exportação por filtro ou seleção.
- Correção: o "Nº do medidor" mostrava o texto informado inteiro ("a/b/c") quando só um número batia; agora mostra só o número lido.
- Dois artefatos: "Experimento de OCR 1" e "Piloto e detector v0" (links em contexto.md).

**Pendências para a próxima conversa**
- 24/10: cronograma revisado (incluir o teto de 46% contra a meta de 50%) e decisão desktop ou web.
- Medir o MVP nas 100 fotos de validação anotadas: cobertura, perdas e erros ("Confere" em foto ilegível tem de ser zero); calibrar o limiar de 0,90.
- Decidir se o sistema confere só a leitura (número do cadastro) ou leitura e número.
- Velocidade: comparar PP-OCRv5 mobile com v6 medium e processar fotos em paralelo (≈ 10 s por foto hoje; a GPU AMD não acelera Paddle no Windows).
- Reconhecedor próprio do visor (ajuste fino com recortes legíveis); comparar EasyOCR e Tesseract.
- Certeza de legibilidade por foto (opção A, classificador simples sobre sinais do detector e do OCR, decidido em 18/10); definir o destino das fotos excluídas (pedir nova foto?).
- Abrir e mesclar os PRs de `docs/guia-do-grupo` e `docs/baseline-ocr`; atualizar o Notion com o trabalho de 18/10.
