# MLOps (BD031, turma BD20262_4A)

Fonte: Google Classroom da disciplina, lido em 04/10/2026. Resumo da tarefa "AV1 - Entrega Prática" e dos avisos de aula. Cópia fiel do enunciado, sem interpretação.

## Ligação com o projeto

O professor pede como objeto ideal o próprio projeto da Neoenergia (triagem das fotos de leitura de consumo, mesma fonte de dados e mesmo modo de inferência da primeira prova). Outro objeto exigia proposta ao professor aprovada até 30/09. O que muda em relação ao Projeto 4: a inferência sai do notebook e passa a ser chamável por outra pessoa.

## Notas da AV1

- Primeira nota: prova de Entendimento do Negócio e dos Dados (60 pontos). Entregue.
- Segunda e última nota: Entrega Prática, 40 pontos, 40% da AV1.
- Entrega fora do prazo: nota multiplicada por 0,8.

## Prazos

| O quê | Quando |
|---|---|
| Entrega do repositório no Classroom | 06/10/2026 (terça) 23:59 |
| Tag `sr1` no commit entregue | 06/10/2026 23:59 (`git tag -a sr1 -m "Entrega do SR1"` e `git push origin sr1`) |
| Apresentação | 07/10/2026 (quarta), aula das 19:00 |
| Ordem das equipes | sorteada e publicada até 05/10/2026 |

Sem extensão de prazo.

## O que entregar

1. Repositório público no GitHub com código, instruções e evidência de execução.
2. Serviço rodando na máquina do grupo no dia da apresentação.
3. Apresentação de 15 minutos mais 5 de perguntas. Todos os integrantes falam e o professor escolhe quem responde.

## Escopo (serviço, não produto)

- Mínimo: um endpoint que recebe uma imagem e devolve a extração (número do medidor, função, consumo e grau de confiança).
- BentoML é o caminho recomendado. Outra pilha (FastAPI, MLServer) só com proposta aprovada até 30/09.
- O modelo pode ser pré-treinado, de terceiro por API, agente sobre plataforma ou treinado pelo grupo. Avalia-se o serviço em volta, não o modelo.
- Não vale ponto: front-end, deploy em nuvem, treinar modelo, integração com SAP, varredura de pastas, planilha de saída, log de experimentos.

## Regras sobre dados (repositório público)

- Nenhuma imagem do cliente versionada. Para README e demonstração, usar 3 a 5 imagens sintéticas ou fotografadas pelo grupo.
- Nenhuma linha do CSV real. Exemplo, só fictício com o mesmo esquema de colunas.
- O README descreve o domínio como "triagem de fotos de medidor de energia", sem nomear o cliente. O uso do nome Neoenergia em material público é restrito pelo acordo entre a CESAR School e a empresa.
- `.gitignore` cobrindo as pastas de dados antes do primeiro commit.
- Nenhum segredo no repositório. Variáveis de ambiente com `.env.example`.

## Itens obrigatórios do repositório

README que leva do `git clone` à primeira predição (comandos exatos, versão do Python, tempo aproximado), dependências fixadas (`pyproject.toml` com `uv.lock`; `justfile` recomendado), contrato documentado (endpoint, exemplo de entrada e saída, `curl` que funciona), LICENSE e seção "Uso de IA" no README (ferramenta, o que foi pedido e avaliação crítica). Desejáveis: comando único, revisão por pull request, análise do modelo com limitações e melhorias.

## Apresentação: quatro perguntas, nesta ordem

1. Qual modelo está sendo carregado? De onde vem, quem treinou, como e para quê?
2. Quais os limites do modelo? Executa todas as funções do projeto ou só algumas? Que ajustes são necessários?
3. Como se põe a API ou o pipeline no ar? Do `git clone` até o serviço respondendo, com o README na tela.
4. Demonstre o uso básico: uma chamada (curl, Swagger ou equivalente) e a resposta.

Plano B: vídeo de dois minutos da mesma demonstração, caso o serviço não suba. Baixar modelo e dependências antes, sem confiar no wifi da sala.

## Rubrica (40 pontos)

| Critério | Pontos |
|---|---|
| Adequação do modelo (limitações, casos de sucesso) | 10 |
| Serviço de pé e demonstrado | 10 |
| Instruções reproduzíveis | 10 |
| Repositório (itens obrigatórios) | 6 |
| Domínio oral (individual) | 4 |

Código gerado por IA que ninguém do grupo sabe explicar conta como não entregue.

## Avisos relevantes da disciplina

- 26/08 a 09/09: aulas com BentoML, exemplos de processamento de imagens e de reconhecimento de imagens em BentoML (repositórios públicos de exemplo do professor, citados nos avisos), e monitoramento de uso e qualidade do modelo.
- 30/09: aula só de dúvidas. Leituras sugeridas para quem estiver adiantado: observabilidade (OpenTelemetry), Rules of ML (Google) e detecção de data drift (Evidently).
