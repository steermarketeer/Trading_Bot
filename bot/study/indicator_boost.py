"""
Which indicators improve the CURRENT strategy?

Trade sets (same as strategy_eval):
  A  breakouts, certainty >= 7, 2h / 4h / 1D, fixes F1 (stop >= 0.6%) + F2 (not the quietest 20%), exit 2:1
  B  1D zone tested >= 4 times, bounce confirmed, exit 3:1
For every indicator reading at the entry time (all ~260 multi-timeframe hint states, the event-candle features,
and the NEW indicators below), trades are split into "indicator says yes" vs "no" (flags: > 0; continuous values:
above the research median). Metric = average R after costs at the setup's target, plus win %.
An indicator HELPS only if: Welch t-test false-discovery q < 0.10 across all indicators of that set, the gain has
the same sign in 2022-23 and in 2024-25, and then it is checked on the holdout (Nov 2025 on).

New indicators (on the trade's own timeframe, read from candles closed by the entry time):
  squeeze        Bollinger(20,2) inside Keltner(20,1.5 ATR) in any of the last 5 candles (volatility contraction)
  bbw_pct        Bollinger width percentile over the last 120 candles (low = contraction)
  nr7            the last closed candle had the narrowest range of the last 7
  chop           Choppiness Index(14) (high = choppy)
  aroon          Aroon oscillator(25), in the trade direction
  hma_slope      Hull MA(20) slope over 3 candles, in the trade direction (ATR units)
  rvol_tod       volume of the last candle vs the average of the same time-of-day over the last 20 days
  obv_slope      OBV change over 10 candles / 10-candle volume, in the trade direction
  ha_trend       last 3 Heikin-Ashi candles all in the trade direction
  elder          Elder bull/bear power (EMA13) in the trade direction (ATR units)
  stoch / cci / mfi   in the trade direction (high = momentum our way)
  room_2r        no strong S/R zone between entry and the 2R target (1 = clear path)
  zone_dist_r    distance to the nearest strong zone in the target direction, in R
  btc_4h         BTC 4h close vs its EMA20, in the trade direction
  btc_24h        BTC 24h return in the trade direction
  funding_crowd  latest 3 funding rates average x direction (high = our side is crowded/paying)
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .concepts import Bars
from .indicators import atr, bollinger, cci, ema, keltner, mfi, obv, stochastic
from .levels import _level_table, strong_levels
from .level_tests import tests_for
from .mtf import hints_at, resample
from .mtf2 import load_funding_table, tf_hints2
from .smalltf import COST_TAKER
from .sr2_run import _pct, _r, _table
from .strategy_eval import HOLDOUT, build_rows, load_breakouts

SPLIT = pd.Timestamp("2024-01-01")


def _hma(s: pd.Series, n: int = 20) -> pd.Series:
    def wma(x, k):
        w = np.arange(1, k + 1)
        return x.rolling(k, min_periods=k).apply(lambda v: np.dot(v, w) / w.sum(), raw=True)
    return wma(2 * wma(s, n // 2) - wma(s, n), int(np.sqrt(n)))


def tf_new_states(b: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Direction-free raw values per candle (sign convention: + = bullish); turned relative later."""
    c, h, l, v = b["close"], b["high"], b["low"], b["volume"]
    a = atr(b, 14)
    mid, bu, bl = bollinger(c)
    km, ku, kl = keltner(b, 20, 1.5, 20)
    out = pd.DataFrame({"close_time": b["close_time"]})
    sq = (bu < ku) & (bl > kl)
    out["squeeze"] = sq.astype(float).rolling(5, min_periods=1).max()
    bw = (bu - bl) / mid
    out["bbw_pct"] = bw.rolling(120, min_periods=60).apply(lambda x: (x[-1] >= x).mean(), raw=True)
    rng = h - l
    out["nr7"] = (rng <= rng.rolling(7, min_periods=7).min()).astype(float)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    chop = 100 * np.log10(tr.rolling(14).sum() / (h.rolling(14).max() - l.rolling(14).min())) / np.log10(14)
    out["chop"] = chop
    up = h.rolling(26).apply(lambda x: len(x) - 1 - np.argmax(x), raw=True)
    dn = l.rolling(26).apply(lambda x: len(x) - 1 - np.argmin(x), raw=True)
    out["aroon"] = (100 * (25 - up) / 25) - (100 * (25 - dn) / 25)
    hm = _hma(c, 20)
    out["hma_slope"] = (hm - hm.shift(3)) / a
    if pd.Timedelta(tf) < pd.Timedelta("1D"):
        tod = b["open_time"].dt.hour * 60 + b["open_time"].dt.minute
        out["rvol_tod"] = v / v.groupby(tod).transform(lambda s: s.shift(1).rolling(20, min_periods=10).mean())
    else:
        out["rvol_tod"] = v / v.shift(1).rolling(20, min_periods=10).mean()
    ob = obv(b)
    out["obv_slope"] = (ob - ob.shift(10)) / v.rolling(10).sum()
    ha_c = (b["open"] + h + l + c) / 4
    vals = np.empty(len(ha_c))
    o0, cc = b["open"].to_numpy(), ha_c.to_numpy()
    for i in range(len(vals)):
        vals[i] = (o0[0] + c.iloc[0]) / 2 if i == 0 else (vals[i - 1] + cc[i - 1]) / 2
    ha_dir = np.sign(cc - vals)
    out["ha_trend"] = pd.Series(ha_dir).rolling(3).apply(lambda x: x[0] if (x == x[0]).all() else 0, raw=True).to_numpy()
    e13 = ema(c, 13)
    out["elder"] = ((h - e13) + (l - e13)) / a
    out["stoch"] = stochastic(b) - 50
    out["cci"] = cci(b)
    out["mfi"] = mfi(b) - 50
    return out


