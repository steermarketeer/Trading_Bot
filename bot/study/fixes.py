"""
Fix pipeline: v3.1 + the journal filters, plus what was learnt about failures, breaks / rejections and trendlines.
Every rule is defined in docs/trading_definitions.md; decisions use candle closes only; only closed candles are used.

Base  B   v3.1 ETH trades, one position per move, skipping (a) an untaken double / triple top between entry and target and
          (b) 3+ rejections / failed pushes at the resistance ahead (the two journal filters).
Entry filters
  TL      skip if a valid trendline against the trade (3+ swing touches within 0.25 ATR, no close through it since its
          second point) lies between the entry and the target at entry (1h and 4h lines through the last 6 swings).
  BQ      breakouts only: keep only a strong breaking candle (the signal candle: body >= 60% of its range, range >= 1.5 ATR,
          volume >= 1.2x its 20-candle average). Bounces unaffected.
Exits (after entry, 1h closes)
  XF      failure exit once in profit: after the trade has been >= +0.5R, the next 1h push fails to make a new high and a
          1h candle CLOSES below the pullback low -> exit at the next open.
  XA      the same without the profit condition.
Entry
  RT      retest entry: after the first 4h close beyond the signal price (confirmation), wait up to 24h for a 1h candle that
          comes back within 0.25 ATR(1h) of the signal price and CLOSES back on the trade's side; enter at the next open;
          same stop and target prices; skipped if stop / target was hit first or reward:risk < 1.2.
Choice: research = trades 2022 - Oct 2025 that ended before the holdout; combination with the best t-score of R after
costs among those with >= 60 trades and positive avg R in >= 3 of 4 years. Holdout once.
"""
from __future__ import annotations

import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import C_LMT, C_MKT, LIMIT_BUFFER, MAX_TF_BARS, _funding_cum, account, stats
from .defs import TF
from .fibliq import Swings, plan as fib_plan
from .levels import _level_table, strong_levels
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
FIVE = pd.Timedelta(minutes=5)
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}


def trendline_in_way(t: TF, et, e, tg, d) -> bool:
    n = t.closed_before(et)
    sw = [(i, p) for i, p, cf in (t.sh if d > 0 else t.sl) if cf < n][-6:]
    for (i1, p1), (i2, p2) in itertools.combinations(sw, 2):
        slope = (p2 - p1) / (i2 - i1)
        line = lambda j: p1 + slope * (j - i1)  # noqa: E731
        if any((t.c[j] - line(j)) * d > 0.25 * t.a[j] for j in range(i2 + 1, n)):
            continue                                                      # broken by a close
        touches = sum(1 for i, p in sw if abs(p - line(i)) <= 0.25 * t.a[i])
        if touches < 3:
            continue
        v = line(n)
        if (v - e) * d > 0 and (tg - v) * d > 0:
            return True
    return False


def break_quality(t: TF, et) -> bool:
    j = t.closed_before(et) - 1
    rng = t.h[j] - t.l[j]
    vavg = t.v[max(0, j - 20):j].mean()
    return rng > 0 and abs(t.c[j] - t.o[j]) >= 0.6 * rng and rng >= 1.5 * t.a[j] and t.v[j] >= 1.2 * vavg


def replay(ctx, i0, end, d, e, s, tg, exit_mode, h1):
    O, H, L, C, t5 = ctx["O"], ctx["H"], ctx["L"], ctx["C"], ctx["t5"]
    o, h, l, c = (O, H, L, C) if d > 0 else (-O, -L, -H, -C)
    e, s, tg = (e, s, tg) if d > 0 else (-e, -s, -tg)
    risk = e - s
    buf = LIMIT_BUFFER * abs(e)
    H1 = h1.h if d > 0 else -h1.l
    L1 = h1.l if d > 0 else -h1.h
    C1 = h1.c if d > 0 else -h1.c
    peak, pull, lower_high, best = -np.inf, np.inf, False, -np.inf
    for i in range(i0, end):
        if i > i0 and o[i] <= s:
            return (o[i] - e) / risk, i, "stop"
        if l[i] <= s:
            return (s - e) / risk, i, "stop"
        if h[i] >= tg + buf:
            return (tg - e) / risk, i, "target"
        best = max(best, (h[i] - e) / risk)
        if exit_mode and (pd.Timestamp(t5[i]) + FIVE).minute == 0:      # a 1h candle closed at the end of this 5m candle
            j = h1.closed_before(pd.Timestamp(t5[i]) + FIVE) - 1
            if H1[j] > peak:
                peak, pull, lower_high = H1[j], np.inf, False
            else:
                if np.isfinite(pull) and pull < H1[j] < peak:
                    lower_high = True
                armed = exit_mode == "XA" or best >= 0.5
                if armed and lower_high and C1[j] < pull and i + 1 < end:
                    return (o[i + 1] - e) / risk, i + 1, "failure exit"
                pull = min(pull, L1[j])
    return (c[end - 1] - e) / risk, end - 1, "time"


