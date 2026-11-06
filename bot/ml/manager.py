"""
Machine-learning trade manager: the trader's failure concepts as MEASUREMENTS, the machine decides how they combine.

Rules cannot be exact (a "3rd rejection" rule breaks when the market does it slightly differently), so instead of hard
rules every 4h close inside an open trade becomes one example. At that close the model sees, all from closed candles:
  trade      open R, best R so far, give-back from the best, distance to target, age, stop size, timeframe
  failures   failure to make a new high on 1h / 4h / 1D (lower high after the peak, close below the pullback low),
             rejections at the trade's top (touch within 0.25 ATR, close back by >= 0.25 ATR), sweeps of the top
             (wick above, close back below), closes below the Bollinger middle since the peak
  context    Bollinger position / band failure, MACD histogram and slope, RSI (4h and 1D), volume of the last pushes,
             untaken swing liquidity and equal highs / lows ahead and behind, trendline through the last two swings,
             EMA 20 / 50 / 200 (1D), 4h structure, the last candle's body
Label: what holding from this close earns versus closing now at the next open (both after costs and funding, in R).
The model predicts that difference; the manager exits at the first 4h close where the prediction is below a margin
chosen inside the training years (out-of-fold, by time). Walk-forward by year, holdout (Nov 2025 on) last.

Training examples: every 4h close in the ~10,700 main-rule signals (entered at the signal, 2 : 1, 60 candles) and in
all v3.1 trades, from earlier years only. Tested on the v3.1 trades after the journal filters.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..study.defs import TF, equal_levels
from ..study.fibliq import Swings, plan as fib_plan
from ..study.indicators import ema, macd, rsi
from ..study.mtf import resample
from ..study.sr2_run import _pct, _table
from .targets import C_LMT, C_MKT, LIMIT_BUFFER, MAX_TF_BARS, _funding_cum, account, stats

HOLDOUT = pd.Timestamp("2025-11-01")
GAP = pd.Timedelta(days=62)
YEARS = [2022, 2023, 2024, 2025]
FIVE = pd.Timedelta(minutes=5)
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
MARGINS = (-1.0, -0.75, -0.5, -0.35, -0.25, -0.15, -0.05)
PARAMS = dict(objective="regression", learning_rate=0.03, num_leaves=15, min_data_in_leaf=300, feature_fraction=0.7,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, seed=7)
ROUNDS = 300


# ----------------------------------------------------------------------------- per-candle context (both sides)
def _sw(pts):
    a = np.array([(i, p, cf) for i, p, cf in pts], dtype=float).reshape(-1, 3)
    return a[:, 0].astype(int), a[:, 1], a[:, 2].astype(int)


def _untaken(t: TF, sw, j, above: bool):
    """Nearest untaken swing (confirmed by candle j) beyond the close of j, distance in ATR; 20 if none."""
    ii, pp, cf = sw
    k1 = int(np.searchsorted(cf, j, side="right"))
    k0 = int(np.searchsorted(ii, j - 150, side="left"))
    best = 20.0
    for k in range(k0, k1):
        i, p = ii[k], pp[k]
        if above:
            if p <= t.c[j] or t.h[i + 1:j + 1].max(initial=-np.inf) > p:
                continue
            best = min(best, (p - t.c[j]) / t.a[j])
        else:
            if p >= t.c[j] or t.l[i + 1:j + 1].min(initial=np.inf) < p:
                continue
            best = min(best, (t.c[j] - p) / t.a[j])
    return best


def _trendline(t: TF, sw, j):
    """Line through the last two swings confirmed by j: (distance of the close from it in ATR, touches of the last 6)."""
    ii, pp, cf = sw
    k1 = int(np.searchsorted(cf, j, side="right"))
    if k1 < 2:
        return 0.0, 0.0
    i1, a1, i2, a2 = ii[k1 - 2], pp[k1 - 2], ii[k1 - 1], pp[k1 - 1]
    sl = (a2 - a1) / (i2 - i1)
    v = a1 + sl * (j - i1)
    touch = sum(1 for k in range(max(0, k1 - 6), k1) if abs(pp[k] - (a1 + sl * (ii[k] - i1))) <= 0.25 * t.a[ii[k]])
    return (t.c[j] - v) / t.a[j], float(touch)


def context_table(t: TF, daily: bool = False) -> dict:
    """Arrays indexed by candle: values for longs ('L') and mirrored for shorts ('S')."""
    n = t.n
    c = pd.Series(t.c)
    m_line, m_sig = (x.to_numpy(float) for x in macd(c))
    m_hist = m_line - m_sig
    r = rsi(c).to_numpy(float)
    out = {k: np.full(n, np.nan) for k in (
        "upliq", "dnliq", "eqH", "eqL", "tl_lo", "tl_lo_n", "tl_hi", "tl_hi_n", "bfU", "bfL", "struct")}
    swh, swl = _sw(t.sh), _sw(t.sl)
    for j in range(30, n):
        if not np.isfinite(t.a[j]) or t.a[j] <= 0:
            continue
        out["upliq"][j] = _untaken(t, swh, j, True)
        out["dnliq"][j] = _untaken(t, swl, j, False)
        if not daily:
            eh = [x.price for x in equal_levels(t, "H", j + 1) if x.taken_at < 0 and x.price > t.c[j]]
            el = [x.price for x in equal_levels(t, "L", j + 1) if x.taken_at < 0 and x.price < t.c[j]]
            out["eqH"][j] = (min(eh) - t.c[j]) / t.a[j] if eh else 20.0
            out["eqL"][j] = (t.c[j] - max(el)) / t.a[j] if el else 20.0
        out["tl_lo"][j], out["tl_lo_n"][j] = _trendline(t, swl, j)
        d_hi, out["tl_hi_n"][j] = _trendline(t, swh, j)
        out["tl_hi"][j] = -d_hi
        k0 = max(0, j - 3)
        out["bfU"][j] = float(t.c[j] < t.up[j] and (t.c[k0:j] > t.up[k0:j]).any())
        out["bfL"][j] = float(t.c[j] > t.lo[j] and (t.c[k0:j] < t.lo[k0:j]).any())
        kh, kl = int(np.searchsorted(swh[2], j, side="right")), int(np.searchsorted(swl[2], j, side="right"))
        sh, sl = swh[1][max(0, kh - 2):kh], swl[1][max(0, kl - 2):kl]
        out["struct"][j] = (1.0 if len(sh) == 2 and len(sl) == 2 and sh[1] > sh[0] and sl[1] > sl[0] else
                            -1.0 if len(sh) == 2 and len(sl) == 2 and sh[1] < sh[0] and sl[1] < sl[0] else 0.0)
    a = t.a
    bbw = np.where(t.up - t.mid > 0, t.up - t.mid, np.nan)
    vol3 = pd.Series(t.v).rolling(3).mean().to_numpy()
    vol20 = pd.Series(t.v).shift(3).rolling(20).mean().to_numpy()
    rng = np.where(t.h - t.l > 0, t.h - t.l, np.nan)
    e20, e50, e200 = (ema(c, k).to_numpy(float) for k in (20, 50, 200))
    L = {"bb": (t.c - t.mid) / bbw, "bf_top": out["bfU"], "bf_bot": out["bfL"], "macd_h": m_hist / a,
         "macd_slope": (m_hist - np.r_[np.full(3, np.nan), m_hist[:-3]]) / a, "macd_line": m_line / a, "rsi": r,
         "vol": vol3 / vol20, "liq_ahead": out["upliq"], "liq_behind": out["dnliq"], "eq_ahead": out["eqH"],
         "eq_behind": out["eqL"], "tl_support": out["tl_lo"], "tl_support_n": out["tl_lo_n"], "tl_ceiling": out["tl_hi"],
         "tl_ceiling_n": out["tl_hi_n"], "struct": out["struct"], "body": (t.c - t.o) / a, "close_pos": (t.c - t.l) / rng,
         "e20": (t.c - e20) / a, "e50": (t.c - e50) / a, "e200": (t.c - e200) / a}
    S = {"bb": -L["bb"], "bf_top": out["bfL"], "bf_bot": out["bfU"], "macd_h": -L["macd_h"], "macd_slope": -L["macd_slope"],
         "macd_line": -L["macd_line"], "rsi": 100 - r, "vol": L["vol"], "liq_ahead": out["dnliq"], "liq_behind": out["upliq"],
         "eq_ahead": out["eqL"], "eq_behind": out["eqH"], "tl_support": out["tl_hi"], "tl_support_n": out["tl_hi_n"],
         "tl_ceiling": out["tl_lo"], "tl_ceiling_n": out["tl_lo_n"], "struct": -out["struct"], "body": -L["body"],
         "close_pos": 1 - L["close_pos"], "e20": -L["e20"], "e50": -L["e50"], "e200": -L["e200"]}
    return {1: L, -1: S}


# ----------------------------------------------------------------------------- one trade, every 4h close
class FailState:
    """Failure to make a new high, on closed candles of one timeframe (oriented: longs; shorts are mirrored)."""

    def __init__(self):
        self.peak, self.pull, self.lh, self.n_lh, self.fail, self.since_peak = -np.inf, np.inf, False, 0, False, 0

    def step(self, h, l, c):
        if h > self.peak:
            self.peak, self.pull, self.lh, self.n_lh, self.fail, self.since_peak = h, np.inf, False, 0, False, 0
            return False
        self.since_peak += 1
        if np.isfinite(self.pull) and self.pull < h < self.peak:
            self.lh = True
            self.n_lh += 1
        hit = self.lh and c < self.pull
        self.fail = self.fail or hit
        self.pull = min(self.pull, l)
        return hit


def trade_states(M, tr: dict) -> tuple[list[dict], dict]:
    """Replay one trade on 5m candles (stop first inside a candle) and build one example per 4h close while open."""
    O, H, L_, C, t5 = M["O"], M["H"], M["L"], M["C"], M["t5"]
    d, e, s, tg, i0, end = tr["d"], tr["e"], tr["s"], tr["tg"], tr["i0"], tr["end"]
    o, h, l, c = (O, H, L_, C) if d > 0 else (-O, -L_, -H, -C)
    e_, s_, tg_ = (e, s, tg) if d > 0 else (-e, -s, -tg)
    risk = e_ - s_
    buf = LIMIT_BUFFER * abs(e)
    seg_s = np.nonzero(l[i0:end] <= s_)[0]
    seg_t = np.nonzero(h[i0:end] >= tg_ + buf)[0]
    xs = i0 + seg_s[0] if len(seg_s) else end
    xt = i0 + seg_t[0] if len(seg_t) else end
    if xs <= xt and xs < end:
        xi, kind = xs, "stop"
        R = ((o[xi] - e_) if (xi > i0 and o[xi] <= s_) else (s_ - e_)) / risk
    elif xt < end:
        xi, kind, R = xt, "target", (tg_ - e_) / risk
    else:
        xi, kind, R = end - 1, "time", (c[end - 1] - e_) / risk
    ft, fc = M["fund"]
    sp = risk / abs(e)
    a_ = np.searchsorted(ft, t5[i0], side="right")

    def fund(t_end):
        b_ = np.searchsorted(ft, t_end, side="left")
        return (fc[b_] - fc[a_]) * d if b_ > a_ else 0.0

    x_time = t5[xi] + np.timedelta64(5, "m")
    final = R - (C_MKT + (C_LMT if kind == "target" else C_MKT) + fund(x_time)) / sp
    res = {"net": final, "kind": kind, "xi": xi, "exit_time": pd.Timestamp(x_time), "sp": sp}
    # 4h closes strictly after the entry and while the trade is open (the exit candle may start at that close)
    t4, t1, tD = M["tf"]["4h"], M["tf"]["1h"], M["tf"]["1D"]
    et = t5[i0]
    j4a = int(np.searchsorted(t4.ct, et, side="right"))
    j4b = int(np.searchsorted(t4.ct, t5[min(xi, end - 1)], side="right"))
    states = []
    if j4a >= j4b:
        return states, res
    run_hi = np.maximum.accumulate(h[i0:xi + 1])
    run_lo = np.minimum.accumulate(l[i0:xi + 1])
    fs = {"1h": FailState(), "4h": FailState(), "1D": FailState()}
    nxt = {"1h": int(np.searchsorted(t1.ct, et, side="right")), "1D": int(np.searchsorted(tD.ct, et, side="right"))}
    H4 = t4.h if d > 0 else -t4.l
    L4 = t4.l if d > 0 else -t4.h
    C4 = t4.c if d > 0 else -t4.c
    MID4 = t4.mid if d > 0 else -t4.mid
    peak4, rej4, swp4, below_mid, fail1_block = -np.inf, 0, 0, 0, 0
    rej1, swp1, peak1 = 0, 0, -np.inf
    cx4, cxD = M["ctx"]["4h"][d], M["ctx"]["1D"][d]
    for j in range(j4a, j4b):
        T = t4.ct[j]
        iT = int(np.searchsorted(t5, T))
        if iT > xi or iT >= end:
            break
        # 1h candles closed up to T
        fail1_block = 0
        H1 = t1.h if d > 0 else -t1.l
        L1 = t1.l if d > 0 else -t1.h
        C1 = t1.c if d > 0 else -t1.c
        while nxt["1h"] < t1.n and t1.ct[nxt["1h"]] <= T:
            k = nxt["1h"]; a1 = t1.a[k]
            if np.isfinite(peak1):
                if H1[k] >= peak1 - 0.25 * a1 and C1[k] <= peak1 - 0.25 * a1:
                    rej1 += 1
                if H1[k] > peak1 and C1[k] < peak1:
                    swp1 += 1
            peak1 = max(peak1, H1[k])
            fail1_block += int(fs["1h"].step(H1[k], L1[k], C1[k]))
            nxt["1h"] += 1
        while nxt["1D"] < tD.n and tD.ct[nxt["1D"]] <= T:
            k = nxt["1D"]
            fs["1D"].step(*(((tD.h[k], tD.l[k], tD.c[k])) if d > 0 else (-tD.l[k], -tD.h[k], -tD.c[k])))
            nxt["1D"] += 1
        a4 = t4.a[j]
        if np.isfinite(peak4):
            if H4[j] >= peak4 - 0.25 * a4 and C4[j] <= peak4 - 0.25 * a4:
                rej4 += 1
            if H4[j] > peak4 and C4[j] < peak4:
                swp4 += 1
        new_peak = H4[j] > peak4
        peak4 = max(peak4, H4[j])
        fail4 = fs["4h"].step(H4[j], L4[j], C4[j])
        below_mid = 0 if new_peak else below_mid + int(C4[j] < MID4[j])
        # value of closing now: market at the next open (= this close time)
        r_now = (C4[j] - e_) / risk
        x_now = (o[iT] - e_) / risk - (2 * C_MKT + fund(T)) / sp
        mfe = (run_hi[iT - 1 - i0] - e_) / risk
        mae = (run_lo[iT - 1 - i0] - e_) / risk
        jd = int(np.searchsorted(tD.ct, T, side="right")) - 1
        f = {"r_now": r_now, "mfe": mfe, "mae": mae, "giveback": mfe - r_now, "to_target": (tg_ - C4[j]) / risk,
             "target_r": (tg_ - e_) / risk, "age": len(states) + 1, "stop_pct": sp, "tf_h": tr["tf_h"],
             "lh_1h": float(fs["1h"].lh), "fail_1h_now": float(fail1_block > 0), "fail_1h": float(fs["1h"].fail),
             "nlh_1h": fs["1h"].n_lh, "lh_4h": float(fs["4h"].lh), "fail_4h_now": float(fail4), "fail_4h": float(fs["4h"].fail),
             "nlh_4h": fs["4h"].n_lh, "since_peak_4h": fs["4h"].since_peak, "lh_1d": float(fs["1D"].lh),
             "fail_1d": float(fs["1D"].fail), "rej_top_4h": rej4, "sweep_top_4h": swp4, "rej_top_1h": rej1,
             "sweep_top_1h": swp1, "below_mid_4h": below_mid}
        f.update({f"c4_{k}": v[j] for k, v in cx4.items()})
        if jd >= 0:
            f.update({f"cd_{k}": v[jd] for k, v in cxD.items()})
        f.update({"x_now": x_now, "y": final - x_now, "iT": iT, "T": pd.Timestamp(T)})
        states.append(f)
    return states, res


def simulate(states: pd.DataFrame, pred: np.ndarray, margin: float, final: float):
    """Exit at the first 4h close whose predicted gain from holding is below the margin."""
    hit = np.nonzero(pred < margin)[0]
    if len(hit):
        k = hit[0]
        return float(states["x_now"].iloc[k]), k
    return final, -1


# ----------------------------------------------------------------------------- trade lists
def pool_trades(M) -> list[dict]:
    X = pd.read_pickle(ROOT / "results" / "journal_ml_table.pkl")
    t5 = M["t5"]
    out = []
    for dt, tf, d, rk in zip(X["decision_time"], X["tf"], X["direction"], X["risk"]):
        st = int(np.searchsorted(t5, np.datetime64(dt)))
        bpt = int(pd.Timedelta(tf) / FIVE)
        if st >= len(t5) or t5[st] != np.datetime64(dt) or st + MAX_TF_BARS * bpt > len(t5) or rk <= 0:
            continue
        e = M["O"][st]
        out.append({"src": "pool", "d": int(d), "e": e, "s": e - d * rk, "tg": e + d * 2.0 * rk, "i0": st,
                    "end": st + MAX_TF_BARS * bpt, "tf_h": bpt / 12, "decision_time": pd.Timestamp(dt), "setup": "pool"})
    return out


def v31_trades(M, df5u) -> list[dict]:
    """v3.1 trades exactly as in bot/study/fixes.py: base (entry at the signal) and S786 (bounce stop below 0.786)."""
    X = pd.read_pickle(ROOT / "results" / "defs_review.pkl").reset_index(drop=True)
    t5 = M["t5"]
    swf = {k_: Swings(df5u, r_) for k_, r_ in (("15m", "15min"), ("1h", "1h"), ("4h", "4h"), ("1D", "1D"))}
    out = []
    for k, r in X.iterrows():
        et, d, e, rk = pd.Timestamp(r["entry_time"]), int(r["direction"]), float(r["px"]), float(r["risk"])
        st = int(np.searchsorted(t5, np.datetime64(et)))
        bpt = int(pd.Timedelta(r["tf"]) / FIVE)
        end = min(len(t5), st + MAX_TF_BARS * bpt)
        filt = not bool(r["eq_highs_ahead"]) and not bool(r["rej_3plus"])
        base = {"src": "v31", "sig": k, "setup": r["setup"], "filtered": filt, "hold": bool(r["hold"]), "d": d,
                "i0": st, "end": end, "tf_h": bpt / 12, "decision_time": pd.Timestamp(t5[st]), "entry_time": et}
        out.append({**base, "variant": "base", "e": e, "s": e - d * rk, "tg": e + d * TGT[r["setup"]] * rk})
        fp = fib_plan(r, swf)
        if fp is None:
            continue
        e0 = M["O"][st]
        s = e - d * rk
        s_f = fp["f786"] - d * 0.001 * e0 if r["setup"] == "1D bounce" else None
        if s_f is not None and (e0 - s_f) * d <= 0:
            s_f = None
        s2 = s_f if s_f is not None else s
        tg2 = e0 + d * TGT[r["setup"]] * abs(e0 - s2)
        if (tg2 - e0) * d / abs(e0 - s2) < 1.2:
            tg2 = e0 + d * 1.2 * abs(e0 - s2)
        out.append({**base, "variant": "S786", "e": e0, "s": s2, "tg": tg2})
    return out


def break_quality(t: TF, et) -> bool:
    j = t.closed_before(et) - 1
    rng = t.h[j] - t.l[j]
    vavg = t.v[max(0, j - 20):j].mean()
    return rng > 0 and abs(t.c[j] - t.o[j]) >= 0.6 * rng and rng >= 1.5 * t.a[j] and t.v[j] >= 1.2 * vavg


# ----------------------------------------------------------------------------- model
def _fit(S: pd.DataFrame, cols):
    import lightgbm as lgb
    y = S["y"].clip(-4, 4).to_numpy()
    return lgb.train(PARAMS, lgb.Dataset(S[cols].to_numpy(float), y, weight=S["w"].to_numpy()), num_boost_round=ROUNDS)


def _choose_margin(S: pd.DataFrame, T: pd.DataFrame, cols) -> float:
    """Out-of-fold by time inside the training data: the margin that gives the best average trade R."""
    tids = T.sort_values("decision_time")["tid"].to_numpy()
    folds = np.array_split(tids, 4)
    gains = {m: [] for m in MARGINS}
    for k in range(1, 4):
        tr_ids, te_ids = np.concatenate(folds[:k]), folds[k]
        lim = T.set_index("tid").loc[te_ids, "decision_time"].min() - GAP
        tr_ok = T[T["tid"].isin(tr_ids) & (T["exit_time"] < lim)]["tid"]
        Str = S[S["tid"].isin(tr_ok)]
        if len(Str) < 2000:
            continue
        mdl = _fit(Str, cols)
        Ste = S[S["tid"].isin(te_ids)]
        p = mdl.predict(Ste[cols].to_numpy(float))
        Ste = Ste.assign(p=p)
        fin = T.set_index("tid")["net"]
        for tid in te_ids:
            g = Ste[Ste["tid"] == tid]
            for m in MARGINS:
                r_, _ = simulate(g, g["p"].to_numpy(), m, fin[tid]) if len(g) else (fin[tid], -1)
                gains[m].append(r_)
    score = {m: np.mean(v) for m, v in gains.items() if v}
    return max(score, key=score.get) if score else MARGINS[0]


def run_manager(cfg: Config, out_dir: Path, rebuild: bool = False) -> Path:
    cache = ROOT / "results" / "manager_states.pkl"
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    M = {"t5": df5n["open_time"].to_numpy(), "fund": _funding_cum(cfg),
         **{k: df5n[x].to_numpy(float) for k, x in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}}
    M["tf"] = {k: TF(resample(df5u, r)) for k, r in (("1h", "1h"), ("2h", "2h"), ("4h", "4h"), ("1D", "1D"))}
    if cache.exists() and not rebuild:
        T, S = pd.read_pickle(cache)
    else:
        M["ctx"] = {"4h": context_table(M["tf"]["4h"]), "1D": context_table(M["tf"]["1D"], daily=True)}
        print("context tables", flush=True)
        trades = pool_trades(M) + v31_trades(M, df5u)
        print("trades", len(trades), flush=True)
        rows, st_rows = [], []
        for tid, tr in enumerate(trades):
            states, res = trade_states(M, tr)
            rows.append({**{k: v for k, v in tr.items()}, **res, "tid": tid})
            for s_ in states:
                s_["tid"] = tid
            st_rows.extend(states)
            if tid % 2000 == 0:
                print(tid, len(st_rows), flush=True)
        T = pd.DataFrame(rows)
        S = pd.DataFrame(st_rows)
        bq_tf = M["tf"]
        T["BQ"] = [True if (r.src != "v31" or r.setup == "1D bounce") else break_quality(bq_tf[{2: "2h", 4: "4h", 24: "1D"}[int(round(r.tf_h))]], r.entry_time)
                   for r in T.itertuples()]
        pd.to_pickle((T, S), cache)
    n_st = S.groupby("tid").size()
    S["w"] = 1.0 / np.sqrt(S["tid"].map(n_st).to_numpy())
    cols = [c for c in S.columns if c not in ("x_now", "y", "iT", "T", "tid", "w")]
    T["year"] = T["decision_time"].dt.year
    T["is_hold"] = T["decision_time"] >= HOLDOUT
    # walk-forward
    scored = []
    margins = {}
    for per, start, stop in [(str(y), pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y + 1}-01-01")) for y in YEARS] + \
                            [("holdout", HOLDOUT, pd.Timestamp("2100-01-01"))]:
        lim = min(start, HOLDOUT)
        Ttr = T[(T["exit_time"] < lim - pd.Timedelta(days=1)) & (T["decision_time"] < lim - GAP)]
        Str = S[S["tid"].isin(Ttr["tid"])]
        Tte = T[(T["decision_time"] >= start) & (T["decision_time"] < stop)]
        if per != "holdout":
            Tte = Tte[~Tte["is_hold"]]
        mdl = _fit(Str, cols)
        m = _choose_margin(Str, Ttr, cols)
        margins[per] = (m, len(Ttr), len(Str))
        Ste = S[S["tid"].isin(Tte["tid"])]
        Ste = Ste.assign(p=mdl.predict(Ste[cols].to_numpy(float)))
        grp = dict(tuple(Ste.groupby("tid")))
        for r in Tte.itertuples():
            g = grp.get(r.tid)
            if g is None:
                ml, k, xt = r.net, -1, r.exit_time
            else:
                ml, k = simulate(g, g["p"].to_numpy(), m, r.net)
                xt = g["T"].iloc[k] if k >= 0 else r.exit_time
            scored.append({"tid": r.tid, "period": per, "net_ml": ml, "ml_exit": k >= 0, "exit_ml": xt})
        print(per, "margin", m, "train trades", len(Ttr), flush=True)
        if per == "holdout":
            final_model = mdl
    P = T.merge(pd.DataFrame(scored), on="tid")
    P.to_pickle(ROOT / "results" / "manager_scored.pkl")
    return write_report(P, final_model, cols, margins, out_dir)


def write_report(P: pd.DataFrame, mdl, cols, margins, out_dir: Path) -> Path:
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    L = ["# Machine-learning trade manager: your failure concepts as measurements, the machine combines them", "",
         "At every 4h close inside a trade the model predicts what holding earns versus closing now (after costs). "
         "It exits at the first close where holding is predicted to lose more than a margin chosen on earlier years. "
         "Every number below is out-of-sample: each year is managed by a model trained only on earlier years; the "
         "holdout (Nov 2025 on) last. **win % = profit after costs.**", "",
         "Margins chosen per period (exit when predicted gain from holding < margin, in R):", "",
         _table(pd.DataFrame([{"per": k, "m": v[0], "nt": v[1], "ns": v[2]} for k, v in margins.items()]),
                [("per", "period", str), ("m", "margin", lambda v: f"{v:+.2f}"), ("nt", "training trades", str),
                 ("ns", "training 4h closes", str)]), ""]
    groups = [("v3.1 after journal filters, entry at signal, fixed target", (P["src"] == "v31") & P["filtered"] & (P["variant"] == "base")),
              ("v3.1 filtered, bounce stop below 0.786 + strong breaking candle", (P["src"] == "v31") & P["filtered"] & (P["variant"] == "S786") & P["BQ"]),
              ("v3.1 filtered: 1D bounces only (base)", (P["src"] == "v31") & P["filtered"] & (P["variant"] == "base") & (P["setup"] == "1D bounce")),
              ("v3.1 filtered: breakouts only (base)", (P["src"] == "v31") & P["filtered"] & (P["variant"] == "base") & (P["setup"] != "1D bounce")),
              ("all main-rule signals (2 : 1)", P["src"] == "pool")]
    rows = []
    for name, m in groups:
        for scope, sm in (("2022 - Oct 2025", P["period"] != "holdout"), ("holdout", P["period"] == "holdout")):
            g = P[m & sm]
            if g.empty:
                continue
            a, b = stats(g["net"].to_numpy()), stats(g["net_ml"].to_numpy())
            row = {"set": name, "scope": scope, "n": a["n"], "w0": a["win"], "a0": a["avg"], "w1": b["win"], "a1": b["avg"],
                   "ex": g["ml_exit"].mean()}
            if name.startswith("v3.1") and "only" not in name:
                gg = g.assign(stop_pct=g["sp"])
                row["eq0"], row["dd0"] = account(gg.reset_index(drop=True), "net", "exit_time", RISK)
                row["eq1"], row["dd1"] = account(gg.reset_index(drop=True), "net_ml", "exit_ml", RISK)
            rows.append(row)
    R = pd.DataFrame(rows)
    acc = lambda v: "" if v != v else f"{v:.2f}x"  # noqa: E731
    dd = lambda v: "" if v != v else f"-{v:.0%}"  # noqa: E731
    L += ["## Hold to stop / target vs the machine-learning manager", "", _table(R, [
        ("set", "trades", str), ("scope", "period", str), ("n", "n", str), ("w0", "win % (hold)", _pct), ("a0", "avg R (hold)", f2),
        ("w1", "win % (ML manager)", _pct), ("a1", "avg R (ML manager)", f2), ("ex", "closed early by ML", _pct),
        ("eq0", "account (hold)", acc), ("dd0", "worst drop", dd), ("eq1", "account (ML)", acc), ("dd1", "worst drop", dd)]), ""]
    rows = []
    for (per,), g in P[(P["src"] == "v31") & P["filtered"] & (P["variant"] == "base")].groupby(["period"]):
        a, b = stats(g["net"].to_numpy()), stats(g["net_ml"].to_numpy())
        rows.append({"per": per, "n": a["n"], "w0": a["win"], "a0": a["avg"], "w1": b["win"], "a1": b["avg"]})
    L += ["## By year (v3.1 filtered, entry at signal, fixed target)", "", _table(pd.DataFrame(rows), [
        ("per", "period", str), ("n", "trades", str), ("w0", "win % hold", _pct), ("a0", "avg R hold", f2),
        ("w1", "win % ML", _pct), ("a1", "avg R ML", f2)]), ""]
    imp = pd.Series(mdl.feature_importance("gain"), index=cols).sort_values(ascending=False)
    imp = (imp / imp.sum()).head(20).reset_index()
    imp.columns = ["input", "share"]
    L += ["## What the manager leans on most (holdout model)", "",
          _table(imp, [("input", "input", str), ("share", "share of the model's decisions", _pct)]), ""]
    L += diagnose(cols)
    path = out_dir / "manager.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


def diagnose(cols) -> list[str]:
    """Does the model see anything? Train on states of trades that ended before Nov 2023, test on 2024 - Oct 2025."""
    import lightgbm as lgb
    from scipy.stats import spearmanr
    T, S = pd.read_pickle(ROOT / "results" / "manager_states.pkl")
    S = S.merge(T[["tid", "decision_time", "exit_time", "src"]], on="tid")
    S["w"] = 1.0 / np.sqrt(S["tid"].map(S.groupby("tid").size()))
    tr = S[S["exit_time"] < pd.Timestamp("2023-11-01")]
    te = S[(S["decision_time"] >= pd.Timestamp("2024-01-01")) & (S["decision_time"] < HOLDOUT)]
    mdl = lgb.train(PARAMS, lgb.Dataset(tr[cols].to_numpy(float), tr["y"].clip(-4, 4), weight=tr["w"]), ROUNDS)
    p = mdl.predict(te[cols].to_numpy(float))
    te = te.assign(p=p, dec=pd.qcut(p, 10, labels=False) + 1)
    D = te.groupby("dec").agg(pred=("p", "mean"), actual=("y", "mean"), n=("y", "size")).reset_index()
    D["dec"], D["n"] = D["dec"].astype(int), D["n"].astype(int)
    f2 = lambda v: f"{v:+.2f}"  # noqa: E731
    out = ["## Does the model see anything? (trained on trades ended before Nov 2023, tested on 2024 - Oct 2025)", "",
           f"Rank correlation between predicted and actual gain from holding: **{spearmanr(p, te['y'])[0]:+.3f}** "
           f"({len(te):,} 4h closes). If the model saw something, the actual gain would rise from group 1 to group 10.", "",
           _table(D, [("dec", "group (1 = model most wants to exit)", lambda v: f"{int(v)}"),
                      ("pred", "predicted gain from holding", f2), ("actual", "actual gain from holding", f2),
                      ("n", "4h closes", lambda v: f"{int(v):,}")]), ""]
    R = S[S["decision_time"] < HOLDOUT]
    rows = []
    for name, on in (("1h failure (lower high, close below pullback low) on this close", R["fail_1h_now"] > 0),
                     ("1h failure after the trade was +0.5R", (R["fail_1h_now"] > 0) & (R["mfe"] >= 0.5)),
                     ("4h failure on this close", R["fail_4h_now"] > 0),
                     ("daily failure since the peak", R["fail_1d"] > 0),
                     ("3+ 4h rejections at the trade's top", R["rej_top_4h"] >= 3),
                     ("sweep of the top (wick above, close back below), 4h", R["sweep_top_4h"] > 0),
                     ("v3.1 trades: daily failure since the peak", (R["src"] == "v31") & (R["fail_1d"] > 0))):
        rows.append({"sig": name, "n": int(on.sum()), "on": R.loc[on, "y"].mean(),
                     "off": R.loc[~on & ((R["src"] == "v31") if name.startswith("v3.1") else True), "y"].mean()})
    out += ["## Your failure signals on their own (2022 - Oct 2025): average gain from HOLDING after the signal", "",
            "Positive = holding on to the stop / target still earned more than closing at that close.", "",
            _table(pd.DataFrame(rows), [("sig", "signal at a 4h close", str), ("n", "4h closes", str),
                                        ("on", "gain from holding when present", f2), ("off", "when absent", f2)]), ""]
    return out


if __name__ == "__main__":
    import sys
    from ..config import load_config
    print(run_manager(load_config(ROOT / "config.yaml"), ROOT / "reports", rebuild="--rebuild" in sys.argv))
