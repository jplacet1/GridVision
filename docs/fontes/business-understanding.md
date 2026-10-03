# Business Understanding, GridVision

Fonte: `Business Understanding - GridVision.docx` (Drive, Entregáveis SR1). Criado em 18/08/2026, modificado em 22/08/2026.

## Contexto

A Neoenergia é controlada pelo grupo espanhol Iberdrola e atua em geração, transmissão, distribuição e comercialização de energia.

Existe um processo de análise de aproximadamente **70 mil imagens de medidores por mês**, feito manualmente por uma equipe de aproximadamente **seis funcionários**.

O processo começa quando uma leitura registrada pelo sistema tem valor considerado fora da faixa esperada. Um funcionário de campo vai ao local, faz nova verificação e registra imagens do medidor e do ambiente. Depois, as imagens são analisadas manualmente. Há diferentes modelos de medidores e condições de captura.

## Problema atual

- Seis funcionários analisam cerca de 70 mil imagens por mês.
- Não há controle imediato sobre a qualidade das imagens enviadas.
- A análise não acontece na captura. Se a imagem estiver ilegível, pode ser difícil refazer a coleta.
- Diferentes tipos de medidores aumentam a complexidade.
- O volume aumenta a chance de erro humano e dificulta escalar.

## Problema de negócio

Como reduzir o esforço manual necessário para analisar um grande volume de imagens de medidores, mantendo um nível adequado de confiabilidade na identificação das informações presentes nas imagens?

## Impactos

Tempo gasto na análise, dependência de trabalho manual, dificuldade de aumentar a capacidade sem aumentar a equipe, erros de análise, atrasos e custo operacional.

## Stakeholders

Neoenergia; funcionários que analisam as imagens; funcionários de campo que coletam as imagens; gestores da área; outras áreas que usem as informações.

## Objetivo de negócio

Reduzir a dependência de análise manual no processo de leitura e validação de medidores, aumentando eficiência, velocidade e capacidade de lidar com grandes volumes.

## Objetivos específicos

- Compreender em detalhe o processo atual de análise.
- Identificar gargalos e limitações.
- Investigar a automação parcial da leitura com visão computacional.
- Avaliar a capacidade de um modelo identificar corretamente informações nos medidores.
- Desenvolver um MVP que demonstre a viabilidade.

## Critérios de sucesso

Redução do tempo de análise, da intervenção manual, capacidade de processar mais imagens, confiabilidade aceitável e facilidade de uso. **Os valores quantitativos ainda deverão ser definidos** após entender os dados e validar com a Neoenergia.

## Escopo

Dentro: análise das imagens fornecidas; estudo dos tipos de medidores; preparação dos dados; desenvolvimento e avaliação de modelos de visão computacional; MVP; avaliação de assertividade e limitações.

Fora (escopo negativo): substituição dos sistemas internos; implantação em produção; alteração dos procedimentos dos funcionários de campo; treinamento operacional; garantia de automatizar 100% das situações.

## Restrições e premissas

Disponibilidade dos dados; qualidade e variedade das imagens; prazo acadêmico; capacidade computacional; acesso limitado a informações internas; privacidade dos dados; validação com a Neoenergia.

## Riscos

Dados insuficientes ou pouco variados; baixa qualidade das imagens; diferenças entre tipos de medidores; desempenho insuficiente do modelo; dificuldade de acesso a informações do processo; complexidade acima do escopo e do prazo.

## Perguntas em aberto

- Tempo médio atual de análise das imagens?
- Tipos de medidores mais frequentes?
- Qualidade média das imagens recebidas?
- Nível de precisão aceitável para a Neoenergia?
- Situações que continuarão dependendo de análise humana?

## Próximos passos

Seguir para Data Understanding.
