
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 1. Localizar a base tratada
pasta_projeto = Path(__file__).resolve().parent

caminho = pasta_projeto / "dados" / "dados_tratados.csv"

# 2. Carregar os dados
df = pd.read_csv(
    caminho,
    sep=";",
    encoding="utf-8-sig",
    parse_dates=["Mes_Ano_Data"]
)

print("\n=== BASE CARREGADA ===")
print("Registros:", len(df))
print("Produtos:", df["Produto_Padronizado"].nunique())

# 3. Escolher o produto para análise
produto_escolhido = "Arroz"

df_produto = df[
    df["Produto_Padronizado"] == produto_escolhido
].copy()

# 4. Calcular a mediana mensal do preço padronizado
precos_mensais = (
    df_produto
    .groupby("Mes_Ano_Data")["PPK"]
    .median()
    .sort_index()
)

print("\n=== PREÇOS MENSAIS DO ARROZ ===")
print(precos_mensais.to_string())

# 5. Criar o gráfico
plt.figure(figsize=(12, 6))

plt.plot(
    precos_mensais.index,
    precos_mensais.values,
    marker="o",
    linewidth=2
)

plt.title("Evolução mensal do preço do arroz")
plt.xlabel("Mês")
plt.ylabel("Preço padronizado (R$ por unidade de referência)")
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# 6. Salvar o gráfico
pasta_graficos = pasta_projeto / "graficos"
pasta_graficos.mkdir(exist_ok=True)

plt.savefig(
    pasta_graficos / "evolucao_arroz.png",
    dpi=300
)

plt.show()

# 7. Comparar a evolução de diferentes produtos

print("\n=== COMPARAÇÃO ENTRE PRODUTOS ===")

produtos_comparar = [
    "Arroz",
    "Feijão",
    "Açúcar",
    "Óleo"
]

plt.figure(figsize=(12, 6))

for produto in produtos_comparar:

    dados_produto = df[
        df["Produto_Padronizado"] == produto
    ]

    serie = (
        dados_produto
        .groupby("Mes_Ano_Data")["PPK"]
        .median()
        .sort_index()
    )

    # Transformar preços em índice base 100
    indice = (serie / serie.iloc[0]) * 100

    plt.plot(
        indice.index,
        indice.values,
        marker="o",
        linewidth=2,
        label=produto
    )

plt.title("Evolução relativa dos preços da cesta básica")
plt.xlabel("Mês")
plt.ylabel("Índice de preços (primeiro mês = 100)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    pasta_graficos / "comparacao_produtos.png",
    dpi=300
)

plt.show()

# =========================================================
# 8. CORRELAÇÃO ENTRE VARIAÇÕES MENSAIS DOS PRODUTOS
# =========================================================

print("\n=== CORRELAÇÃO ENTRE PRODUTOS ===")

# Calcular a mediana mensal de cada produto
precos_produtos = (
    df[df["Produto_Padronizado"].isin(produtos_comparar)]
    .groupby(["Mes_Ano_Data", "Produto_Padronizado"])["PPK"]
    .median()
    .unstack()
    .sort_index()
)

# Variação percentual em relação ao mês anterior
variacoes = precos_produtos.pct_change(
    fill_method=None
).dropna()

# Calcular a correlação de Pearson
correlacao = variacoes.corr()

print("\nMatriz de correlação:")
print(correlacao.round(3).to_string())

# Criar gráfico da matriz
plt.figure(figsize=(8, 6))

plt.imshow(
    correlacao,
    cmap="coolwarm",
    vmin=-1,
    vmax=1
)

plt.colorbar(label="Correlação de Pearson")

plt.xticks(
    range(len(correlacao.columns)),
    correlacao.columns
)

plt.yticks(
    range(len(correlacao.index)),
    correlacao.index
)

for i in range(len(correlacao.index)):
    for j in range(len(correlacao.columns)):
        plt.text(
            j, i,
            f"{correlacao.iloc[i, j]:.2f}",
            ha="center",
            va="center"
        )

plt.title("Correlação entre variações mensais dos preços")
plt.tight_layout()

plt.savefig(
    pasta_graficos / "correlacao_produtos.png",
    dpi=300
)

plt.show()

# =========================================================
# 9. TESTE DE ESTACIONARIEDADE (ADF)
# =========================================================

from statsmodels.tsa.stattools import adfuller

print("\n=== TESTE DE ESTACIONARIEDADE ADF ===")

for produto in produtos_comparar:

    serie = (
        df[df["Produto_Padronizado"] == produto]
        .groupby("Mes_Ano_Data")["PPK"]
        .median()
        .sort_index()
        .dropna()
    )

    resultado = adfuller(
    serie,
    autolag="AIC",
    result_object=False
    )

    estatistica = resultado[0]
    p_valor = resultado[1]

    print(f"\nProduto: {produto}")
    print(f"Estatística ADF: {estatistica:.4f}")
    print(f"P-valor: {p_valor:.4f}")

    if p_valor < 0.05:
        print("Resultado: rejeitamos a hipótese de raiz unitária.")
    else:
        print("Resultado: não rejeitamos a hipótese de raiz unitária.")