def add_new_indicators(trades: pd.DataFrame, df5: pd.DataFrame, btc5: pd.DataFrame, funding: pd.DataFrame,
                       table: pd.DataFrame) -> pd.DataFrame:
    t = trades.copy()
    t["_et"] = pd.to_datetime(t["entry_time"]).dt.tz_localize("UTC").dt.as_unit("ns") \
        if pd.to_datetime(t["entry_time"]).dt.tz is None else pd.to_datetime(t["entry_time"]).dt.as_unit("ns")
    t["_row"] = np.arange(len(t))
    parts = []
    for tf, g in t.groupby("tf"):
        st = tf_new_states(resample(df5, tf).reset_index(drop=True), tf)
        st["close_time"] = pd.to_datetime(st["close_time"], utc=True).dt.as_unit("ns")
        m = pd.merge_asof(g.sort_values("_et"), st.sort_values("close_time"), left_on="_et", right_on="close_time",
                          direction="backward")
        parts.append(m)
    t = pd.concat(parts).sort_values("_row")
    d = t["direction"].to_numpy()
    for col in ("aroon", "hma_slope", "obv_slope", "ha_trend", "elder", "stoch", "cci", "mfi"):
        t[f"n_{col}"] = t[col] * d
    for col in ("squeeze", "bbw_pct", "nr7", "chop", "rvol_tod"):
        t[f"n_{col}"] = t[col]
    # BTC
    b4 = resample(btc5, "4h")
    b4["side"] = np.sign(b4["close"] - ema(b4["close"], 20))
    b4["ret24"] = b4["close"] / b4["close"].shift(6) - 1
    b4["close_time"] = pd.to_datetime(b4["close_time"], utc=True).dt.as_unit("ns")
    m = pd.merge_asof(t[["_et", "_row"]].sort_values("_et"), b4[["close_time", "side", "ret24"]].sort_values("close_time"),
                      left_on="_et", right_on="close_time", direction="backward").sort_values("_row")
    t["n_btc_4h"] = m["side"].to_numpy() * d
    t["n_btc_24h"] = m["ret24"].to_numpy() * d
    f = funding.sort_values("time").copy()
    f["avg3"] = f["rate"].rolling(3).mean()
    f["time"] = pd.to_datetime(f["time"], utc=True).dt.as_unit("ns")
    m = pd.merge_asof(t[["_et", "_row"]].sort_values("_et"), f[["time", "avg3"]], left_on="_et", right_on="time",
                      direction="backward").sort_values("_row")
    t["n_funding_crowd"] = m["avg3"].to_numpy() * d
    # room to target (strong zones known at entry)
    room, dist = [], []
    for et, dd, e, rk in zip(t["_et"], t["direction"], t["entry"], t["risk"]):
        z = strong_levels(table, pd.Timestamp(et))
        tgt = e + dd * 2 * rk
        ahead = z[(z - e) * dd > 0.05 * rk]
        inpath = ahead[(ahead - tgt) * dd < 0]
        room.append(float(len(inpath) == 0))
        dist.append(float(np.min(np.abs(ahead - e)) / rk) if len(ahead) else 10.0)
    t["n_room_2r"], t["n_zone_dist_r"] = room, dist
    return t.drop(columns=["_et", "_row", "close_time"], errors="ignore")


