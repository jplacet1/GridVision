# Piloto de anotação (item 3 da checklist)

Primeira rodada de marcação manual: 300 fotos do conjunto de treino, para testar as regras e o tempo de anotação e gerar os primeiros exemplos para o detector (visor, placa, medidor).

## Arquivos

| Arquivo | O que é |
|---|---|
| `preparar_piloto.py` | Gera a divisão e a amostra, e copia as fotos para uma pasta fora do Git |
| `divisao_v1.csv` | Conjunto de cada foto: `treino`, `validacao`, `teste` (por medidor, 70/15/15 nos lotes de maio) ou `teste_temporal` (lote de 03/07). Só nomes de arquivo |
| `piloto_v1.csv` | As 300 fotos do piloto, com estrato (`nitida`, `borrada`, `fora_do_csv`), anotador e segundo anotador (50 fotos com dupla anotação) |
| `label_studio_config.xml` | Interface de anotação para colar no Label Studio |

Divisão gerada em 17/10/2026 (seed 42): treino 6.544 fotos, validação 1.402, teste 1.402, teste temporal 2.992.

## Passo a passo

1. **Fotos.** Peça ao João Pedro a pasta `piloto/fotos` (300 fotos) por canal privado. Guarde fora do repositório. Nunca coloque as fotos no Git, no Drive ou em chat público (LGPD).
2. **Instalar o Label Studio** (uma vez):
   ```bash
   python -m venv venv_labelstudio
   venv_labelstudio\Scripts\activate        # Mac/Linux: source venv_labelstudio/bin/activate
   pip install label-studio
   label-studio start
   ```
   Abre em `http://localhost:8080`. Crie uma conta local (fica só na sua máquina).
3. **Criar o projeto:** *Create Project*, nome `GridVision piloto - <seu nome>`.
   - *Data Import*: arraste só as fotos que são suas em `piloto_v1.csv` (coluna `anotador`, e também as da coluna `segundo_anotador` com o seu nome).
   - *Labeling Setup*: *Custom template*, apague o que estiver lá e cole o conteúdo de `label_studio_config.xml`. Salve.
4. **Anotar** cada foto seguindo as regras abaixo. Clique em *Submit* para ir à próxima.
5. **Exportar** ao terminar: *Export*, formato **JSON**. Mande o arquivo ao João Pedro. O JSON tem só caixas e respostas, sem a foto, mas mesmo assim não publique.

## Regras

**Caixas** (atalhos 1, 2, 3):
- **medidor:** o aparelho inteiro, da borda externa da caixa do medidor. Sem incluir a parede ou o padrão (caixa de proteção) em volta.
- **placa:** a etiqueta ou plaqueta onde está impresso o número do medidor. Só o número e a moldura dele, não a placa inteira com especificações técnicas.
- **visor:** onde aparece a leitura de consumo. No digital, o retângulo do display; no analógico, a janela dos roletes ou o conjunto dos ponteiros.
- Caixa justa, encostando na borda do objeto, sem sobra grande.
- Objeto cortado na foto: desenhe a caixa só na parte visível.
- Mais de um medidor: desenhe as caixas de todos (medidor, placa e visor de cada um que aparecer) e marque "mais de um" na pergunta 2. Nas perguntas de legibilidade, responda "sim" só se todos forem legíveis; se algum não for, responda "não" e diga na observação qual (ex.: "o da direita está ilegível"). Se os visores forem de tipos diferentes, marque o do medidor maior ou mais central e anote na observação.
- A caixa "placa" é a do identificador do medidor (o número de série que vai no CSV), esteja ele numa plaqueta ou impresso no corpo do medidor. Não inclua código de barras, especificações técnicas, marca ou datas.
- Não tem medidor (fachada, poste, chão): nenhuma caixa, e responda "não" na pergunta 2.

**Perguntas:**
- **Legível** quer dizer que você consegue ler todos os dígitos com segurança, sem chutar. Se precisou adivinhar um dígito, é "não".
- Use "não aparece" quando a placa ou o visor não estiverem na foto.
- **Não compare com o CSV.** Marque o que a foto mostra, mesmo que pareça diferente do registrado.
- Na dúvida, escreva na observação. As dúvidas viram regra na próxima rodada.

Tempo esperado: 20 a 30 segundos por foto, cerca de 1 hora para 100 fotos.

## Depois do piloto

O João Pedro junta os JSON, confere se tem foto sem resposta, conta quantas fotos são legíveis ou sem medidor e calcula a concordância (kappa de Cohen) nas 50 fotos com dupla anotação. As regras são ajustadas antes da anotação maior.
