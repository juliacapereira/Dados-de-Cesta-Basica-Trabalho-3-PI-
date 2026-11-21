import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ----------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Cesta Básica — Análise e Previsão",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

PASTA = Path(__file__).resolve().parent
CAMINHO_DADOS = PASTA / "dados" / "dados_tratados.csv"
CAMINHO_METRICAS = PASTA / "resultados" / "metricas_modelos.csv"
CAMINHO_PREVISOES = PASTA / "resultados" / "previsoes_walkforward.csv"
CAMINHO_GRANGER = PASTA / "resultados" / "granger_produtos.csv"
CAMINHO_DM = PASTA / "resultados" / "teste_diebold_mariano.csv"


# ----------------------------------------------------------------------
# CARREGAMENTO COM CACHE
# ----------------------------------------------------------------------
@st.cache_data
def carregar_dados():
    df = pd.read_csv(
        CAMINHO_DADOS, sep=";", encoding="utf-8-sig", parse_dates=["Mes_Ano_Data"]
    )
    metricas = pd.read_csv(CAMINHO_METRICAS, sep=";", encoding="utf-8-sig")
    previsoes = pd.read_csv(
        CAMINHO_PREVISOES, sep=";", encoding="utf-8-sig", parse_dates=["Mes_Alvo"]
    )
    granger = pd.read_csv(CAMINHO_GRANGER, sep=";", encoding="utf-8-sig")
    dm = pd.read_csv(CAMINHO_DM, sep=";", encoding="utf-8-sig")
    return df, metricas, previsoes, granger, dm


df, metricas, previsoes, granger, dm = carregar_dados()

# ----------------------------------------------------------------------
# BARRA LATERAL (FILTROS)
# ----------------------------------------------------------------------
st.sidebar.title("Filtros da Análise")

produtos_foco = ["Arroz", "Feijão", "Açúcar", "Óleo"]
todos_produtos = sorted(df["Produto_Padronizado"].dropna().unique())

produto_sel = st.sidebar.selectbox(
    "Produto principal (Previsão e Detalhes)",
    options=produtos_foco,
    index=0,
)

produtos_comp = st.sidebar.multiselect(
    "Produtos para comparação histórica",
    options=todos_produtos,
    default=produtos_foco,
)

data_min = df["Mes_Ano_Data"].min().date()
data_max = df["Mes_Ano_Data"].max().date()
periodo = st.sidebar.slider(
    "Período de análise",
    min_value=data_min,
    max_value=data_max,
    value=(data_min, data_max),
    format="MM/YYYY",
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Projeto Integrador / Extensão — PUC-Campinas\n"
    "Base: ICB (Set/2022 a Ago/2026)"
)

# Filtrar base pelo período
mask_periodo = (df["Mes_Ano_Data"].dt.date >= periodo[0]) & (
    df["Mes_Ano_Data"].dt.date <= periodo[1]
)
df_filtrado = df[mask_periodo].copy()

