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
- A base tem 48 meses, de setembro/2022 a agosto/2026, coletados em 51
  supermercados (44.514 registros após a limpeza). As quatro séries mensais
  estão completas, sem meses faltantes.
- O teste ADF indicou que as quatro séries não são estacionárias em nível
  (p entre 0,24 e 0,64) e que ficam estacionárias após uma diferenciação para
  feijão, açúcar e óleo (p < 0,01). No arroz, a evidência após diferenciar é
  mais fraca (p = 0,14).
- A análise de sazonalidade mostrou diferenças entre os meses (maior amplitude
  no óleo), mas sem evidência suficiente de sazonalidade estável, pois a base
  cobre só quatro ciclos anuais.
- A correlação entre variações mensais dos produtos foi fraca (entre -0,13 e
  +0,11). Isso não descarta relações defasadas, o que justifica testar se um
  produto ajuda a prever outro (Granger e modelos com variáveis cruzadas).

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
- Teste de Diebold-Mariano (perda quadrática, correção de Harvey-Leybourne-
  Newbold) de cada modelo contra o ingênuo, para verificar se as diferenças de
  erro são estatisticamente significativas (`05_teste_dm.py`).
- A questão é considerada respondida se for possível dizer, com base nas
  métricas e por produto, qual modelo erra menos e se ele supera o baseline.

## Conclusão
Resultados do walk-forward (23 previsões de 1 mês por produto, de out/2024 a
ago/2026; treino inicial de 25 meses):

- **Melhor modelo por produto.** O ingênuo teve o menor MAE nos quatro
  produtos e o menor RMSE em arroz, feijão e açúcar. Só no óleo outro modelo
  teve RMSE menor: ARIMA (0,331 contra 0,363 do ingênuo, ganho de 8,95%), com
  RF próprio logo atrás (ganho de 5,07%). No açúcar o ARIMA empata com o
  ingênuo, porque suas previsões são iguais às dele.
- **Significância.** Pelo teste de Diebold-Mariano, nenhum modelo é
  significativamente melhor que o ingênuo em nenhum produto. Mesmo o ganho do
  ARIMA no óleo não é significativo (p = 0,29). As 4 comparações significativas
  a 5% (SARIMA em arroz e açúcar; média móvel em feijão e óleo) indicam
  modelos significativamente **piores** que o ingênuo. Essas contas não têm
  correção para comparações múltiplas.
- **Informação de outros produtos.** Não ajuda de forma consistente. O RF
  cruzado reduziu o RMSE em relação ao RF próprio no feijão (0,375 contra
  0,424), mas piorou ou empatou no arroz, no açúcar e no óleo, e em nenhum
  caso superou o ingênuo no RMSE, exceto no óleo, sem significância.
- **Precedência entre produtos.** O teste de Granger não encontrou
  precedência a 5% em nenhuma das 12 direções. O menor p-valor foi 0,074
  (feijão para açúcar, defasagem de 1 mês).
- **Resposta à questão.** Com este histórico, os preços mensais medianos se
  comportam quase como um passeio aleatório: repetir o último preço é uma
  referência difícil de superar, e o objetivo de medir a capacidade preditiva
  foi atingido, ainda que com resultado negativo para os modelos mais
  elaborados.
- **Limitações.** Série curta (48 meses, 23 previsões de teste, o que dá baixo
  poder aos testes); uso da mediana entre mercados, que muda com a composição
  mensal de supermercados e marcas; registros sem data exata e sem marca;
  unidade de referência do PPK ainda a confirmar na documentação da base;
  exclusão de 7 preços suspeitos por critério fixo, sem análise de
  sensibilidade; hiperparâmetros do Gradient Boosting fixados sem busca; ordem
  do ARIMA e parâmetros do RF escolhidos só na janela inicial; apenas horizonte
  de 1 mês; sem comparação com preço do produtor nem análise por mercado.
- **Próximos passos possíveis.** Horizontes de 2 a 4 meses, previsão por
  supermercado, comparação com os custos de produção da Conab e modelos
  multivariados (VAR).

Observação: um resultado do tipo "nenhum modelo supera o baseline" é uma
resposta válida, e é o que os dados mostram aqui.