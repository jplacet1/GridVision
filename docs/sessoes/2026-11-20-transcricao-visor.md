# 20/11/2026: transcrição do visor (12a) e leitor CTC v1

## O que foi feito

- Projeto 7 "GridVision transcrição do visor" criado no Label Studio local com os 500 recortes do kit de 24/10, pré-preenchidos com o texto e as caixas do OCR (`criar_projeto_transcricao.py`). Login e senha ficam fora do repositório.
- Ajustes para transcrever mais rápido, sem mudar o template (as anotações já feitas ficaram intactas): Submit no Enter quando o foco não está num campo (atalho do usuário no Label Studio) e "legível, é o consumo" pré-marcado nas 330 tarefas em que o OCR leu algo. A coluna `conjunto` (treino ou validação) foi gravada nas tarefas para filtrar.
- Regra da exportação: texto e caixas só valem com a situação "legível, é o consumo" (registrada em `contexto.md`).
- João Pedro transcreveu 497 dos 500. Exportação em `gridvision_dados/transcricao/export_20261120.json`, fora do Git.
- Leitor CTC v1 ([../../experiments/leitor_ctc/treinar_transcricao.py](../../experiments/leitor_ctc/treinar_transcricao.py)): ajuste fino do ctc_v0 com 263 recortes legíveis, com o espaço entre função e leitura como símbolo. Na validação (64): texto exato 44% contra 33% do OCR atual e 19% do v0; leitura empatada com o v0 (38 contra 39). Números em `contexto.md`.
- Item 12a concluído nos três lugares; prioridades renumeradas (10d passa a ser a 1).

## Pendências

- Treinar o leitor com o recorte da caixa de leitura (ainda não usada) e ver se melhora os dígitos.
- Testar o v1 como passe extra no app (se acrescenta Confere) e como sinal do classificador de legibilidade (12h).
- 3 tarefas de treino ficaram sem anotação no projeto 7.
