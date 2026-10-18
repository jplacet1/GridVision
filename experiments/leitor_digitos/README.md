# Leitor de dígitos do visor (CNN), 18/10/2026

Tentativa de trocar o OCR genérico por uma CNN própria que lê os dígitos do recorte do visor.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `montar_recortes.py` | Detector v0 em treino, validação e teste (teste temporal intocado): recorte do visor, leitura do CSV como rótulo, chance de legível. 7.305 recortes, 1.374 fotos sem visor, 4 min |
| `treinar_cnn.py` | CNN de 6 posições (dígito 0 a 9 cada; rótulo = leitura completada com zeros à esquerda). `v0`: CNN pequena do zero; `v1`: ResNet18 pré-treinada |
| `diagnostico_rotulos.py` | Confere com o OCR se a leitura do CSV aparece no recorte |

Recortes e pesos ficam fora do Git, em `gridvision_dados/leitor_digitos`.

## Resultado

Treino: 3.075 recortes de treino com chance de legível ≥ 0,6 e leitura diferente de "0". Validação: 667 recortes (rótulo = leitura do CSV).

| Versão | Épocas | Acerto exato (6 posições) | Por dígito | Tempo (CPU) |
|---|---|---|---|---|
| v0, CNN pequena do zero | 40 | 20,1% | - | 35 min |
| v1, ResNet18 pré-treinada | 30 | 7,9% | 54,9% | 21 min |

As duas ficam abaixo do OCR genérico (28% na foto inteira ampliada). A v1 passou 10 épocas sem aprender.

## Diagnóstico: os rótulos estão sujos

Em 200 recortes de treino sorteados (chance de legível ≥ 0,6), o PaddleOCR no recorte:

| Resultado | Recortes |
|---|---|
| Lê exatamente a leitura do CSV | 66 (33%) |
| Lê com confiança outro número de tamanho parecido | 27 (13%); em 21 a diferença é de 3 dígitos ou mais |
| Não lê dígitos | 46 (23%) |
| Lê algo fraco ou de outro tamanho | 61 (31%) |

Só cerca de um terço dos rótulos é confirmado e pelo menos 10% não batem com a imagem (provável: display em outra função, valor digitado em outro momento, ou foto ilegível que passou pelo filtro). Com 3 mil exemplos e esse ruído, a rede recebe sinais contraditórios.

Próximo passo proposto: transcrever o visor à mão (só o recorte, digitando o que está escrito, inclusive a função) em cerca de 500 recortes, e treinar de novo a CNN e/ou ajustar o reconhecedor do PaddleOCR com rótulos limpos. As correções do analista no app também viram rótulos limpos.
