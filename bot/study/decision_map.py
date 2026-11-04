"""
Decision map: which concepts and indicators support a trade, and how much - per setup.

Setups: breakout (certainty >= 7, F1 + F2) at 2:1, and 1D 4th-test bounce at 3:1.
Every factor is a yes/no question asked at the entry time, grouped in layers (context, structure & liquidity,
momentum, volume, stretch & noise). Factor definitions were fixed in advance from earlier studies.
Points: L2 logistic regression of "trade won (after costs)" on all factors of the setup, fitted on research data;
points = coefficient x 10, rounded. A trade's score = sum of the points of the factors that are true.
Validation of the score: each year from 2023 is scored with points fitted only on earlier years; the holdout is
scored with points fitted on all research data.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .failure_liquidity import liquidity_features, swing_tables
from .smalltf import COST_TAKER
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")


def breakout_factors(A: pd.DataFrame) -> pd.DataFrame:
    med = lambda c: A.loc[~A["hold"], c].median()  # noqa: E731  (research medians)
    F = pd.DataFrame(index=A.index)
    F["Context | BTC 4h trend agrees"] = A["n_btc_4h"] > 0
    F["Context | weekly trend agrees"] = A["m_1W_trend"] > 0
    F["Context | daily trend agrees"] = A["m_1D_trend"] > 0
    F["Structure | clean risk zone (no liquidity between entry and stop)"] = (A["liq_in_risk"] == 0) & (A["pool_near_stop"] == 0)
    F["Structure | no untaken liquidity before target"] = A["liq_in_path"] == 0
    F["Structure | low-volume path to target (volume profile)"] = A["n_vp_lvn_share"] > med("n_vp_lvn_share")
    F["Structure | no high-volume node before target"] = A["n_vp_hvn_path"] <= 0
    F["Momentum | 6h MACD agrees"] = A["m_6h_macd"] > 0
    F["Momentum | 4h Supertrend agrees"] = A["m_4h_supertrend"] > 0
    F["Momentum | 12h EMA slope agrees"] = A["m_12h_slope"] > 0
    F["Momentum | strong DI spread (above median)"] = A["f_di"] > med("f_di")
    F["Momentum | no 6h MACD fade"] = A["m_6h_macd_fade"] >= 0
    F["Volume | 2h volume climax our way"] = A["m_2h_climax"] > 0
    F["Volume | breakout candle volume > 1.5x"] = A["f_vol"] > 1.5
    F["Volume | price beyond weekly VWAP our way"] = A["n_vwap_week"] > 0
    F["Volume | buy/sell pressure (CVD) our way"] = A["n_cvd_trend"] > 0
    F["Stretch | 1h RSI stretched our way (momentum)"] = A["m_1h_rsi_ext"] < 0
    F["Stretch | no Bollinger squeeze before break"] = A["n_squeeze"] <= 0
    F["Stretch | not choppy (Choppiness below median)"] = A["n_chop"] < med("n_chop")
    return F.astype(float)


def bounce_factors(B: pd.DataFrame) -> pd.DataFrame:
    F = pd.DataFrame(index=B.index)
    F["Context | BTC 4h trend agrees"] = B["n_btc_4h"] > 0
    F["Context | weekly trend agrees"] = B["m_1W_trend"] > 0
    F["Context | daily trend agrees"] = B["m_1D_trend"] > 0
    F["Structure | level tested 6+ times"] = B["test_n"] >= 6
    F["Structure | an earlier failed break of the level"] = B["prev_failed"] > 0
    F["Structure | no untaken liquidity before target"] = B["liq_in_path"] == 0
    F["Structure | low-volume path to target (volume profile)"] = B["n_vp_lvn_share"] > B.loc[~B["hold"], "n_vp_lvn_share"].median()
    F["Momentum | MACD turning our way"] = B["f_macd_turn"] > 0
    F["Momentum | 1D RSI stretched against us (oversold/overbought)"] = B["m_1D_rsi_ext"] > 0
    F["Momentum | 1D Stochastic stretched against us"] = B["m_1D_stoch_ext"] > 0
    F["Volume | volume trend rising (10 candles)"] = B["f_vol_slope"] > 0.03
    F["Volume | touch candle volume > 1.5x"] = B["f_vol_prev"] > 1.5
    F["Volume | bounce volume at least 0.8x the touch"] = (B["f_vol"] / B["f_vol_prev"]) >= 0.8
    F["Volume | buy/sell pressure (CVD) with the bounce"] = B["n_cvd_trend"] > 0
    F["Stretch | strong bounce candle (body > 0.5 ATR)"] = B["f_body"] > 0.5
    return F.astype(float)


def fit_points(F: pd.DataFrame, y: pd.Series) -> pd.Series:
    from sklearn.linear_model import LogisticRegression
    m = LogisticRegression(C=0.5, max_iter=2000).fit(F.to_numpy(), y.to_numpy().astype(int))
    return pd.Series(np.round(m.coef_[0] * 10).astype(int), index=F.columns)


def factor_table(F, X):
    rows = []
    for col in F.columns:
        for per, pm in (("r", ~X["hold"]), ("h", X["hold"])):
            pass
        r, h = ~X["hold"], X["hold"]
        y = X["net"] > 0
        row = {"factor": col, "layer": col.split(" | ")[0], "name": col.split(" | ")[1],
               "share": F.loc[r, col].mean()}
        for p, m in (("r", r), ("h", h)):
            yes, no = m & (F[col] > 0), m & (F[col] <= 0)
            row[f"{p}_yes"] = y[yes].mean() if yes.sum() else math.nan
            row[f"{p}_no"] = y[no].mean() if no.sum() else math.nan
            row[f"{p}_n_yes"] = int(yes.sum())
        rows.append(row)
    return pd.DataFrame(rows)


def score_validation(F, X):
    y = X["net"] > 0
    years = sorted(X.loc[~X["hold"], "decision_time"].dt.year.unique())
    scored = []
    for yr in [v for v in years if v >= 2023]:
        train = (X["decision_time"].dt.year < yr) & ~X["hold"]
        test = (X["decision_time"].dt.year == yr) & ~X["hold"]
        if train.sum() < 60:
            continue
        pts = fit_points(F[train], y[train])
        scored.append(pd.DataFrame({"score": F[test] @ pts, "win": y[test], "net": X.loc[test, "net"], "period": str(yr)}))
    pts_all = fit_points(F[~X["hold"]], y[~X["hold"]])
    scored.append(pd.DataFrame({"score": F[X["hold"]] @ pts_all, "win": y[X["hold"]], "net": X.loc[X["hold"], "net"],
                                "period": "holdout"}))
    return pd.concat(scored), pts_all


def draw_map(tab: pd.DataFrame, pts: pd.Series, title: str, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = tab.copy()
    t["points"] = t["factor"].map(pts)
    t["d_r"] = (t["r_yes"] - t["r_no"]) * 100
    t["d_h"] = (t["h_yes"] - t["h_no"]) * 100
    layers = list(dict.fromkeys(t["layer"]))
    t["lorder"] = t["layer"].map({l: i for i, l in enumerate(layers)})
    t = t.sort_values(["lorder", "points"], ascending=[True, False]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(13, 0.42 * len(t) + 1.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(len(t), -1.2)
    ax.axis("off")
    heads = [("factor (true = supports the trade?)", 0.05, "left"), ("points", 5.6, "center"),
             ("win % yes / no (research)", 7.0, "center"), ("holdout yes / no", 8.7, "center")]
    for txt, x, ha in heads:
        ax.text(x, -0.7, txt, ha=ha, va="center", fontsize=9, fontweight="bold")
    cmap = plt.get_cmap("RdYlGn")
    prev = None
    for i, r in t.iterrows():
        if r["layer"] != prev:
            ax.axhline(i - 0.5, color="#999", linewidth=0.8)
            prev = r["layer"]
        ax.text(0.05, i, f"[{r['layer']}] {r['name']}", va="center", fontsize=8.5)
        p = r["points"]
        ax.add_patch(plt.Rectangle((5.25, i - 0.4), 0.7, 0.8, color=cmap(0.5 + max(-0.5, min(0.5, p / 12)))))
        ax.text(5.6, i, f"{p:+d}", ha="center", va="center", fontsize=9, fontweight="bold")
        for x, a, b, d in ((7.0, r["r_yes"], r["r_no"], r["d_r"]), (8.7, r["h_yes"], r["h_no"], r["d_h"])):
            col = cmap(0.5 + max(-0.5, min(0.5, (d if d == d else 0) / 40)))
            ax.add_patch(plt.Rectangle((x - 0.75, i - 0.4), 1.5, 0.8, color=col, alpha=0.85))
            txt = "-" if (a != a or b != b) else f"{a:.0%} / {b:.0%}"
            ax.text(x, i, txt, ha="center", va="center", fontsize=8.5)
    ax.set_title(title, fontsize=11, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run_decision_map(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    sw = swing_tables(df5u)
    L = ["# Decision map: which concepts and indicators support the trade", "",
         "Each factor is a yes/no question at the entry time. **points** come from fitting all factors together "
         "(they share credit, so a factor that only repeats another gets few points). *win % yes / no* = win rate "
         "after costs when the factor is true / false. Score = sum of points of the true factors.", ""]
    sets = []
    A = pd.read_pickle(ROOT / "results" / "boost_A_flow.pkl")
    A["T"], A["atr_px"] = 2.0, A["f_atr_pct"] * A["entry"]
    A = pd.concat([A, liquidity_features(A, sw, df5n)], axis=1)
    A["net"] = A["R_2:1"] - COST_TAKER / A["stop_pct"]
    sets.append(("Breakouts (2:1)", A, breakout_factors(A)))
    B = pd.read_pickle(ROOT / "results" / "boost_B_flow.pkl")
    B = B[B["decision_time"] >= pd.Timestamp("2020-06-01")].copy()
    B["T"], B["atr_px"] = 3.0, B["f_atr_pct"] * B["entry"]
    B = pd.concat([B, liquidity_features(B, sw, df5n)], axis=1)
    B["net"] = B["R_3:1"] - COST_TAKER / B["stop_pct"]
    sets.append(("1D 4th-test bounces (3:1)", B, bounce_factors(B)))
    for name, X, F in sets:
        X = X.reset_index(drop=True)
        F = F.reset_index(drop=True).fillna(0)
        tab = factor_table(F, X)
        sv, pts = score_validation(F, X)
        img = out_dir / f"decision_map_{'breakout' if 'Break' in name else 'bounce'}.png"
        draw_map(tab, pts, f"Decision map - {name}  (points: + supports, - opposes)", img)
        tab["points"] = tab["factor"].map(pts)
        L += [f"## {name}", "", f"![map]({img.name})", "",
              _table(tab.sort_values(["layer", "points"], ascending=[True, False]),
                     [("layer", "layer", str), ("name", "factor", str), ("points", "points", lambda v: f"{int(v):+d}"),
                      ("share", "how often true", _pct), ("r_yes", "win % if true", _pct), ("r_no", "win % if false", _pct),
                      ("h_yes", "holdout win % if true", _pct), ("h_no", "holdout win % if false", _pct)]), ""]
        # score bands (out-of-sample scores)
        q = sv["score"].quantile([0.33, 0.67]).to_numpy()
        sv["band"] = np.where(sv["score"] <= q[0], "low score", np.where(sv["score"] <= q[1], "middle score", "high score"))
        rows = []
        for per in ("2023-25", "holdout"):
            g = sv[sv["period"] != "holdout"] if per == "2023-25" else sv[sv["period"] == "holdout"]
            for band in ("low score", "middle score", "high score"):
                gg = g[g["band"] == band]
                rows.append({"period": per, "band": band, "n": len(gg), "win": gg["win"].mean() if len(gg) else math.nan,
                             "avg": gg["net"].mean() if len(gg) else math.nan})
        L += ["### Does a higher score win more? (scores never fitted on the trades they score)", "",
              f"Bands: low = score <= {q[0]:.0f}, high = score > {q[1]:.0f}.", "",
              _table(pd.DataFrame(rows), [("period", "period", str), ("band", "score band", str), ("n", "trades", str),
                                          ("win", "win %", _pct), ("avg", "avg R after costs", lambda v: f"{v:+.2f}")]), ""]
    path = out_dir / "decision_map.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