def evaluate(x: pd.DataFrame, rule: str, cols: list[str]) -> pd.DataFrame:
    from scipy import stats as st

    res = x[~x["hold"]]
    hold = x[x["hold"]]
    net = lambda g: g[f"R_{rule}"] - COST_TAKER / g["stop_pct"]  # noqa: E731
    rows = []
    for col in cols:
        v = res[col]
        if v.notna().sum() < 60 or v.nunique() < 2:
            continue
        flag = v.nunique() <= 3
        thr = 0.0 if flag else float(v.median())
        yes = res[v > thr]
        no = res[~(v > thr)]
        if len(yes) < 25 or len(no) < 25:
            continue
        ny, nn = net(yes), net(no)
        t_, p = st.ttest_ind(ny, nn, equal_var=False)
        h1 = res["decision_time"] < SPLIT
        d1 = net(res[(v > thr) & h1]).mean() - net(res[~(v > thr) & h1]).mean()
        d2 = net(res[(v > thr) & ~h1]).mean() - net(res[~(v > thr) & ~h1]).mean()
        hv = hold[col]
        hy, hn = hold[hv > thr], hold[~(hv > thr)]
        rows.append({"indicator": col, "rule": "> 0" if flag else f"> {thr:.3g}", "n_yes": len(yes),
                     "avg_yes": ny.mean(), "avg_no": nn.mean(), "win_yes": (ny > 0).mean(), "win_no": (nn > 0).mean(),
                     "t": t_, "p": p, "half1": d1, "half2": d2,
                     "h_n_yes": len(hy), "h_avg_yes": net(hy).mean() if len(hy) else math.nan,
                     "h_avg_no": net(hn).mean() if len(hn) else math.nan,
                     "h_win_yes": (net(hy) > 0).mean() if len(hy) else math.nan,
                     "h_win_no": (net(hn) > 0).mean() if len(hn) else math.nan})
    t = pd.DataFrame(rows)
    if t.empty:
        return t
    from .indicator_search import bh_qvalues
    t["q"] = bh_qvalues(t["p"].to_numpy())
    same = (np.sign(t["half1"]) == np.sign(t["avg_yes"] - t["avg_no"])) & (np.sign(t["half2"]) == np.sign(t["avg_yes"] - t["avg_no"]))
    t["consistent"] = same
    t["verdict"] = np.where((t["q"] < 0.10) & same, np.where(t["avg_yes"] > t["avg_no"], "HELPS", "HURTS"),
                            np.where(same, "consistent", "noise"))
    t["holdout_agrees"] = np.sign(t["h_avg_yes"] - t["h_avg_no"]) == np.sign(t["avg_yes"] - t["avg_no"])
    return t.sort_values("t", key=abs, ascending=False)


def _label(c: str) -> str:
    if c.startswith("n_"):
        return f"NEW {c[2:]}"
    if c.startswith("m_"):
        tf, _, h = c[2:].partition("_")
        return f"{tf} {h}"
    return c


