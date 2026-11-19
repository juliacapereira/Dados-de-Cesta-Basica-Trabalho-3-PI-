# Passo 3: Definição da questão

## Questão principal
É possível prever o preço mensal de produtos da cesta básica (arroz, feijão,
açúcar e óleo) utilizando seus valores históricos? Qual modelo apresenta a
maior precisão?

## Questão complementar
A variação de preço de um produto antecede (ajuda a prever) a variação de
preço de outro?

## Objetivo e motivação
**Objetivo:** verificar se o histórico de preços contém informação suficiente
para antecipar o preço do mês seguinte e medir quanto cada modelo melhora a
previsão em relação a um palpite simples (repetir o último preço).

**Motivação:** a cesta básica pesa no orçamento das famílias. Uma previsão
confiável apoia o planejamento de compras de famílias e instituições, e saber
quais produtos são mais voláteis ou imprevisíveis ajuda a priorizar o
acompanhamento. A questão complementar mostra se o aumento de um item serve de
sinal de alerta para outro. Esse conhecimento tem aplicação direta no
acompanhamento de preços de alimentos na região de Campinas.

**Motivação vinda da exploração (passos 1 e 2):**
- A base tem [N] meses, de [mês/ano] a [mês/ano], coletados em [N] mercados.
- O teste ADF indicou que as séries [não são estacionárias em nível / ...] e
  que [ficam estacionárias após uma diferenciação].
- A análise de sazonalidade mostrou [padrão observado ou ausência dele].
- A correlação entre variações mensais dos produtos foi [fraca/moderada/forte],
  o que justifica testar se um produto ajuda a prever outro.

## Método
**Dados:** mediana mensal do preço padronizado (PPK) por produto, usando a
base tratada no passo 1. A mediana reduz o efeito de preços extremos.

**Modelos e justificativa:**
| Modelo | Por que foi escolhido |
|---|---|
| Ingênuo (último valor) | Baseline obrigatório. Qualquer modelo precisa superá-lo para valer a pena. |
| Média móvel (3 meses) | Segundo baseline, mais suave que o ingênuo. |
| ARIMA (d=1) | Padrão para séries temporais. d=1 porque o ADF indica não estacionariedade. A ordem (p, q) é escolhida por AIC. |
| SARIMA | Testa se a sazonalidade anual melhora a previsão. |
| Random Forest | Captura relações não lineares usando lags, médias móveis e mês do ano. Foi testado só com o histórico do próprio produto e também com os outros produtos. |
| Gradient Boosting | Alternativa de ML baseada em árvores, para comparar com o Random Forest. |

**Detalhes metodológicos:**
- Os modelos de ML preveem a variação do preço, não o nível, porque árvores
  não extrapolam a tendência de alta.
- Os hiperparâmetros do Random Forest são escolhidos com validação temporal
  (TimeSeriesSplit), sem embaralhar os dados.
- Para a questão complementar usa-se o teste de Granger sobre as variações
  logarítmicas dos preços, com até 3 defasagens.

**Avaliação:**
- Validação walk-forward (janela expansível): o modelo é treinado até o mês t
  e prevê o mês t+1, repetindo ao longo da série.
- Métricas: MAE, RMSE e MAPE.
- Comparação de cada modelo com o ingênuo pelo ganho percentual de RMSE.
- A questão é considerada respondida se for possível dizer, com base nas
  métricas e por produto, qual modelo erra menos e se ele supera o baseline.

## Conclusão esperada (preencher após o passo 5)
- Algum modelo supera o ingênuo de forma consistente? Para quais produtos?
- Os modelos com informação de outros produtos ajudam ou não?
- Existe precedência entre produtos (Granger)?
- Limitações: [tamanho da série, mediana entre mercados, mudanças de marca,
  meses sem coleta, etc.]
- Observação: um resultado do tipo "nenhum modelo supera o baseline" também é
  uma resposta válida, desde que seja bem discutido.