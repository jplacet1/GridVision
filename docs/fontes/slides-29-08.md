# slide-29_08.pptx (apresentação de 29/08)

Fonte: `slide-29_08.pptx` (Drive, Apresentações). Modificado em 12/09/2026. Resume ideação, matriz e definição da solução em 8 slides. Versão anterior ao pivô descrito no SR1.

Cliente: Neoenergia PE. Grupo G4: Alana Cavalcanti, Henrique Bouwman, **João Pedro Lacet**. Docente: Erick Simões de Matos.

## Slide 2, Ideação e Matriz CSD

- Certezas: visitas mensais geram volume massivo de fotos; auditoria 100% manual é inviável; dificuldade de confirmar fotos gera erros na fatura; cliente sugeriu IA para nitidez, tipo de foto e nota de ocorrência (ex.: I100).
- S3 confirmada (296 casos). S4 confirmada (31,8% abaixo do limiar de nitidez). S5 confirmada (dados pessoais).
- S2 enfraquecida: **"92% das fotos anexadas referiam-se a notas que não exigiam foto"**.
- D3: **"resolução das fotos (360x480) inviabiliza leitura direta de dígitos (OCR)"**.
- Nenhuma das 12.340 fotos tem EXIF.

## Slide 3, as 8 ideias

I1 a I8, mesmas da ideação (I2 em PyTorch com medidor, fachada/portão, caixa, outro; I4 "depende de alta resolução").

## Slide 4, matriz

Mesmas notas do documento 3. Quadrantes: alto impacto e baixo esforço (I6, I1, I7); alto impacto e alto esforço (I2, I3, I8, "coração do MVP"); baixo e baixo (I5); alto esforço com incerteza (I4).

## Slide 5, MVP

Dentro: I6, I1, I2, I3, I7, I8. Fora: I4 (teste em 100 recortes até 19/09), I5 (se houver folga após o SR1), integração com legados, alteração no app do leiturista.

## Slide 6, ordem das verificações

Passo 1 I6 (regra CSV), passo 2 I1 (nitidez), passo 3 I2 (CNN), passo 4 I3 (tabela de evidência), passo 5 I5 (hash perceptual), passo 6 I7/I8 (veredito e tela).

## Slide 7, arquitetura

I2 em PyTorch (MobileNetV3), 900 a 1.200 fotos rotuladas. Colab GPU, Label Studio, GitHub, DVC, Streamlit.

## Slide 8, métricas de sucesso

- Automação do lote: **pelo menos 50%**.
- Revocação (fotos ruins): pelo menos 0,85.
- Precisão (reprovações): pelo menos 0,70.
- I2: F1 macro após piloto de rotulagem com validação cruzada.
- Tempo: menos de 10 minutos para 3.500 fotos.
