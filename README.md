# GridVision

O **GridVision** é um projeto de visão computacional desenvolvido como parte da disciplina de Projeto 4 (Dados) da CESAR School, em parceria com a Neoenergia Pernambuco.

O objetivo do projeto é automatizar a análise de fotos associadas ao processo de leitura de medidores de energia, reduzindo a necessidade de inspeção manual de grandes volumes de imagens.

## Objetivo

O sistema deverá receber lotes contendo registros de leitura e imagens dos medidores, realizar diferentes verificações sobre essas imagens e gerar um resultado para cada registro, indicando se ele deve ser:

- **Aprovado**
- **Reprovado**
- **Revisado manualmente**

Sempre que possível, o sistema também deverá informar o motivo da decisão.

## Abordagem

A solução está sendo construída como um pipeline de processamento de imagens, combinando:

- Processamento clássico de imagens com **OpenCV**
- Redes neurais convolucionais (**CNNs**)
- Transfer Learning com modelos pré-treinados
- Classificação de imagens
- Detecção de problemas de qualidade das fotos
- Comparação entre o conteúdo da imagem e os dados registrados

## Tecnologias

As principais tecnologias consideradas no projeto são:

- Python
- OpenCV
- PyTorch
- torchvision
- Streamlit
- Label Studio
- DVC
- GitHub

## Estrutura planejada

```text
GridVision/
├── data/
├── notebooks/
├── src/
│   ├── preprocessing/
│   ├── models/
│   └── pipeline/
├── app/
├── experiments/
├── requirements.txt
└── README.md