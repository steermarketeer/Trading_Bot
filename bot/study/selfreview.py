"""
Self-review: every pattern found in the journal, checked automatically on every v3.1 ETH trade (one position per move).

Known at entry (usable as rules / ML inputs):
  stretched        1h RSI > 70 and the 1h close above the 1h upper Bollinger band (longs; mirrored for shorts)
  macd_div_1h      1h bearish MACD divergence: the push to entry made a higher high, MACD a lower high
  liq_under_stop   an untaken 15m / 1h swing low within 0.5R beyond the stop (stops resting there)
  daily_against    daily close on the wrong side of the daily EMA 200
  ema200_near      daily EMA 200 between the entry and the target
  ceiling          strong S/R zone or untaken 4h swing between the entry and the target
  vertical_day     the last daily candle moved more than 2 daily ATR in the trade direction
  falling_highs    the last three 4h swing highs fall (longs)
  second_try       a same-direction loss within 7 days and 1% of the price (closed before entry)
  stacked          another signal fired on the same candle in the same direction
Known only after entry (exit / ML-on-the-trade inputs):
  unconfirmed_4h   the first 4h close after the entry is back beyond the entry
  band_fail_4h     a 4h poke beyond the outer Bollinger band that closes back inside, then a 4h close through the middle band
  double_top_15m   15m double top / lower high + neckline break before the trade ended (journal lesson 1)
Outcome only (diagnosis, never an input):
  hunted           stopped, then price reached the original target within 20 days
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import stats
from .concepts import Bars
from .indicators import atr, bollinger, ema, macd
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
PRE = ["stretched", "macd_div_1h", "liq_under_stop", "daily_against", "ema200_near", "ceiling", "vertical_day",
       "falling_highs", "second_try", "stacked"]
POST = ["unconfirmed_4h", "band_fail_4h", "double_top_15m"]
NAMES = {"stretched": "Entry stretched (1h RSI > 70, above the 1h upper Bollinger band)",
         "macd_div_1h": "1h MACD divergence against the trade at entry",
         "liq_under_stop": "Untaken liquidity just beyond the stop (within 0.5R)",
         "daily_against": "Daily trend against the trade (wrong side of the daily EMA 200)",
         "ema200_near": "Daily EMA 200 between the entry and the target",
         "ceiling": "Resistance / untaken 4h high between the entry and the target",
         "vertical_day": "Entry after a vertical day (> 2 daily ATR)",
         "falling_highs": "Falling 4h highs (longs) / rising lows (shorts)",
         "second_try": "Second try at a level that just failed",
         "stacked": "More than one signal on the same candle",
         "unconfirmed_4h": "First 4h close after entry back beyond the entry (no confirmation)",
         "band_fail_4h": "4h Bollinger band failure after entry",
         "double_top_15m": "15m double top / lower high + breakdown after entry"}


def run_selfreview(cfg: Config, out_dir: Path) -> Path:
    L_ = pd.read_pickle(ROOT / "results" / "lessons.pkl")            # one position per move, base outcomes, filters
    B_ = pd.read_pickle(ROOT / "results" / "bandfail.pkl")
    A = pd.read_pickle(ROOT / "results" / "coins_v31.pkl")
    eth = A[A["coin"] == "ETH"]
    stack = eth.groupby(["entry_time", "direction"]).size()
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df = df5u.assign(t=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    T = L_.copy()
    T["band_fail_4h"] = B_["closed_early"].to_numpy()
    T["double_top_15m"] = (T["kind_L1"] == "15m failure exit")
    T["stacked"] = [stack.get((t, d), 1) > 1 for t, d in zip(T["entry_time"], T["direction"])]
    T["daily_against"] = T["d1_wrong_side"]
    T["falling_highs"] = T["falling_highs"].astype(bool)
    T["ceiling"] = T["ceiling"].astype(bool)
    # 1h stretch + MACD divergence
    b1 = Bars(resample(df5u, "1h"))
    ct1 = b1.ct.dt.tz_convert(None).to_numpy()
    _, bu1, bl1 = (x.to_numpy() for x in bollinger(pd.Series(b1.c)))
    m1 = macd(pd.Series(b1.c))[0].to_numpy()
    # daily
    d1 = resample(df5u, "1D")
    d1ct = pd.to_datetime(d1["close_time"], utc=True).dt.tz_convert(None).to_numpy()
    d1e200 = ema(d1["close"], 200).to_numpy()
    d1atr = atr(d1, 14).to_numpy()
    d1o, d1c = d1["open"].to_numpy(float), d1["close"].to_numpy(float)
    b4 = resample(df5u, "4h")
    t4 = pd.to_datetime(b4["open_time"], utc=True).dt.tz_convert(None).to_numpy()
    c4 = b4["close"].to_numpy(float)
    # untaken 15m / 1h swings
    sw = {}
    for tf, rule in (("15m", "15min"), ("1h", "1h")):
        b = b1 if tf == "1h" else Bars(resample(df5u, rule))
        sw[tf] = (b, b.ct.dt.tz_convert(None).to_numpy())

    def untaken(tf, t, side, lookback=150):
        b, ct = sw[tf]
        n = int(np.searchsorted(ct, np.datetime64(t), side="right"))
        out = []
        for i, p, cf in (b.sl if side == "L" else b.sh):
            if cf < n and i >= n - lookback:
                seg = b.l[i + 1:n] if side == "L" else b.h[i + 1:n]
                if not len(seg) or (seg.min() >= p if side == "L" else seg.max() <= p):
                    out.append(p)
        return np.array(out)

    rows = []
    for _, r in T.iterrows():
        et, d, e, rk = r["entry_time"], int(r["direction"]), float(r["px"]), float(r["risk"])
        s, tg = e - d * rk, e + d * TGT[r["setup"]] * rk
        n = int(np.searchsorted(ct1, np.datetime64(et), side="right")); j = n - 1
        rsi_ok = (b1.r[j] > 70) if d > 0 else (b1.r[j] < 30)
        band_ok = (b1.c[j] > bu1[j]) if d > 0 else (b1.c[j] < bl1[j])
        pts = [(i, p) for i, p, cf in (b1.sh if d > 0 else b1.sl) if cf < n]
        k = j - 8 + int(np.argmax(b1.h[j - 8:j + 1] if d > 0 else -b1.l[j - 8:j + 1]))
        ext_now = b1.h[k] if d > 0 else b1.l[k]
        div = bool(pts) and ((ext_now - pts[-1][1]) * d > 0) and ((m1[k] - m1[pts[-1][0]]) * d < 0)
        liq = np.r_[untaken("15m", et, "L" if d > 0 else "H"), untaken("1h", et, "L" if d > 0 else "H")]
        beyond = (s - liq) * d
        kd = int(np.searchsorted(d1ct, np.datetime64(et), side="right")) - 1
        em = d1e200[kd]
        ema_near = (em - e) * d > 0 and (tg - em) * d > 0
        vert = (d1c[kd] - d1o[kd]) * d > 2 * d1atr[kd]
        j4 = int(np.searchsorted(t4, np.datetime64(et), side="left"))
        unconf = (c4[j4] - e) * d < 0 if j4 < len(c4) else False
        w = df[(df["t"] > et) & (df["t"] < et + pd.Timedelta(days=20))]
        hit = ((w["high"] >= tg) if d > 0 else (w["low"] <= tg)).any()
        rows.append({"stretched": bool(rsi_ok and band_ok), "macd_div_1h": bool(div),
                     "liq_under_stop": bool(((beyond > 0) & (beyond <= 0.5 * rk)).any()), "ema200_near": bool(ema_near),
                     "vertical_day": bool(vert), "unconfirmed_4h": bool(unconf),
                     "hunted": bool(r["net_base"] <= 0 and hit)})
    F = pd.DataFrame(rows, index=T.index)
    T = pd.concat([T.drop(columns=[c for c in F.columns if c in T.columns]), F], axis=1)
    T["loss"] = T["net_base"] <= 0
    T.to_pickle(ROOT / "results" / "selfreview.pkl")
    res = ~T["hold"]
    L = ["# Self-review: every journal pattern, checked on every v3.1 ETH trade", "",
         f"{len(T)} trades, one position per move ({int(T['loss'].sum())} losers). **win % = profit after all costs.** "
         "A pattern only explains losses if it is clearly more common in losers than in winners, in both periods.", ""]
    rows = []
    for c in PRE + POST:
        for per, pm in (("2022 - Oct 2025", res), ("holdout", ~res)):
            x = T[pm]
            f = x[c].astype(bool)
            rows.append({"p": NAMES[c], "when": "at entry" if c in PRE else "after entry", "per": per,
                         "loss_share": f[x["loss"]].mean(), "win_share": f[~x["loss"]].mean(), "n": int(f.sum()),
                         "w_with": (~x.loc[f, "loss"]).mean() if f.any() else math.nan,
                         "w_without": (~x.loc[~f, "loss"]).mean() if (~f).any() else math.nan,
                         "a_with": x.loc[f, "net_base"].mean() if f.any() else math.nan,
                         "a_without": x.loc[~f, "net_base"].mean()})
    R = pd.DataFrame(rows)
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    L += ["## Each pattern: losers vs winners", "", _table(R, [
        ("p", "pattern", str), ("when", "known", str), ("per", "period", str), ("loss_share", "in losers", _pct),
        ("win_share", "in winners", _pct), ("n", "trades with it", str), ("w_with", "win % with", _pct),
        ("w_without", "win % without", _pct), ("a_with", "avg R with", f2), ("a_without", "avg R without", f2)]), ""]
    # consistent separators: lower win % with the pattern in BOTH periods by >= 5 points
    cons = []
    for c in PRE + POST:
        a = R[(R["p"] == NAMES[c]) & (R["per"] == "2022 - Oct 2025")].iloc[0]
        b = R[(R["p"] == NAMES[c]) & (R["per"] == "holdout")].iloc[0]
        if a["w_with"] <= a["w_without"] - 0.05 and b["w_with"] <= b["w_without"] - 0.05:
            cons.append(NAMES[c])
    L += ["## Patterns that mark losers in BOTH periods (win % at least 5 points lower)", "",
          *(f"- {c}" for c in cons), "" if cons else "- none", ""]
    # how many patterns each loser had
    cnt = T[PRE].sum(axis=1)
    rows = []
    for k in range(0, int(cnt.max()) + 1):
        for per, pm in (("2022 - Oct 2025", res), ("holdout", ~res)):
            m = pm & (cnt == k)
            if m.any():
                rows.append({"k": k, "per": per, "n": int(m.sum()), "win": (~T.loc[m, "loss"]).mean(), "avg": T.loc[m, "net_base"].mean()})
    L += ["## Win % by the number of warning signs at entry", "", _table(pd.DataFrame(rows), [
        ("k", "warning signs at entry", str), ("per", "period", str), ("n", "trades", str), ("win", "win %", _pct),
        ("avg", "avg R", f2)]), ""]
    h = T[T["loss"]]
    L += [f"Losers that were hunted (stopped, then the target was reached within 20 days): "
          f"{h['hunted'].mean():.0%} (2022-25: {h.loc[~h['hold'], 'hunted'].mean():.0%}, holdout: {h.loc[h['hold'], 'hunted'].mean():.0%}).", ""]
    path = out_dir / "selfreview.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
