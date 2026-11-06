"""
1D bounces, fixed with the trader's reading (22 May 2024 review): repeated failure to go down = the long entry;
repeated failure to go up = the exit. Candle closes decide; only closed candles are used.

Trades: v3.1 ETH 1D bounces that pass the two journal filters (results/defs_review.pkl).
Support level L = the touch candle's extreme (the low for longs). A daily REJECTION = the daily low reaches
L + 0.25 ATR or below and the daily CLOSE is back above L + 0.25 ATR (mirrored for shorts).
Entry
  E0  as now: next open after the touch candle is confirmed (v3.1)
  E2  wait for the 2nd rejection close (the touch counts as the 1st) within 10 days; enter at the next open
  E3  wait for the 3rd rejection close within 10 days
  stop for E2 / E3: 0.1% below the lowest low since the touch (above the highest high for shorts)
Target
  T3  3R of the trade's own risk (as now)
  TL  the first untaken daily swing high / strong zone ahead if >= 1.2R away, else 3R
Exit
  none  stop / target / time only
  XD    daily failure exit: after the trade's highest daily high, a daily push fails to make a new high and a
        daily CLOSE goes below the pullback low -> exit at the next open (any time)
Choice on 2022 - Oct 2025 (>= 25 trades, best t-score of R); holdout once. Costs and funding as everywhere.
"""
from __future__ import annotations

import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import C_LMT, C_MKT, LIMIT_BUFFER, MAX_TF_BARS, _funding_cum, stats
from .defs import TF
from .fibliq import Swings
from .levels import _level_table, strong_levels
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
FIVE = pd.Timedelta(minutes=5)


def run(ctx, d1, i0, end, d, e, s, tg, daily_exit):
    O, H, L, C, t5 = ctx["O"], ctx["H"], ctx["L"], ctx["C"], ctx["t5"]
    o, h, l, c = (O, H, L, C) if d > 0 else (-O, -L, -H, -C)
    e, s, tg = (e, s, tg) if d > 0 else (-e, -s, -tg)
    risk = e - s
    buf = LIMIT_BUFFER * abs(e)
    DH = d1.h if d > 0 else -d1.l
    DL = d1.l if d > 0 else -d1.h
    DC = d1.c if d > 0 else -d1.c
    peak, pull, lower_high = -np.inf, np.inf, False
    for i in range(i0, end):
        if i > i0 and o[i] <= s:
            return (o[i] - e) / risk, i, "stop"
        if l[i] <= s:
            return (s - e) / risk, i, "stop"
        if h[i] >= tg + buf:
            return (tg - e) / risk, i, "target"
        tend = pd.Timestamp(t5[i]) + FIVE
        if daily_exit and tend.hour == 0 and tend.minute == 0:          # a daily candle just closed
            j = d1.closed_before(tend) - 1
            if DH[j] > peak:
                peak, pull, lower_high = DH[j], np.inf, False
            else:
                if np.isfinite(pull) and pull < DH[j] < peak:
                    lower_high = True
                if lower_high and DC[j] < pull and i + 1 < end:
                    return (o[i + 1] - e) / risk, i + 1, "daily failure exit"
                pull = min(pull, DL[j])
    return (c[end - 1] - e) / risk, end - 1, "time"


