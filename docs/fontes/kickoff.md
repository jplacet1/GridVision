# Kickoff (12/09/2026)

Fonte: `GridVision_Kickoff.pdf` (Drive, Entregáveis SR1; o arquivo interno se chama `GridVision_Kickoff_v2.pptx`). Equipe: Alana Cavalcanti, João Pedro Lins, Henrique Bouwman.

## Agenda

Contexto e definição do problema; solução proposta; a jornada; encerramento.

## Contexto do cliente

Distribuidora que atende praticamente todo o estado de Pernambuco, ex-Celpe, parte do grupo Neoenergia (Iberdrola) desde 2021. Na leitura e entrega de contas, os leituristas visitam quase todos os clientes mensalmente. Toda leitura gera um registro fotográfico do medidor, feito pelo leiturista, como comprovação.

## Dores

- Controle de qualidade: nem sempre dá para confirmar se a foto corresponde ao medidor.
- Tempo e custo: revisar milhares de fotos manualmente consome recursos e atrasa processos.
- Risco de inconsistências: erros de leitura e questionamentos de clientes.

Causa raiz: ausência de solução automatizada capaz de analisar grandes volumes de imagens e apoiar a fiscalização. Quem mais sente: o cliente final (o erro chega na fatura).

## Objetivo

Desenvolver uma solução baseada em dados e IA para auxiliar a fiscalização das imagens de leitura, mais eficiente, escalável e confiável.

## Persona e premissas

Persona: analista da equipe de fiscalização de leitura da Neoenergia PE, que hoje revisa manualmente as fotos.

1. A IA apoia o auditor, não substitui a decisão humana.
2. Toda reprovação vem com o motivo, e o auditor pode discordar.
3. A qualidade depende dos dados disponíveis.
4. Desenvolvido inicialmente como MVP.

## Visão do produto

Verificador automático de fotos de leitura. Entra: CSV com medidor, leitura e nota de ocorrência, mais pasta de fotos do lote do dia. A máquina decide se a foto existe e está legível, o que mostra e se combina com a nota registrada. Sai: veredito (aprovada, reprovada ou revisar), sempre com motivo escrito.

Fluxo: entrada (CSV e fotos), foto existe e é legível (OpenCV), o que a foto mostra (CNN), bate com a nota (evidência esperada), veredito e motivo, tela do auditor (Streamlit).

## Escopo do MVP

Faz: verifica existência e legibilidade, identifica o que a foto mostra, compara com a nota, entrega veredito com motivo.

Não faz: não pune nem decide sozinho o caso duvidoso, não altera o app de campo, não integra aos sistemas internos (roda sobre lote exportado).

## Metodologia e ferramentas

CRISP-DM em seis etapas. Gestão: Google Site, GitHub, repositório de decisões. Dados: Label Studio e DVC. Desenvolvimento: Python, OpenCV, PyTorch, Streamlit, Colab (GPU).

## Próximos passos

Validar com a Neoenergia o critério de foto por nota de ocorrência; testar a viabilidade do OCR; continuar as etapas do CRISP-DM.
