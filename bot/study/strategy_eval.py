"""
(1) 2:1 breakout fixes from the failure analysis, (2) combined strategy with the 1D 4th-test bounce.

Breakouts: certainty >= 7 on 2h / 4h / 1D (scored out-of-sample). Fixes (thresholds fixed in advance; the volatility
cut-off is the 20th percentile of research trades of the same timeframe):
  F1 stop distance >= 0.6% of price (about 3x the round-trip costs)
  F2 volatility: ATR% not in the bottom 20% for that timeframe
  F3 daily trend not against the trade (1D close vs EMA50)
  F4 real breakout: entry at least 0.25 ATR beyond the broken level
1D level bounce: zone tested >= 4 times, bounce confirmed by the next candle, target 3:1.
All trades replayed on 5m candles (stop before target inside a 5m candle), costs = market orders.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .level_tests import tests_for
from .smalltf import COST_TAKER, account
from .sr2_run import _pct, _r, _table

FIVE = pd.Timedelta(minutes=5)
HOLDOUT = pd.Timestamp("2025-11-01")
MAX_TF_BARS = 60


def _first(m, s=0):
    if s >= len(m):
        return -1
    i = np.flatnonzero(m[s:])
    return int(i[0]) + s if len(i) else -1


def replay_one(O, H, Lw, C, t5, entry_time, tf, d, risk, targets):
    """Returns {name: (R before costs, exit time)} for fixed targets + 'half@1R+2R'; None if data missing."""
    bpt = int(pd.Timedelta(tf) / FIVE)
    ts = pd.Timestamp(entry_time).to_datetime64()
    st = int(np.searchsorted(t5, ts))
    if st >= len(t5) or t5[st] != ts or st + MAX_TF_BARS * bpt > len(O):
        return None
    en = st + MAX_TF_BARS * bpt
    o, h, l, c = O[st:en], H[st:en], Lw[st:en], C[st:en]
    if d < 0:
        o, h, l, c = -o, -l, -h, -c
    e = o[0]
    s0 = e - risk
    i_s = _first(l <= s0)
    sf = lambda i, lv: min(o[i], lv) if i > 0 else lv  # noqa: E731
    tf_ = lambda i, lv: max(o[i], lv) if i > 0 else lv  # noqa: E731
    out = {}
    for T in targets:
        tg = e + T * risk
        i_t = _first(h >= tg)
        if i_s >= 0 and (i_t < 0 or i_s <= i_t):
            out[f"{T:g}:1"] = ((sf(i_s, s0) - e) / risk, i_s)
        elif i_t >= 0:
            out[f"{T:g}:1"] = ((tf_(i_t, tg) - e) / risk, i_t)
        else:
            out[f"{T:g}:1"] = ((c[-1] - e) / risk, len(o) - 1)
    i_1 = _first(h >= e + risk)
    if i_1 < 0 or (i_s >= 0 and i_s <= i_1):
        out["half@1R+2R"] = out.get("1:1") or ((sf(i_s, s0) - e) / risk if i_s >= 0 else (c[-1] - e) / risk, i_s if i_s >= 0 else len(o) - 1)
    else:
        tg = e + 2 * risk
        i_be, i_t = _first(l <= e, i_1 + 1), _first(h >= tg, i_1 + 1)
        if i_be >= 0 and (i_t < 0 or i_be <= i_t):
            out["half@1R+2R"] = (0.5 + 0.5 * (sf(i_be, e) - e) / risk, i_be)
        elif i_t >= 0:
            out["half@1R+2R"] = (0.5 + 0.5 * (tf_(i_t, tg) - e) / risk, i_t)
        else:
            out["half@1R+2R"] = (0.5 + 0.5 * (c[-1] - e) / risk, len(o) - 1)
    t0 = pd.Timestamp(entry_time)
    return {k: (v[0], t0 + FIVE * (v[1] + 1)) for k, v in out.items()}, abs(e)


def build_rows(trades: pd.DataFrame, df5: pd.DataFrame, targets, keep: list[str]) -> pd.DataFrame:
    t5 = df5["open_time"].to_numpy()
    O, H, Lw, C = (df5[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    rows = []
    for _, t in trades.iterrows():
        r = replay_one(O, H, Lw, C, t5, t["entry_time"], t["tf"], int(t["direction"]), float(t["risk"]), targets)
        if r is None:
            continue
        ex, px = r
        row = {k: t[k] for k in keep}
        row["stop_pct"] = float(t["risk"]) / px
        row["decision_time"] = pd.Timestamp(t["entry_time"])
        for k, (rv, xt) in ex.items():
            row[f"R_{k}"], row[f"exit_{k}"] = rv, xt
        rows.append(row)
    return pd.DataFrame(rows)


def wr(x: pd.DataFrame, rule: str) -> dict:
    if not len(x):
        return {"n": 0, "win": math.nan, "avg": math.nan}
    net = x[f"R_{rule}"] - COST_TAKER / x["stop_pct"]
    return {"n": len(x), "win": (net > 0).mean(), "avg": net.mean()}


def load_breakouts() -> pd.DataFrame:
    parts = []
    for f in ("scored_breakout_2h.pkl", "scored_breakout.pkl"):
        d = pd.read_pickle(ROOT / "results" / f)
        d.attrs = {}
        parts.append(d)
    b = pd.concat(parts, ignore_index=True)
    b = b[(b["certainty"] >= 7) & b["tf"].isin(["2h", "4h", "1D"])].copy()
    b["entry_time"] = pd.to_datetime(b["decision_time"], utc=True).dt.tz_convert(None)
    b["hold"] = b["entry_time"] >= HOLDOUT
    b["break_dist"] = (b["entry"] - b["ref_level"]) * b["direction"] / b["atr"]
    b["atr_pct"] = b["atr"] / b["entry"]
    return b


def run_strategy_eval(cfg: Config, out_dir: Path, risk_frac: float = 0.03) -> Path:
    df5, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5["open_time"] = pd.to_datetime(df5["open_time"], utc=True).dt.tz_convert(None)
    b = load_breakouts()
    keep = ["tf", "event", "direction", "hold", "break_dist", "atr_pct", "m_1D_trend", "certainty"]
    br = build_rows(b, df5, (1.0, 2.0, 3.0), keep)
    # volatility cut-off per timeframe from RESEARCH trades only
    q = br[~br["hold"]].groupby("tf")["atr_pct"].quantile(0.2)
    br["F1"] = br["stop_pct"] >= 0.006
    br["F2"] = br["atr_pct"] >= br["tf"].map(q)
    br["F3"] = br["m_1D_trend"] >= 0
    br["F4"] = br["break_dist"] >= 0.25
    L = ["# 2:1 fixes and the combined strategy", "",
         "All numbers after market-order costs, every trade replayed on 5-minute candles. **win %** = trades that "
         "ended in profit. Research = up to Oct 2025 (scored out-of-sample, 2022-25); holdout = Nov 2025 onward.", "",
         "## 1. Fixing 2:1 breakouts (certainty >= 7, 2h / 4h / 1D)", "",
         "F1 = stop at least 0.6% away · F2 = not the quietest 20% of markets · F3 = daily trend not against · "
         "F4 = entry at least 0.25 ATR beyond the broken level.", ""]
    variants = [("no fix", np.ones(len(br), bool)), ("F1 stop >= 0.6%", br["F1"]), ("F2 volatility", br["F2"]),
                ("F3 daily trend", br["F3"]), ("F4 real breakout", br["F4"]),
                ("F1 + F2", br["F1"] & br["F2"]), ("F1 + F3", br["F1"] & br["F3"]),
                ("F1 + F2 + F3", br["F1"] & br["F2"] & br["F3"]),
                ("all four", br["F1"] & br["F2"] & br["F3"] & br["F4"])]
    rows = []
    for name, m in variants:
        m = np.asarray(m, bool)
        for per, pm in (("research", ~br["hold"].to_numpy()), ("holdout", br["hold"].to_numpy())):
            g = br[m & pm]
            a2, ah = wr(g, "2:1"), wr(g, "half@1R+2R")
            weeks = max((g["decision_time"].max() - g["decision_time"].min()).days / 7, 1) if len(g) > 1 else math.nan
            rows.append({"fix": name, "period": per, "n": a2["n"], "pw": a2["n"] / weeks if weeks == weeks else math.nan,
                         "w2": a2["win"], "a2": a2["avg"], "wh": ah["win"], "ah": ah["avg"]})
    T = pd.DataFrame(rows)
    L += [_table(T, [("fix", "fix", str), ("period", "period", str), ("n", "trades", str),
                     ("pw", "trades/wk", lambda v: "-" if pd.isna(v) else f"{v:.1f}"),
                     ("w2", "win % at 2:1", _pct), ("a2", "avg R 2:1", _r),
                     ("wh", "win % half@1:1+2:1", _pct), ("ah", "avg R half", _r)]), ""]
    # choose the fix set on RESEARCH avg R at 2:1 (min 150 research trades)
    cand = T[(T["period"] == "research") & (T["n"] >= 150)].sort_values("a2", ascending=False)
    best = cand.iloc[0]["fix"]
    L += [f"**Chosen on research (best avg R at 2:1 with >= 150 trades): {best}.**", ""]
    bm = np.asarray(dict(variants)[best], bool)

    # ---- 1D level bounce at 4th+ test
    lt = tests_for(df5.assign(open_time=df5["open_time"].dt.tz_localize("UTC")), "1D")
    lt = lt[lt.get("traded", pd.Series(False, index=lt.index)).fillna(False).astype(bool) & (lt["test_n"] >= 4)].copy()
    lt["tf"] = "1D"
    lt["entry_time"] = (pd.to_datetime(lt["time"], utc=True) + pd.Timedelta(days=1)).dt.tz_convert(None)
    lt["hold"] = lt["entry_time"] >= HOLDOUT
    lt["event"] = "level_4th_test"
    lt["certainty"] = np.nan
    lb = build_rows(lt, df5, (1.0, 2.0, 3.0), ["tf", "event", "direction", "hold", "certainty"])
    lb = lb[(lb["decision_time"] < HOLDOUT - pd.Timedelta(days=62)) | lb["hold"]]
    rows = []
    for per, g in (("research", lb[~lb["hold"]]), ("holdout", lb[lb["hold"]])):
        row = {"period": per}
        for rule in ("1:1", "2:1", "3:1"):
            a = wr(g, rule)
            row["n"], row[f"w{rule}"], row[f"a{rule}"] = a["n"], a["win"], a["avg"]
        rows.append(row)
    L += ["## 2. 1D level tested 4+ times: bounce trade", "",
          _table(pd.DataFrame(rows), [("period", "period", str), ("n", "trades", str),
                                      ("w1:1", "win % 1:1", _pct), ("w2:1", "win % 2:1", _pct), ("w3:1", "win % 3:1", _pct),
                                      ("a1:1", "avg R 1:1", _r), ("a2:1", "avg R 2:1", _r), ("a3:1", "avg R 3:1", _r)]), ""]

    # ---- combined strategy
    brk = br[bm].copy()
    brk["setup"] = "breakout (2:1)"
    brk["R_use"], brk["exit_use"] = brk["R_2:1"], brk["exit_2:1"]
    lvl = lb.copy()
    lvl["setup"] = "1D 4th-test bounce (3:1)"
    lvl["R_use"], lvl["exit_use"] = lvl["R_3:1"], lvl["exit_3:1"]
    comb = pd.concat([brk, lvl], ignore_index=True).sort_values("decision_time").reset_index(drop=True)
    comb["net"] = comb["R_use"] - COST_TAKER / comb["stop_pct"]
    comb["year"] = np.where(comb["hold"], "holdout", comb["decision_time"].dt.year.astype(str))
    comb = comb[comb["decision_time"] >= pd.Timestamp("2022-01-01")]
    rows = []
    for (yr, setup), g in comb.groupby(["year", "setup"]):
        rows.append({"year": yr, "setup": setup, "n": len(g), "win": (g["net"] > 0).mean(), "avg": g["net"].mean()})
    for yr, g in comb.groupby("year"):
        rows.append({"year": yr, "setup": "COMBINED", "n": len(g), "win": (g["net"] > 0).mean(), "avg": g["net"].mean()})
    Y = pd.DataFrame(rows).sort_values(["year", "setup"])
    L += ["## 3. Combined strategy: fixed 2:1 breakouts + 1D 4th-test bounces (3:1)", "",
          "### Win % per trade, year by year", "",
          _table(Y, [("year", "year", str), ("setup", "setup", str), ("n", "trades", str), ("win", "win %", _pct),
                     ("avg", "avg R after costs", _r)]), ""]
    # account simulation (uses the account() helper: needs R_<rule>, exit_<rule>)
    acc_rows = []
    for per, g in (("2022-25", comb[~comb["hold"]]), ("holdout", comb[comb["hold"]])):
        g = g.reset_index(drop=True).assign(**{"R_use": g["R_use"].to_numpy(), "exit_use": g["exit_use"].to_numpy()})
        for rf in (0.02, 0.03, 0.05):
            a = account(g, "use", COST_TAKER, rf)
            wk = _weekly(g, rf)
            acc_rows.append({"period": per, "risk": f"{rf:.0%}", "n": len(g), **a, **wk})
    A = pd.DataFrame(acc_rows)
    L += ["### Account (compounding, positions can overlap, leverage cap 5x)", "",
          _table(A, [("period", "period", str), ("risk", "risk / trade", str), ("n", "trades", str),
                     ("final", "end equity", lambda v: f"{v:,.2f}x"), ("winning_weeks", "winning weeks", _pct),
                     ("median_week", "median week", lambda v: f"{v:+.1%}"), ("avg_week", "avg week", lambda v: f"{v:+.1%}"),
                     ("weeks_20", "weeks >= +20%", _pct), ("max_dd", "max drawdown", lambda v: f"{v:.0%}")]), ""]
    comb.to_pickle(ROOT / "results" / "combined_strategy_trades.pkl")
    path = out_dir / "strategy_eval.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


def _weekly(g: pd.DataFrame, rf: float) -> dict:
    """Share of calendar weeks (with at least one trade closing) that ended positive, from the account curve."""
    a = account(g, "use", COST_TAKER, rf)
    if not a:
        return {}
    # rebuild weekly returns quickly from per-trade net results sized at rf (approximation for the 'winning weeks' stat)
    t = g.assign(pnl=(g["R_use"] - COST_TAKER / g["stop_pct"]) * rf)
    wk = t.groupby(pd.to_datetime(t["exit_use"]).dt.to_period("W-SUN"))["pnl"].sum()
    return {"winning_weeks": float((wk > 0).mean()) if len(wk) else math.nan}