# ----------------------------------------------------------------------
# CABEÇALHO E KPIs
# ----------------------------------------------------------------------
st.title("Monitoramento e Previsão de Preços da Cesta Básica")
st.markdown(
    "Análise exploratória e comparação de modelos preditivos (validação *walk-forward*) "
    "sobre o Indicador da Cesta Básica (PPK)."
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Registros tratados", f"{len(df_filtrado):,}".replace(",", "."))
col2.metric("Produtos monitorados", df_filtrado["Produto_Padronizado"].nunique())
col3.metric("Supermercados", df_filtrado["Estab"].nunique())
col4.metric("Meses na janela", df_filtrado["Mes_Ano_Data"].nunique())

st.markdown("---")

# ----------------------------------------------------------------------
# ABAS PRINCIPAIS
# ----------------------------------------------------------------------
aba1, aba2, aba3, aba4 = st.tabs(
    [
        "1. Evolução e Comparação",
        "2. Supermercados",
        "3. Previsão (Walk-Forward)",
        "4. Precedência (Granger)",
    ]
)

# ==================== ABA 1: EVOLUÇÃO ====================
with aba1:
    st.subheader("Evolução Relativa dos Preços (Base 100)")
    if produtos_comp:
        serie_comp = (
            df_filtrado[df_filtrado["Produto_Padronizado"].isin(produtos_comp)]
            .groupby(["Mes_Ano_Data", "Produto_Padronizado"])["PPK"]
            .median()
            .unstack()
            .sort_index()
        )
        indice_100 = serie_comp.apply(lambda s: (s / s.dropna().iloc[0]) * 100)
        indice_long = indice_100.reset_index().melt(
            id_vars="Mes_Ano_Data", var_name="Produto", value_name="Índice (Base 100)"
        )
        fig_comp = px.line(
            indice_long,
            x="Mes_Ano_Data",
            y="Índice (Base 100)",
            color="Produto",
            markers=True,
            labels={"Mes_Ano_Data": "Mês"},
        )
        fig_comp.update_layout(hovermode="x unified", height=430)
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Selecione ao menos um produto na barra lateral.")

    st.subheader(f"Série Mensal em Reais (PPK) — {produto_sel}")
    serie_prod = (
        df_filtrado[df_filtrado["Produto_Padronizado"] == produto_sel]
        .groupby("Mes_Ano_Data")["PPK"]
        .median()
        .reset_index()
    )
    fig_prod = px.line(
        serie_prod,
        x="Mes_Ano_Data",
        y="PPK",
        markers=True,
        labels={"Mes_Ano_Data": "Mês", "PPK": "Preço Mediano (R$)"},
    )
    fig_prod.update_traces(line_color="#1f77b4", line_width=2.5)
    fig_prod.update_layout(hovermode="x unified", height=360)
    st.plotly_chart(fig_prod, use_container_width=True)

# ==================== ABA 2: SUPERMERCADOS ====================
with aba2:
    st.subheader(f"Comparação de Preço Mediano por Supermercado — {produto_sel}")
    top_n = st.slider("Quantidade de supermercados (mais frequentes)", 5, 25, 10)

    dados_prod = df_filtrado[df_filtrado["Produto_Padronizado"] == produto_sel]
    top_mercados = dados_prod["Estab"].value_counts().head(top_n).index

    comp_merc = (
        dados_prod[dados_prod["Estab"].isin(top_mercados)]
        .groupby("Estab")
        .agg(Preco_Mediano=("PPK", "median"), Coletas=("PPK", "size"))
        .sort_values("Preco_Mediano")
        .reset_index()
    )

    fig_merc = px.bar(
        comp_merc,
        x="Estab",
        y="Preco_Mediano",
        text="Preco_Mediano",
        hover_data=["Coletas"],
        labels={"Estab": "Supermercado", "Preco_Mediano": "Preço Mediano (R$)"},
    )
    fig_merc.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside")
    fig_merc.update_layout(height=450)
    st.plotly_chart(fig_merc, use_container_width=True)

    st.caption(
        "Nota: a comparação reflete a mediana histórica na janela filtrada, sem controle "
        "de marca ou frequência de coleta em cada mês."
    )

# ==================== ABA 3: MODELAGEM E PREVISÃO ====================
with aba3:
    st.subheader(f"Previsão Walk-Forward — {produto_sel}")

    prev_prod = previsoes[previsoes["Produto"] == produto_sel].copy()
    met_prod = metricas[metricas["Produto"] == produto_sel].sort_values("RMSE")

    modelos_disponiveis = [
        c for c in prev_prod.columns if c not in ("Produto", "Mes_Alvo", "Real", "Ingenuo")
    ]
    melhor_modelo = met_prod[met_prod["Modelo"] != "Ingenuo"].iloc[0]["Modelo"]

    modelos_sel = st.multiselect(
        "Modelos para exibir no gráfico (além de Real e Ingênuo)",
        options=modelos_disponiveis,
        default=[melhor_modelo],
    )

    fig_prev = go.Figure()
    fig_prev.add_trace(
        go.Scatter(
            x=prev_prod["Mes_Alvo"],
            y=prev_prod["Real"],
            mode="lines+markers",
            name="Real",
            line=dict(color="black", width=3),
        )
    )
    fig_prev.add_trace(
        go.Scatter(
            x=prev_prod["Mes_Alvo"],
            y=prev_prod["Ingenuo"],
            mode="lines",
            name="Ingênuo (Baseline)",
            line=dict(color="gray", dash="dash"),
        )
    )
    for m in modelos_sel:
        fig_prev.add_trace(
            go.Scatter(
                x=prev_prod["Mes_Alvo"],
                y=prev_prod[m],
                mode="lines+markers",
                name=m,
            )
        )

    fig_prev.update_layout(
        xaxis_title="Mês Alvo",
        yaxis_title="Preço Padronizado PPK (R$)",
        hovermode="x unified",
        height=430,
    )
    st.plotly_chart(fig_prev, use_container_width=True)

    st.subheader(f"Tabela de Métricas — {produto_sel}")
    st.dataframe(
        met_prod.style.format(
            {
                "MAE": "{:.4f}",
                "RMSE": "{:.4f}",
                "MAPE(%)": "{:.2f}%",
                "Ganho_RMSE_vs_Ingenuo(%)": "{:+.2f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(f"Teste de Diebold-Mariano vs. Ingênuo — {produto_sel}")
    st.markdown(
        "Compara o erro quadrático de cada modelo com o do ingênuo. "
        "**DM negativo**: o modelo erra menos. **DM positivo**: o modelo erra mais. "
        "A diferença só é significativa se o p-valor for menor que 0,05."
    )

    dm_prod = dm[dm["Produto"] == produto_sel][
        ["Modelo", "DM", "p_valor", "Sig_5%"]
    ].copy()

    def _leitura(linha):
        if pd.isna(linha["p_valor"]):
            return "Não calculável (previsões idênticas às do ingênuo)"
        if not linha["Sig_5%"]:
            return "Sem diferença significativa"
        return "Significativamente melhor" if linha["DM"] < 0 else "Significativamente pior"

    dm_prod["Leitura"] = dm_prod.apply(_leitura, axis=1)

    st.dataframe(
        dm_prod.drop(columns="Sig_5%").style.format(
            {"DM": "{:+.3f}", "p_valor": "{:.4f}"}, na_rep="—"
        ),
        use_container_width=True,
        hide_index=True,
    )

    if dm_prod[(dm_prod["Sig_5%"]) & (dm_prod["DM"] < 0)].empty:
        st.info(
            "Nenhum modelo foi significativamente melhor que o ingênuo para este "
            "produto (23 previsões de teste, sem correção para comparações múltiplas)."
        )

# ==================== ABA 4: GRANGER ====================
with aba4:
    st.subheader("Teste de Precedência Temporal (Causalidade de Granger)")
    st.markdown(
        "Verifica se as variações mensais do produto **Causa (B)** ajudam a prever "
        "o produto **Efeito (A)** (nível de significância de 5%)."
    )
    st.dataframe(
        granger.style.format({"p_valor": "{:.4f}"}),
        use_container_width=True,
        hide_index=True,
    )
    if not granger["Sig_5%"].any():
        st.warning(
            "Nenhum par apresentou p-valor < 0,05. As variações de um produto não "
            "antecedem estatisticamente as de outro nessa janela mensal."
        )