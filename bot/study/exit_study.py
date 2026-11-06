"""
Exit study on the chosen version (v3.1 + journal filters + 0.786 bounce stop; targets 2 : 1 breakouts, 5 : 1 bounces):
same 162 trades, same entries and initial stops, same 5m replay, costs and funding. Only the exit changes.

Exits (each alone; the fixed target stays as a ceiling unless the name ends in "-NT" = no target):
  fixed      stop / target / 60-candle time limit (the reference)
  BE1 BE1.5 BE2   break-even: once a 5m candle's extreme reaches +kR, the stop moves to the entry from the next candle
  X4H        exit at the next open if the FIRST 4h close after entry is back beyond the entry price
  CH2 CH3    Chandelier: after +1R, at each 4h close the stop rises to (highest high since entry - k x ATR_1D); never loosens
  SW         structure: after +1R, at each 4h close the stop rises to the last confirmed 4h swing low * (1 - 0.1%)
  PT         partial: half the position closes at +2R (limit), the stop of the rest moves to the entry, the rest runs
  CH3-NT SW-NT    the trailing stops with no fixed target (the trade ends only on the trail, the stop or the time limit)
  SWP1D SWP4H   sweep of the trade's running high (trader's concept): after +1R, a daily (4h) candle that makes a new high
             above the running high of the closed candles since entry and CLOSES below that previous high -> exit at the
             next 5m open. SWP1D0 = the same from the entry, without waiting for +1R.
  SKIP3      an ENTRY filter for comparison: skip trades with all three liquidity reasons (ceiling before the target,
             against the daily EMA 200, liquidity just beyond the stop; results/failure_study.pkl)
Stops are price orders: a 5m candle that opens through the stop fills at the open, else at the stop. Trail updates use
only closed 4h candles and are applied from the next 5m candle. Choice on 2022 - Oct 2025 (best t-score of net R,
>= 3 of 4 good years); the holdout (Nov 2025 on) is shown once. **win % = profit after costs.**
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..live.v3 import TARGET
from ..ml.targets import C_LMT, C_MKT, LIMIT_BUFFER, _funding_cum, account, stats
from .defs import TF
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
MODES = ["fixed", "BE1", "BE1.5", "BE2", "X4H", "CH2", "CH3", "SW", "PT", "CH3-NT", "SW-NT", "SWP1D", "SWP1D0", "SWP4H"]


def run_exit(M, t4, d1, i0, end, d, e, s0, tg, mode):
    """Replay one trade on 5m candles with the chosen exit. Returns (R, exit index, kind, costs in R-free form:
    list of (fraction, kind) legs)."""
    O, H, L, C, t5 = M["O"], M["H"], M["L"], M["C"], M["t5"]
    o, h, l, c = (O, H, L, C) if d > 0 else (-O, -L, -H, -C)
    e_, s_ = d * e, d * s0
    risk = e_ - s_
    tg_ = None if (tg is None or mode.endswith("-NT")) else d * tg
    buf = LIMIT_BUFFER * abs(e)
    H4 = t4.h if d > 0 else -t4.l
    C4 = t4.c if d > 0 else -t4.c
    SL4 = t4.sl if d > 0 else [(i, -p, cf) for i, p, cf in t4.sh]        # oriented swing lows (confirm index)
    be_k = {"BE1": 1.0, "BE1.5": 1.5, "BE2": 2.0}.get(mode)
    ch_k = {"CH2": 2.0, "CH3": 3.0, "CH3-NT": 3.0}.get(mode)
    HD, CD = (d1.h, d1.c) if d > 0 else (-d1.l, -d1.c)                  # oriented daily high / close
    run4 = -np.inf                                                      # running high of the closed 4h candles since entry
    rund = -np.inf                                                      # running high of the closed daily candles since entry
    stop = s_
    armed = False
    hh = -np.inf
    j4 = int(np.searchsorted(t4.ct, t5[i0], side="right"))             # first 4h candle closing after entry
    first4 = True
    legs = []                                                           # (fraction, R, exit index, kind)
    frac = 1.0
    pending_stop = None
    def skind(st):
        return "stop" if st < e_ - 1e-9 else ("break-even" if st < e_ + 1e-9 else "trail")

    for i in range(i0, end):
        if pending_stop is not None:                                    # trail decided at the previous close
            stop = max(stop, pending_stop); pending_stop = None
        if i > i0 and o[i] <= stop:
            legs.append((frac, (o[i] - e_) / risk, i, skind(stop))); frac = 0; break
        if l[i] <= stop:
            legs.append((frac, (stop - e_) / risk, i, skind(stop))); frac = 0; break
        if mode == "PT" and frac == 1.0 and h[i] >= e_ + 2 * risk + buf:
            legs.append((0.5, 2.0, i, "target")); frac = 0.5
            stop = max(stop, e_)
        if tg_ is not None and h[i] >= tg_ + buf:
            legs.append((frac, (tg_ - e_) / risk, i, "target")); frac = 0; break
        hh = max(hh, h[i])
        if not armed and (hh - e_) >= risk:
            armed = True
        if be_k is not None and (hh - e_) >= be_k * risk:
            pending_stop = max(pending_stop or -np.inf, e_)
        # a 4h candle closed at the end of this 5m candle?
        while j4 < t4.n and t4.ct[j4] <= t5[i] + np.timedelta64(5, "m"):
            if mode == "X4H" and first4 and C4[j4] < e_ and i + 1 < end:
                legs.append((frac, (o[i + 1] - e_) / risk, i + 1, "4h against")); frac = 0
            first4 = False
            if armed and ch_k is not None and np.isfinite(d1.a[d1.closed_before(t4.ct[j4]) - 1]):
                atr_d = d1.a[d1.closed_before(t4.ct[j4]) - 1]
                pending_stop = max(pending_stop or -np.inf, hh - ch_k * atr_d)
            if mode.startswith("SWP") and i + 1 < end:
                go = armed or mode == "SWP1D0"
                if mode == "SWP4H":
                    if go and run4 > -np.inf and H4[j4] > run4 and C4[j4] < run4:
                        legs.append((frac, (o[i + 1] - e_) / risk, i + 1, "sweep")); frac = 0
                    run4 = max(run4, H4[j4])
                elif pd.Timestamp(t4.ct[j4]).hour == 0:                 # a daily candle closed too
                    kd = d1.closed_before(t4.ct[j4]) - 1
                    if go and rund > -np.inf and HD[kd] > rund and CD[kd] < rund:
                        legs.append((frac, (o[i + 1] - e_) / risk, i + 1, "sweep")); frac = 0
                    rund = max(rund, HD[kd])
            if armed and mode in ("SW", "SW-NT"):
                lows = [p for ii, p, cf in SL4 if cf <= j4 and ii >= j4 - 60]
                if lows:
                    pending_stop = max(pending_stop or -np.inf, lows[-1] * (1 - 0.001) if d > 0 else lows[-1] - 0.001 * abs(lows[-1]))
            j4 += 1
        if frac == 0:
            break
    if frac > 0:
        legs.append((frac, (c[end - 1] - e_) / risk, end - 1, "time"))
    return legs


def book(M, i0, legs, d, risk_pct):
    ft, fc = M["fund"]
    t5 = M["t5"]
    net = 0.0
    for frac, R, xi, kind in legs:
        x_t = t5[xi] + (np.timedelta64(0, "m") if kind in ("4h against", "sweep") else np.timedelta64(5, "m"))
        a_ = np.searchsorted(ft, t5[i0], side="right"); b_ = np.searchsorted(ft, x_t, side="left")
        fund = (fc[b_] - fc[a_]) * d if b_ > a_ else 0.0
        cost = C_MKT + (C_LMT if kind == "target" else C_MKT) + fund
        net += frac * (R - cost / risk_pct)
    last = max(legs, key=lambda x: x[2])
    return net, pd.Timestamp(t5[last[2]]) + (pd.Timedelta(0) if last[3] in ("4h against", "sweep") else pd.Timedelta(minutes=5)), \
        "+".join(sorted({k for _, _, _, k in legs}))


def run_exit_study(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    M = {"t5": df5n["open_time"].to_numpy(), "fund": _funding_cum(cfg),
         **{k: df5n[x].to_numpy(float) for k, x in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}}
    t4, d1 = TF(resample(df5u, "4h")), TF(resample(df5u, "1D"))
    T = pd.read_pickle(ROOT / "results" / "manager_states.pkl")[0]
    T = T[(T["src"] == "v31") & T["filtered"] & (T["variant"] == "S786")].copy()
    FS = pd.read_pickle(ROOT / "results" / "failure_study.pkl").set_index("entry_time")
    rows = []
    for r in T.itertuples():
        d, e, s, i0, end = int(r.d), float(r.e), float(r.s), int(r.i0), int(r.end)
        risk = abs(e - s)
        tg = e + d * TARGET[r.setup] * risk
        f = FS.loc[pd.Timestamp(r.entry_time)]
        skip3 = bool(f["ceiling"] and f["daily against"] and f["liq at stop"])
        for mode in MODES:
            legs = run_exit(M, t4, d1, i0, end, d, e, s, tg, mode)
            net, xt, kind = book(M, i0, legs, d, risk / e)
            rows.append({"mode": mode, "setup": r.setup, "decision_time": pd.Timestamp(r.decision_time), "exit_time": xt,
                         "net": net, "kind": kind, "stop_pct": risk / e, "skip3": skip3,
                         "hold": pd.Timestamp(r.decision_time) >= HOLDOUT})
        print(len(rows) // len(MODES), flush=True) if (len(rows) // len(MODES)) % 40 == 0 else None
    D = pd.DataFrame(rows)
    D.to_pickle(ROOT / "results" / "exit_study.pkl")
    res = ~D["hold"] & (D["exit_time"] < HOLDOUT)
    FX = pd.read_pickle(ROOT / "results" / "fixes.pkl")
    FX = FX[(FX["entry"] == "now") & (FX["exit"] == "none") & (FX["fib"] == "S786")]
    ref = FX.set_index(pd.to_datetime(FX["decision_time"]))["net"]
    fx = D[D["mode"] == "fixed"].set_index("decision_time")["net"]
    diff = float((fx - ref.reindex(fx.index)).abs().max())
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    names = {"fixed": "fixed target (as now)", "BE1": "break-even after +1R", "BE1.5": "break-even after +1.5R",
             "BE2": "break-even after +2R", "X4H": "exit on the first 4h close against the entry",
             "CH2": "Chandelier 2 ATR (after +1R)", "CH3": "Chandelier 3 ATR (after +1R)",
             "SW": "trail below the last 4h swing low (after +1R)", "PT": "half at +2R, rest to break-even and run",
             "CH3-NT": "Chandelier 3 ATR, no target", "SW-NT": "4h swing trail, no target",
             "SWP1D": "exit after a daily sweep of the trade's high (after +1R)", "SWP1D0": "exit after a daily sweep of the trade's high (from entry)",
             "SWP4H": "exit after a 4h sweep of the trade's high (after +1R)",
             "SKIP3": "entry filter: skip all three liquidity reasons"}
    L = ["# Exit study on the chosen version", "",
         "Same 162 trades, entries, initial stops, replay, costs and funding; only the exit changes. **win % = profit after "
         "costs.** Chosen on 2022 - Oct 2025 (best t-score, >= 3 of 4 good years); the holdout is shown once.", "",
         f"Check: the 'fixed' rows reproduce the chosen version's trades to {diff:.2e} R.", ""]
    for scope, fam in (("all trades", None), ("breakouts", "breakout"), ("1D bounces", "1D bounce")):
        tab = []
        for mode in MODES + ["SKIP3"]:
            if mode == "SKIP3":
                g = D[(D["mode"] == "fixed") & ~D["skip3"]]
            else:
                g = D[D["mode"] == mode]
            if fam == "breakout":
                g = g[g["setup"] != "1D bounce"]
            elif fam:
                g = g[g["setup"] == fam]
            r_, h_ = g[res.reindex(g.index)], g[g["hold"]]
            yrs = sum(1 for y in (2022, 2023, 2024, 2025) if r_.loc[r_["decision_time"].dt.year == y, "net"].mean() > 0)
            tsc = r_["net"].mean() / (r_["net"].std(ddof=1) / math.sqrt(len(r_))) if len(r_) > 2 and r_["net"].std() > 0 else 0
            sr, sh = stats(r_["net"].to_numpy()), stats(h_["net"].to_numpy())
            eq, dd = account(r_.reset_index(drop=True), "net", "exit_time", RISK) if len(r_) else (math.nan, math.nan)
            eqh, ddh = account(h_.reset_index(drop=True), "net", "exit_time", RISK) if len(h_) else (math.nan, math.nan)
            days = (r_["exit_time"] - r_["decision_time"]).dt.total_seconds().mean() / 86400 if len(r_) else math.nan
            tab.append({"mode": names[mode], "n": sr["n"], "w": sr["win"], "a": sr["avg"], "pf": sr["pf"], "t": tsc, "yrs": yrs,
                        "eq": eq, "dd": dd, "days": days, "nh": sh["n"], "wh": sh["win"], "ah": sh["avg"], "eqh": eqh, "ddh": ddh})
        Tb = pd.DataFrame(tab)
        ok = Tb[(Tb["yrs"] >= 3)].sort_values("t", ascending=False)
        L += [f"## {scope}", "", f"Chosen on 2022-25 (t-score): **{ok.iloc[0]['mode'] if len(ok) else '-'}**; most profit on 2022-25: "
              f"**{Tb.sort_values('eq', ascending=False).iloc[0]['mode']}**", "",
              _table(Tb, [("mode", "exit", str), ("n", "trades", str), ("w", "win %", _pct), ("a", "avg R", f2),
                          ("pf", "profit factor", lambda v: f"{v:.2f}"), ("t", "t-score", lambda v: f"{v:.2f}"), ("yrs", "good years /4", str),
                          ("eq", "account 2022-25", lambda v: f"{v:.2f}x"), ("dd", "worst drop", lambda v: f"-{v:.0%}"),
                          ("days", "avg hold (days)", lambda v: f"{v:.1f}"), ("wh", "holdout win %", _pct), ("ah", "holdout avg R", f2),
                          ("eqh", "holdout account", lambda v: "" if v != v else f"{v:.2f}x"), ("ddh", "holdout drop", lambda v: "" if v != v else f"-{v:.0%}")]), ""]
    L += ["## Reading", "",
          "- Breakouts (2 : 1): nothing beats the fixed target by more than noise; break-even after +2R and the partial "
          "exit are the same trade as the fixed target (2R = the target). The trails after +1R add +0.01 .. +0.02R.",
          "- 1D bounces (5 : 1): **break-even after +2R** is the only exit that improves both the profit and the t-score on "
          "2022-25 (+1.19R vs +1.09R, 2.86x vs 2.59x, drop -14% vs -16%) without hurting the holdout (+2.07R vs +2.08R). "
          "It changes 5 research trades (losers that had run 2R and came back to the stop, now ~0R) and 1 holdout trade. "
          "Five trades is a logical, small edge, not a proof.",
          "- Every early exit on a 4h signal against the trade (first 4h close against, Chandelier, swing trail) wins more "
          "often but earns less per trade: the trades it saves are smaller than the winners it cuts.",
          "- No target + trailing stop loses in both periods (fewer, bigger winners do not pay for the many trail stops).",
          "- Exiting after a sweep of the trade's running high (the 22 Nov 2024 reading; daily or 4h, with or without waiting "
          "for +1R) earns +0.48 .. +0.62R vs +0.88R: the sweep of a high continues up about 3 times in 4 (reports/sideways_test.md), "
          "so it is not an exit.",
          "- Skipping the 'all three liquidity reasons' trades raises the average R but lowers the account (fewer trades) "
          "and deepens the drawdown; it is a post-hoc hypothesis and stays out.", "",
          "Audit: rounds 28 and 29a, independent re-implementation of the replay for all 162 trades x 14 exits, the booking, every "
          "table line and the SKIP3 flags; zero result-impacting issues."]
    path = out_dir / "exit_study.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_exit_study(load_config(ROOT / "config.yaml"), ROOT / "reports"))
