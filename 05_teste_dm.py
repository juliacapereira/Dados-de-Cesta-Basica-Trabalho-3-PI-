"""
05_teste_dm.py  -  Passo 5: as diferenças entre modelos são estatisticamente
significativas?

Aplica o teste de Diebold-Mariano (perda quadrática, horizonte H=1, correção
de pequenas amostras de Harvey-Leybourne-Newbold) comparando cada modelo com o
ingênuo, usando as previsões walk-forward de 04_modelagem.py.

H0: o modelo e o ingênuo têm a mesma acurácia preditiva.
Estatística DM < 0  -> o modelo erra menos que o ingênuo.

Entrada : resultados/previsoes_walkforward.csv
Saída   : resultados/teste_diebold_mariano.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PASTA = Path(__file__).resolve().parent
PASTA_RES = PASTA / "resultados"
H = 1  # mesmo horizonte usado em 04_modelagem.py


def diebold_mariano(erro_modelo, erro_base, h=H):
    """DM com perda quadrática e correção HLN; p-valor bilateral (t, n-1 gl)."""
    d = np.asarray(erro_modelo) ** 2 - np.asarray(erro_base) ** 2
    n = len(d)
    media = d.mean()
    # variância de longo prazo (autocovariâncias até h-1; para h=1 é a variância)
    gamma0 = np.var(d, ddof=0)
    var_lp = gamma0
    for k in range(1, h):
        cov = np.cov(d[k:], d[:-k], ddof=0)[0, 1]
        var_lp += 2 * cov
    if var_lp <= 0 or np.isclose(var_lp, 0):
        return np.nan, np.nan
    dm = media / np.sqrt(var_lp / n)
    hln = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    dm_corr = dm * hln
    p = 2 * (1 - stats.t.cdf(abs(dm_corr), df=n - 1))
    return dm_corr, p


def main():
    prev = pd.read_csv(PASTA_RES / "previsoes_walkforward.csv", sep=";",
                       encoding="utf-8-sig")
    modelos = [c for c in prev.columns
               if c not in ("Produto", "Mes_Alvo", "Real", "Ingenuo")]
    linhas = []
    for produto, g in prev.groupby("Produto"):
        e_base = g["Real"] - g["Ingenuo"]
        for m in modelos:
            e_mod = g["Real"] - g[m].fillna(g["Ingenuo"])
            dm, p = diebold_mariano(e_mod, e_base)
            linhas.append({
                "Produto": produto, "Modelo": m, "n_previsoes": len(g),
                "DM": dm, "p_valor": p,
                "Sig_5%": bool(p < 0.05) if pd.notna(p) else False,
                "Melhor_que_ingenuo": bool(dm < 0) if pd.notna(dm) else False,
            })
    res = pd.DataFrame(linhas)
    res.to_csv(PASTA_RES / "teste_diebold_mariano.csv", sep=";",
               index=False, encoding="utf-8-sig")
    print("=== DIEBOLD-MARIANO vs INGÊNUO (perda quadrática, HLN) ===")
    print(res.round(4).to_string(index=False))
    print(f"\nComparações significativas a 5%: {int(res['Sig_5%'].sum())} "
          f"de {len(res)} (sem correção para comparações múltiplas).")


if __name__ == "__main__":
    main()