import pandas as pd
from pathlib import Path

# 1. Localizar a planilha
pasta_projeto = Path(__file__).resolve().parent
caminho = pasta_projeto / "dados" / "ICB_DADOS_2026.xlsx"

# 2. Ler o arquivo Excel
df = pd.read_excel(caminho)

# 3. Mostrar as primeiras linhas
print("\n=== PRIMEIRAS 5 LINHAS ===")
print(df.head())

# 4. Verificar tamanho da base
print("\n=== DIMENSÕES ===")
print(f"Quantidade de registros: {df.shape[0]}")
print(f"Quantidade de colunas: {df.shape[1]}")

# 5. Verificar nomes e tipos das colunas
print("\n=== INFORMAÇÕES DAS COLUNAS ===")
df.info()

# 6. Verificar valores ausentes
print("\n=== VALORES AUSENTES ===")
print(df.isnull().sum())


# 7. Identificar produtos e supermercados
print("\n=== PRODUTOS E SUPERMERCADOS ===")

print("Quantidade de produtos:", df["Produto"].nunique())
print("Quantidade de supermercados:", df["Estab"].nunique())

print("\nProdutos encontrados:")
print(sorted(df["Produto"].unique()))

# 8. Verificar o período dos dados
print("\n=== PERÍODO DOS DADOS ===")

print("Primeiro mês:", df["Mes_Ano_Data"].min())
print("Último mês:", df["Mes_Ano_Data"].max())
print("Quantidade de meses:", df["Mes_Ano_Data"].nunique())

# 9. Verificar duplicatas
print("\n=== REGISTROS DUPLICADOS ===")

duplicados = df.duplicated().sum()
print("Registros exatamente duplicados:", duplicados)

# 10. Investigar os preços
print("\n=== ANÁLISE DOS PREÇOS ===")

print("Preço mínimo:", df["Preco"].min())
print("Preço máximo:", df["Preco"].max())
print("Preço médio:", df["Preco"].mean())

print("Preços iguais a zero:", (df["Preco"] == 0).sum())
print("Preços negativos:", (df["Preco"] < 0).sum())


# 11. Investigar registros duplicados
print("\n=== DUPLICATAS POR PRODUTO ===")

duplicados_df = df[df.duplicated(keep=False)]

print(
    duplicados_df["Produto"]
    .value_counts()
    .head(15)
)

# 12. Investigar os maiores preços
print("\n=== 15 MAIORES PREÇOS ===")

print(
    df.nlargest(15, "Preco")[
        ["Mes_Ano_Data", "Estab", "Produto",
         "Marca", "Preco", "Quantidade", "PPK"]
    ].to_string(index=False)
)

# 13. Investigar os menores preços
print("\n=== 15 MENORES PREÇOS ===")

print(
    df.nsmallest(15, "Preco")[
        ["Mes_Ano_Data", "Estab", "Produto",
         "Marca", "Preco", "Quantidade", "PPK"]
    ].to_string(index=False)
)

# 14. Investigar as quantidades registradas
print("\n=== QUANTIDADES ===")

print(
    df["Quantidade"]
    .value_counts()
    .sort_index()
    .to_string()
)


# 15. Identificar possíveis outliers pelo método IQR

print("\n=== POSSÍVEIS OUTLIERS POR PRODUTO ===")

def identificar_outliers(grupo):
    q1 = grupo["PPK"].quantile(0.25)
    q3 = grupo["PPK"].quantile(0.75)

    iqr = q3 - q1

    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    return grupo[
        (grupo["PPK"] < limite_inferior) |
        (grupo["PPK"] > limite_superior)
    ]

outliers = []

for produto, grupo in df.groupby("Produto"):
    encontrados = identificar_outliers(grupo)

    if not encontrados.empty:
        outliers.append(encontrados)

if outliers:
    df_outliers = pd.concat(outliers)

    print("Total de possíveis outliers:", len(df_outliers))

    print("\nProdutos com mais outliers:")
    print(
        df_outliers["Produto"]
        .value_counts()
        .head(15)
    )

    # Salvar os casos suspeitos para investigação
    pasta_resultados = pasta_projeto / "resultados"
    pasta_resultados.mkdir(exist_ok=True)

    df_outliers.to_excel(
        pasta_resultados / "outliers_identificados.xlsx",
        index=False
    )

    print("\nArquivo de outliers salvo com sucesso.")

else:
    print("Nenhum outlier identificado.")


# 16. Investigar a distribuição temporal dos outliers

print("\n=== OUTLIERS POR ANO ===")

df_outliers = df_outliers.copy()

df_outliers["Ano"] = (
    df_outliers["Mes_Ano_Data"].dt.year
)

print(
    df_outliers["Ano"]
    .value_counts()
    .sort_index()
)

# 17. Verificar os meses com mais outliers

print("\n=== MESES COM MAIS OUTLIERS ===")

print(
    df_outliers["Mes_Ano_Data"]
    .value_counts()
    .head(10)
    .to_string()
)

# 18. Verificar os supermercados com mais outliers

print("\n=== SUPERMERCADOS COM MAIS OUTLIERS ===")

print(
    df_outliers["Estab"]
    .value_counts()
    .head(10)
    .to_string()
)


# 19. Investigar produtos com nomes semelhantes

print("\n=== PRODUTOS COM NOMES SEMELHANTES ===")

produtos_investigar = [
    "Carne Acem",
    "Carne Bovina Acem",
    "Carne Coxão Mole",
    "Carne Bovina Coxão Mole",
    "Carne Pernil",
    "Carne Suína Pernil",
    "Pernil",
    "Farinha",
    "Farinha de Trigo",
    "Pão",
    "Pão Francês"
]

