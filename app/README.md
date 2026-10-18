# Interface do GridVision (protótipo)

Protótipo desktop em ttkbootstrap, com o fluxo completo do analista. A escolha entre desktop e web ainda está em aberto (pauta do atendimento de 24/10, ver `docs/contexto.md`).

## Fluxo

As cinco etapas do topo são clicáveis, a qualquer momento (o contador entre parênteses mostra quantas fotos há em cada uma):

1. **Lote:** o analista escolhe a pasta de fotos e, se tiver, o CSV com a leitura informada pelo leiturista (formato da base: `;`, colunas `Foto do medidor`, `Numero do medidor`, `Posicao do medidor lida`).
2. **Processamento:** abre sozinha ao começar o lote. Progresso e contadores ao vivo; dá para sair dela e voltar, o lote continua.
3. **Resultados:** o que já está resolvido. As fotos com "Confere" (alta confiança) entram aqui enquanto o lote processa; também aparecem as revisadas e as excluídas (sem medidor). Filtro por situação e por tipo de problema; duplo clique reabre a foto para corrigir.
4. **Revisão:** fila do que está pendente, que cresce enquanto o lote processa, com filtro por tipo de problema. Ao decidir, a próxima abre sozinha. Enter confirma.
5. **Exportação:** CSV com status, problemas, valor lido, valor informado e decisão. Exportar todos, só os filtrados (situação, status, problema) ou as linhas selecionadas (Ctrl e Shift para várias).

**Histórico** (no topo): todas as decisões do analista, de todos os lotes, com filtro por decisão, status e tipo de problema e busca por foto ou lote. Duplo clique reabre a foto para revisar de novo. Cada decisão é gravada na hora em `~/gridvision_dados/historico/historico.csv` (fora do Git; outro caminho com `GRIDVISION_HISTORICO`); revisar de novo acrescenta uma linha, e vale a mais recente.

Tipos de problema (filtro em Resultados, Revisão, Exportação e Histórico): sem medidor, visor não encontrado, placa não encontrada, leitura não lida, número não lido, display em outra função, leitura diferente da informada, confiança baixa, foto borrada, sem leitura informada. Uma foto pode ter mais de um.

Status possíveis:

| Status | Quando | Vai ao analista? |
|---|---|---|
| Confere | leitura da foto igual à informada (ignorando zeros à esquerda) e confiança alta | não |
| Diverge | leitura da foto diferente da informada | sim |
| Lido | sem leitura informada; o valor lido volta ao analista | sim |
| Revisão manual | confiança abaixo de 0,90 | sim |
| Ilegível | número ou leitura não legíveis | sim |
| Ilegível (certeza alta) | chance de a leitura ser legível abaixo de 0,20 (classificador de legibilidade), sem ter conferido | não: sai da fila como "Excluída (ilegível): pedir nova foto" |
| Sem medidor | nenhum medidor na foto | não: sai da fila de revisão, mas fica na tabela e na exportação como "Excluída" |

O limiar de confiança (0,90) é provisório. O erro tolerado nas leituras resolvidas sozinhas é zero, então o sistema só decide quando tem certeza.

## Modelo

A extração vem de [src/gridvision/extracao.py](../src/gridvision/extracao.py), o mesmo código usado nas avaliações:

1. **Detector v0** (YOLO11n): tem medidor? onde estão visor e placa?
2. **PaddleOCR 3.7** na foto inteira ampliada 2x, guardando a posição de cada texto.
3. **Fiscal:** a leitura só vale se estiver dentro da caixa do visor; o número do medidor, dentro da placa (ou em qualquer lugar, se tiver 6 dígitos ou mais).
4. **Função do display:** o código da função (03 = consumo) aparece à esquerda da leitura e é separado dela. Se a função não for de consumo, a leitura não é aceita. Outros códigos: `GRIDVISION_FUNCOES_LEITURA="03,..."`.
5. **Leitura sem zeros à esquerda:** o display mostra 007237, o CSV traz 7237 (nenhuma leitura da base começa com 0). O valor lido sai no formato do CSV; o que o visor mostrava fica no motivo. O número do medidor não é alterado (o zero faz parte do identificador).
6. **Confiança:** a menor entre a do OCR na leitura e no número.

Se as bibliotecas ou os pesos do detector não estiverem na máquina, o app volta à extração simulada e avisa no topo da tela. Para forçar o modo simulado (só mexer na interface): `GRIDVISION_SIMULADO=1`.

Rodar o app não ensina nada ao modelo. O app avisa quando o lote tem fotos do treino (servem para demonstrar, não para medir) ou do teste e do teste temporal (reservadas para a medida final).

## Como rodar

Só a interface (extração simulada):

```
pip install -r app/requirements.txt
python app/main.py
python -m unittest discover app    # testes da regra de decisão
```

Com o modelo real (Python 3.12 recomendado; fora do repositório, ex.: `venv_app`):

```
python -m venv venv_app
venv_app\Scripts\activate                        # Mac/Linux: source venv_app/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r app/requirements-modelo.txt
python app/main.py
```

Os pesos do detector (`best.pt`, cerca de 5 MB) ficam fora do Git. Peça ao João Pedro e salve em `~/gridvision_dados/detector_v0/runs/v0/weights/best.pt`, ou aponte outro caminho com `GRIDVISION_DETECTOR`. Na primeira execução o PaddleOCR baixa os modelos dele (cerca de 100 MB).

As fotos e o CSV ficam fora do Git (LGPD). Aponte a interface para a pasta local e salve a exportação fora do repositório.
