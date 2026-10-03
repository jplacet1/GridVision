# Status Report 1 (03/10/2026)

Fonte: `GridVision SR1.pdf` (Drive, Entregáveis SR1; título interno "Recriação de slides GridVision"). Grupo G4, cliente Neoenergia PE. Autores: Alana Cavalcanti, Henrique Bouwman, João Pedro Lins.

## Contexto e problema

A Neoenergia PE visita praticamente todos os clientes todo mês. Cada leitura gera uma foto, e a equipe de fiscalização revisa à mão.

Pergunta: **como extrair identificação e leitura das fotos de medidores de campo?** Entrada: a foto (e, se vier, a leitura informada). Saída: leitura lida da foto, confere ou diverge do informado, ou revisão.

## O que mudou desde o Kickoff

- No Kickoff (12/09): verificar se a foto combinava com a nota de ocorrência.
- Agora: na operação, o que chega com certeza é a foto. A nota de ocorrência não vem junto, só existe na base histórica. A solução passa a ler da foto o número do medidor e a leitura. Se a leitura informada vier junto, compara; se não, devolve o valor lido.
- O CRISP-DM é iterativo: voltaram ao Business Understanding.

## Dados e EDA

- 13.669 registros no CSV; 12.340 fotos JPG; 4 lotes (20, 21 e 22/05 e 03/07/2026).
- 866 fotos (7,0%) sem registro no CSV. 296 registros sem foto onde a nota exige foto.
- 1.316 registros com mais de um medidor ("/") e 768 com letras no número do medidor.
- Nenhuma caixa ou texto anotado nas fotos.
- O CSV traz número do medidor e leitura em 100% dos registros, mas 14,2% das leituras têm 1 a 3 dígitos e 347 são zero.
- Todas as fotos têm 360 x 480 px, sem EXIF.
- Amostra aleatória de 1.200 fotos: 31,8% abaixo do limiar de nitidez (variância do Laplaciano < 100), 2,1% subexpostas (brilho médio < 40), 2,0% com baixo contraste (desvio-padrão < 20).
- O OCR pronto não achou texto em 16 de 100 fotos nítidas.

## Etapas da solução

1. Verificar qualidade. 2. Localizar medidor, ID e visor. 3. Ler número do medidor e leitura. 4. Comparar com o registro (conforme ou divergente). Saídas de falha: foto ilegível, medidor não encontrado, leitura sem confiança, que levam a nova foto ou revisão.

## Preparação dos dados

| Achado | Decisão |
|---|---|
| 12 medidores aparecem em mais de um lote | Dividir treino/validação/teste por medidor, não por linha (70/15/15 nos três lotes de maio) |
| Lote de 03/07 é seis semanas mais recente e tem mais registros sem foto | Reservar como teste temporal |
| CSVs usam o texto "NA" | Ler com `keep_default_na=False` (senão 2.195 referências de foto e 9.109 notas viram nulo) |
| Nenhuma caixa anotada | Anotar um conjunto piloto |
| Desfoque é o que a etapa 1 detecta | Aumento de dados sem desfoque sintético |
| Número do medidor com "/" ou letras; zeros à esquerda no display | Normalizar os dois lados antes de comparar |
| 866 fotos órfãs | Usar na anotação de caixas (detector), não na de leitura |

## Modelagem

Localizar: detector com CNN encontra medidor, ID e visor. Ler: reconhecedor de caracteres nos recortes. Baseline: PaddleOCR na foto inteira, sem recorte e sem treino, feito em 02/10. Hipótese: analógicos e digitais podem precisar de tratamentos diferentes.

## Primeiro experimento (02/10/2026)

PaddleOCR, 100 fotos nítidas sorteadas, sem recorte e sem treino. Zeros à esquerda ignorados na comparação.

- Número do medidor na placa: **42%** de acerto. Leitura no display: **20%**.
- 8 leituras erraram por um único dígito.
- Em 16 fotos nítidas o OCR não achou texto nenhum.

## Métricas

1. Localização: encontrou medidor, ID e visor? 2. Extração: ID inteiro e leitura inteira corretos (acerto exato). 3. Segurança: quantas vão para revisão e quantas respostas erradas passam como confiáveis. Analisar separadamente escuras, desfocadas, analógicas e digitais.

## Fundamentação

Sabemos: 360x480 e sem EXIF; 31,8% sem nitidez; CSV com ID e leitura em 100%; sem caixas; OCR sem recorte lê a placa (42%) mas não o display (20%).

Assumimos: a leitura informada vai chegar junto com a foto; com o visor recortado, a resolução basta.

Vamos investigar: quantas fotos não mostram o medidor; quanto o recorte melhora o OCR e se vale treinar reconhecedor próprio; se ID e leitura do CSV servem de texto-alvo; quais analógicos e digitais precisam de tratamento diferente; que taxa de acerto o cliente aceita; quantas fotos o piloto precisa.

## Integração de disciplinas

Visão Computacional (nitidez, brilho, recorte), Deep Learning (detector e reconhecedor), MLOps (rastrear experimentos, versionar dados e rótulos; baseline com script, amostra com seed e saída bruta), Projeto 4 Dados (EDA, qualidade, divisão por medidor e teste temporal).

## Próximos passos

1. Anotar conjunto piloto (caixas e texto). 2. Repetir o OCR nos recortes do visor e comparar com os 20%; treinar o detector. 3. Se o recorte não bastar, treinar reconhecedor próprio para o display e ampliar a anotação. Meta: chegar ao SR2 (05/12/2026) com a arquitetura escolhida.
