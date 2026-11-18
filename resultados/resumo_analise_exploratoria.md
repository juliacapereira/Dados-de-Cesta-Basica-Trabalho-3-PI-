# Trabalho 3 — Exploração de Dados da Cesta Básica

## Etapa 2 — Relatório da Análise Exploratória

### 1. Descrição da base de dados

O estudo utiliza uma base de preços de produtos da cesta básica, com registros coletados entre setembro de 2022 e agosto de 2026, abrangendo 48 meses.

A base original contém 46.264 registros, envolvendo 51 supermercados e 30 denominações de produtos.

Durante o pré-processamento, foram identificadas e retiradas provisoriamente 1.743 duplicatas exatas e sete registros com preços extremamente suspeitos. Também foram realizadas três padronizações de nomenclatura, reduzindo a quantidade de categorias de produtos de 30 para 27.

A base resultante possui 44.514 registros. A base original foi preservada para rastreabilidade.

### 2. Evolução temporal do preço do arroz

Foi calculada a mediana mensal do indicador de preço padronizado (`PPK`) do arroz.

O gráfico mostrou relativa estabilidade entre setembro de 2022 e meados de 2023, seguida por crescimento significativo até 2024, quando o indicador alcançou aproximadamente R$ 6,89.

Posteriormente, observou-se uma tendência de queda, com valores próximos de R$ 5,10 em agosto de 2026.

**Conclusão:** a série apresenta mudanças de tendência que podem dificultar sua previsão, justificando a comparação entre diferentes modelos.

**Evidência:** `graficos/evolucao_arroz.png`

### 3. Comparação da evolução dos produtos

Foram analisados arroz, feijão, açúcar e óleo por meio de índices relativos, utilizando setembro de 2022 como base 100.

O arroz apresentou valorização expressiva em 2024, enquanto o óleo apresentou queda acentuada em 2023. O açúcar exibiu menor amplitude de variação relativa, e o feijão apresentou oscilações ao longo do período.

**Conclusão:** os produtos possuem comportamentos temporais distintos, sugerindo a necessidade de avaliar individualmente o desempenho dos modelos de previsão.

**Evidência:** `graficos/comparacao_produtos.png`

### 4. Correlação entre as variações mensais

Foi utilizada a correlação de Pearson sobre as variações percentuais mensais dos quatro produtos.

Os coeficientes ficaram próximos de zero, variando aproximadamente entre -0,13 e +0,11 nas comparações entre produtos diferentes.

**Conclusão:** não foram identificadas correlações lineares contemporâneas fortes. Isso não descarta possíveis relações com defasagens temporais.

**Evidência:** `graficos/correlacao_produtos.png`

### 5. Testes de estacionariedade

Foi aplicado o teste Augmented Dickey-Fuller (ADF), adotando nível de significância de 5%.

| Produto | P-valor original | P-valor após primeira diferença |
|---|---:|---:|
| Arroz | 0,2398 | 0,1406 |
| Feijão | 0,2932 | 0,0005 |
| Açúcar | 0,6429 | inferior a 0,0001 |
| Óleo | 0,3783 | 0,0015 |

Nas séries originais, não foi possível rejeitar a hipótese de presença de raiz unitária.

Após a primeira diferenciação, essa hipótese foi rejeitada para feijão, açúcar e óleo, mas não para o arroz.

**Conclusão:** a diferenciação mostrou-se relevante para três séries. A escolha definitiva dos parâmetros dos modelos dependerá também da avaliação preditiva.

### 6. Análise exploratória de sazonalidade

Os preços mensais foram normalizados pela mediana do respectivo ano, permitindo comparar índices relativos entre os meses do calendário.

O óleo apresentou a maior amplitude entre os índices mensais, com 114,62 em janeiro e 97,92 em julho.

O feijão apresentou índices relativamente maiores entre março e junho, enquanto arroz e açúcar mostraram amplitudes menores.

**Conclusão:** existem diferenças entre os meses, mas não há evidência suficiente para afirmar a existência de sazonalidade estatisticamente significativa. O curto histórico disponível e as tendências dos preços limitam a interpretação.

**Evidência:** `graficos/sazonalidade_produtos.png`

### 7. Comparação entre supermercados

Foram selecionados os dez supermercados com maior número de registros de arroz.

O SUP_06 apresentou preço padronizado mediano de R$ 5,03, enquanto o SUP_27 apresentou R$ 6,20.

A diferença foi de R$ 1,17, equivalente a aproximadamente 23,3% em relação à mediana do SUP_06.

**Conclusão:** foram identificadas diferenças entre as medianas históricas dos supermercados. Entretanto, a análise não controla diferenças entre períodos de coleta, marcas ou composição dos produtos, não permitindo estabelecer uma classificação definitiva de estabelecimentos mais baratos.

**Evidência:** `graficos/comparacao_supermercados.png`

### 8. Limitações metodológicas

A base apresenta algumas limitações que devem ser consideradas:

- Existem registros sem data exata de coleta e sem identificação de marca.
- Algumas equivalências entre nomes de produtos permanecem provisórias.
- A unidade de referência do indicador `PPK` deve ser confirmada na documentação da base.
- A retirada de duplicatas e preços suspeitos deverá ser considerada na avaliação de sensibilidade dos resultados.
- As séries mensais possuem apenas 48 observações, limitando análises de sazonalidade e modelos estatísticos mais complexos.
- As análises realizadas identificam associações e padrões, mas não estabelecem relações causais.

### 9. Conclusão geral da Etapa 2

A análise exploratória permitiu identificar diferentes comportamentos de preços entre os produtos da cesta básica, incluindo mudanças de tendência, variações mensais, diferenças entre supermercados e resultados distintos nos testes de estacionariedade.

Essas observações fundamentam a próxima etapa do trabalho: investigar a capacidade de previsão dos preços mensais por meio de modelos estatísticos e algoritmos de aprendizado supervisionado.

A eficácia desses modelos deverá ser avaliada em dados cronologicamente posteriores aos utilizados no treinamento, com comparação a métodos simples de referência.