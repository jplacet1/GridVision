# GridVision: Data Understanding

Fonte: Google Doc "Data Understanding" (Drive, Entregáveis SR1). Criado em 26/08/2026, modificado em 26/08/2026. O documento está curto e incompleto (a coluna "Colunas" das imagens está com `___`).

## Objetivo da etapa

Compreender os dados e as características do dataset.

## Tipos de dados

| Tipo | Descrição | Colunas | Formato |
|---|---|---|---|
| Imagens | Separadas em 4 pastas, cada uma com cerca de 3000 | `___` (vazio) | .jpg |
| Planilhas, Fotos | Relacionam o que foi analisado na leitura com a própria foto | Numero do medidor; Posicao do medidor lida; Nota de leitura Atual; Foto do medidor | .xlsx |
| Planilhas, Descrição das Leituras | Relaciona o tipo de nota de leitura com sua descrição e se exige foto | NOTA; DESCRICAO; NOTA EXIGE FOTO | .xlsx |

## Descrição do conjunto

- Os arquivos vieram em `Base de Dados Neoenergia PE.zip`. Ao extrair, há 4 pastas, uma por dia, e uma planilha que descreve os tipos de leitura e seus códigos.
- Cerca de 12 mil imagens no total, cerca de 3 mil por pasta. Qualidade, posição do leiturista, iluminação, angulação e legibilidade variam bastante.
- Há uma planilha em cada pasta de fotos, relacionando a foto ao que foi dado como lido pelo analista.
