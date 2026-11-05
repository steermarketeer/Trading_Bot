"""
ML profit-taking (Master Plan workstream 2): the target is chosen per trade, never below 1.2:1.

Labels  every main-rule candidate (2h / 4h / 1D, bot/ml/two_layer.load_candidates) and every v3.1 trade is replayed
        on 5m candles: entry = next open (market), stop = the setup's own stop, time limit 60 candles of the trade
        timeframe. For each target in GRID we record the result: target reached (limit exit), stopped first (stop
        wins inside a candle = conservative), or time limit (market exit at the close).
        A limit target counts as filled only if price trades THROUGH it by LIMIT_BUFFER (no fill on a bare touch).
Costs   entry market 0.09% (taker 0.04% + 5 bps slippage); target exit limit 0.02% (maker); stop / time exit 0.09%.
        Funding: actual ETH funding at 00/08/16 UTC for every funding time the position is held over.
Liquidity map (the core inputs): untaken swing highs/lows (1h / 4h / 1D, last 100 candles, not yet traded through)
        and strong S/R zones on the target side, as distances in R: nearest, 2nd, 3rd pool, nearest zone, and how
        many pools lie within 1R / 2R / 3R / 4R; plus liquidity on the stop side (bot/ml/context.py).
Model   one LightGBM per target: P(target reached before the stop). Inputs: liquidity map + main-rule context first,
        then setup / volatility, then indicators. Probabilities forced non-increasing in the target.
        Expected R(T) = p*T + (1-p)*avg R when missed (training data) - costs(T); chosen target = argmax, T >= 1.25.
Walk-forward: test years 2022-2025 use models trained on trades decided >= 62 days before the year (all trades end
        within 60 days); the holdout (Nov 2025 on) uses models trained on research data only.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_funding, load_klines_5m
from ..study.concepts import Bars
from ..study.levels import _level_table, strong_levels
from ..study.mtf import resample
from ..study.sr2_run import _pct, _table
from .context import RMQ, build_context
from .two_layer import EVENTS, add_layer2_extras, load_candidates

GRID = (1.25, 1.5, 2.0, 2.5, 3.0, 4.0)
FIVE = pd.Timedelta(minutes=5)
MAX_TF_BARS = 60
LIMIT_BUFFER = 0.0002       # price must trade 0.02% through a limit target to count as filled
C_MKT = 0.0009              # taker 0.04% + 5 bps slippage, per side
C_LMT = 0.0002              # maker, per side
HOLDOUT = pd.Timestamp("2025-11-01")
GAP = pd.Timedelta(days=62)
YEARS = [2022, 2023, 2024, 2025]
FIXED = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}   # v3.1 fixed targets


# ----------------------------------------------------------------------------- labels
def _funding_cum(cfg: Config):
    f = load_funding(cfg.data_dir, cfg.symbol)
    pts = sorted((pd.Timestamp(day) + pd.Timedelta(hours=h), r) for day, lst in f.items() for h, r in lst)
    t = np.array([p[0].to_datetime64() for p in pts], dtype="datetime64[ns]")
    return t, np.r_[0.0, np.cumsum([p[1] for p in pts])]


def label_paths(tr: pd.DataFrame, df5n: pd.DataFrame, fund) -> pd.DataFrame:
    """tr: decision_time (= entry candle open, UTC-naive), tf, direction, risk. Returns per-target R / exit."""
    t5 = df5n["open_time"].to_numpy()
    O, H, Lw, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    ft, fc = fund
    out = []
    for dt, tf, d, risk in zip(tr["decision_time"], tr["tf"], tr["direction"], tr["risk"]):
        row = {"ok": False}
        bpt = int(pd.Timedelta(tf) / FIVE)
        st = int(np.searchsorted(t5, pd.Timestamp(dt).to_datetime64()))
        if st >= len(t5) or t5[st] != pd.Timestamp(dt).to_datetime64() or st + MAX_TF_BARS * bpt > len(O) or risk <= 0:
            out.append(row)
            continue
        en = st + MAX_TF_BARS * bpt
        o, h, l, c = O[st:en], H[st:en], Lw[st:en], C[st:en]
        if d < 0:
            o, h, l, c = -o, -l, -h, -c
        e = o[0]
        s0 = e - risk
        hit_s = np.flatnonzero(l <= s0)
        i_s = int(hit_s[0]) if len(hit_s) else -1
        r_stop = ((min(o[i_s], s0) if i_s > 0 else s0) - e) / risk if i_s >= 0 else math.nan
        # best favourable move before the stop candle (the stop candle itself is assumed to stop first)
        lim = i_s if i_s >= 0 else len(h)
        row["mfe_r"] = (h[:lim].max() - e) / risk if lim > 0 else 0.0
        row["ok"], row["px"], row["stop_pct"] = True, abs(e), risk / abs(e)
        for T in GRID:
            tg = e + T * risk
            hit_t = np.flatnonzero(h >= tg + LIMIT_BUFFER * abs(e))
            i_t = int(hit_t[0]) if len(hit_t) else -1
            if i_s >= 0 and (i_t < 0 or i_s <= i_t):
                r, xi, kind = r_stop, i_s, "stop"
            elif i_t >= 0:
                r, xi, kind = T, i_t, "target"
            else:
                r, xi, kind = (c[-1] - e) / risk, len(o) - 1, "time"
            x_time = pd.Timestamp(dt) + FIVE * (xi + 1)
            a, b = np.searchsorted(ft, pd.Timestamp(dt).to_datetime64(), side="right"), \
                np.searchsorted(ft, x_time.to_datetime64(), side="left")
            fund_frac = (fc[b] - fc[a]) * d if b > a else 0.0     # long pays a positive rate
            cost = C_MKT + (C_LMT if kind == "target" else C_MKT)
            row[f"R_{T:g}"] = r
            row[f"hit_{T:g}"] = int(kind == "target")
            row[f"net_{T:g}"] = r - (cost + fund_frac) / row["stop_pct"]
            row[f"exit_{T:g}"] = x_time
        out.append(row)
    return pd.DataFrame(out, index=tr.index)


# ----------------------------------------------------------------------------- liquidity map
def liquidity_map(tr: pd.DataFrame, df5: pd.DataFrame) -> pd.DataFrame:
    """Untaken liquidity and strong zones on the target side, in R. Only swings confirmed before the decision."""
    b1 = Bars(resample(df5, "1h"))
    h1t = b1.ot.dt.tz_convert(None).to_numpy()
    rmax, rmin = RMQ(b1.h, np.maximum), RMQ(b1.l, np.minimum)
    sw = {}
    for tf in ("1h", "4h", "1D"):
        bb = b1 if tf == "1h" else Bars(resample(df5, tf))
        ct, ot = bb.ct.dt.tz_convert(None).to_numpy(), bb.ot.dt.tz_convert(None).to_numpy()
        sw[tf] = {k: (np.array([ot[i] for i, _, _ in pts]), np.array([p for _, p, _ in pts]),
                      np.array([ct[cf] for _, _, cf in pts])) for k, pts in (("H", bb.sh), ("L", bb.sl))}
    table = _level_table(df5)
    tt_all = pd.to_datetime(tr["decision_time"]).dt.as_unit("ns").to_numpy()
    e_all, rk_all, d_all = (tr[c].to_numpy(float) for c in ("entry", "risk", "direction"))
    cols = ["lq_pool1_r", "lq_pool2_r", "lq_pool3_r", "lq_htf_pool_r", "lq_zone_r", "lq_n_1r", "lq_n_2r",
            "lq_n_3r", "lq_n_4r", "lq_eq_pool_r"]
    res = np.full((len(tr), len(cols)), np.nan)
    for n_, (tt, e, rk, dd) in enumerate(zip(tt_all, e_all, rk_all, d_all)):
        if not (np.isfinite(e) and rk > 0):
            continue
        side = "H" if dd > 0 else "L"
        i_now = np.searchsorted(h1t, tt)
        dist, htf = [], []
        for tfx in ("1h", "4h", "1D"):
            bar = np.timedelta64(int((100 * pd.Timedelta(tfx)).value), "ns")
            f, p, k = sw[tfx][side]
            m = (k <= tt) & (f >= tt - bar)
            for ff, pp in zip(f[m], p[m]):
                i0 = np.searchsorted(h1t, ff) + 1
                ext = rmax.q(i0, i_now) if dd > 0 else rmin.q(i0, i_now)
                if ext == ext and ((ext > pp) if dd > 0 else (ext < pp)):
                    continue                                   # already taken
                r = (pp - e) * dd / rk
                if r > 0:
                    dist.append(r)
                    if tfx != "1h":
                        htf.append(r)
        ds = np.sort(np.array(dist))
        res[n_, 0:3] = [ds[i] if len(ds) > i else 20.0 for i in range(3)]
        res[n_, 3] = min(htf) if htf else 20.0
        z = strong_levels(table, pd.Timestamp(tt).tz_localize("UTC"))
        za = ((z - e) * dd / rk) if len(z) else np.array([])
        za = za[za > 0]
        res[n_, 4] = za.min() if len(za) else 20.0
        for j, lim in enumerate((1, 2, 3, 4)):
            res[n_, 5 + j] = float((ds <= lim).sum())
        # equal highs / lows: two untaken swings within 0.1R of each other = a resting pool
        eq = ds[1:][np.diff(ds) <= 0.1] if len(ds) > 1 else np.array([])
        res[n_, 9] = eq.min() if len(eq) else 20.0
    return pd.DataFrame(res, columns=cols, index=tr.index)


# ----------------------------------------------------------------------------- v3.1 trades
def load_v31() -> pd.DataFrame:
    t = pd.read_pickle(ROOT / "results" / "failure_liquidity.pkl")
    t.attrs = {}
    skip = (t["setup"] == "1D bounce") & (t["f_vol"] / t["f_vol_prev"] < 0.8)   # v3.1 bounce-volume rule
    t = t[~skip].copy()
    t["decision_time"] = pd.to_datetime(t["decision_time"])
    t["atr"] = t["atr_px"]
    t["event"] = np.where(t["setup"] == "1D bounce", "level_test_bounce", "zone_break")
    # liquidity_features of the failure study use other definitions under the same names: keep context's
    drop = ["liq_in_path", "liq_in_risk", "pool_near_stop"] + [c for c in t.columns if c.startswith(("R_", "exit_"))]
    return t.drop(columns=[c for c in drop if c in t.columns]).reset_index(drop=True)


def _setup_flags(df: pd.DataFrame) -> pd.DataFrame:
    for e in EVENTS:
        df[f"is_{e}"] = (df["event"] == e).astype(int)
    for tf in ("2h", "4h", "1D"):
        df[f"is_{tf}"] = (df["tf"] == tf).astype(int)
    df["is_long"] = (df["direction"] > 0).astype(int)
    df["x_stop_pct"] = df["risk"] / df["entry"]
    df["x_atr_r"] = df["atr"] / df["risk"]
    return df


def feature_cols(df: pd.DataFrame) -> list[str]:
    liq = [c for c in df.columns if c.startswith("lq_")]
    ctx = [c for c in df.columns if c.startswith(("st_", "brk_", "pat_", "ev_", "zone_", "liq_", "pool_")) or
           c in ("at_zone", "wtrend", "vol_regime")]
    setup = [c for c in df.columns if c.startswith(("is_", "x_"))]
    ind = [c for c in df.columns if c.startswith(("m_", "n_"))]
    return liq + ctx + setup + ind


# ----------------------------------------------------------------------------- model
PARAMS = dict(objective="binary", learning_rate=0.03, num_leaves=15, min_data_in_leaf=100, feature_fraction=0.6,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, seed=7)


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    import lightgbm as lgb
    P = pd.DataFrame(index=test.index)
    for T in GRID:
        ds = lgb.Dataset(train[cols].to_numpy(float), train[f"hit_{T:g}"].to_numpy())
        m = lgb.train(PARAMS, ds, num_boost_round=300)
        P[f"p_{T:g}"] = m.predict(test[cols].to_numpy(float))
    P[:] = np.minimum.accumulate(P.to_numpy(), axis=1)        # can't be likelier to reach a farther target
    miss = {T: train.loc[train[f"hit_{T:g}"] == 0, f"R_{T:g}"].mean() for T in GRID}
    sp = test["stop_pct"].to_numpy()
    for T in GRID:
        p = P[f"p_{T:g}"].to_numpy()
        cost = (C_MKT + p * C_LMT + (1 - p) * C_MKT) / sp
        P[f"e_{T:g}"] = p * T + (1 - p) * miss[T] - cost
    E = P[[f"e_{T:g}" for T in GRID]].to_numpy()
    P["T_ml"] = np.array(GRID)[E.argmax(axis=1)]
    P["e_best"] = E.max(axis=1)
    return P


def _pick(df: pd.DataFrame, T: pd.Series, col: str) -> np.ndarray:
    return np.array([df.at[i, f"{col}_{t:g}"] for i, t in zip(df.index, T)])


def liquidity_rule_target(df: pd.DataFrame) -> pd.Series:
    """Non-ML comparison: aim just before the nearest untaken pool / zone that is at least 1.25R away (max 4R)."""
    lv = df[["lq_pool1_r", "lq_pool2_r", "lq_pool3_r", "lq_zone_r"]].to_numpy()
    lv = np.where(lv >= 1.35, lv - 0.1, np.nan)                 # 0.1R in front of the liquidity
    t = np.nanmin(lv, axis=1)
    t = np.where(np.isfinite(t), t, 4.0)
    return pd.Series([min(GRID, key=lambda g: abs(g - min(x, 4.0))) for x in t], index=df.index)


def stats(net: np.ndarray, R: np.ndarray | None = None) -> dict:
    if not len(net):
        return {"n": 0, "win": math.nan, "avg": math.nan, "pf": math.nan}
    g, l = net[net > 0].sum(), -net[net <= 0].sum()
    return {"n": len(net), "win": float((net > 0).mean()), "avg": float(net.mean()), "pf": g / l if l > 0 else math.inf}


def account(tr: pd.DataFrame, net_col: str, exit_col: str, risk_map: dict, lev_cap: float = 5.0) -> tuple[float, float]:
    """Compounding equity, overlapping positions; size = risk% / stop%, capped at lev_cap; booked at exit."""
    ev = sorted([(r.decision_time, 0, i) for i, r in tr.iterrows()] + [(r[exit_col], 1, i) for i, r in tr.iterrows()],
                key=lambda x: (x[0], -x[1]))
    eq, peak, mdd, notional = 1.0, 1.0, 0.0, {}
    for _, kind, i in ev:
        r = tr.loc[i]
        if kind == 0:
            notional[i] = eq * min(risk_map.get(r["setup"], 0.02) / r["stop_pct"], lev_cap)
        else:
            eq += notional.pop(i) * r[net_col] * r["stop_pct"]
            peak = max(peak, eq)
            mdd = max(mdd, 1 - eq / peak)
    return eq, mdd


# ----------------------------------------------------------------------------- runner
def run_targets(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    fund = _funding_cum(cfg)
    cache = ROOT / "results" / "two_layer_candidates.pkl"
    cand = pd.read_pickle(cache) if cache.exists() else None
    if cand is None:
        raise SystemExit("run `python -m bot two-layer` first (builds the candidate table)")
    cand.attrs = {}
    v3 = load_v31()
    allev = pd.concat([cand[["decision_time", "tf", "event", "direction"]],
                       v3[["decision_time", "tf", "event", "direction"]]], ignore_index=True)
    v3 = pd.concat([v3, build_context(v3, df5u, allev)], axis=1)
    v3 = add_layer2_extras(v3.drop(columns=["n_btc_4h"]), cfg, df5u)
    print(f"candidates {len(cand)}, v3.1 trades {len(v3)}; labelling + liquidity map")
    for name in ("cand", "v3"):
        df = cand if name == "cand" else v3
        lab = label_paths(df, df5n, fund)
        lm = liquidity_map(df, df5u)
        df = pd.concat([df.drop(columns=[c for c in lab.columns.union(lm.columns) if c in df.columns]), lab, lm], axis=1)
        df = _setup_flags(df[df["ok"].astype(bool)].copy())
        if name == "cand":
            cand = df
        else:
            v3 = df
    v3["hold"] = v3["decision_time"] >= HOLDOUT
    cand["hold"] = cand["decision_time"] >= HOLDOUT
    cols = [c for c in feature_cols(cand) if c in v3.columns]
    v3["src"], cand["src"] = 1, 0
    cols_all = cols + ["src"]
    pool = pd.concat([cand[cols_all + [f"{k}_{T:g}" for k in ("hit", "R") for T in GRID] + ["decision_time", "hold"]],
                      v3[cols_all + [f"{k}_{T:g}" for k in ("hit", "R") for T in GRID] + ["decision_time", "hold"]]],
                     ignore_index=True)
    preds = []
    for yr in YEARS:
        s = pd.Timestamp(f"{yr}-01-01")
        tr_ = pool[(pool["decision_time"] < s - GAP) & ~pool["hold"]]
        te = v3[(v3["decision_time"] >= s) & (v3["decision_time"] < pd.Timestamp(f"{yr + 1}-01-01")) & ~v3["hold"]]
        if len(te):
            preds.append(fit_predict(tr_, te, cols_all).assign(period=str(yr)))
    tr_ = pool[(pool["decision_time"] < HOLDOUT - GAP) & ~pool["hold"]]
    preds.append(fit_predict(tr_, v3[v3["hold"]], cols_all).assign(period="holdout"))
    P = pd.concat(preds)
    X = v3.join(P, how="inner")
    X["T_fixed"] = X["setup"].map(FIXED)
    X["T_liq"] = liquidity_rule_target(X)
    for k in ("fixed", "liq", "ml"):
        X[f"net_{k}"] = _pick(X, X[f"T_{k}"], "net")
        X[f"exit_{k}"] = _pick(X, X[f"T_{k}"], "exit")
    X["take_ml"] = X["e_best"] > 0
    X.to_pickle(ROOT / "results" / "ml_targets.pkl")
    return write_report(X, cand, out_dir)


def write_report(X: pd.DataFrame, cand: pd.DataFrame, out_dir: Path) -> Path:
    L = ["# ML profit-taking: the target chosen per trade (never below 1.25:1)", "",
         f"Trades: the v3.1 strategy ({len(X)} trades 2022 - Oct 2026). Models learn from {len(cand):,} main-rule "
         "trades + the v3.1 trades, walk-forward (each year scored by models that never saw it). "
         "**win % = profit after all costs** (market entry, limit target exit, market stop, actual funding).", "",
         "Limit fills are conservative: price must trade 0.02% through the target.", ""]
    variants = [("fixed targets (v3.1: 2:1 breakouts, 3:1 bounces)", "fixed", None),
                ("liquidity rule: just before the next pool / zone (no ML)", "liq", None),
                ("ML target (best expected R)", "ml", None),
                ("ML target + skip trades with negative expected R", "ml", "take_ml")]
    rows = []
    for per, pm in (("2022-2025 (research, walk-forward)", ~X["hold"]), ("holdout Nov 2025 - Oct 2026", X["hold"])):
        for name, k, filt in variants:
            m = pm & (X[filt] if filt else True)
            s = stats(X.loc[m, f"net_{k}"].to_numpy())
            rows.append({"period": per, "rule": name, **s, "avgT": X.loc[m, f"T_{k}"].mean()})
    L += ["## Results", "", _table(pd.DataFrame(rows), [
        ("period", "period", str), ("rule", "profit-taking", str), ("n", "trades", str), ("win", "win %", _pct),
        ("avg", "avg R per trade", lambda v: f"{v:+.2f}"), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("avgT", "avg target", lambda v: f"{v:.2f}R")]), ""]
    rows = []
    for per, g in X.groupby("period"):
        r = {"period": per}
        for k in ("fixed", "ml"):
            s = stats(g[f"net_{k}"].to_numpy())
            r[f"n_{k}"], r[f"w_{k}"], r[f"a_{k}"] = s["n"], s["win"], s["avg"]
        rows.append(r)
    L += ["## By year: fixed vs ML target", "", _table(pd.DataFrame(rows), [
        ("period", "period", str), ("n_fixed", "trades", str), ("w_fixed", "win % fixed", _pct),
        ("a_fixed", "avg R fixed", lambda v: f"{v:+.2f}"), ("w_ml", "win % ML", _pct),
        ("a_ml", "avg R ML", lambda v: f"{v:+.2f}")]), ""]
    rows = []
    for per, pm in (("research", ~X["hold"]), ("holdout", X["hold"])):
        for setup, g in X[pm].groupby("setup"):
            r = {"period": per, "setup": setup, "n": len(g)}
            for k in ("fixed", "ml"):
                s = stats(g[f"net_{k}"].to_numpy())
                r[f"w_{k}"], r[f"a_{k}"] = s["win"], s["avg"]
            r["avgT"] = g["T_ml"].mean()
            rows.append(r)
    L += ["## By setup", "", _table(pd.DataFrame(rows), [
        ("period", "period", str), ("setup", "setup", str), ("n", "trades", str), ("w_fixed", "win % fixed", _pct),
        ("a_fixed", "avg R fixed", lambda v: f"{v:+.2f}"), ("w_ml", "win % ML", _pct),
        ("a_ml", "avg R ML", lambda v: f"{v:+.2f}"), ("avgT", "avg ML target", lambda v: f"{v:.2f}R")]), ""]
    dist = X.groupby(["period", "T_ml"]).size().unstack(fill_value=0)
    dist.columns = [f"{c:g}R" for c in dist.columns]
    dist = dist.reset_index()
    L += ["## Which targets the ML picks (trades per target)", "",
          _table(dist, [(c, c, str) for c in dist.columns]), ""]
    # calibration of the ML probability for the chosen target
    X["p_chosen"] = _pick(X, X["T_ml"], "p")
    X["hit_chosen"] = _pick(X, X["T_ml"], "hit")
    X["pbin"] = pd.cut(X["p_chosen"], [0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0])
    cal = X.groupby("pbin", observed=True).agg(n=("hit_chosen", "size"), predicted=("p_chosen", "mean"),
                                               actual=("hit_chosen", "mean")).reset_index()
    cal["pbin"] = cal["pbin"].astype(str)
    L += ["## Is the model's probability honest? (chosen target, all periods out-of-sample)", "",
          _table(cal, [("pbin", "predicted chance", str), ("n", "trades", str), ("predicted", "avg predicted", _pct),
                       ("actual", "actually reached", _pct)]), ""]
    risk = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
    rows = []
    for per, pm in (("research 2022-2025", ~X["hold"]), ("holdout", X["hold"])):
        for name, k, filt in variants:
            g = X[pm & (X[filt] if filt else True)]
            eq, mdd = account(g, f"net_{k}", f"exit_{k}", risk)
            rows.append({"period": per, "rule": name, "eq": eq, "mdd": mdd})
    L += ["## Account (A+ 4% risk, others 2%, max 5x, compounding)", "", _table(pd.DataFrame(rows), [
        ("period", "period", str), ("rule", "profit-taking", str), ("eq", "end / start", lambda v: f"{v:.2f}x"),
        ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    path = out_dir / "ml_targets.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
