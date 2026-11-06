"""
Machine learning on the journal's precise inputs (docs/trading_definitions.md), for every main-rule signal.

Signals: all main-rule candidates on 2h / 4h / 1D since 2020 (results/two_layer_candidates.pkl, ~16,600), one per
candle and direction (the highest-priority event kept).
Two ways to enter each signal (both labelled on 5m candles, 2 : 1 from the signal's own stop, costs + funding):
  now        market at the signal
  confirm4h  the trader's lesson: wait for the first 4h close after the signal; enter at the next open only if that
             close is beyond the signal price; same stop and target PRICES; skipped if stop / target was hit first or the
             reward:risk left is under 1.2
Inputs (known at the entry moment): journal patterns with the precise detectors, liquidity map, main-rule context,
then indicators. Walk-forward by year (train on signals decided >= 62 days before the test year), holdout last.
The decision: take the trade when the model's chance of a win is above the cut-off chosen on the training years.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..study.concepts import Bars
from ..study.defs import TF, equal_levels, failed_pushes, rejections
from ..study.indicators import atr, bollinger, ema, macd
from ..study.levels import _level_table, strong_levels
from ..study.mtf import resample
from ..study.sr2_run import _pct, _table
from .targets import C_LMT, C_MKT, LIMIT_BUFFER, _funding_cum, account, liquidity_map, stats

HOLDOUT = pd.Timestamp("2025-11-01")
GAP = pd.Timedelta(days=62)
YEARS = [2022, 2023, 2024, 2025]
FIVE = pd.Timedelta(minutes=5)
MAX_TF_BARS = 60
T_R = 2.0
PRIO = {"zone_break": 0, "range_break": 1, "liq_run": 2, "bos": 3, "tl_break": 4, "choch": 5, "zone_bounce": 6,
        "level_test_bounce": 7, "liq_sweep": 8, "tl_bounce": 9}


# ----------------------------------------------------------------------------- labels
def _replay(O, H, L, C, i0, end, d, e, s, tg):
    o, h, l, c = (O, H, L, C) if d > 0 else (-O, -L, -H, -C)
    e, s, tg = (e, s, tg) if d > 0 else (-e, -s, -tg)
    risk = e - s
    buf = LIMIT_BUFFER * abs(e)
    for i in range(i0, end):
        if i > i0 and o[i] <= s:
            return (o[i] - e) / risk, i, "stop"
        if l[i] <= s:
            return (s - e) / risk, i, "stop"
        if h[i] >= tg + buf:
            return (tg - e) / risk, i, "target"
    return (c[end - 1] - e) / risk, end - 1, "time"


def label(cand: pd.DataFrame, df5n: pd.DataFrame, fund, b4t: np.ndarray, b4c: np.ndarray) -> pd.DataFrame:
    t5 = df5n["open_time"].to_numpy()
    O, H, L, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    ft, fc = fund
    rows = []
    for dt, tf, d, rk in zip(cand["decision_time"], cand["tf"], cand["direction"], cand["risk"]):
        out = {}
        st = int(np.searchsorted(t5, np.datetime64(dt)))
        bpt = int(pd.Timedelta(tf) / FIVE)
        if st >= len(t5) or t5[st] != np.datetime64(dt) or st + MAX_TF_BARS * bpt + 48 * 12 > len(O) or rk <= 0:
            rows.append({"ok": False}); continue
        e = O[st]; s = e - d * rk; tg = e + d * T_R * rk
        for mode in ("now", "confirm4h"):
            i0, ent = st, e
            if mode == "confirm4h":
                j = int(np.searchsorted(b4t + np.timedelta64(4, "h"), np.datetime64(dt), side="right"))
                close_t = b4t[j] + np.timedelta64(4, "h")
                i0 = int(np.searchsorted(t5, close_t))
                if (b4c[j] - e) * d <= 0:
                    out[f"ok_{mode}"] = False; continue                      # not confirmed: no trade
                seg_l = (L[st:i0] <= s) if d > 0 else (H[st:i0] >= s)
                seg_t = (H[st:i0] >= tg) if d > 0 else (L[st:i0] <= tg)
                if seg_l.any() or seg_t.any():
                    out[f"ok_{mode}"] = False; continue
                ent = O[i0]
                if (ent - s) * d <= 0 or (tg - ent) * d / ((ent - s) * d) < 1.2:
                    out[f"ok_{mode}"] = False; continue
            end = i0 + MAX_TF_BARS * bpt
            R, xi, kind = _replay(O, H, L, C, i0, end, d, ent, s, tg)
            risk = abs(ent - s)
            sp = risk / abs(ent)
            xt = pd.Timestamp(t5[xi]) + FIVE
            a_ = np.searchsorted(ft, t5[i0], side="right"); b_ = np.searchsorted(ft, xt.to_datetime64(), side="left")
            cost = C_MKT + (C_LMT if kind == "target" else C_MKT) + ((fc[b_] - fc[a_]) * d if b_ > a_ else 0.0)
            out.update({f"ok_{mode}": True, f"net_{mode}": R - cost / sp, f"exit_{mode}": xt, f"sp_{mode}": sp,
                        f"entry_t_{mode}": pd.Timestamp(t5[i0])})
        out["ok"] = True
        rows.append(out)
    return pd.DataFrame(rows, index=cand.index)


# ----------------------------------------------------------------------------- journal features (entry-time)
def journal_features(cand: pd.DataFrame, df5u: pd.DataFrame) -> pd.DataFrame:
    tf = {k: TF(resample(df5u, r)) for k, r in (("15m", "15min"), ("1h", "1h"), ("4h", "4h"))}
    b1 = tf["1h"]
    m1 = macd(pd.Series(b1.c))[0].to_numpy()
    d1 = resample(df5u, "1D")
    d1ct = pd.to_datetime(d1["close_time"], utc=True).dt.tz_convert(None).to_numpy()
    d1e200 = ema(d1["close"], 200).to_numpy(); d1atr = atr(d1, 14).to_numpy()
    d1o, d1c = d1["open"].to_numpy(float), d1["close"].to_numpy(float)
    rsi1 = Bars(resample(df5u, "1h")).r
    table = _level_table(df5u)
    rows = []
    for dt, d, e, rk in zip(cand["decision_time"], cand["direction"], cand["entry"], cand["risk"]):
        d = int(d); s, tg = e - d * rk, e + d * T_R * rk
        hi_side, lo_side = ("H", "L") if d > 0 else ("L", "H")
        f = {}
        n1 = b1.closed_before(dt); j = n1 - 1
        f["j_stretched"] = float(((rsi1[j] > 70) and (b1.c[j] > b1.up[j])) if d > 0 else ((rsi1[j] < 30) and (b1.c[j] < b1.lo[j])))
        pts = [(i, p) for i, p, cf in (b1.sh if d > 0 else b1.sl) if cf < n1]
        k = j - 8 + int(np.argmax(b1.h[j - 8:j + 1] if d > 0 else -b1.l[j - 8:j + 1]))
        ext = b1.h[k] if d > 0 else b1.l[k]
        f["j_macd_div"] = float(bool(pts) and (ext - pts[-1][1]) * d > 0 and (m1[k] - m1[pts[-1][0]]) * d < 0)
        kd = int(np.searchsorted(d1ct, np.datetime64(dt), side="right")) - 1
        f["j_daily_against"] = float((d1c[kd] - d1e200[kd]) * d < 0)
        f["j_ema200_in_way"] = float((d1e200[kd] - e) * d > 0 and (tg - d1e200[kd]) * d > 0)
        f["j_vertical_day"] = float((d1c[kd] - d1o[kd]) * d > 2 * d1atr[kd])
        t4 = tf["4h"]; n4 = t4.closed_before(dt)
        lows4 = [p for i, p, cf in (t4.sh if d > 0 else t4.sl) if cf < n4][-3:]
        f["j_falling_highs"] = float(len(lows4) == 3 and ((lows4[0] > lows4[1] > lows4[2]) if d > 0 else (lows4[0] < lows4[1] < lows4[2])))
        z = strong_levels(table, pd.Timestamp(dt).tz_localize("UTC"))
        sw = [p for i, p, cf in (t4.sh if d > 0 else t4.sl) if cf < n4 and i >= n4 - 150
              and ((t4.h[i + 1:n4].max() <= p) if d > 0 else (t4.l[i + 1:n4].min() >= p))]
        lv = np.array(list(z) + sw)
        ahead = lv[((lv - e) * d > 0) & ((tg - lv) * d > 0)] if len(lv) else np.array([])
        if len(ahead):
            ceil = ahead[np.argmin((ahead - e) * d)]
            side = "R" if d > 0 else "S"
            rej = rejections(t4, ceil, side, n4 - 30, n4)
            fp = failed_pushes(t4, ceil, side, (rej[-1] + 1) if rej else n4, n4)
            f["j_rejections"] = float(len(rej)); f["j_failed_pushes"] = float(len(fp))
            f["j_ceiling_dist_r"] = float((ceil - e) * d / rk)
        else:
            f["j_rejections"] = f["j_failed_pushes"] = 0.0; f["j_ceiling_dist_r"] = 20.0
        top = [x for kk in ("1h", "4h") for x in equal_levels(tf[kk], hi_side, tf[kk].closed_before(dt))
               if x.taken_at < 0 and (x.price - e) * d > 0 and (tg - x.price) * d >= 0]
        f["j_dtop_in_way"] = float(len(top) > 0)
        f["j_dtop_in_way_n"] = float(max((len(x.idx) for x in top), default=0))
        pool = [x for kk in ("15m", "1h") for x in equal_levels(tf[kk], lo_side, tf[kk].closed_before(dt))
                if x.taken_at < 0 and 0 < (s - x.price) * d <= 0.5 * rk]
        f["j_eqlows_at_stop"] = float(len(pool) > 0)
        inside = [x for kk in ("15m", "1h") for x in equal_levels(tf[kk], lo_side, tf[kk].closed_before(dt))
                  if x.taken_at < 0 and (e - x.price) * d > 0 and (x.price - s) * d > 0]
        f["j_eqlows_in_risk"] = float(len(inside) > 0)
        rows.append(f)
    return pd.DataFrame(rows, index=cand.index)


# ----------------------------------------------------------------------------- model
PARAMS = dict(objective="binary", learning_rate=0.03, num_leaves=15, min_data_in_leaf=120, feature_fraction=0.6,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, seed=3)


def feature_cols(df):
    j = [c for c in df.columns if c.startswith("j_")]
    lq = [c for c in df.columns if c.startswith("lq_")]
    ctx = [c for c in df.columns if c.startswith(("st_", "brk_", "pat_", "ev_", "zone_", "liq_", "pool_"))
           or c in ("at_zone", "wtrend", "vol_regime", "test_n", "prev_failed_breaks", "tl_touches")]
    setup = [c for c in df.columns if c.startswith("is_")] + ["x_stop_pct"]
    ind = [c for c in df.columns if c.startswith(("m_", "n_"))]
    return j + lq + ctx + setup + ind


def fit_predict(train, test, cols, ycol):
    import lightgbm as lgb
    m = lgb.train(PARAMS, lgb.Dataset(train[cols].to_numpy(float), train[ycol].to_numpy()), num_boost_round=300)
    return m.predict(test[cols].to_numpy(float)), m


def oof_cut(train, cols, ycol, ncol):
    """Cut-off chosen inside the training data (4 time folds): the probability cut that maximises avg R x trades^0.5."""
    import lightgbm as lgb
    tr = train.sort_values("decision_time")
    folds = np.array_split(np.arange(len(tr)), 4)
    p = np.full(len(tr), np.nan)
    for k in range(1, 4):
        a = np.concatenate(folds[:k]); b = folds[k]
        m = lgb.train(PARAMS, lgb.Dataset(tr.iloc[a][cols].to_numpy(float), tr.iloc[a][ycol].to_numpy()), num_boost_round=300)
        p[b] = m.predict(tr.iloc[b][cols].to_numpy(float))
    ok = ~np.isnan(p)
    best, cut = -1e9, 0.5
    for q in (0.4, 0.5, 0.6, 0.7, 0.8):
        c_ = np.quantile(p[ok], q)
        sel = ok & (p >= c_)
        if sel.sum() < 50:
            continue
        sc = tr[ncol].to_numpy()[sel].mean() * math.sqrt(sel.sum())
        if sc > best:
            best, cut = sc, c_
    return cut


def run_journal_ml(cfg: Config, out_dir: Path, rebuild: bool = False) -> Path:
    cache = ROOT / "results" / "journal_ml_table.pkl"
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    if cache.exists() and not rebuild:
        X = pd.read_pickle(cache)
    else:
        df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
        c = pd.read_pickle(ROOT / "results" / "two_layer_candidates.pkl"); c.attrs = {}
        c["prio"] = c["event"].map(PRIO).fillna(9)
        c = c.sort_values(["decision_time", "direction", "prio"]).drop_duplicates(["decision_time", "direction"])
        c = c[c["risk"] > 0].reset_index(drop=True)
        print("signals", len(c), flush=True)
        b4 = resample(df5u, "4h")
        b4t = pd.to_datetime(b4["open_time"], utc=True).dt.tz_convert(None).to_numpy()
        lab = label(c, df5n, _funding_cum(cfg), b4t, b4["close"].to_numpy(float))
        print("labelled", flush=True)
        jf = journal_features(c, df5u)
        print("journal features", flush=True)
        lm = liquidity_map(c, df5u)
        X = pd.concat([c.drop(columns=[x for x in lab.columns.union(jf.columns).union(lm.columns) if x in c.columns]),
                       lab, jf, lm], axis=1)
        X = X[X["ok"].fillna(False).astype(bool)].reset_index(drop=True)
        X["x_stop_pct"] = X["risk"] / X["entry"]
        X.to_pickle(cache)
    X["hold"] = X["decision_time"] >= HOLDOUT
    cols = feature_cols(X)
    res_rows, picks = [], []
    for mode in ("now", "confirm4h"):
        D = X[X[f"ok_{mode}"].fillna(False).astype(bool)].copy()
        D["y"] = (D[f"net_{mode}"] > 0).astype(int)
        D["net"], D["exit_time"], D["stop_pct"] = D[f"net_{mode}"], D[f"exit_{mode}"], D[f"sp_{mode}"]
        D["decision_time_e"] = D[f"entry_t_{mode}"]
        for per, start, end in [(str(y), pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y + 1}-01-01")) for y in YEARS] + \
                               [("holdout", HOLDOUT, pd.Timestamp("2100-01-01"))]:
            tr = D[(D["exit_time"] < start - pd.Timedelta(days=1)) & (D["decision_time"] < min(start, HOLDOUT) - GAP)]
            te = D[(D["decision_time"] >= start) & (D["decision_time"] < end)]
            if per != "holdout":
                te = te[~te["hold"]]
            if len(tr) < 400 or te.empty:
                continue
            p, _ = fit_predict(tr, te, cols, "y")
            cut = oof_cut(tr, cols, "y", "net")
            te = te.assign(p=p, take=p >= cut, mode=mode, period=per)
            picks.append(te)
    P = pd.concat(picks, ignore_index=True)
    P.to_pickle(ROOT / "results" / "journal_ml_scored.pkl")
    # report
    L = ["# Machine learning on the journal's precise inputs", "",
         f"{len(X):,} main-rule signals (2h / 4h / 1D, one per candle and direction). 2 : 1 from the signal's stop, labelled "
         "on 5m candles with costs and funding. Every number is out-of-sample (walk-forward by year; holdout last). "
         "**win % = profit after costs.**", ""]
    rows = []
    wk = lambda per: (52 if per != "holdout" else (P["decision_time"].max() - HOLDOUT).days / 7)  # noqa: E731
    for mode in ("now", "confirm4h"):
        for scope, per_sel in (("2022 - 2025", lambda x: x["period"] != "holdout"), ("holdout", lambda x: x["period"] == "holdout")):
            g = P[(P["mode"] == mode) & per_sel(P)]
            for who, m in (("all signals", pd.Series(True, index=g.index)), ("model takes", g["take"])):
                x = g[m].rename(columns={"decision_time": "dt_sig"}).rename(columns={"decision_time_e": "decision_time"})
                s_ = stats(x["net"].to_numpy())
                eq, mdd = account(x.assign(setup="x").reset_index(drop=True), "net", "exit_time", {"x": 0.02}) if len(x) else (math.nan, math.nan)
                weeks = (4 * 52) if scope != "holdout" else wk("holdout")
                rows.append({"mode": "enter at the signal" if mode == "now" else "wait for the 4h close (your lesson)",
                             "scope": scope, "who": who, **s_, "pw": s_["n"] / weeks, "eq": eq, "mdd": mdd})
    f2 = lambda v: f"{v:+.2f}"  # noqa: E731
    L += ["## Results (2% risk per trade, max 5x, compounding, overlapping positions)", "", _table(pd.DataFrame(rows), [
        ("mode", "entry", str), ("scope", "period", str), ("who", "trades", str), ("n", "n", str),
        ("pw", "per week", lambda v: f"{v:.1f}"), ("win", "win %", _pct), ("avg", "avg R", f2),
        ("pf", "profit factor", lambda v: f"{v:.2f}"), ("eq", "account", lambda v: f"{v:.2f}x"),
        ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    rows = []
    for (mode, per), g in P.groupby(["mode", "period"]):
        a, b = stats(g["net"].to_numpy()), stats(g.loc[g["take"], "net"].to_numpy())
        rows.append({"mode": mode, "per": per, "n": a["n"], "w": a["win"], "a": a["avg"], "nt": b["n"], "wt": b["win"], "at": b["avg"]})
    L += ["## By year (every scored period is shown)", "", _table(pd.DataFrame(rows), [
        ("mode", "entry", str), ("per", "period", str), ("n", "all signals", str), ("w", "win %", _pct), ("a", "avg R", f2),
        ("nt", "model takes", str), ("wt", "win %", _pct), ("at", "avg R", f2)]), ""]
    # which inputs matter (final model on research, gain importance)
    import lightgbm as lgb
    D = X[X["ok_confirm4h"].fillna(False).astype(bool) & ~X["hold"]].copy()
    D["y"] = (D["net_confirm4h"] > 0).astype(int)
    m = lgb.train(PARAMS, lgb.Dataset(D[cols].to_numpy(float), D["y"].to_numpy()), num_boost_round=300)
    imp = pd.Series(m.feature_importance("gain"), index=cols).sort_values(ascending=False)
    imp = (imp / imp.sum()).head(20).reset_index()
    imp.columns = ["input", "share"]
    L += ["## The 20 inputs the model leans on most (confirm-4h model, research data)", "",
          _table(imp, [("input", "input", str), ("share", "share of the model's decisions", _pct)]), ""]
    path = out_dir / "journal_ml.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
