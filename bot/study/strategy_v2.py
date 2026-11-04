"""
Strategy v2: filtered 2:1 breakouts (+ A+ tier) and 1D 4th-test bounces at 3:1.

Inputs (built by `indicator-boost` + flow features):
  results/boost_A_flow.pkl  breakouts certainty >= 7 (2h/4h/1D), F1 + F2, replayed at 2:1, with all indicators
  results/boost_B.pkl       1D zone tested >= 4 times, bounce confirmed, replayed at 3:1
Rules:
  breakout   BTC 4h close above/below its EMA20 in the trade direction AND 6h MACD histogram in the trade direction
  A+         breakout AND low-volume path to the 2R target (LVN share above the research median)
  bounce     unchanged
Account: compounding, positions may overlap, each trade risks a % of equity at entry, leverage capped at 5x,
P&L booked at the exit; market-order costs.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from .smalltf import COST_TAKER
from .sr2_run import _pct, _r, _table

HOLDOUT = pd.Timestamp("2025-11-01")
START = pd.Timestamp("2022-01-01")


def build_trades() -> pd.DataFrame:
    A = pd.read_pickle(ROOT / "results" / "boost_A_flow.pkl")
    B = pd.read_pickle(ROOT / "results" / "boost_B.pkl")
    lvn_med = A.loc[~A["hold"], "n_vp_lvn_share"].median()
    brk = A[(A["n_btc_4h"] > 0) & (A["m_6h_macd"] > 0)].copy()
    brk["setup"] = np.where(brk["n_vp_lvn_share"] > lvn_med, "A+ breakout (2:1)", "breakout (2:1)")
    brk["R"], brk["exit"] = brk["R_2:1"], brk["exit_2:1"]
    bnc = B.copy()
    bnc["setup"] = "1D 4th-test bounce (3:1)"
    bnc["R"], bnc["exit"] = bnc["R_3:1"], bnc["exit_3:1"]
    cols = ["decision_time", "exit", "setup", "tf", "direction", "stop_pct", "R", "hold"]
    t = pd.concat([brk[cols], bnc[cols]], ignore_index=True)
    t = t[t["decision_time"] >= START].sort_values("decision_time").reset_index(drop=True)
    t["net"] = t["R"] - COST_TAKER / t["stop_pct"]
    t["year"] = np.where(t["hold"], "holdout", t["decision_time"].dt.year.astype(str))
    t.attrs["lvn_med"] = float(lvn_med)
    return t


def simulate(t: pd.DataFrame, risk: dict, lev_cap: float = 5.0) -> dict:
    ev = sorted([(r.decision_time, 0, i) for i, r in t.iterrows()] + [(r.exit, 1, i) for i, r in t.iterrows()])
    eq, open_n, curve = 1.0, {}, [(t["decision_time"].min(), 1.0)]
    for ts, kind, i in ev:
        r = t.loc[i]
        if kind == 0:
            open_n[i] = eq * min(risk[r.setup] / r.stop_pct, lev_cap)
        else:
            eq = max(eq + open_n.pop(i) * (r.R * r.stop_pct - COST_TAKER), 0.0)
            curve.append((ts, eq))
            if eq <= 0:
                break
    s = pd.Series([v for _, v in curve], index=pd.DatetimeIndex([k for k, _ in curve])).sort_index()
    s = s[~s.index.duplicated(keep="last")]
    wk = s.resample("W-MON", label="left", closed="left").last().ffill()
    wr = wk.pct_change().dropna()
    active = wr[wr != 0]
    months = s.resample("ME").last().ffill().pct_change().dropna()
    return {"final": float(s.iloc[-1]), "max_dd": float((s / s.cummax() - 1).min()),
            "avg_week": float(wr.mean()), "win_weeks": float((active > 0).mean()) if len(active) else math.nan,
            "weeks_20": float((wr >= 0.2).mean()), "avg_month": float(months.mean()) if len(months) else math.nan,
            "win_months": float((months > 0).mean()) if len(months) else math.nan}


def run_strategy_v2(cfg: Config, out_dir: Path) -> Path:
    t = build_trades()
    t.to_pickle(ROOT / "results" / "strategy_v2_trades.pkl")
    L = ["# Strategy v2: filtered 2:1 breakouts (+ A+) and 1D 4th-test bounces (3:1)", "",
         "Breakouts: certainty >= 7 on 2h / 4h / 1D, stop >= 0.6%, not the quietest 20% of markets, **BTC 4h trend "
         "agrees and 6h MACD agrees**. **A+** = also breaking into a low-volume zone (volume profile). Bounces: 1D zone "
         "tested 4+ times, confirmed bounce, 3:1. Every trade replayed on 5-minute candles; market-order costs. "
         "**win %** = trades closed in profit. Research 2022 - Oct 2025 (scored out-of-sample), holdout Nov 2025 on.", ""]
    rows = []
    for (yr, st), g in t.groupby(["year", "setup"]):
        rows.append({"year": yr, "setup": st, "n": len(g), "win": (g["net"] > 0).mean(), "avg": g["net"].mean()})
    for yr, g in t.groupby("year"):
        rows.append({"year": yr, "setup": "ALL TRADES", "n": len(g), "win": (g["net"] > 0).mean(), "avg": g["net"].mean()})
    for per, g in (("2022-25 total", t[~t["hold"]]), ("holdout total", t[t["hold"]])):
        for st, gg in list(g.groupby("setup")) + [("ALL TRADES", g)]:
            rows.append({"year": per, "setup": st, "n": len(gg), "win": (gg["net"] > 0).mean(), "avg": gg["net"].mean()})
    Y = pd.DataFrame(rows)
    order = {"2022": 0, "2023": 1, "2024": 2, "2025": 3, "holdout": 4, "2022-25 total": 5, "holdout total": 6}
    Y = Y.sort_values(["year", "setup"], key=lambda s: s.map(order) if s.name == "year" else s)
    L += ["## Win % per trade", "", _table(Y, [("year", "period", str), ("setup", "setup", str), ("n", "trades", str),
                                                ("win", "win %", _pct), ("avg", "avg R after costs", _r)]), ""]
    weeks = {p: max((g["decision_time"].max() - g["decision_time"].min()).days / 7, 1)
             for p, g in (("research", t[~t["hold"]]), ("holdout", t[t["hold"]]))}
    L += [f"Trades per week: research {(~t['hold']).sum() / weeks['research']:.1f}, "
          f"holdout {t['hold'].sum() / weeks['holdout']:.1f}.", ""]
    sizing = {
        "flat 2%": {"A+ breakout (2:1)": 0.02, "breakout (2:1)": 0.02, "1D 4th-test bounce (3:1)": 0.02},
        "flat 3%": {"A+ breakout (2:1)": 0.03, "breakout (2:1)": 0.03, "1D 4th-test bounce (3:1)": 0.03},
        "tiered: A+ 4%, others 2%": {"A+ breakout (2:1)": 0.04, "breakout (2:1)": 0.02, "1D 4th-test bounce (3:1)": 0.02},
        "tiered: A+ 5%, breakout 3%, bounce 2%": {"A+ breakout (2:1)": 0.05, "breakout (2:1)": 0.03,
                                                  "1D 4th-test bounce (3:1)": 0.02},
    }
    rows = []
    for per, g in (("2022-25", t[~t["hold"]]), ("holdout", t[t["hold"]])):
        g = g.reset_index(drop=True)
        for name, rk in sizing.items():
            rows.append({"period": per, "sizing": name, **simulate(g, rk)})
    S = pd.DataFrame(rows)
    L += ["## Account (compounding, overlapping positions, leverage cap 5x)", "",
          _table(S, [("period", "period", str), ("sizing", "risk per trade", str),
                     ("final", "end equity", lambda v: f"{v:,.2f}x"), ("win_weeks", "winning weeks*", _pct),
                     ("win_months", "winning months", _pct), ("avg_week", "avg week", lambda v: f"{v:+.1%}"),
                     ("avg_month", "avg month", lambda v: f"{v:+.1%}"), ("weeks_20", "weeks >= +20%", _pct),
                     ("max_dd", "max drawdown", lambda v: f"{v:.0%}")]), "",
          "*weeks in which at least one trade closed.", ""]
    path = out_dir / "strategy_v2.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
