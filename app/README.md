# Interface do GridVision (protótipo)

Protótipo desktop em ttkbootstrap, com o fluxo completo do analista. A escolha entre desktop e web ainda está em aberto (pauta do atendimento de 24/10, ver `docs/contexto.md`).

## Fluxo

1. **Lote:** o analista escolhe a pasta de fotos e, se tiver, o CSV com a leitura informada pelo leiturista (formato da base: `;`, colunas `Foto do medidor`, `Numero do medidor`, `Posicao do medidor lida`).
2. **Processamento:** para cada foto, mede a nitidez, extrai número do medidor e leitura e decide o status.
3. **Resultados:** resumo por status e tabela filtrável. Duplo clique abre a foto na revisão.
4. **Revisão:** o analista vê a foto, confirma, corrige ou marca como ilegível. Enter confirma.
5. **Exportação:** CSV com status, valor lido, valor informado e decisão do analista.

Status possíveis:

| Status | Quando | Vai ao analista? |
|---|---|---|
| Confere | leitura da foto igual à informada (ignorando zeros à esquerda) e confiança alta | não |
| Diverge | leitura da foto diferente da informada | sim |
| Lido | sem leitura informada; o valor lido volta ao analista | sim |
| Revisão manual | confiança abaixo de 0,90 | sim |
| Ilegível | número ou leitura não legíveis | sim |
| Sem medidor | nenhum medidor na foto | não: sai da fila de revisão, mas fica na tabela e na exportação como "Excluída" |

O limiar de confiança (0,90) é provisório. O erro tolerado nas leituras resolvidas sozinhas é zero, então o sistema só decide quando tem certeza.

## Modelo

A extração vem de [src/gridvision/extracao.py](../src/gridvision/extracao.py), o mesmo código usado nas avaliações:

1. **Detector v0** (YOLO11n): tem medidor? onde estão visor e placa?
2. **PaddleOCR 3.7** na foto inteira ampliada 2x, guardando a posição de cada texto.
3. **Fiscal:** a leitura só vale se estiver dentro da caixa do visor; o número do medidor, dentro da placa (ou em qualquer lugar, se tiver 6 dígitos ou mais).
4. **Função do display:** o código da função (03 = consumo) aparece à esquerda da leitura e é separado dela. Se a função não for de consumo, a leitura não é aceita. Outros códigos: `GRIDVISION_FUNCOES_LEITURA="03,..."`.
5. **Confiança:** a menor entre a do OCR na leitura e no número.

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