# =========================================================
# 10. TESTE ADF APÓS PRIMEIRA DIFERENCIAÇÃO
# =========================================================

print("\n=== TESTE ADF APÓS DIFERENCIAÇÃO ===")

for produto in produtos_comparar:

    serie = (
        df[df["Produto_Padronizado"] == produto]
        .groupby("Mes_Ano_Data")["PPK"]
        .median()
        .sort_index()
        .dropna()
    )

    # Calcular a diferença entre meses consecutivos
    serie_diferenciada = serie.diff().dropna()

    resultado = adfuller(
        serie_diferenciada,
        autolag="AIC",
        result_object=False
    )

    estatistica = resultado[0]
    p_valor = resultado[1]

    print(f"\nProduto: {produto}")
    print(f"Estatística ADF: {estatistica:.4f}")
    print(f"P-valor: {p_valor:.4f}")

    if p_valor < 0.05:
        print("Resultado: rejeitamos a hipótese de raiz unitária.")
    else:
        print("Resultado: não rejeitamos a hipótese de raiz unitária.")


# =========================================================
# 11. ANÁLISE DE SAZONALIDADE
# =========================================================

print("\n=== ANÁLISE DE SAZONALIDADE ===")

# Produtos que vamos investigar
produtos_sazonalidade = [
    "Arroz",
    "Feijão",
    "Açúcar",
    "Óleo"
]

# Obter as medianas mensais dos produtos
dados_sazonais = (
    df[df["Produto_Padronizado"].isin(produtos_sazonalidade)]
    .groupby(["Mes_Ano_Data", "Produto_Padronizado"])["PPK"]
    .median()
    .reset_index()
)

# Extrair mês e ano
dados_sazonais["Mes"] = dados_sazonais["Mes_Ano_Data"].dt.month
dados_sazonais["Ano"] = dados_sazonais["Mes_Ano_Data"].dt.year

# Normalizar cada produto pela mediana de seu próprio ano
mediana_anual = (
    dados_sazonais
    .groupby(["Produto_Padronizado", "Ano"])["PPK"]
    .transform("median")
)

dados_sazonais["Indice_Anual"] = (
    dados_sazonais["PPK"] / mediana_anual * 100
)

# Calcular a média do índice para cada mês do calendário
sazonalidade = (
    dados_sazonais
    .groupby(["Produto_Padronizado", "Mes"])["Indice_Anual"]
    .mean()
    .unstack(0)
)

# Ordenar os meses de janeiro a dezembro
sazonalidade = sazonalidade.reindex(range(1, 13))

print("\nÍndice sazonal exploratório:")
print(sazonalidade.round(2).to_string())

# Criar gráfico
plt.figure(figsize=(12, 6))

for produto in produtos_sazonalidade:
    plt.plot(
        sazonalidade.index,
        sazonalidade[produto],
        marker="o",
        linewidth=2,
        label=produto
    )

plt.axhline(
    y=100,
    color="gray",
    linestyle="--",
    alpha=0.7
)

plt.title("Padrões mensais exploratórios dos preços")
plt.xlabel("Mês do ano")
plt.ylabel("Índice relativo à mediana anual (100 = referência)")
plt.xticks(
    range(1, 13),
    ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
     "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
)

plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(
    pasta_graficos / "sazonalidade_produtos.png",
    dpi=300
)

plt.show()


# =========================================================
# 12. COMPARAÇÃO DE PREÇOS ENTRE SUPERMERCADOS
# =========================================================

print("\n=== COMPARAÇÃO ENTRE SUPERMERCADOS ===")

produto_mercados = "Arroz"

dados_arroz = df[
    df["Produto_Padronizado"] == produto_mercados
].copy()

# Contar observações por supermercado
quantidade_coletas = (
    dados_arroz
    .groupby("Estab")
    .size()
    .sort_values(ascending=False)
)

# Selecionar os 10 supermercados com mais registros
mercados_selecionados = quantidade_coletas.head(10).index

dados_selecionados = dados_arroz[
    dados_arroz["Estab"].isin(mercados_selecionados)
]

# Calcular mediana e quantidade de registros
comparacao = (
    dados_selecionados
    .groupby("Estab")
    .agg(
        Preco_Mediano=("PPK", "median"),
        Quantidade_Registros=("PPK", "size")
    )
    .sort_values("Preco_Mediano")
)

print("\nMediana do preço do arroz por supermercado:")
print(comparacao.round(2).to_string())

# Criar gráfico
plt.figure(figsize=(12, 6))

plt.bar(
    comparacao.index,
    comparacao["Preco_Mediano"]
)

plt.title("Comparação do preço mediano do arroz entre supermercados")
plt.xlabel("Supermercado")
plt.ylabel("Preço padronizado (R$ por unidade de referência)")
plt.xticks(rotation=45)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(
    pasta_graficos / "comparacao_supermercados.png",
    dpi=300
)

plt.show()