def run_indicator_boost(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    btc5, _ = load_klines_5m(cfg.data_dir, cfg.btc_symbol)
    funding = load_funding_table(cfg.data_dir, cfg.symbol)
    table = _level_table(df5u)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))

    # ---- set A: breakouts with F1 + F2
    b = load_breakouts()
    feat_cols = [c for c in b.columns if c.startswith(("m_", "f_"))]
    keep = ["tf", "event", "direction", "hold", "atr_pct", "certainty", "entry", "risk", "entry_time"] + feat_cols
    A = build_rows(b, df5n, (2.0,), keep)
    q = A[~A["hold"]].groupby("tf")["atr_pct"].quantile(0.2)
    A = A[(A["stop_pct"] >= 0.006) & (A["atr_pct"] >= A["tf"].map(q))].reset_index(drop=True)
    A = add_new_indicators(A, df5u, btc5, funding, table)

    # ---- set B: 1D 4th+ test bounce
    lt = tests_for(df5u, "1D")
    lt = lt[lt.get("traded", pd.Series(False, index=lt.index)).fillna(False).astype(bool) & (lt["test_n"] >= 4)].copy()
    lt["tf"] = "1D"
    lt["entry_time"] = (pd.to_datetime(lt["time"], utc=True) + pd.Timedelta(days=1)).dt.tz_convert(None)
    lt["hold"] = lt["entry_time"] >= HOLDOUT
    bars = Bars(resample(df5u, "1D"))
    fe = pd.DataFrame([bars.features(int(j) + 1, int(d)) for j, d in zip(lt["j"], lt["direction"])], index=lt.index)
    lt = pd.concat([lt, fe], axis=1)
    h1 = hints_at(df5u, pd.DataFrame({"entry_time": pd.to_datetime(lt["entry_time"]).dt.tz_localize("UTC"),
                                      "direction": lt["direction"]}, index=lt.index)).drop(columns=["entry_time", "direction"])
    h2 = tf_hints2(df5u, pd.DataFrame({"entry_time": pd.to_datetime(lt["entry_time"]).dt.tz_localize("UTC"),
                                       "direction": lt["direction"]}, index=lt.index))
    hh = pd.concat([h1, h2], axis=1)
    hh.columns = [f"m_{c}" for c in hh.columns]
    lt = pd.concat([lt, hh], axis=1)
    lt["prev_failed"] = lt["prev_failed_breaks"]
    keepB = ["tf", "direction", "hold", "entry", "risk", "entry_time", "test_n", "prev_failed"] + \
        [c for c in lt.columns if c.startswith(("m_", "f_"))]
    B = build_rows(lt, df5n, (3.0,), keepB)
    B = B[(B["decision_time"] < HOLDOUT - pd.Timedelta(days=62)) | B["hold"]]
    B = B[B["decision_time"] >= pd.Timestamp("2020-06-01")].reset_index(drop=True)
    B = add_new_indicators(B, df5u, btc5, funding, table)

    # ---- other models (C, D, E)
    extra = {}

    def scored(files, cond, family_target):
        parts = []
        for f in files:
            d = pd.read_pickle(ROOT / "results" / f)
            d.attrs = {}
            parts.append(d)
        x = pd.concat(parts, ignore_index=True)
        x = x[cond(x)].copy()
        x["entry_time"] = pd.to_datetime(x["decision_time"], utc=True).dt.tz_convert(None)
        x["hold"] = x["entry_time"] >= HOLDOUT
        fc = [c for c in x.columns if c.startswith(("m_", "f_"))]
        rows = build_rows(x, df5n, (family_target,), ["tf", "event", "direction", "hold", "entry", "risk",
                                                       "entry_time", "certainty"] + fc)
        return add_new_indicators(rows, df5u, btc5, funding, table)

    extra["C. Breakouts certainty 5-6 (2h/4h/1D) at 2:1"] = (scored(
        ["scored_breakout_2h.pkl", "scored_breakout.pkl"],
        lambda x: x["certainty"].between(5, 6) & x["tf"].isin(["2h", "4h", "1D"]), 2.0), "2:1")
    extra["D. Reversals, all certainties (2h/4h/1D) at 2:1"] = (scored(
        ["scored_reversal_2h.pkl", "scored_reversal.pkl"], lambda x: x["tf"].isin(["2h", "4h", "1D"]), 2.0), "2:1")
    ce = pd.read_pickle(ROOT / "results" / "concept_events_1D.pkl")
    ce = ce[ce["event"] == "zone_bounce"].copy()
    ce["tf"], ce["certainty"] = "1D", np.nan
    ce["entry_time"] = pd.to_datetime(ce["decision_time"], utc=True).dt.tz_convert(None)
    ce["hold"] = ce["entry_time"] >= HOLDOUT
    ce = ce[(ce["entry_time"] < HOLDOUT - pd.Timedelta(days=62)) | ce["hold"]]
    ce = ce[ce["entry_time"] >= pd.Timestamp("2020-06-01")]
    fc = [c for c in ce.columns if c.startswith(("m_", "f_"))]
    E = build_rows(ce, df5n, (2.0, 3.0), ["tf", "event", "direction", "hold", "entry", "risk", "entry_time"] + fc)
    extra["E. All 1D zone bounces at 3:1"] = (add_new_indicators(E, df5u, btc5, funding, table), "3:1")

    L = ["# Which indicators improve the current strategy?", "",
         "Split per indicator into *yes* / *no* (flags > 0, values above the research median). avg R after costs at the "
         "setup's target. **HELPS** = Welch t-test FDR q < 0.10 across all indicators of that set AND the same sign in "
         "2022-23 and 2024-25. The holdout columns are a later check, never used to choose.", ""]
    summary = []
    sets = [("A. Breakouts (certainty >= 7, fixed) at 2:1", A, "2:1"),
            ("B. 1D zone tested 4+ times, bounce at 3:1", B, "3:1")] + [(k, v[0], v[1]) for k, v in extra.items()]
    for name, X, rule in sets:
        cols = [c for c in X.columns if c.startswith(("m_", "f_", "n_"))] + (["test_n", "prev_failed"] if "test_n" in X else [])
        ev = evaluate(X, rule, cols)
        ev.to_csv(out_dir / f"indicator_boost_{name[0]}.csv", index=False)
        base_r = X[~X["hold"]]
        net = base_r[f"R_{rule}"] - COST_TAKER / base_r["stop_pct"]
        hb = X[X["hold"]]
        hnet = hb[f"R_{rule}"] - COST_TAKER / hb["stop_pct"]
        L += [f"## {name}", "",
              f"Baseline: research {len(base_r)} trades, win {(net > 0).mean():.0%}, avg {net.mean():+.2f} R · "
              f"holdout {len(hb)} trades, win {(hnet > 0).mean():.0%}, avg {hnet.mean():+.2f} R. "
              f"Indicators tested: {len(ev)}.", ""]
        top = ev[ev["verdict"].isin(["HELPS", "HURTS"])]
        if top.empty:
            L += ["No indicator passed the strict test. Closest (consistent in both halves, sorted by strength):", ""]
            top = ev[ev["consistent"]].head(12)
        top = top.assign(name=top["indicator"].map(_label))
        L += [_table(top, [("name", "indicator", str), ("rule", "yes when", str), ("n_yes", "trades yes", str),
                           ("win_yes", "win yes", _pct), ("win_no", "win no", _pct),
                           ("avg_yes", "avg R yes", _r), ("avg_no", "avg R no", _r),
                           ("q", "q", lambda v: f"{v:.2f}"), ("verdict", "verdict", str),
                           ("h_win_yes", "holdout win yes", _pct), ("h_win_no", "holdout win no", _pct),
                           ("h_avg_yes", "holdout R yes", _r), ("h_avg_no", "holdout R no", _r),
                           ("holdout_agrees", "holdout agrees", lambda v: "yes" if v else "no")]), ""]
        # best single filter for this set: strongest HELPS (or strongest consistent) chosen on research only
        pool = ev[ev["verdict"] == "HELPS"]
        if pool.empty:
            pool = ev[ev["consistent"] & (ev["avg_yes"] > ev["avg_no"])]
        if len(pool):
            bst = pool.sort_values("t", ascending=False).iloc[0]
            summary.append({"set": name, "base_n": len(base_r), "base_win": (net > 0).mean(), "base_r": net.mean(),
                            "h_base_win": (hnet > 0).mean(), "h_base_r": hnet.mean(),
                            "filter": f"{_label(bst['indicator'])} {bst['rule']}", "verdict": bst["verdict"],
                            "n": bst["n_yes"], "win": bst["win_yes"], "r": bst["avg_yes"],
                            "h_n": bst["h_n_yes"], "h_win": bst["h_win_yes"], "h_r": bst["h_avg_yes"]})
        newonly = ev[ev["indicator"].str.startswith("n_")].assign(name=lambda d: d["indicator"].map(_label))
        L += ["New indicators (all of them):", "",
              _table(newonly, [("name", "indicator", str), ("rule", "yes when", str), ("n_yes", "trades yes", str),
                               ("win_yes", "win yes", _pct), ("win_no", "win no", _pct), ("avg_yes", "avg R yes", _r),
                               ("avg_no", "avg R no", _r), ("q", "q", lambda v: f"{v:.2f}"), ("verdict", "verdict", str),
                               ("h_avg_yes", "holdout R yes", _r), ("h_avg_no", "holdout R no", _r)]), ""]
    S = pd.DataFrame(summary)
    head = ["## Summary: best indicator filter per model (chosen on research; holdout = check)", "",
            _table(S, [("set", "model", str), ("base_win", "win now", _pct), ("base_r", "avg R now", _r),
                       ("filter", "best filter", str), ("verdict", "strength", str), ("n", "trades kept", str),
                       ("win", "win with filter", _pct), ("r", "avg R with filter", _r),
                       ("h_base_win", "holdout win now", _pct), ("h_win", "holdout win with filter", _pct),
                       ("h_base_r", "holdout R now", _r), ("h_r", "holdout R with filter", _r)]), ""] if len(S) else []
    L = L[:3] + head + L[3:]
    path = out_dir / "indicator_boost.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
