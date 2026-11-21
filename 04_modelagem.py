"""
04_modelagem.py  -  Passo 4: modelagem e comparação de modelos

Questão principal:
  É possível prever o preço mensal de produtos da cesta básica usando seus
  valores históricos, e qual modelo apresenta maior precisão?

Entrada : dados/dados_tratados.csv  (gerado por 01_limpeza.py)
Saídas  : resultados/metricas_modelos.csv
          resultados/previsoes_walkforward.csv
          resultados/granger_produtos.csv
          graficos/previsao_<produto>.png
          graficos/comparacao_rmse_modelos.png

Modelos comparados (todos avaliados com walk-forward, sem embaralhar):
  - Ingenuo       : preço do último mês (baseline obrigatório)
  - Media_Movel   : média dos últimos JANELA_MM meses (baseline obrigatório)
  - ARIMA         : ordem escolhida por AIC só na janela inicial de treino
  - SARIMA        : ARIMA com componente sazonal anual (12 meses)
  - RF_proprio    : Random Forest só com o histórico do próprio produto
  - RF_cruzado    : Random Forest com histórico do produto + variações dos outros
  - GB_cruzado    : Gradient Boosting com as mesmas variáveis do RF_cruzado
"""
import io
import warnings
from contextlib import redirect_stdout
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import grangercausalitytests

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# CONFIGURAÇÃO (tudo que você precisa justificar na arguição está aqui)
# ----------------------------------------------------------------------
PRODUTOS = ["Arroz", "Feijão", "Açúcar", "Óleo"]
H = 1               # horizonte de previsão em meses (tente 1, 2, 3...)
JANELA_MM = 3       # janela da média móvel (baseline)
LAGS = 3            # quantidade de defasagens usadas nos modelos de ML
SEMENTE = 42
MAX_LAG_GRANGER = 3

PASTA = Path(__file__).resolve().parent
CAMINHO = PASTA / "dados" / "dados_tratados.csv"
PASTA_RES = PASTA / "resultados"
PASTA_GRAF = PASTA / "graficos"
PASTA_RES.mkdir(exist_ok=True)
PASTA_GRAF.mkdir(exist_ok=True)


# ----------------------------------------------------------------------
# 1. SÉRIES MENSAIS
# ----------------------------------------------------------------------
def carregar_series():
    """Mediana mensal do PPK por produto (mesma definição do 02_analise.py)."""
    df = pd.read_csv(CAMINHO, sep=";", encoding="utf-8-sig",
                     parse_dates=["Mes_Ano_Data"])
    precos = (
        df[df["Produto_Padronizado"].isin(PRODUTOS)]
        .groupby(["Mes_Ano_Data", "Produto_Padronizado"])["PPK"]
        .median().unstack().sort_index()
    )
    precos.index = precos.index.to_period("M").to_timestamp()
    calendario = pd.date_range(precos.index.min(), precos.index.max(), freq="MS")
    precos = precos.reindex(calendario)
    meses_faltantes = precos.isna().sum()
    # ffill usa só o passado (não vaza informação do futuro)
    precos = precos.ffill().dropna()
    return precos[[p for p in PRODUTOS if p in precos.columns]], meses_faltantes


# ----------------------------------------------------------------------
# 2. MODELOS DE SÉRIES TEMPORAIS
# ----------------------------------------------------------------------
def escolher_ordem_arima(treino):
    """Grade pequena de (p,1,q) por AIC, só com a janela inicial de treino.
    d=1 porque o ADF (02_analise.py) indica séries não estacionárias em nível."""
    melhor, melhor_aic = (1, 1, 1), np.inf
    for p in range(3):
        for q in range(3):
            try:
                aic = ARIMA(np.log(treino), order=(p, 1, q)).fit().aic
                if aic < melhor_aic:
                    melhor, melhor_aic = (p, 1, q), aic
            except Exception:
                continue
    return melhor


def prever_arima(treino, ordem):
    try:
        modelo = ARIMA(np.log(treino), order=ordem).fit()
        return float(np.exp(modelo.forecast(H).iloc[-1]))
    except Exception:
        return np.nan


def prever_sarima(treino, ordem):
    try:
        modelo = SARIMAX(np.log(treino), order=ordem,
                         seasonal_order=(0, 1, 1, 12)).fit(disp=False)
        return float(np.exp(modelo.forecast(H).iloc[-1]))
    except Exception:
        return np.nan


