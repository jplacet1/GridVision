# Contexto do projeto

Fonte única de verdade do GridVision. Se algo mudar, atualize este arquivo no mesmo commit.

Os documentos do Drive estão resumidos em [fontes/](fontes/). Conflitos entre eles e o que ainda está pendente estão em [inconsistencias.md](inconsistencias.md). Em caso de divergência, vale este arquivo.

## Projeto

- Disciplina: BD023, Projeto 4 (Dados), CESAR School, turma BD20262_4A, semestre 2026.2
- Docente: Erick Simões de Matos
- Parceiro: Neoenergia Pernambuco
- Objetivo: diminuir o trabalho manual dos analistas da Neoenergia automatizando parte da leitura dos medidores a partir das fotos de campo
- Problema técnico: extrair das fotos de medidores o número do medidor e a leitura. Se a leitura informada pelo leiturista vier junto com a foto, comparar as duas (confere ou diverge). Se não vier, devolver o valor lido ao analista. Casos incertos vão para revisão manual.
- Volume atual: 50 mil a 70 mil leituras por mês (faixa do Google Site), a maioria manual, com equipe de seis pessoas. A Business Understanding fala em 70 mil imagens por mês. A unidade (leitura ou imagem) está pendente.
- Metodologia: CRISP-DM

## Grupo 4: GridVision

- Alana Cecília Costa Cavalcanti (nas apresentações: Alana Cavalcanti)
- Henrique Valença Bouwman (nas apresentações: Henrique Bouwman)
- João Pedro Lins Lacet Dias (nas apresentações: João Pedro Lins)

Documentos que exigem nome completo usam o nome completo. Nos demais, usar a forma das apresentações.

## Marcos

| Marco | Data |
|---|---|
| Kick-off | 12/09/2026 (realizado) |
| SR1 | 03/10/2026 (realizado) |
| SR2 (entrega final) | 05/12/2026 |

Cronograma completo: `Cronograma_CRISP_DM_Projeto_4.pdf` na pasta do Drive. É o cronograma oficial. As datas de entregáveis da Definição da Solução (05/09, 26/09, 24/10, 14/11, 21/11, 28/11) pertenciam ao desenho antigo e não valem mais.

## Links

- [Google Site](https://sites.google.com/cesar.school/gridvision/home)
- [Notion](https://app.notion.com/p/GridVision-3c10a1e8539280048ea3ec14161c1709)
- [Drive](https://drive.google.com/drive/folders/1s2D1-MM3H-wqDQ6Sd0mfykE-Dz6VTJ3J)
- [Repositório](https://github.com/jplacet1/GridVision)

## Dados (números da EDA apresentados no SR1)

- 13.669 registros nos CSVs e 12.340 fotos JPG, em 4 lotes: 20, 21 e 22/05 e 03/07/2026.
- Todas as fotos têm 360 x 480 px e nenhuma tem EXIF.
- 866 fotos (7,0%) sem registro no CSV. 296 registros sem foto onde a nota exige foto.
- 1.316 registros com mais de um medidor ("/") e 768 com letras no número do medidor.
- O CSV traz número do medidor e leitura em 100% dos registros, mas 14,2% das leituras têm 1 a 3 dígitos e 347 são zero.
- Amostra aleatória de 1.200 fotos: 31,8% abaixo do limiar de nitidez (variância do Laplaciano menor que 100), 2,1% subexpostas (brilho médio menor que 40), 2,0% com baixo contraste (desvio-padrão menor que 20).
- Dicionário de notas: 61 notas, só 19 aparecem nos lotes.
- Nenhuma foto tem caixa ou texto anotado.
- Os CSVs usam o texto "NA" no lugar de campo vazio. Ler com `keep_default_na=False`.
- Baseline de 02/10/2026: PaddleOCR na foto inteira, sem recorte e sem treino, 100 fotos nítidas. Acerto de 42% no número do medidor (placa) e 20% na leitura (display).

## Decisões e definições

### 03/10/2026

- **Problema oficial é o do SR1.** Ler número do medidor e leitura da foto, e comparar com o informado quando vier junto. O desenho anterior (veredito por foto contra a nota de ocorrência, com classificação do conteúdo da foto e tabela de evidência por nota) fica como histórico. Motivo: na operação, o que chega com certeza é a foto, e a nota de ocorrência só existe na base histórica. Itens do desenho antigo que ainda podem servir de apoio: verificação de nitidez, detecção de registro sem foto e tela de revisão do analista.
- **Meta de redução do trabalho.** A Neoenergia já disse que reduzir 50% do trabalho dos analistas é válido. O grupo quer reduzir o máximo possível. Tratar 50% como piso. A forma de medir esse percentual (por exemplo, percentual do lote resolvido sem analista) é interpretação do grupo e não foi validada com o cliente.
- **Outras metas numéricas são provisórias.** Revocação 0,85, precisão 0,70 e 10 minutos para 3.500 fotos vieram da Definição da Solução, do desenho antigo, e não foram validadas pelo grupo nem pela Neoenergia. As métricas do SR1 (localização, acerto exato da leitura, segurança) ainda não têm valor-alvo.
- **Arquitetura ainda não escolhida.** O SR1 propõe detector (medidor, ID e visor) mais reconhecedor de caracteres. A escolha final depende dos próximos testes (OCR nos recortes do visor) e deve estar fechada no SR2.
- **Divisão dos dados.** Treino, validação e teste divididos por medidor, não por linha (70/15/15 nos três lotes de maio). Lote de 03/07 reservado como teste temporal.
- **Teste de legibilidade dos dígitos (previsto para 19/09).** Em aberto. Se foi feito, foi pelo Henrique. O único resultado registrado é o baseline de 02/10.

## Pendências

Ver [inconsistencias.md](inconsistencias.md), seção "Pendências".
