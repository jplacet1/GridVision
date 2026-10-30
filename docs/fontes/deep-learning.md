# Deep Learning (BD019)

Fonte: Google Classroom da disciplina, lido em 04/10/2026. Resumo da tarefa "Lab 02 - Arquitetura" e dos materiais publicados. O Classroom só exportou o texto da tarefa. O guia, o esqueleto de código e o bloco específico de cada grupo são anexos que ainda não foram lidos (ver pendências em [../contexto.md](../contexto.md)).

## Ligação com o projeto

A disciplina usa o projeto da Neoenergia como objeto de trabalho. O Lab 02 transforma o estado atual do Projeto 4 em uma arquitetura de rede profunda justificada, verificada e com o primeiro bloco treinado. Não é o modelo final: é a base que o Marco 2 da disciplina (29/10/2026) vai cobrar funcionando.

## Lab 02: A arquitetura profunda do seu projeto

- Valor: 1,0 ponto. Entrega por grupo do Projeto 4.
- Prazo: 08/10/2026, 23:59.
- O enunciado tem uma parte comum e uma parte específica por grupo. O texto da tarefa cita quatro nomes de grupo (Korvian, Luminus, VoltLens e Nortdata). GridVision não aparece. Fazer só o bloco do próprio grupo.
- Entrega: link da pasta `lab-02/` do repositório do grupo, postado no Classroom.

Conteúdo da pasta `lab-02/`:

1. `ARQUITETURA.md`: ficha de arquitetura, no modelo da seção 14 do guia.
2. `lab02.ipynb`: executado do zero, com as saídas visíveis.
3. `rotulos/`: esquema de rótulos e pelo menos 300 fotos rotuladas, 50 delas com dupla rotulagem às cegas (kappa de Cohen reportado).
4. `README.md`: respostas, tabelas e leitura dos resultados.
5. `USO-DE-IA.md`: obrigatório. Sem ele, a nota é zero.

Regras sem exceção: as fotos do cliente não vão para o repositório e a partição é por lote, nunca aleatória por foto.

O esqueleto roda em CPU com `python esqueleto_arquitetura.py` e mostra as quatro verificações de sanidade do item D. Orientação do enunciado: começar pela rotulagem (item C), porque sem rótulo o resto não anda.

## Outras tarefas da disciplina

- AutoAvaliação 1 (prazo 10/09) e Apresentações 17/09 (prazo 19/09), sem entrega no Classroom.
- LAB 3, prazo 08/10/2026 23:59 (mesmo dia do Lab 02).

## Conteúdo das aulas (materiais publicados)

Plano de Ensino, Apostila, Aula 01, Práticas da Aula 1, Tensores/AutoGrad/Perceptron, Aula 03 (MLP e BackPropagation) e Aula 04 (Treinamento, 25/09). Há também um portal de materiais da disciplina indicado no aviso de 25/09.