# ----------------------------------------------------------------------
# 3. MODELOS DE APRENDIZADO SUPERVISIONADO
# ----------------------------------------------------------------------
def montar_features(precos, produto, usar_outros):
    """
    Alvo: variação logarítmica entre t e t+H (log(P[t+H]) - log(P[t])).
    Prever a variação, e não o nível, evita que árvores (que não extrapolam)
    falhem diante da tendência de alta dos preços.
    Todas as variáveis da linha t usam apenas informação até t.
    """
    lp = np.log(precos)
    ret = lp.diff()
    X = pd.DataFrame(index=precos.index)
    for k in range(LAGS):
        X[f"ret_lag{k}"] = ret[produto].shift(k)
    X["ret_mm3"] = ret[produto].rolling(3).mean()
    X["ret_mm6"] = ret[produto].rolling(6).mean()
    X["desvio_mm12"] = lp[produto] - lp[produto].rolling(12).mean()
    X["mes_sin"] = np.sin(2 * np.pi * precos.index.month / 12)
    X["mes_cos"] = np.cos(2 * np.pi * precos.index.month / 12)
    if usar_outros:
        for outro in precos.columns:
            if outro != produto:
                X[f"{outro}_ret_lag0"] = ret[outro]
                X[f"{outro}_ret_lag1"] = ret[outro].shift(1)
    y = lp[produto].shift(-H) - lp[produto]
    return X, y


def dados_treino(X, y, t):
    """Linhas cujo alvo já é conhecido no instante t (posição s <= t-H)."""
    Xtr, ytr = X.iloc[: t - H + 1], y.iloc[: t - H + 1]
    ok = Xtr.notna().all(axis=1) & ytr.notna()
    return Xtr[ok], ytr[ok]


def ajustar_rf(X, y, origem_inicial):
    """Hiperparâmetros do RF escolhidos com validação temporal (TimeSeriesSplit)
    usando apenas a janela inicial de treino."""
    Xtr, ytr = dados_treino(X, y, origem_inicial)
    grade = {"max_depth": [2, 3, 5, None], "min_samples_leaf": [1, 3, 5]}
    busca = GridSearchCV(
        RandomForestRegressor(n_estimators=200, random_state=SEMENTE),
        grade, cv=TimeSeriesSplit(n_splits=3),
        scoring="neg_mean_absolute_error",
    )
    busca.fit(Xtr, ytr)
    return busca.best_params_


# ----------------------------------------------------------------------
# 4. WALK-FORWARD
# ----------------------------------------------------------------------
def walk_forward(precos, produto, origem_inicial):
    serie = precos[produto]
    n = len(serie)
    feats = {False: montar_features(precos, produto, False),
             True: montar_features(precos, produto, True)}

    ordem = escolher_ordem_arima(serie.iloc[: origem_inicial + 1])
    params_rf = {u: ajustar_rf(*feats[u], origem_inicial) for u in (False, True)}
    print(f"  {produto}: ordem ARIMA={ordem} | RF próprio={params_rf[False]} "
          f"| RF cruzado={params_rf[True]}")

    registros = []
    for t in range(origem_inicial, n - H):
        ultimo = serie.iloc[t]
        treino = serie.iloc[: t + 1]
        pred = {
            "Ingenuo": ultimo,
            "Media_Movel": serie.iloc[t - JANELA_MM + 1: t + 1].mean(),
            "ARIMA": prever_arima(treino, ordem),
            "SARIMA": prever_sarima(treino, ordem),
        }
        for nome, usar_outros in [("RF_proprio", False), ("RF_cruzado", True)]:
            X, y = feats[usar_outros]
            Xtr, ytr = dados_treino(X, y, t)
            m = RandomForestRegressor(n_estimators=200, random_state=SEMENTE,
                                      **params_rf[usar_outros])
            m.fit(Xtr, ytr)
            pred[nome] = ultimo * np.exp(m.predict(X.iloc[[t]])[0])
        X, y = feats[True]
        Xtr, ytr = dados_treino(X, y, t)
        gb = GradientBoostingRegressor(n_estimators=150, learning_rate=0.05,
                                       max_depth=2, subsample=0.8,
                                       random_state=SEMENTE)
        gb.fit(Xtr, ytr)
        pred["GB_cruzado"] = ultimo * np.exp(gb.predict(X.iloc[[t]])[0])

        registros.append({"Produto": produto, "Mes_Alvo": serie.index[t + H],
                          "Real": serie.iloc[t + H], **pred})
    return pd.DataFrame(registros)


# ----------------------------------------------------------------------
# 5. MÉTRICAS
# ----------------------------------------------------------------------
def calcular_metricas(previsoes):
    modelos = [c for c in previsoes.columns
               if c not in ("Produto", "Mes_Alvo", "Real")]
    linhas = []
    for produto, g in previsoes.groupby("Produto"):
        for m in modelos:
            # se ARIMA/SARIMA falhou em algum mês, usa o ingênuo naquele mês
            p = g[m].fillna(g["Ingenuo"])
            erro = g["Real"] - p
            linhas.append({
                "Produto": produto, "Modelo": m,
                "MAE": erro.abs().mean(),
                "RMSE": np.sqrt((erro ** 2).mean()),
                "MAPE(%)": (erro.abs() / g["Real"]).mean() * 100,
                "Falhas": int(g[m].isna().sum()),
            })
    res = pd.DataFrame(linhas)
    base = res[res["Modelo"] == "Ingenuo"].set_index("Produto")["RMSE"]
    res["Ganho_RMSE_vs_Ingenuo(%)"] = (
        (1 - res["RMSE"] / res["Produto"].map(base)) * 100
    )
    return res


