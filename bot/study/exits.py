"""
Exit-rule research on 5-minute data.

Each trade (entry at the open after the decision candle, initial stop as defined by its concept) is replayed
on 5m candles for up to 60 candles of its own timeframe. Within a 5m candle the stop is checked before any
target (conservative). Rule changes (break-even, trailing) take effect from the NEXT 5m candle.
Results are in R = initial risk; costs (fees + slippage, round trip) are subtracted in R.

Rules (all parameters fixed in advance):
  fixed_T          target T R, stop unchanged                      (T = 1, 1.5, 2, 3)
  be_X_T           move stop to entry once +X R is reached          (X = 0.5, 1; T = 2, 3)
  partial_T        close half at +1R, stop to entry, rest to T R    (T = 2, 3, trail)
  atr_trail_k      no target; stop trails k x ATR below the best price since entry, from the start (k = 1.5, 2, 3)
  atr_trail_k_1R   same, but trailing only starts after +1R
  low3_trail       no target; after each candle of the trade's timeframe, stop = lowest low of the last 3 candles
  time_N           target 2R, but exit at the close of candle N if +0.5R was never reached (N = 3, 6)
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .sr2_run import COST_FRAC, _pct, _r, _table

MAX_TF_BARS = 60
FIVE = pd.Timedelta(minutes=5)


def _first(mask: np.ndarray, start: int = 0) -> int:
    """Index of the first True at or after `start`, or -1."""
    if start >= len(mask):
        return -1
    idx = np.flatnonzero(mask[start:])
    return int(idx[0]) + start if len(idx) else -1


def simulate(o, h, l, c, entry, risk, atr_, bars_per_tf):
    """
    Long-only representation (shorts are mirrored by the caller). Returns {rule: R before costs}.
    o/h/l/c: 5m arrays from the entry candle on. entry = o[0].
    """
    n = len(o)
    stop0 = entry - risk
    out = {}
    last_close = c[-1]

    def stop_fill(i, level):
        return min(o[i], level) if i > 0 else level   # gap through the stop fills at the open

    def tgt_fill(i, level):
        return max(o[i], level) if i > 0 else level

    hit_stop0 = l <= stop0

    # --- fixed targets
    for T in (1.0, 1.5, 2.0, 3.0):
        tgt = entry + T * risk
        i_s, i_t = _first(hit_stop0), _first(h >= tgt)
        if i_s >= 0 and (i_t < 0 or i_s <= i_t):
            out[f"fixed_{T:g}R"] = (stop_fill(i_s, stop0) - entry) / risk
        elif i_t >= 0:
            out[f"fixed_{T:g}R"] = (tgt_fill(i_t, tgt) - entry) / risk
        else:
            out[f"fixed_{T:g}R"] = (last_close - entry) / risk

    # --- break-even after +X
    for X in (0.5, 1.0):
        i_x = _first(h >= entry + X * risk)
        for T in (2.0, 3.0):
            tgt = entry + T * risk
            i_s0, i_t = _first(hit_stop0), _first(h >= tgt)
            key = f"be{X:g}_{T:g}R"
            if i_x < 0 or (i_s0 >= 0 and i_s0 <= i_x):          # stopped before reaching +X (or same candle)
                if i_s0 >= 0 and (i_t < 0 or i_s0 <= i_t):
                    out[key] = (stop_fill(i_s0, stop0) - entry) / risk
                elif i_t >= 0:
                    out[key] = (tgt_fill(i_t, tgt) - entry) / risk
                else:
                    out[key] = (last_close - entry) / risk
                continue
            if i_t >= 0 and i_t <= i_x:
                out[key] = (tgt_fill(i_t, tgt) - entry) / risk
                continue
            i_be = _first(l <= entry, i_x + 1)
            if i_be >= 0 and (i_t < 0 or i_be <= i_t):
                out[key] = (stop_fill(i_be, entry) - entry) / risk
            elif i_t >= 0:
                out[key] = (tgt_fill(i_t, tgt) - entry) / risk
            else:
                out[key] = (last_close - entry) / risk

    # --- trailing helpers
    def trail_result(stop_path):
        """stop_path[i] = stop level in force during 5m candle i."""
        i_s = _first(l <= stop_path)
        if i_s < 0:
            return (last_close - entry) / risk
        return (stop_fill(i_s, stop_path[i_s]) - entry) / risk

    best_before = np.maximum.accumulate(np.r_[entry, h[:-1]])  # best high strictly before candle i
    i_1r = _first(h >= entry + risk)
    for k in (1.5, 2.0, 3.0):
        trail = np.maximum(stop0, best_before - k * atr_)
        out[f"atr_trail_{k:g}"] = trail_result(trail)
        active = (np.arange(n) > i_1r) if i_1r >= 0 else np.zeros(n, dtype=bool)
        out[f"atr_trail_{k:g}_after1R"] = trail_result(np.where(active, trail, stop0))

    # --- partial: half at +1R, stop to entry, rest to T / trail
    def second_half(start, rest_stop_path, T):
        if start >= n:
            return (last_close - entry) / risk
        hh, ll = h[start:], l[start:]
        sp = rest_stop_path[start:]
        i_s = _first(ll <= sp)
        i_t = _first(hh >= entry + T * risk) if T else -1
        if i_s >= 0 and (i_t < 0 or i_s <= i_t):
            return (stop_fill(start + i_s, sp[i_s]) - entry) / risk
        if i_t >= 0:
            return (tgt_fill(start + i_t, entry + T * risk) - entry) / risk
        return (last_close - entry) / risk

    i_s0 = _first(hit_stop0)
    for T in (2.0, 3.0, None):
        key = f"partial_{'trail2ATR' if T is None else f'{T:g}R'}"
        if i_1r < 0 or (i_s0 >= 0 and i_s0 <= i_1r):       # never reached +1R, or stopped first / same candle
            out[key] = (stop_fill(i_s0, stop0) - entry) / risk if i_s0 >= 0 else (last_close - entry) / risk
            continue
        if T is None:
            sp = np.maximum(entry, best_before - 2.0 * atr_)
        else:
            sp = np.full(n, entry)
        out[key] = 0.5 * 1.0 + 0.5 * second_half(i_1r + 1, sp, T)

    # --- 3-candle low trail on the trade's own timeframe
    tf_n = int(math.ceil(n / bars_per_tf))
    tf_low = np.array([l[i * bars_per_tf:(i + 1) * bars_per_tf].min() for i in range(tf_n)])
    sp = np.full(n, stop0)
    for m in range(1, tf_n):
        lvl = max(stop0, tf_low[max(0, m - 3):m].min())
        sp[m * bars_per_tf:(m + 1) * bars_per_tf] = lvl
    out["low3_trail"] = trail_result(np.maximum.accumulate(sp))

    # --- time stop: target 2R, out at candle N close if +0.5R never reached
    for N in (3, 6):
        cut = min(n, N * bars_per_tf)
        reached = _first(h[:cut] >= entry + 0.5 * risk) >= 0
        if reached:
            out[f"time{N}_2R"] = out["fixed_2R"]
            continue
        i_s = _first(hit_stop0[:cut])
        out[f"time{N}_2R"] = (stop_fill(i_s, stop0) - entry) / risk if i_s >= 0 else (c[cut - 1] - entry) / risk
    return out


def run_trades(trades: pd.DataFrame, df5: pd.DataFrame) -> pd.DataFrame:
    t5 = df5["open_time"].to_numpy()
    O, H, Lw, C = (df5[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    rows = []
    for _, t in trades.iterrows():
        bar = pd.Timedelta(t["tf"])
        bpt = int(bar / FIVE)
        start = int(np.searchsorted(t5, pd.Timestamp(t["decision_time"]).to_datetime64(), side="left"))
        if start >= len(t5) or t5[start] != pd.Timestamp(t["decision_time"]).to_datetime64():
            continue  # entry candle missing in the 5m data
        end = min(len(O), start + MAX_TF_BARS * bpt)
        if end - start < MAX_TF_BARS * bpt:
            continue  # not enough data to finish the trade
        d = int(t["direction"])
        o, h, l, c = O[start:end], H[start:end], Lw[start:end], C[start:end]
        if d < 0:  # mirror shorts into longs
            o, h, l, c = -o, -l, -h, -c
        entry = o[0]
        risk = float(t["risk"])
        res = simulate(o, h, l, c, entry, risk, float(t["atr"]), bpt)
        cost_r = COST_FRAC * abs(entry) / risk
        rows.append({"decision_time": t["decision_time"], "tf": t["tf"], "period": t["period"],
                     "certainty": t.get("certainty", np.nan), "event": t["event"], "cost_r": cost_r,
                     **{k: v - cost_r for k, v in res.items()}})
    return pd.DataFrame(rows)


def summarize(x: pd.DataFrame, rules: list[str]) -> pd.DataFrame:
    rows = []
    for r in rules:
        v = x[r].dropna()
        if not len(v):
            continue
        wins, losses = v[v > 0].sum(), -v[v <= 0].sum()
        rows.append({"rule": r, "n": len(v), "win": (v > 0).mean(), "avg_r": v.mean(),
                     "pf": wins / losses if losses > 0 else math.nan, "worst": v.min()})
    return pd.DataFrame(rows)


def run_exits(cfg: Config, out_dir: Path) -> Path:
    df5, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5 = df5.assign(open_time=pd.to_datetime(df5["open_time"], utc=True))
    df5["open_time"] = df5["open_time"].dt.tz_convert(None)
    br = pd.read_pickle(ROOT / "results" / "scored_breakout.pkl")
    br["decision_time"] = pd.to_datetime(br["decision_time"], utc=True).dt.tz_convert(None)
    rv = pd.read_pickle(ROOT / "results" / "concept_events_1D.pkl")
    rv = rv[rv["event"] == "zone_bounce"].copy()
    rv["tf"] = "1D"
    rv["decision_time"] = pd.to_datetime(rv["decision_time"], utc=True).dt.tz_convert(None)
    rv["period"] = np.where(rv["decision_time"] >= pd.Timestamp("2025-11-01"), "holdout",
                            np.where(rv["decision_time"] < pd.Timestamp("2025-11-01") - pd.Timedelta(days=62),
                                     "research", "gap"))
    rv = rv[rv["period"] != "gap"]
    sets = {
        "Breakouts, certainty >= 7": br[br["certainty"] >= 7],
        "Breakouts, certainty >= 6": br[br["certainty"] >= 6],
        "1D S/R zone bounce (all)": rv,
    }
    L = ["# Exit rules: how should a trade be closed?", "",
         "Each trade is replayed on **5-minute candles** (stop checked before target inside each 5m candle; a moved "
         "stop applies from the next 5m candle). Results in R (1R = the initial risk), **after fees and slippage**. "
         "*win* = the trade ended with a profit after costs. *PF* = profit factor (gross wins / gross losses). "
         "The rule to use is chosen on the research years only (2022-25 for breakouts, 2020-25 for zone bounces), "
         "then checked on the holdout.", ""]
    picks = []
    for name, trades in sets.items():
        sim = run_trades(trades, df5)
        if sim.empty:
            continue
        safe = "".join(ch if ch.isalnum() else "_" for ch in name)
        sim.to_pickle(ROOT / "results" / f"exits_{safe}.pkl")
        rules = [c for c in sim.columns if c not in ("decision_time", "tf", "period", "certainty", "event", "cost_r")]
        res, hold = sim[sim["period"] != "holdout"], sim[sim["period"] == "holdout"]
        a, b = summarize(res, rules), summarize(hold, rules)
        m = a.merge(b, on="rule", suffixes=("", "_h"))
        best = m.sort_values("avg_r", ascending=False).iloc[0]
        picks.append({"set": name, "rule": best["rule"], "n": best["n"], "win": best["win"], "avg_r": best["avg_r"],
                      "n_h": best["n_h"], "win_h": best["win_h"], "avg_r_h": best["avg_r_h"]})
        m = m.sort_values("avg_r", ascending=False)
        yr = sim.assign(year=np.where(sim["period"] == "holdout", "holdout",
                                      pd.to_datetime(sim["decision_time"]).dt.year.astype(str)))
        key_rules = ["fixed_1R", "partial_2R", "fixed_2R", "be1_2R", "atr_trail_2", "atr_trail_3"]
        yt = yr.groupby("year")[key_rules].mean().reset_index()
        yt["n"] = yr.groupby("year").size().to_numpy()
        yw = yr.groupby("year")[key_rules].agg(lambda v: (v > 0).mean()).reset_index()
        L += [f"## {name}", "", f"Research {len(res)} trades, holdout {len(hold)} trades.", "",
              "**Year by year (avg R after costs, win % in brackets):**", "",
              _table(yt.assign(**{r: [f"{a:+.2f} ({b:.0%})" for a, b in zip(yt[r], yw[r])] for r in key_rules}),
                     [("year", "year", str), ("n", "trades", str), *[(r, r, str) for r in key_rules]]), "",
              "All rules, sorted by research avg R:", "",
              _table(m, [("rule", "exit rule", str), ("win", "win (research)", _pct), ("avg_r", "avg R (research)", _r),
                         ("pf", "PF", lambda x: "-" if pd.isna(x) else f"{x:.2f}"),
                         ("win_h", "win (holdout)", _pct), ("avg_r_h", "avg R (holdout)", _r),
                         ("pf_h", "PF (holdout)", lambda x: "-" if pd.isna(x) else f"{x:.2f}")]), ""]
    p = pd.DataFrame(picks)
    head = ["## Summary: best exit per trade set (chosen on research, then checked on holdout)", "",
            _table(p, [("set", "trades", str), ("rule", "best exit (research)", str), ("n", "research n", str),
                       ("win", "research win", _pct), ("avg_r", "research avg R", _r), ("n_h", "holdout n", str),
                       ("win_h", "holdout win", _pct), ("avg_r_h", "holdout avg R", _r)]), "",
            "Rule names: fixed_T = fixed target; beX_T = stop to entry after +X R, target T; partial_* = half off at "
            "+1R then the rest to target/trail with stop at entry; atr_trail_k = trailing stop k x ATR (\"_after1R\" "
            "= starts after +1R); low3_trail = stop under the lowest low of the last 3 candles; timeN_2R = 2R target "
            "but exit after N candles if +0.5R was never reached.", ""]
    L = L[:3] + head + L[3:]
    path = out_dir / "exit_study.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
