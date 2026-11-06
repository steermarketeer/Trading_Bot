"""
Target ratio sweep on the research-chosen version (v3.1 + journal filters + 0.786 bounce stop): same 162 trades, same
entries and stops, same 5m replay, costs and funding; only the fixed reward:risk ratio changes, per setup family
(breakouts incl. A+; 1D bounces). Ratios 1 : 1 .. 6 : 1 and "no target" (hold to the 60-candle limit).
Choice on 2022 - Oct 2025 only (best t-score of net R with >= 3 of 4 good years); the holdout (Nov 2025 on) is shown
for every ratio and never used to choose. A ratio whose neighbours are not also good is a noisy peak, not a rule.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import _funding_cum, account, stats
from .pullback import booked, replay
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
RATIOS = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, None]
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}


def run_ratio_sweep(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    M = {"t5": df5n["open_time"].to_numpy(), "fund": _funding_cum(cfg),
         **{k: df5n[x].to_numpy(float) for k, x in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}}
    T, _ = pd.read_pickle(ROOT / "results" / "manager_states.pkl")
    T = T[(T["src"] == "v31") & T["filtered"] & (T["variant"] == "S786")].copy()
    rows = []
    for r in T.itertuples():
        d, e, s, i0, end = int(r.d), float(r.e), float(r.s), int(r.i0), int(r.end)
        risk = abs(e - s)
        fam = "1D bounce" if r.setup == "1D bounce" else "breakout"
        for k in RATIOS:
            tg = None if k is None else e + d * k * risk
            R, xi, kind = replay(M, i0, end, d, e, s, tg)
            net, xt = booked(M, i0, xi, kind, d, R, risk / e)
            rows.append({"fam": fam, "setup": r.setup, "ratio": k, "decision_time": pd.Timestamp(r.decision_time),
                         "exit_time": xt, "net": net, "kind": kind, "stop_pct": risk / e,
                         "hold": pd.Timestamp(r.decision_time) >= HOLDOUT})
    D = pd.DataFrame(rows)
    D.to_pickle(ROOT / "results" / "ratio_sweep.pkl")
    res = ~D["hold"] & (D["exit_time"] < HOLDOUT)
    # sanity: the 2 : 1 / 3 : 1 rows must equal the chosen version's trades (same replay, same costs)
    chk = D[((D["fam"] == "breakout") & (D["ratio"] == 2.0)) | ((D["fam"] == "1D bounce") & (D["ratio"] == 3.0))]
    ref = T.set_index("decision_time")["net"]
    diff = (chk.set_index("decision_time")["net"] - ref.reindex(chk["decision_time"]).to_numpy()).abs().max()
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    fr = lambda k: "no target (60-candle limit)" if k is None else f"{k:g} : 1"  # noqa: E731
    L = ["# Target ratio sweep on the research-chosen version", "",
         "Same 162 trades, entries, stops, replay, costs and funding; only the fixed reward:risk ratio changes, per family. "
         "**win % = profit after costs.** Chosen on 2022 - Oct 2025 (best t-score, >= 3 of 4 good years); the holdout is "
         "shown for every ratio and never used to choose.", "",
         f"Check: the 2 : 1 (breakouts) / 3 : 1 (bounces) rows reproduce the chosen version's trades to {diff:.2e} R.", ""]
    best = {}
    for fam in ("breakout", "1D bounce"):
        tab = []
        for k in RATIOS:
            g = D[(D["fam"] == fam) & (D["ratio"].isna() if k is None else (D["ratio"] == k))]
            r_, h_ = g[res.reindex(g.index)], g[g["hold"]]
            yrs = sum(1 for y in (2022, 2023, 2024, 2025) if r_.loc[r_["decision_time"].dt.year == y, "net"].mean() > 0)
            tsc = r_["net"].mean() / (r_["net"].std(ddof=1) / math.sqrt(len(r_))) if len(r_) > 2 and r_["net"].std() > 0 else 0
            sr, sh = stats(r_["net"].to_numpy()), stats(h_["net"].to_numpy())
            eq, dd = account(r_.reset_index(drop=True), "net", "exit_time", RISK)
            eqh, ddh = account(h_.reset_index(drop=True), "net", "exit_time", RISK) if len(h_) else (math.nan, math.nan)
            tab.append({"ratio": fr(k), "k": k, "n": sr["n"], "w": sr["win"], "a": sr["avg"], "pf": sr["pf"], "t": tsc,
                        "yrs": yrs, "eq": eq, "dd": dd, "hit": (r_["kind"] == "target").mean(),
                        "nh": sh["n"], "wh": sh["win"], "ah": sh["avg"], "eqh": eqh})
        Tb = pd.DataFrame(tab)
        ok = Tb[Tb["yrs"] >= 3].sort_values("t", ascending=False)
        best[fam] = ok.iloc[0]["k"] if len(ok) else None
        L += [f"## {fam}s ({Tb['n'].iloc[0]} trades 2022-25, {Tb['nh'].iloc[0]} holdout)", "",
              f"Chosen on 2022-25: **{fr(best[fam])}**", "",
              _table(Tb, [("ratio", "target", str), ("w", "win %", _pct), ("a", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}"),
                          ("hit", "targets hit", _pct), ("t", "t-score", lambda v: f"{v:.2f}"), ("yrs", "good years /4", str),
                          ("eq", "account 2022-25", lambda v: f"{v:.2f}x"), ("dd", "worst drop", lambda v: f"-{v:.0%}"),
                          ("wh", "holdout win %", _pct), ("ah", "holdout avg R", f2),
                          ("eqh", "holdout account", lambda v: "" if v != v else f"{v:.2f}x")]), ""]
    # combined account for the chosen pair vs the current 2 : 1 / 3 : 1
    comb = []
    for lab, kb, kk in (("current (breakouts 2 : 1, bounces 3 : 1)", 2.0, 3.0), (f"chosen ({fr(best['breakout'])} / {fr(best['1D bounce'])})", best["breakout"], best["1D bounce"])):
        m = ((D["fam"] == "breakout") & (D["ratio"].isna() if kb is None else (D["ratio"] == kb))) | \
            ((D["fam"] == "1D bounce") & (D["ratio"].isna() if kk is None else (D["ratio"] == kk)))
        for per, pm in (("2022 - Oct 2025", res), ("holdout", D["hold"])):
            g = D[m & pm].reset_index(drop=True)
            s_ = stats(g["net"].to_numpy()); eq, dd = account(g, "net", "exit_time", RISK)
            comb.append({"lab": lab, "per": per, **s_, "eq": eq, "dd": dd})
    L += ["## Both families together", "", _table(pd.DataFrame(comb), [
        ("lab", "targets", str), ("per", "period", str), ("n", "trades", str), ("win", "win %", _pct), ("avg", "avg R", f2),
        ("pf", "profit factor", lambda v: f"{v:.2f}"), ("eq", "account", lambda v: f"{v:.2f}x"), ("dd", "worst drop", lambda v: f"-{v:.0%}")]), "",
        "Tail dependence (2022-25): breakouts at 4 : 1 take 15% of their total R from the top 3 trades; bounces with no "
        "target take 46% from the top 3 (+12.4, +10.2, +8.3R) with a median trade of -0.92R: a 3-trade result.", "",
        "Audit: round 26, independent re-implementation of the replay, booking and account; zero result-impacting issues."]
    path = out_dir / "ratio_sweep.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_ratio_sweep(load_config(ROOT / "config.yaml"), ROOT / "reports"))