# ----------------------------------------------------------------------
# 6. GRANGER ENTRE PRODUTOS (questão complementar)
# ----------------------------------------------------------------------
def granger_produtos(precos):
    """Testa se a variação de B ajuda a prever a variação de A (log-diferença)."""
    ret = np.log(precos).diff().dropna()
    linhas = []
    for a in ret.columns:
        for b in ret.columns:
            if a == b:
                continue
            with redirect_stdout(io.StringIO()):
                r = grangercausalitytests(ret[[a, b]], maxlag=MAX_LAG_GRANGER)
            pvals = {lag: r[lag][0]["ssr_ftest"][1] for lag in r}
            lag_best = min(pvals, key=pvals.get)
            linhas.append({"Causa(B)": b, "Efeito(A)": a,
                           "Melhor_lag": lag_best,
                           "p_valor": pvals[lag_best],
                           "Sig_5%": pvals[lag_best] < 0.05})
    return pd.DataFrame(linhas).sort_values("p_valor")


# ----------------------------------------------------------------------
# 7. GRÁFICOS
# ----------------------------------------------------------------------
def graficos(previsoes, metricas):
    for produto, g in previsoes.groupby("Produto"):
        melhor = (metricas[(metricas["Produto"] == produto)
                           & (metricas["Modelo"] != "Ingenuo")]
                  .sort_values("RMSE").iloc[0]["Modelo"])
        plt.figure(figsize=(12, 5))
        plt.plot(g["Mes_Alvo"], g["Real"], "k-o", label="Real", linewidth=2)
        plt.plot(g["Mes_Alvo"], g["Ingenuo"], "--", label="Ingênuo", alpha=0.7)
        plt.plot(g["Mes_Alvo"], g[melhor], "-s", label=f"Melhor modelo: {melhor}")
        plt.title(f"{produto}: previsão walk-forward ({H} mês à frente)")
        plt.xlabel("Mês"); plt.ylabel("PPK (R$)")
        plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
        plt.savefig(PASTA_GRAF / f"previsao_{produto}.png", dpi=300)
        plt.close()

    tabela = metricas.pivot(index="Modelo", columns="Produto", values="RMSE")
    tabela.plot(kind="bar", figsize=(12, 6))
    plt.title("RMSE por modelo e produto (menor = melhor)")
    plt.ylabel("RMSE (R$)"); plt.xticks(rotation=30)
    plt.grid(axis="y", alpha=0.3); plt.tight_layout()
    plt.savefig(PASTA_GRAF / "comparacao_rmse_modelos.png", dpi=300)
    plt.close()


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    precos, faltantes = carregar_series()
    n = len(precos)
    print("=== SÉRIES MENSAIS ===")
    print(f"Meses: {n} ({precos.index.min():%Y-%m} a {precos.index.max():%Y-%m})")
    print("Meses sem coleta preenchidos (ffill):")
    print(faltantes.to_string())

    origem_inicial = max(24, int(0.5 * n))
    if n - origem_inicial - H < 10:
        print("\nATENÇÃO: poucos meses para avaliar. Reduza H ou a janela inicial.")
    print(f"\nTreino inicial: {origem_inicial + 1} meses | "
          f"previsões avaliadas por produto: {n - origem_inicial - H}")

    print("\n=== WALK-FORWARD ===")
    previsoes = pd.concat(
        [walk_forward(precos, p, origem_inicial) for p in precos.columns],
        ignore_index=True,
    )
    metricas = calcular_metricas(previsoes)

    print("\n=== MÉTRICAS (ordenadas por RMSE dentro de cada produto) ===")
    print(metricas.sort_values(["Produto", "RMSE"]).round(3).to_string(index=False))

    print("\n=== MODELO MÉDIO (RMSE médio entre produtos) ===")
    print(metricas.groupby("Modelo")[["MAE", "RMSE", "MAPE(%)"]]
          .mean().sort_values("RMSE").round(3).to_string())

    print("\n=== GRANGER ENTRE PRODUTOS ===")
    granger = granger_produtos(precos)
    print(granger.round(4).to_string(index=False))

    previsoes.to_csv(PASTA_RES / "previsoes_walkforward.csv", sep=";",
                     index=False, encoding="utf-8-sig")
    metricas.to_csv(PASTA_RES / "metricas_modelos.csv", sep=";",
                    index=False, encoding="utf-8-sig")
    granger.to_csv(PASTA_RES / "granger_produtos.csv", sep=";",
                   index=False, encoding="utf-8-sig")
    graficos(previsoes, metricas)
    print("\nResultados e gráficos salvos.")


if __name__ == "__main__":
    main()