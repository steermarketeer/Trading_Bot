"""
Meta-labeling (Master Plan workstream 3): the v3.1 rules pick the trade; a model may only VETO it.

Trades: the 626 v3.1 trades (2022 - Oct 2026) with fixed targets (2:1 breakouts, 3:1 bounces), costs as in
bot/ml/targets.py (market entry, limit target, market stop, actual funding). Label = won after costs.
Inputs (fixed in advance, main rules first):
  M  main rules + liquidity map: structure 1h-1W, breaks / CHoCH, patterns, other main-rule events, zones,
     liquidity in risk / path, untaken pools ahead in R, weekly trend, volatility regime, stop size
  MI M + indicators (multi-timeframe indicator states, BTC trend, order flow, volume profile)
Models: L2 logistic regression (strong regularisation, C=0.05, standardised inputs) - ~100-500 training trades is
  too few for tree models. Variants: per setup (trained only on that setup's own trades) and pooled (all v3.1
  trades, with setup flags).
Veto rule (fixed in advance): veto a trade when its predicted chance is below the 25th percentile of the
  predictions on the training trades (i.e. remove roughly the worst quarter). 10% and 40% shown for reference.
Walk-forward: 2023, 2024, 2025 each scored by a model trained on trades decided >= 62 days before the year
  (2022 = training only); holdout scored by a model trained on research trades only.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..study.sr2_run import _pct, _table
from .targets import account, stats

HOLDOUT = pd.Timestamp("2025-11-01")
GAP = pd.Timedelta(days=62)
TEST_YEARS = [2023, 2024, 2025]
SETUPS = ["A+ breakout", "breakout", "1D bounce"]
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
VETO_SHARES = (0.10, 0.25, 0.40)
MAIN_VETO = 0.25


def main_cols(df):
    return [c for c in df.columns if c.startswith(("lq_", "st_", "brk_", "pat_", "ev_", "zone_", "liq_", "pool_", "x_"))
            or c in ("at_zone", "wtrend", "vol_regime", "is_long", "is_2h", "is_4h", "is_1D")]


def ind_cols(df):
    return [c for c in df.columns if c.startswith(("m_", "n_"))]


def _fit(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.linear_model import LogisticRegression
    Xtr = train[cols].to_numpy(float)
    med = np.nanmedian(Xtr, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    fill = lambda a: np.where(np.isfinite(a), a, med)  # noqa: E731  (training medians only)
    Xtr = fill(Xtr)
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd = np.where(sd > 0, sd, 1.0)
    m = LogisticRegression(C=0.05, max_iter=5000).fit((Xtr - mu) / sd, train["won"].to_numpy())
    p_tr = m.predict_proba((Xtr - mu) / sd)[:, 1]
    p_te = m.predict_proba((fill(test[cols].to_numpy(float)) - mu) / sd)[:, 1]
    return p_tr, p_te


def score(X: pd.DataFrame, cols: list[str], per_setup: bool) -> pd.DataFrame:
    """Out-of-sample predicted chance + veto flags for every scored trade."""
    out = []
    groups = [(s, X["setup"] == s) for s in SETUPS] if per_setup else [("all", pd.Series(True, index=X.index))]
    for _, gm in groups:
        g = X[gm]
        periods = [(str(y), pd.Timestamp(f"{y}-01-01"), (g["decision_time"] >= pd.Timestamp(f"{y}-01-01")) &
                    (g["decision_time"] < pd.Timestamp(f"{y + 1}-01-01")) & ~g["hold"]) for y in TEST_YEARS]
        periods.append(("holdout", HOLDOUT, g["hold"]))
        for per, start, tm in periods:
            train, test = g[(g["decision_time"] < start - GAP) & ~g["hold"]], g[tm]
            if len(test) == 0 or len(train) < 30 or train["won"].nunique() < 2:
                continue
            p_tr, p_te = _fit(train, test, cols)
            r = pd.DataFrame({"p": p_te, "period": per}, index=test.index)
            for v in VETO_SHARES:
                r[f"keep_{int(v * 100)}"] = p_te >= np.quantile(p_tr, v)
            out.append(r)
    return pd.concat(out)


def run_meta(cfg: Config, out_dir: Path) -> Path:
    X = pd.read_pickle(ROOT / "results" / "ml_targets.pkl")
    X.attrs = {}
    X["won"] = (X["net_fixed"] > 0).astype(int)
    M, I = main_cols(X), ind_cols(X)
    pooled_flags = ["is_A+", "is_bounce"]
    X["is_A+"] = (X["setup"] == "A+ breakout").astype(int)
    X["is_bounce"] = (X["setup"] == "1D bounce").astype(int)
    variants = {
        "per setup, main rules + liquidity": score(X, M, True),
        "per setup, + indicators": score(X, M + I, True),
        "pooled, main rules + liquidity": score(X, M + pooled_flags, False),
        "pooled, + indicators": score(X, M + I + pooled_flags, False),
    }
    scored = X.index.isin(variants["per setup, main rules + liquidity"].index)
    S = X[scored].copy()
    weeks_r = (pd.Timestamp("2025-11-01") - pd.Timestamp("2023-01-01")).days / 7
    weeks_h = (S["decision_time"].max() - HOLDOUT).days / 7
    L = ["# Meta-labeling: the main rules pick the trade, the model can only veto it", "",
         f"v3.1 trades with fixed targets (2:1 breakouts, 3:1 bounces); scored out-of-sample: 2023-2025 "
         f"walk-forward ({int((~S['hold']).sum())} trades) and the holdout ({int(S['hold'].sum())} trades). "
         "**win % = profit after all costs.** Veto rule fixed in advance: remove trades the model rates below the "
         "worst 25% of its training trades.", ""]
    rows = []
    for per, pm, wk in (("research 2023-2025", ~S["hold"], weeks_r), ("holdout", S["hold"], weeks_h)):
        base = S[pm]
        s = stats(base["net_fixed"].to_numpy())
        eq, mdd = account(base, "net_fixed", "exit_fixed", RISK)
        rows.append({"period": per, "rule": "no veto (v3.1)", **s, "pw": s["n"] / wk, "eq": eq, "mdd": mdd})
        for name, V in variants.items():
            keep = V.loc[base.index.intersection(V.index), f"keep_{int(MAIN_VETO * 100)}"]
            g = base.loc[keep[keep].index]
            s = stats(g["net_fixed"].to_numpy())
            eq, mdd = account(g, "net_fixed", "exit_fixed", RISK)
            rows.append({"period": per, "rule": f"veto: {name}", **s, "pw": s["n"] / wk, "eq": eq, "mdd": mdd})
    L += ["## Win % with and without the veto (25% rule)", "", _table(pd.DataFrame(rows), [
        ("period", "period", str), ("rule", "rule", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
        ("win", "win %", _pct), ("avg", "avg R", lambda v: f"{v:+.2f}"), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("eq", "account", lambda v: f"{v:.2f}x"), ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    rows = []
    for per, pm in (("research", ~S["hold"]), ("holdout", S["hold"])):
        for setup in SETUPS:
            base = S[pm & (S["setup"] == setup)]
            r = {"period": per, "setup": setup, "n": len(base), "win": stats(base["net_fixed"].to_numpy())["win"],
                 "avg": stats(base["net_fixed"].to_numpy())["avg"]}
            for key, name in (("ps", "per setup, main rules + liquidity"), ("pi", "per setup, + indicators")):
                V = variants[name]
                keep = V.loc[base.index.intersection(V.index), "keep_25"]
                kept, vet = base.loc[keep[keep].index], base.loc[keep[~keep].index]
                r[f"n_{key}"], r[f"w_{key}"] = len(kept), stats(kept["net_fixed"].to_numpy())["win"]
                r[f"a_{key}"], r[f"wv_{key}"] = stats(kept["net_fixed"].to_numpy())["avg"], stats(vet["net_fixed"].to_numpy())["win"]
            rows.append(r)
    L += ["## Per setup (model trained only on that setup's own trades)", "", _table(pd.DataFrame(rows), [
        ("period", "period", str), ("setup", "setup", str), ("n", "trades", str), ("win", "win % no veto", _pct),
        ("avg", "avg R no veto", lambda v: f"{v:+.2f}"), ("n_ps", "kept (main rules)", str),
        ("w_ps", "win % kept", _pct), ("a_ps", "avg R kept", lambda v: f"{v:+.2f}"), ("wv_ps", "win % vetoed", _pct),
        ("n_pi", "kept (+ indicators)", str), ("w_pi", "win % kept", _pct), ("wv_pi", "win % vetoed", _pct)]), ""]
    rows = []
    for name, V in variants.items():
        for per, pm in (("research", ~S["hold"]), ("holdout", S["hold"])):
            base = S[pm]
            r = {"rule": name, "period": per}
            for v in VETO_SHARES:
                keep = V.loc[base.index.intersection(V.index), f"keep_{int(v * 100)}"]
                g = base.loc[keep[keep].index]
                st = stats(g["net_fixed"].to_numpy())
                r[f"n{int(v * 100)}"], r[f"w{int(v * 100)}"], r[f"a{int(v * 100)}"] = st["n"], st["win"], st["avg"]
            rows.append(r)
    L += ["## How strict should the veto be? (reference only - 25% was fixed in advance)", "",
          _table(pd.DataFrame(rows), [("rule", "model", str), ("period", "period", str),
                                      ("n10", "trades (veto 10%)", str), ("w10", "win %", _pct), ("a10", "avg R", lambda v: f"{v:+.2f}"),
                                      ("n25", "trades (25%)", str), ("w25", "win %", _pct), ("a25", "avg R", lambda v: f"{v:+.2f}"),
                                      ("n40", "trades (40%)", str), ("w40", "win %", _pct), ("a40", "avg R", lambda v: f"{v:+.2f}")]), ""]
    allp = pd.concat([v.assign(model=k) for k, v in variants.items()])
    allp.join(S[["setup", "net_fixed", "won"]]).to_pickle(ROOT / "results" / "meta_scored.pkl")
    path = out_dir / "meta_labeling.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
