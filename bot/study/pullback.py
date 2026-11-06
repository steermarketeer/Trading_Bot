"""
1D bounces: enter on the 4h pullback that holds, and short the 4h top that fails first (journal, 5 Dec 2023).

The trader's reading: on the 4h the buyers were slowing (lower highs on falling volume after a Bollinger failure at the
top), price pulled back to the 4h Bollinger middle where old resistance, an untaken low and the Fibonacci met, held it
on the closes, and then went up. The long belonged there, not at the daily close; the top was a short.
All decisions on closed candles; mirrored for 1D bounce shorts.

Long (PB)  after the daily signal, within 18 4h candles (3 days): the first 4h candle whose low reaches the 4h
           Bollinger middle (low <= middle + 0.25 ATR) and whose CLOSE is back above it (>= middle + 0.25 ATR), while the
           close is still below the daily signal price. Enter at the next open. Stop 0.25 ATR(4h) below the lower of
           the candle's low and the middle band. Invalid if the original v3.1 stop or target trades first.
  PBL      the same, and the pullback candle swept an untaken 1h swing low (wick below it, close back above it).
  targets  O  the original v3.1 target price      3  3R of the new risk      T  the top before the pullback (the
           highest high since the signal, where the buyers' stops rest), if >= 1.2R, else 3R
  no pullback: skip (S) or enter at the daily close as now (N).
Short (SH) a 4h Bollinger failure at the top (a close above the upper band in the 3 candles before, then a close back
           inside) from 6 candles before the daily signal until the long's pullback trigger. Short at the next open,
           stop 0.1% above the highest high of the last 6 4h candles, exit at the next open after the long's trigger
           close (flip), or after 24 4h candles at the open, or at the stop.
Choice on 2022 - Oct 2025 (best t-score, >= 25 trades, >= 3 good years); holdout once. Costs and funding as everywhere.
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
from .fibliq import Swings
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
W = 18
SH_BACK, SH_MAX = 6, 24


def replay(M, i0, end, d, e, s, tg=None, fx=None):
    """5m replay, stop first in a candle. tg: limit target (None = none). fx: forced market exit at the open of fx."""
    O, H, L, C = M["O"], M["H"], M["L"], M["C"]
    o, h, l, c = (O, H, L, C) if d > 0 else (-O, -L, -H, -C)
    e_, s_ = (e, s) if d > 0 else (-e, -s)
    tg_ = None if tg is None else (tg if d > 0 else -tg)
    risk = e_ - s_
    buf = LIMIT_BUFFER * abs(e)
    stop_at = min(end, fx) if fx is not None else end
    seg = slice(i0, stop_at)
    hs = np.nonzero(l[seg] <= s_)[0]
    ht = np.nonzero(h[seg] >= tg_ + buf)[0] if tg_ is not None else np.array([], int)
    xs = i0 + hs[0] if len(hs) else stop_at
    xt = i0 + ht[0] if len(ht) else stop_at
    if xs <= xt and xs < stop_at:
        R = ((o[xs] - e_) if (xs > i0 and o[xs] <= s_) else (s_ - e_)) / risk
        return R, xs, "stop"
    if xt < stop_at:
        return (tg_ - e_) / risk, xt, "target"
    if fx is not None and fx < end:
        return (o[fx] - e_) / risk, fx, "exit at open"
    return (c[end - 1] - e_) / risk, end - 1, "time"


def booked(M, i0, xi, kind, d, R, risk_pct):
    ft, fc = M["fund"]
    t5 = M["t5"]
    x_t = t5[xi] + (np.timedelta64(0, "m") if kind == "exit at open" else np.timedelta64(5, "m"))
    a_ = np.searchsorted(ft, t5[i0], side="right"); b_ = np.searchsorted(ft, x_t, side="left")
    cost = C_MKT + (C_LMT if kind == "target" else C_MKT) + ((fc[b_] - fc[a_]) * d if b_ > a_ else 0.0)
    return R - cost / risk_pct, pd.Timestamp(x_t)


def run_pullback(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t5 = df5n["open_time"].to_numpy()
    M = {"t5": t5, "fund": _funding_cum(cfg), **{k: df5n[x].to_numpy(float) for k, x in
                                                 (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}}
    t4 = TF(resample(df5u, "4h"))
    sw1 = Swings(df5u, "1h")
    X = pd.read_pickle(ROOT / "results" / "defs_review.pkl").reset_index(drop=True)
    X = X[X["setup"] == "1D bounce"]
    rows, shorts = [], []
    for k, r in X.iterrows():
        et, d, P, rk = pd.Timestamp(r["entry_time"]), int(r["direction"]), float(r["px"]), float(r["risk"])
        s0, tg0 = P - d * rk, P + d * 3.0 * rk
        filt = not bool(r["eq_highs_ahead"]) and not bool(r["rej_3plus"])
        st = int(np.searchsorted(t5, np.datetime64(et)))
        base = {"sig": k, "filtered": filt, "direction": d, "entry_time": et, "hold": bool(et >= HOLDOUT), "year": et.year}
        # as now
        end0 = min(len(t5), st + MAX_TF_BARS * 288)
        R, xi, kind = replay(M, st, end0, d, P, s0, tg0)
        net, xt = booked(M, st, xi, kind, d, R, rk / P)
        rows.append({**base, "entry": "now", "stopm": "orig", "target": "3", "net": net, "kind": kind, "decision_time": pd.Timestamp(t5[st]),
                     "exit_time": xt, "stop_pct": rk / P, "rr": 3.0})
        # oriented 4h arrays
        h4, l4, c4 = (t4.h, t4.l, t4.c) if d > 0 else (-t4.l, -t4.h, -t4.c)
        mid4 = t4.mid if d > 0 else -t4.mid
        up4 = t4.up if d > 0 else -t4.lo
        P_, s0_, tg0_ = d * P, d * s0, d * tg0
        j0 = t4.closed_before(et)                                      # first 4h candle that closes after the signal
        trig = {"PB": None, "PBL": None}
        top = -np.inf
        for j in range(j0, min(t4.n, j0 + W)):
            a = t4.a[j]
            if l4[j] <= s0_ or h4[j] >= tg0_:                           # original stop / target traded first
                break
            hold_mid = l4[j] <= mid4[j] + 0.25 * a and c4[j] >= mid4[j] + 0.25 * a and c4[j] < P_
            if hold_mid:
                if trig["PB"] is None:
                    trig["PB"] = (j, top)
                if trig["PBL"] is None:
                    lows = sw1.untaken(pd.Timestamp(t4.ot[j]), "L" if d > 0 else "H")
                    lows_ = d * lows
                    if len(lows_) and np.any((l4[j] < lows_) & (c4[j] > lows_)):
                        trig["PBL"] = (j, top)
                if trig["PBL"] is not None:
                    break
            top = max(top, h4[j])
        for mode, tv in trig.items():
            if tv is None:
                rows.append({**base, "entry": mode, "target": "none", "net": math.nan, "kind": "no pullback"})
                continue
            j, top_ = tv
            i0 = int(np.searchsorted(t5, t4.ct[j]))                     # close time = next open
            if i0 >= len(t5):
                continue
            e = M["O"][i0]; e_ = d * e
            end = min(len(t5), i0 + MAX_TF_BARS * 288)
            top_all = max(top_, max(h4[j0:j + 1]))
            for sm, s_ in (("tight", min(l4[j], mid4[j]) - 0.25 * t4.a[j]), ("orig", s0_)):
                if e_ - s_ <= 0:
                    continue
                risk = e_ - s_
                for tm, tgt_ in (("O", tg0_), ("3", e_ + 3 * risk), ("T", top_all if top_all - e_ >= 1.2 * risk else e_ + 3 * risk)):
                    if tgt_ - e_ < 1.2 * risk:
                        continue
                    R, xi, kind = replay(M, i0, end, d, e, d * s_, d * tgt_)
                    net, xt = booked(M, i0, xi, kind, d, R, risk / e)
                    rows.append({**base, "entry": mode, "stopm": sm, "target": tm, "net": net, "kind": kind,
                                 "decision_time": pd.Timestamp(t5[i0]), "exit_time": xt, "stop_pct": risk / e, "rr": (tgt_ - e_) / risk})
        # the short first: a Bollinger failure at the 4h top before the long's trigger
        jt = trig["PB"][0] if trig["PB"] is not None else min(t4.n - 1, j0 + W)
        for kk in range(max(4, j0 - SH_BACK), jt):
            if c4[kk] < up4[kk] and np.any(c4[kk - 3:kk] > up4[kk - 3:kk]):
                i0 = int(np.searchsorted(t5, t4.ct[kk]))
                e = M["O"][i0]
                stop = max(t4.h[max(0, kk - 5):kk + 1]) * 1.001 if d > 0 else min(t4.l[max(0, kk - 5):kk + 1]) * 0.999
                ds = -d
                if (e - stop) * ds <= 0:
                    break
                fx_t = t4.ct[trig["PB"][0]] if trig["PB"] is not None else t4.ct[min(t4.n - 1, kk + SH_MAX)]
                fx = int(np.searchsorted(t5, fx_t))
                fx = min(fx, int(np.searchsorted(t5, t4.ct[min(t4.n - 1, kk + SH_MAX)])))
                R, xi, kind = replay(M, i0, min(len(t5), fx + 1), ds, e, stop, None, fx)
                risk = abs(e - stop)
                net, xt = booked(M, i0, xi, kind, ds, R, risk / e)
                shorts.append({**base, "direction": ds, "entry": "SH", "target": "flip", "net": net, "kind": kind,
                               "decision_time": pd.Timestamp(t5[i0]), "exit_time": xt, "stop_pct": risk / e,
                               "flip_to_long": trig["PB"] is not None})
                break
    R_ = pd.DataFrame(rows)
    S_ = pd.DataFrame(shorts)
    R_.to_pickle(ROOT / "results" / "pullback.pkl"); S_.to_pickle(ROOT / "results" / "pullback_shorts.pkl")
    return write_report(R_, S_, out_dir)


def _rule_sets(R_):
    sets = {}
    now = R_[R_["entry"] == "now"]
    sets["as now (enter at the daily close, 3R)"] = now
    for mode, sm, tm, fb in itertools.product(("PB", "PBL"), ("tight", "orig"), ("O", "3", "T"), ("S", "N")):
        g = R_[(R_["entry"] == mode) & (R_["stopm"] == sm) & (R_["target"] == tm)]
        if fb == "N":
            g = pd.concat([g, now[~now["sig"].isin(g["sig"])]])
        name = (f"{'4h middle band holds' if mode == 'PB' else '4h middle band holds + sweep of a 1h low'} · "
                f"{'stop under the pullback' if sm == 'tight' else 'original stop'} · "
                f"{dict(O='original target', T='target the top before the pullback', **{'3': '3R'})[tm]} · "
                f"{'no pullback: skip' if fb == 'S' else 'no pullback: enter as now'}")
        sets[name] = g
    return sets


def _summ(g, res_ok, hold):
    r_, h_ = g[res_ok.reindex(g.index, fill_value=False)], g[hold.reindex(g.index, fill_value=False)]
    r_ = r_.drop_duplicates(["decision_time", "direction"]); h_ = h_.drop_duplicates(["decision_time", "direction"])
    yrs = sum(1 for y in (2022, 2023, 2024, 2025) if r_.loc[r_["year"] == y, "net"].mean() > 0)
    tsc = r_["net"].mean() / (r_["net"].std(ddof=1) / math.sqrt(len(r_))) if len(r_) > 2 and r_["net"].std() > 0 else 0
    return {"n_r": len(r_), "w_r": (r_["net"] > 0).mean() if len(r_) else math.nan, "a_r": r_["net"].mean() if len(r_) else math.nan,
            "t": tsc, "years": yrs, "n_h": len(h_), "w_h": (h_["net"] > 0).mean() if len(h_) else math.nan,
            "a_h": h_["net"].mean() if len(h_) else math.nan, "rr": r_["rr"].mean() if "rr" in r_ and len(r_) else math.nan}


def write_report(R_, S_, out_dir: Path) -> Path:
    R_ = R_[R_["kind"] != "no pullback"].copy()
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    L = ["# 1D bounces: enter where the 4h pullback holds, short the 4h top that fails first", "",
         "Every v3.1 ETH 1D bounce (and the 62 that pass the journal filters). **win % = profit after costs.** "
         "Chosen on 2022 - Oct 2025; the holdout (Nov 2025 on) is the honest check.", ""]
    cols = [("rule", "rule", str), ("n_r", "trades 2022-25", str), ("w_r", "win %", _pct), ("a_r", "avg R", f2),
            ("t", "t-score", lambda v: f"{v:.2f}"), ("years", "good years /4", str), ("n_h", "holdout trades", str),
            ("w_h", "holdout win %", _pct), ("a_h", "holdout avg R", f2), ("rr", "avg reward:risk", lambda v: "" if v != v else f"{v:.1f}")]
    for scope, m in (("journal-filtered bounces (62)", R_["filtered"]), ("all v3.1 1D bounces", pd.Series(True, index=R_.index))):
        D = R_[m]
        res_ok = ~D["hold"] & (D["exit_time"] < HOLDOUT)
        tab = [{"rule": name, **_summ(g, res_ok, D["hold"])} for name, g in _rule_sets(D).items()]
        T = pd.DataFrame(tab).sort_values("t", ascending=False)
        ok = T[(T["n_r"] >= 25) & (T["years"] >= 3)]
        L += [f"## {scope}", "", f"Chosen: **{ok.iloc[0]['rule'] if len(ok) else 'nothing qualified'}**", "", _table(T, cols), ""]
    # shorts
    for scope, m in (("journal-filtered bounces", S_["filtered"]), ("all v3.1 1D bounces", pd.Series(True, index=S_.index))):
        g = S_[m].drop_duplicates(["decision_time", "direction"])
        rows = []
        for per, pm in (("2022 - Oct 2025", ~g["hold"] & (g["exit_time"] < HOLDOUT)), ("holdout", g["hold"])):
            for who, wm in (("all shorts", pd.Series(True, index=g.index)), ("flipped to the long (pullback came)", g["flip_to_long"])):
                x = g[pm & wm]
                s_ = stats(x["net"].to_numpy())
                rows.append({"per": per, "who": who, **s_})
        L += [f"## The short first (4h Bollinger failure at the top, exit on the long's trigger): {scope}", "",
              _table(pd.DataFrame(rows), [("per", "period", str), ("who", "shorts", str), ("n", "n", str), ("win", "win %", _pct),
                                          ("avg", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}")]), ""]
    path = out_dir / "pullback.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_pullback(load_config(ROOT / "config.yaml"), ROOT / "reports"))