resumo_produtos = (
    df[df["Produto"].isin(produtos_investigar)]
    .groupby("Produto")
    .agg(
        Registros=("Preco", "size"),
        Preco_Mediano=("PPK", "median"),
        Preco_Minimo=("PPK", "min"),
        Preco_Maximo=("PPK", "max"),
        Primeiro_Mes=("Mes_Ano_Data", "min"),
        Ultimo_Mes=("Mes_Ano_Data", "max")
    )
)
colunas_precos = [
    "Preco_Mediano",
    "Preco_Minimo",
    "Preco_Maximo"
]

resumo_produtos[colunas_precos] = (
    resumo_produtos[colunas_precos].round(2)
)
print(resumo_produtos.to_string())


# 20. Criar uma coluna de produto padronizado

print("\n=== PADRONIZAÇÃO DOS PRODUTOS ===")

df["Produto_Padronizado"] = df["Produto"]

substituicoes = {
    "Carne Acem": "Carne Bovina Acem",
    "Carne Coxão Mole": "Carne Bovina Coxão Mole",
    "Carne Pernil": "Carne Suína Pernil"
}

df["Produto_Padronizado"] = (
    df["Produto_Padronizado"]
    .replace(substituicoes)
)

print("Produtos antes:", df["Produto"].nunique())

print(
    "Produtos após padronização:",
    df["Produto_Padronizado"].nunique()
)

print("\nRegistros com nomes alterados:")

alterados = df[
    df["Produto"] != df["Produto_Padronizado"]
]

print(
    alterados[
        ["Produto", "Produto_Padronizado"]
    ]
    .value_counts()
    .to_string()
)


# 21. Criar uma versão sem duplicatas exatas

print("\n=== TRATAMENTO DE DUPLICATAS ===")

# Colunas originais usadas para verificar duplicatas
colunas_originais = [
    "Mes_Ano_Data",
    "Data_Coleta",
    "Estab",
    "Produto",
    "Marca",
    "Preco",
    "Quantidade",
    "PPK"
]

# Criar uma cópia, sem modificar o DataFrame original
df_tratado = df.copy()

# Remover repetições exatas das colunas originais
df_tratado = df_tratado.drop_duplicates(
    subset=colunas_originais,
    keep="first"
).copy()

# Comparar quantidades
print("Registros originais:", len(df))
print("Registros após tratamento:", len(df_tratado))

print(
    "Duplicatas removidas:",
    len(df) - len(df_tratado)
)

# Criar pasta para os arquivos tratados
pasta_dados = pasta_projeto / "dados"
pasta_dados.mkdir(exist_ok=True)

# Exportar versão provisória
df_tratado.to_csv(
    pasta_dados / "dados_sem_duplicatas.csv",
    index=False,
    encoding="utf-8-sig",
    sep=";"
)

print("\nBase provisória exportada com sucesso!")


# 22. Investigar preços extremamente suspeitos

print("\n=== INVESTIGAÇÃO DE PREÇOS SUSPEITOS ===")

# Casos que identificamos durante a exploração
casos_suspeitos = (
    (df_tratado["Preco"] == 999.00) |
    (df_tratado["Preco"] == 0.10) |
    (
        (df_tratado["Produto"] == "Pernil") &
        (df_tratado["Preco"] == 1.00)
    )
)

suspeitos = df_tratado.loc[casos_suspeitos].copy()

# Calcular a mediana por produto e mês
medianas = (
    df_tratado
    .groupby(["Produto_Padronizado", "Mes_Ano_Data"])["PPK"]
    .median()
    .rename("Mediana_Mensal")
    .reset_index()
)

# Adicionar a mediana aos registros suspeitos
suspeitos = suspeitos.merge(
    medianas,
    on=["Produto_Padronizado", "Mes_Ano_Data"],
    how="left"
)

# Comparar o preço com a mediana
suspeitos["Razao_Mediana"] = (
    suspeitos["PPK"] / suspeitos["Mediana_Mensal"]
)

colunas_exibir = [
    "Mes_Ano_Data",
    "Estab",
    "Produto",
    "PPK",
    "Mediana_Mensal",
    "Razao_Mediana"
]

tabela_exibir = suspeitos[colunas_exibir].copy()

colunas_numericas = [
    "PPK",
    "Mediana_Mensal",
    "Razao_Mediana"
]

tabela_exibir[colunas_numericas] = (
    tabela_exibir[colunas_numericas].round(2)
)

print(tabela_exibir.to_string(index=False))

# Exportar para investigação
suspeitos.to_csv(
    pasta_resultados / "precos_suspeitos.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig"
)

print("\nInvestigação exportada com sucesso!")


# 23. Separar registros suspeitos da base de análise

print("\n=== PREPARAÇÃO DA BASE TRATADA ===")

# Critérios provisórios de valores extremamente suspeitos
criterios_suspeitos = (
    (df_tratado["Preco"] == 999.00) |
    (df_tratado["Preco"] == 0.10) |
    (
        (df_tratado["Produto"] == "Pernil") &
        (df_tratado["Preco"] == 1.00)
    )
)

# Guardar os registros que serão excluídos provisoriamente
registros_excluidos = df_tratado.loc[
    criterios_suspeitos
].copy()

# Manter os demais registros
df_final = df_tratado.loc[
    ~criterios_suspeitos
].copy()

# Exportar registros separados
registros_excluidos.to_csv(
    pasta_resultados / "registros_excluidos.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig"
)

# Exportar base tratada
df_final.to_csv(
    pasta_dados / "dados_tratados.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig"
)

print("Registros originais:", len(df))
print("Após remover duplicatas:", len(df_tratado))
print("Registros suspeitos separados:", len(registros_excluidos))
print("Registros na base tratada:", len(df_final))

print("\nBase tratada exportada com sucesso!")