def run_fixes(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    ctx = {"t5": df5n["open_time"].to_numpy(), **{k: df5n[x].to_numpy(float) for k, x in
                                                  (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}}
    ft, fc = _funding_cum(cfg)
    tf = {k: TF(resample(df5u, r)) for k, r in (("1h", "1h"), ("2h", "2h"), ("4h", "4h"), ("1D", "1D"))}
    X = pd.read_pickle(ROOT / "results" / "defs_review.pkl")
    X = X[~X["eq_highs_ahead"].astype(bool) & ~X["rej_3plus"].astype(bool)].reset_index(drop=True)
    rows = []
    t5 = ctx["t5"]
    swf = {k_: Swings(df5u, r_) for k_, r_ in (("15m", "15min"), ("1h", "1h"), ("4h", "4h"), ("1D", "1D"))}
    table = _level_table(df5u)
    for k, r in X.iterrows():
        et, d, e, rk = pd.Timestamp(r["entry_time"]), int(r["direction"]), float(r["px"]), float(r["risk"])
        s, tg = e - d * rk, e + d * TGT[r["setup"]] * rk
        base = {"sig": k, "setup": r["setup"], "hold": bool(r["hold"]), "year": et.year,
                "TL": trendline_in_way(tf["1h"], et, e, tg, d) or trendline_in_way(tf["4h"], et, e, tg, d),
                "BQ": True if r["setup"] == "1D bounce" else break_quality(tf[r["tf"]], et)}
        st = int(np.searchsorted(t5, np.datetime64(et)))
        bpt = int(pd.Timedelta(r["tf"]) / FIVE)
        for entry_mode in ("now", "RT"):
            i0, ent = st, e
            if entry_mode == "RT":
                t4, t1 = tf["4h"], tf["1h"]
                j4 = t4.closed_before(et)
                if j4 >= t4.n or (t4.c[j4] - e) * d <= 0:
                    continue                                            # not confirmed by the 4h close
                conf_t = pd.Timestamp(t4.ct[j4]) + pd.Timedelta(milliseconds=1)
                ic = int(np.searchsorted(t5, np.datetime64(pd.Timestamp(t4.ct[j4]))))   # close time = next open
                seg_s = (ctx["L"][st:ic] <= s) if d > 0 else (ctx["H"][st:ic] >= s)
                seg_t = (ctx["H"][st:ic] >= tg) if d > 0 else (ctx["L"][st:ic] <= tg)
                if seg_s.any() or seg_t.any():
                    continue                                            # stop / target already hit before confirmation
                j1 = t1.closed_before(conf_t)
                found = None
                for jj in range(j1, min(t1.n - 1, j1 + 24)):
                    a = t1.a[jj]
                    near = (t1.l[jj] <= e + 0.25 * a) if d > 0 else (t1.h[jj] >= e - 0.25 * a)
                    back = (t1.c[jj] - e) * d > 0
                    hit_s = (t1.l[jj] <= s) if d > 0 else (t1.h[jj] >= s)
                    hit_t = (t1.h[jj] >= tg) if d > 0 else (t1.l[jj] <= tg)
                    if hit_s or hit_t:
                        break
                    if near and back:
                        found = int(np.searchsorted(t5, np.datetime64(pd.Timestamp(t1.ct[jj]))))
                        break
                if found is None or found >= len(t5):
                    continue
                i0, ent = found, ctx["O"][found]
                if (ent - s) * d <= 0 or (tg - ent) * d / ((ent - s) * d) < 1.2:
                    continue
            end = min(len(t5), i0 + MAX_TF_BARS * bpt)
            for exit_mode in (None, "XF", "XA"):
                R, xi, kind = replay(ctx, i0, end, d, ent, s, tg, exit_mode, tf["1h"])
                mkt_open = kind == "failure exit"
                x_t = pd.Timestamp(t5[xi]) + (pd.Timedelta(0) if mkt_open else FIVE)
                a_ = np.searchsorted(ft, t5[i0], side="right"); b_ = np.searchsorted(ft, x_t.to_datetime64(), side="left")
                sp = abs(ent - s) / abs(ent)
                cost = C_MKT + (C_LMT if kind == "target" else C_MKT) + ((fc[b_] - fc[a_]) * d if b_ > a_ else 0.0)
                rows.append({**base, "entry": entry_mode, "exit": exit_mode or "none", "fib": "none", "net": R - cost / sp, "kind": kind,
                             "stop_pct": sp, "decision_time": pd.Timestamp(t5[i0]), "exit_time": x_t,
                             "entry_time": et, "direction": d, "tf": r["tf"]})
        # Fibonacci confluence variants (entry at the signal)
        fp = fib_plan(r, swf)
        if fp is None:
            continue
        e0 = ctx["O"][st]
        a1 = tf["1h"].a[tf["1h"].closed_before(et) - 1]
        tolf = max(0.25 * a1, 0.002 * e0)
        side_t = "H" if d > 0 else "L"
        ahead = [v for kk in ("1h", "4h", "1D") for v in swf[kk].untaken(et, side_t)] + list(strong_levels(table, et.tz_localize("UTC")))
        ahead = np.array([v for v in ahead if (v - e0) * d > 0])
        tg_f = None
        for x_ in sorted([fp["x1272"], fp["x1618"]], key=lambda v: (v - e0) * d):
            if (x_ - e0) * d > 0 and len(ahead) and np.min(np.abs(ahead - x_)) <= tolf and (x_ - e0) * d >= 1.2 * rk:
                tg_f = x_; break
        s_f = fp["f786"] - d * 0.001 * e0 if r["setup"] == "1D bounce" else None
        if s_f is not None and (e0 - s_f) * d <= 0:
            s_f = None
        end = min(len(t5), st + MAX_TF_BARS * bpt)
        for fib_mode in ("FCX", "S786", "FCX+S786"):
            s2 = s_f if ("S786" in fib_mode and s_f is not None) else s
            tg2 = tg_f if ("FCX" in fib_mode and tg_f is not None) else (e0 + d * TGT[r["setup"]] * abs(e0 - s2))
            if (tg2 - e0) * d / abs(e0 - s2) < 1.2:
                tg2 = e0 + d * 1.2 * abs(e0 - s2)
            for exit_mode in (None, "XF"):
                R, xi, kind = replay(ctx, st, end, d, e0, s2, tg2, exit_mode, tf["1h"])
                mkt_open = kind == "failure exit"
                x_t = pd.Timestamp(t5[xi]) + (pd.Timedelta(0) if mkt_open else FIVE)
                a_ = np.searchsorted(ft, t5[st], side="right"); b_ = np.searchsorted(ft, x_t.to_datetime64(), side="left")
                sp = abs(e0 - s2) / abs(e0)
                cost = C_MKT + (C_LMT if kind == "target" else C_MKT) + ((fc[b_] - fc[a_]) * d if b_ > a_ else 0.0)
                rows.append({**base, "entry": "now", "exit": exit_mode or "none", "fib": fib_mode, "net": R - cost / sp,
                             "kind": kind, "stop_pct": sp, "decision_time": pd.Timestamp(t5[st]), "exit_time": x_t,
                             "entry_time": et, "direction": d, "tf": r["tf"]})
    R_ = pd.DataFrame(rows)
    R_.to_pickle(ROOT / "results" / "fixes.pkl")
    res_ok = ~R_["hold"] & (R_["exit_time"] < HOLDOUT)
    combos = []
    for entry_mode, exit_mode, use_tl, use_bq in itertools.product(("now", "RT"), ("none", "XF", "XA"), (False, True), (False, True)):
        m = (R_["entry"] == entry_mode) & (R_["exit"] == exit_mode) & (R_["fib"] == "none")
        if use_tl:
            m &= ~R_["TL"]
        if use_bq:
            m &= R_["BQ"]
        name = " + ".join([x for x, on in (("retest entry" if entry_mode == "RT" else "enter at signal", True),
                                           ({"none": "fixed target", "XF": "failure exit (in profit)", "XA": "failure exit (any)"}[exit_mode], True),
                                           ("no trendline in the way", use_tl), ("strong breaking candle", use_bq)) if on])
        r_ = R_[m & res_ok]; h_ = R_[m & R_["hold"]]
        yrs = sum(1 for y in (2022, 2023, 2024, 2025) if r_.loc[r_["year"] == y, "net"].mean() > 0)
        tsc = r_["net"].mean() / (r_["net"].std(ddof=1) / math.sqrt(len(r_))) if len(r_) > 2 and r_["net"].std() > 0 else 0
        combos.append({"name": name, "mask": m, "n_r": len(r_), "w_r": (r_["net"] > 0).mean() if len(r_) else math.nan,
                       "a_r": r_["net"].mean() if len(r_) else math.nan, "t": tsc, "years": yrs, "n_h": len(h_),
                       "w_h": (h_["net"] > 0).mean() if len(h_) else math.nan, "a_h": h_["net"].mean() if len(h_) else math.nan})
    T = pd.DataFrame(combos)
    ok = T[(T["n_r"] >= 60) & (T["years"] >= 3)].sort_values("t", ascending=False)
    best = ok.iloc[0] if len(ok) else None
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    L = ["# Fixing the remaining failures: breaks / rejections, failures, trendlines", "",
         "Start: v3.1 ETH trades (one position per move) with the two journal filters. **win % = profit after costs.** "
         "The combination is chosen on 2022 - Oct 2025 only; the holdout (Nov 2025 on) is the honest check. "
         "Definitions: docs/trading_definitions.md.", ""]
    base_row = T[T["name"] == "enter at signal + fixed target"].iloc[0]
    rows = [{"label": "start (v3.1 + journal filters)", **base_row.drop("mask").to_dict()}]
    if best is not None:
        rows.append({"label": "chosen on 2022 - 2025", **best.drop("mask").to_dict()})
    L += ["## Start vs chosen", "", _table(pd.DataFrame(rows), [
        ("label", "", str), ("name", "rules", str), ("n_r", "trades 2022-25", lambda v: f"{int(v)}"), ("w_r", "win %", _pct),
        ("a_r", "avg R", f2), ("n_h", "trades holdout", lambda v: f"{int(v)}"), ("w_h", "win % holdout", _pct),
        ("a_h", "avg R holdout", f2)]), ""]
    rows = []
    for lab, mask in (("start", base_row["mask"]), ("chosen", best["mask"] if best is not None else base_row["mask"])):
        for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
            x = R_[mask & (R_["hold"] == hold)].reset_index(drop=True)
            s_ = stats(x["net"].to_numpy())
            eq, mdd = account(x, "net", "exit_time", RISK) if len(x) else (math.nan, math.nan)
            weeks = (HOLDOUT - pd.Timestamp("2022-01-01")).days / 7 if not hold else (R_["entry_time"].max() - HOLDOUT).days / 7
            rows.append({"lab": lab, "per": per, **s_, "pw": s_["n"] / weeks, "eq": eq, "mdd": mdd})
    L += ["## Account (A+ 4%, others 2%, max 5x)", "", _table(pd.DataFrame(rows), [
        ("lab", "", str), ("per", "period", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
        ("win", "win %", _pct), ("avg", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("eq", "account", lambda v: f"{v:.2f}x"), ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    L += ["## Every combination (sorted by the 2022 - 2025 t-score)", "", _table(T.sort_values("t", ascending=False).drop(columns="mask"), [
        ("name", "rules", str), ("n_r", "trades 2022-25", str), ("w_r", "win %", _pct), ("a_r", "avg R", f2),
        ("t", "t-score", lambda v: f"{v:.2f}"), ("years", "good years /4", str), ("n_h", "holdout trades", str),
        ("w_h", "holdout win %", _pct), ("a_h", "holdout avg R", f2)]), ""]
    rows = []
    names = {"none": "no Fibonacci", "FCX": "target at a Fib extension that coincides with liquidity",
             "S786": "bounces: stop below Fib 0.786", "FCX+S786": "both"}
    for fib_mode in ("none", "FCX", "S786", "FCX+S786"):
        for exit_mode in ("none", "XF"):
            for bq in (False, True):
                m = (R_["entry"] == "now") & (R_["exit"] == exit_mode) & (R_["fib"] == fib_mode)
                if fib_mode == "none":
                    m &= R_["sig"].isin(R_.loc[R_["fib"] == "FCX", "sig"].unique())     # same trades as the Fib rows
                if bq:
                    m &= R_["BQ"]
                r_, h_ = R_[m & res_ok], R_[m & R_["hold"]]
                rows.append({"fib": names[fib_mode], "exit": {"none": "fixed / Fib target", "XF": "+ failure exit"}[exit_mode],
                             "bq": "strong breaking candle" if bq else "", "n_r": len(r_), "w_r": (r_["net"] > 0).mean(),
                             "a_r": r_["net"].mean(), "n_h": len(h_), "w_h": (h_["net"] > 0).mean(), "a_h": h_["net"].mean()})
    L += ["## Fibonacci confluence (same trades in every row)", "", _table(pd.DataFrame(rows), [
        ("fib", "Fibonacci", str), ("exit", "exit", str), ("bq", "filter", str), ("n_r", "trades 2022-25", str),
        ("w_r", "win %", _pct), ("a_r", "avg R", f2), ("n_h", "trades holdout", str), ("w_h", "win % holdout", _pct),
        ("a_h", "avg R holdout", f2)]), ""]
    if best is not None:
        R_.loc[best["mask"]].to_pickle(ROOT / "results" / "fixes_chosen.pkl")
    path = out_dir / "fixes.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
