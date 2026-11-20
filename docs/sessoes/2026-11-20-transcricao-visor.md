# 20/11/2026: transcrição do visor (12a), leitor CTC v1 conferência dos Confere (10d) e valores-alvo (11)

## O que foi feito

- Projeto 7 "GridVision transcrição do visor" criado no Label Studio local com os 500 recortes do kit de 24/10, pré-preenchidos com o texto e as caixas do OCR (`criar_projeto_transcricao.py`). Login e senha ficam fora do repositório.
- Ajustes para transcrever mais rápido, sem mudar o template (as anotações já feitas ficaram intactas): Submit no Enter quando o foco não está num campo (atalho do usuário no Label Studio) e "legível, é o consumo" pré-marcado nas 330 tarefas em que o OCR leu algo. A coluna `conjunto` (treino ou validação) foi gravada nas tarefas para filtrar.
- Regra da exportação: texto e caixas só valem com a situação "legível, é o consumo" (registrada em `contexto.md`).
- João Pedro transcreveu 497 dos 500. Exportação em `gridvision_dados/transcricao/export_20261120.json`, fora do Git.
- Leitor CTC v1 ([../../experiments/leitor_ctc/treinar_transcricao.py](../../experiments/leitor_ctc/treinar_transcricao.py)): ajuste fino do ctc_v0 com 263 recortes legíveis, com o espaço entre função e leitura como símbolo. Na validação (64): texto exato 44% contra 33% do OCR atual e 19% do v0; leitura empatada com o v0 (38 contra 39). Números em `contexto.md`.
- Item 12a concluído nos três lugares; prioridades renumeradas (10d passa a ser a 1).
- Item 10d: a 10d tinha sido marcada como concluída sem querer no artefato; voltou para em andamento. Projeto 8 "GridVision conferência dos Confere (lote_demo6)" criado no Label Studio local ([../../experiments/medida_mvp/conferir_confere.py](../../experiments/medida_mvp/conferir_confere.py)): foto inteira com zoom, leitura e número conferidos pelo app ao lado, cinco respostas sem pré-marcação. Resultado: 63 de 63 certos (erro zero; 0 em 90 somando lote_demo2 e validação). 10d concluída nos três lugares; o 11 passa a ser a prioridade 1.
- Item 11: valores-alvo definidos pelo João Pedro (pelo grupo) e registrados em `contexto.md`: localização mAP50 ≥ 0,90 por classe e "tem medidor?" ≥ 95%; acerto exato ≥ 50%; erro no Confere 0 e legíveis entre as negadas ≤ 5%; cobertura ≥ 50%. Hoje passam localização, erro no Confere e cobertura; não passam acerto exato (40%) e negadas (23% no limiar 0,40). Item em andamento até a resposta do professor Erick (a Neoenergia não vai validar).

## Pendências

- Treinar o leitor com o recorte da caixa de leitura (ainda não usada) e ver se melhora os dígitos.
- Testar o v1 como passe extra no app (se acrescenta Confere) e como sinal do classificador de legibilidade (12h).
- 3 tarefas de treino ficaram sem anotação no projeto 7.
- Pedir ao professor Erick que valide os valores-alvo; a Neoenergia não vai validar. Sem resposta, seguir com os valores do grupo, registrados como não validados.
- Conflito a resolver na 12h: cumprir ≤ 5% de legíveis entre as negadas baixa o limiar e derruba a cobertura abaixo de 50%, a menos que o leitor e o classificador melhorem.
