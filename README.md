# Trabalho 3 — Exploração de dados da cesta básica (Projeto Integrador)

Previsão mensal de preços de itens da cesta básica (arroz, feijão, açúcar e
óleo) a partir de uma base de preços coletados em supermercados entre
setembro de 2022 e agosto de 2026. Trabalho de extensão da PUC-Campinas.

## Questão

- **Principal:** é possível prever o preço mensal de produtos da cesta básica
  usando seus valores históricos? Qual modelo apresenta maior precisão?
- **Complementar:** a variação de preço de um produto antecede a de outro?

Detalhes de objetivo, motivação, método e conclusão: [`03_questao.md`](03_questao.md).

## Resultado em uma linha

Repetir o último preço (modelo ingênuo) foi a referência mais difícil de
superar. Só no óleo o ARIMA teve RMSE menor, e a diferença não é
estatisticamente significativa (Diebold-Mariano). O teste de Granger não
encontrou precedência entre produtos a 5%.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `dados/ICB_DADOS_2026.xlsx` | Base original (preservada) |
| `dados/dados_sem_duplicatas.csv` | Base intermediária, sem duplicatas exatas |
| `dados/dados_tratados.csv` | Base usada nas análises (sem duplicatas e sem preços suspeitos) |
| `01_limpeza.py` | Inspeção, duplicatas, outliers, padronização de nomes e base tratada |
| `02_analise.py` | Análise exploratória: evolução, correlação, ADF, sazonalidade, supermercados |
| `03_questao.md` | Questão, objetivo, motivação, método e conclusão |
| `04_modelagem.py` | Modelos (ingênuo, média móvel, ARIMA, SARIMA, RF, GB), walk-forward e Granger |
| `05_teste_dm.py` | Teste de Diebold-Mariano de cada modelo contra o ingênuo |
| `app.py` | Painel interativo em Streamlit |
| `graficos/` | Figuras geradas pelos scripts |
| `resultados/` | Métricas, previsões, Granger, Diebold-Mariano, outliers e resumo exploratório |
| `entrega/` | Relatório técnico (PDF) e zip do projeto |

## Como executar

Requer Python 3.10 ou superior.

```bash
pip install -r requirements.txt
python 01_limpeza.py     # gera dados/dados_tratados.csv e arquivos de apoio
python 02_analise.py     # gráficos e testes exploratórios
python 04_modelagem.py   # walk-forward, métricas e Granger (demora alguns minutos)
python 05_teste_dm.py    # teste de Diebold-Mariano
python -m streamlit run app.py     # painel interativo
```

Os scripts devem ser executados na ordem, a partir da pasta do projeto. As
sementes aleatórias estão fixadas (`SEMENTE = 42`).

## Metodologia (resumo)

- Série mensal: mediana do preço padronizado (PPK) entre os supermercados.
- Avaliação: walk-forward com janela expansível, treino inicial de 25 meses e
  23 previsões de 1 mês por produto, sem embaralhar os dados.
- Métricas: MAE, RMSE e MAPE, mais ganho de RMSE sobre o ingênuo.
- Significância: teste de Diebold-Mariano (perda quadrática, correção HLN).
- Modelos de ML preveem a variação logarítmica do preço, não o nível.

## Limitações

Série curta (48 meses), mediana entre mercados que muda com a composição
mensal, registros sem data exata e sem marca, unidade do PPK a confirmar e
exclusão de preços suspeitos sem análise de sensibilidade. Detalhes em
`03_questao.md` e no relatório técnico.