def run_bounce_fix(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t5 = df5n["open_time"].to_numpy()
    ctx = {"t5": t5, **{k: df5n[x].to_numpy(float) for k, x in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}}
    ft, fc = _funding_cum(cfg)
    d1 = TF(resample(df5u, "1D"))
    sw1d = Swings(df5u, "1D")
    table = _level_table(df5u)
    X = pd.read_pickle(ROOT / "results" / "defs_review.pkl")
    X = X[(X["setup"] == "1D bounce") & ~X["eq_highs_ahead"].astype(bool) & ~X["rej_3plus"].astype(bool)].reset_index(drop=True)
    rows = []
    for k, r in X.iterrows():
        et, d, rk = pd.Timestamp(r["entry_time"]), int(r["direction"]), float(r["risk"])
        jt = d1.closed_before(et) - 1                                    # the touch / confirmation candle
        Lv = d1.l[jt] if d > 0 else d1.h[jt]
        st0 = int(np.searchsorted(t5, np.datetime64(et)))
        for entry_mode, need in (("E0", 0), ("E2", 1), ("E3", 2)):
            if entry_mode == "E0":
                i0, e, s = st0, ctx["O"][st0], ctx["O"][st0] - d * rk
            else:
                cnt, found, ext = 0, None, (d1.l[jt] if d > 0 else d1.h[jt])
                for jj in range(jt + 1, min(d1.n - 1, jt + 11)):
                    a = d1.a[jj]
                    lo_, cl_ = (d1.l[jj], d1.c[jj]) if d > 0 else (-d1.h[jj], -d1.c[jj])
                    Ln = Lv if d > 0 else -Lv
                    ext = min(ext, d1.l[jj]) if d > 0 else max(ext, d1.h[jj])
                    if cl_ < Ln - a:                                    # closed well through the support: failed
                        break
                    if lo_ <= Ln + 0.25 * a and cl_ >= Ln + 0.25 * a:
                        cnt += 1
                        if cnt >= need:
                            found = jj
                            break
                if found is None:
                    continue
                i0 = int(np.searchsorted(t5, np.datetime64(pd.Timestamp(d1.ct[found]))))   # close time = next open
                if i0 >= len(t5):
                    continue
                e = ctx["O"][i0]
                s = ext * (1 - 0.001) if d > 0 else ext * (1 + 0.001)
                if (e - s) * d <= 0:
                    continue
            risk = abs(e - s)
            end = min(len(t5), i0 + MAX_TF_BARS * 288)
            side = "H" if d > 0 else "L"
            et_i = pd.Timestamp(t5[i0])
            lv = np.array(list(sw1d.untaken(et_i, side)) + list(strong_levels(table, et_i.tz_localize("UTC"))))
            lv = lv[(lv - e) * d >= 1.2 * risk] if len(lv) else lv
            tl = lv[np.argmin((lv - e) * d)] if len(lv) else e + d * 3 * risk
            for tmode, tg in (("T3", e + d * 3 * risk), ("TL", tl)):
                for xm in ("none", "XD"):
                    R, xi, kind = run(ctx, d1, i0, end, d, e, s, tg, xm == "XD")
                    mkt = kind == "daily failure exit"
                    x_t = pd.Timestamp(t5[xi]) + (pd.Timedelta(0) if mkt else FIVE)
                    a_ = np.searchsorted(ft, t5[i0], side="right"); b_ = np.searchsorted(ft, x_t.to_datetime64(), side="left")
                    sp = risk / abs(e)
                    cost = C_MKT + (C_LMT if kind == "target" else C_MKT) + ((fc[b_] - fc[a_]) * d if b_ > a_ else 0.0)
                    rows.append({"sig": k, "entry_time": et, "hold": bool(et >= HOLDOUT), "year": et.year, "entry": entry_mode,
                                 "target": tmode, "exit": xm, "net": R - cost / sp, "kind": kind, "stop_pct": sp,
                                 "rr": abs(tg - e) / risk, "decision_time": et_i, "exit_time": x_t, "direction": d})
    R_ = pd.DataFrame(rows)
    R_.to_pickle(ROOT / "results" / "bounce_fix.pkl")
    res_ok = ~R_["hold"] & (R_["exit_time"] < HOLDOUT)
    names = {"E0": "enter as now", "E2": "enter after the 2nd rejection close", "E3": "enter after the 3rd rejection close",
             "T3": "3R target", "TL": "target at the first liquidity >= 1.2R", "none": "no failure exit", "XD": "daily failure exit"}
    tab = []
    for em, tm, xm in itertools.product(("E0", "E2", "E3"), ("T3", "TL"), ("none", "XD")):
        m = (R_["entry"] == em) & (R_["target"] == tm) & (R_["exit"] == xm)
        r_, h_ = R_[m & res_ok], R_[m & R_["hold"]]
        yrs = sum(1 for y in (2022, 2023, 2024, 2025) if r_.loc[r_["year"] == y, "net"].mean() > 0)
        tsc = r_["net"].mean() / (r_["net"].std(ddof=1) / math.sqrt(len(r_))) if len(r_) > 2 and r_["net"].std() > 0 else 0
        tab.append({"rule": f"{names[em]} · {names[tm]} · {names[xm]}", "n_r": len(r_), "w_r": (r_["net"] > 0).mean(),
                    "a_r": r_["net"].mean(), "t": tsc, "years": yrs, "n_h": len(h_),
                    "w_h": (h_["net"] > 0).mean() if len(h_) else math.nan, "a_h": h_["net"].mean() if len(h_) else math.nan,
                    "rr": R_.loc[m, "rr"].mean()})
    T = pd.DataFrame(tab).sort_values("t", ascending=False)
    ok = T[(T["n_r"] >= 25) & (T["years"] >= 3)]
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    L = ["# 1D bounces: enter on repeated failure to go down, exit on repeated failure to go up", "",
         f"{X.shape[0]} v3.1 1D bounces passing the journal filters. **win % = profit after costs.** Chosen on 2022 - Oct 2025; "
         "the holdout (Nov 2025 on) is the honest check.", "",
         f"Chosen (best 2022-25 t-score, >= 25 trades, >= 3 good years): **{ok.iloc[0]['rule'] if len(ok) else 'nothing qualified'}**", "",
         _table(T, [("rule", "entry · target · exit", str), ("n_r", "trades 2022-25", str), ("w_r", "win %", _pct),
                    ("a_r", "avg R", f2), ("t", "t-score", lambda v: f"{v:.2f}"), ("years", "good years /4", str),
                    ("n_h", "holdout trades", str), ("w_h", "holdout win %", _pct), ("a_h", "holdout avg R", f2),
                    ("rr", "avg reward:risk", lambda v: f"{v:.2f}")]), ""]
    path = out_dir / "bounce_fix.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
