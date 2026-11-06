"""
Self-review rerun with the precise definitions (docs/trading_definitions.md, bot/study/defs.py), on every v3.1 ETH trade
(one position per move). Patterns are kept separate: equal highs / lows (double / triple tops / bottoms) are not
rejections, and rejections are not touches.

At entry (longs; shorts mirrored):
  rej_at_ceiling      >= 1 rejection (4h) in the last 30 4h candles at the nearest resistance between entry and target
  rej_3plus           3+ rejections + failed pushes at that resistance (the "4 rejects" read)
  pushes_falling      after the last rejection, 2+ failed pushes, each lower than the last
  dtop_before_1h      a confirmed 1h double / triple top in the last 2 days, entry below its neckline (pattern against)
  eq_highs_ahead      untaken 1h / 4h equal highs between entry and target (buy-side liquidity = fuel)
  eq_lows_at_stop     untaken 15m / 1h equal lows within 0.5R beyond the stop (sell-side pool under the stop)
After entry, before the trade ended:
  dtop_15m_after      a 15m double / triple top formed after entry and confirmed (close below its neckline)
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .defs import TF, equal_levels, failed_pushes, rejections
from .levels import _level_table, strong_levels
from .mtf import resample
from .sr2_run import _pct, _table

TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
NEW = {"rej_at_ceiling": "Rejected (4h) at the resistance between entry and target",
       "rej_3plus": "3+ rejections / failed pushes at that resistance",
       "pushes_falling": "Failed pushes each lower than the last",
       "dtop_before_1h": "Confirmed 1h double / triple top against the trade, before entry",
       "eq_highs_ahead": "Untaken equal highs (double / triple top) between entry and target",
       "eq_lows_at_stop": "Untaken equal lows within 0.5R beyond the stop",
       "dtop_15m_after": "15m double / triple top after entry, confirmed (neckline close)"}


def run_defs_review(cfg: Config, out_dir: Path) -> Path:
    T = pd.read_pickle(ROOT / "results" / "selfreview.pkl")
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    tf = {k: TF(resample(df5u, r)) for k, r in (("15m", "15min"), ("1h", "1h"), ("4h", "4h"))}
    table = _level_table(df5u)
    rows = []
    for _, r in T.iterrows():
        et, d, e, rk = pd.Timestamp(r["entry_time"]), int(r["direction"]), float(r["px"]), float(r["risk"])
        s, tg = e - d * rk, e + d * TGT[r["setup"]] * rk
        hi_side, lo_side = ("H", "L") if d > 0 else ("L", "H")
        out = {}
        # nearest ceiling between entry and target: strong zones + untaken 4h swings on the target side
        t4 = tf["4h"]; n4 = t4.closed_before(et)
        z = strong_levels(table, et.tz_localize("UTC"))
        sw = [p for i, p, cf in (t4.sh if d > 0 else t4.sl) if cf < n4 and i >= n4 - 150
              and ((t4.h[i + 1:n4].max() <= p) if d > 0 else (t4.l[i + 1:n4].min() >= p))]
        lv = np.array(list(z) + sw)
        ahead = lv[((lv - e) * d > 0) & ((tg - lv) * d > 0)] if len(lv) else np.array([])
        if len(ahead):
            ceil = ahead[np.argmin((ahead - e) * d)]
            side = "R" if d > 0 else "S"
            rej = rejections(t4, ceil, side, n4 - 30, n4)
            fp = failed_pushes(t4, ceil, side, (rej[-1] + 1) if rej else n4, n4)
            ext = [t4.h[j] if d > 0 else -t4.l[j] for j in fp]
            out["rej_at_ceiling"] = len(rej) > 0
            out["rej_3plus"] = len(rej) > 0 and len(rej) + len(fp) >= 3
            out["pushes_falling"] = len(fp) >= 2 and bool(np.all(np.diff(ext) < 0))
        else:
            out["rej_at_ceiling"] = out["rej_3plus"] = out["pushes_falling"] = False
        # confirmed 1h double / triple top (bottom for shorts) in the last 2 days, price beyond its neckline
        t1 = tf["1h"]; n1 = t1.closed_before(et)
        pats = [x for x in equal_levels(t1, hi_side, n1, lookback=150) if x.confirmed_at >= n1 - 48]
        out["dtop_before_1h"] = any((e - x.valley) * d < 0 for x in pats)
        # untaken equal highs between entry and target (1h, 4h)
        fuel = [x for k in ("1h", "4h") for x in equal_levels(tf[k], hi_side, tf[k].closed_before(et))
                if x.taken_at < 0 and (x.price - e) * d > 0 and (tg - x.price) * d >= 0]
        out["eq_highs_ahead"] = len(fuel) > 0
        # untaken equal lows within 0.5R beyond the stop (15m, 1h)
        pool = [x for k in ("15m", "1h") for x in equal_levels(tf[k], lo_side, tf[k].closed_before(et))
                if x.taken_at < 0 and 0 < (s - x.price) * d <= 0.5 * rk]
        out["eq_lows_at_stop"] = len(pool) > 0
        # 15m double / triple top after entry, confirmed before the trade ended
        t15 = tf["15m"]; i0 = t15.closed_before(et); i1 = t15.closed_before(pd.Timestamp(r["exit_base"]))
        after = [x for x in equal_levels(t15, hi_side, i1, lookback=max(10, i1 - i0 + 10))
                 if max(x.idx) >= i0 and x.confirmed_at >= i0 and x.confirmed_at < i1]   # last top after entry
        out["dtop_15m_after"] = len(after) > 0
        rows.append(out)
    F = pd.DataFrame(rows, index=T.index)
    X = pd.concat([T, F], axis=1)
    X.to_pickle(ROOT / "results" / "defs_review.pkl")
    res = ~X["hold"]
    L = ["# Self-review with the precise definitions", "",
         f"{len(X)} v3.1 ETH trades, one position per move ({int(X['loss'].sum())} losers). **win % = profit after costs.** "
         "Definitions: docs/trading_definitions.md. A pattern marks losers only if the win % with it is clearly lower in "
         "BOTH periods.", ""]
    rows = []
    for c, name in NEW.items():
        for per, pm in (("2022 - Oct 2025", res), ("holdout", ~res)):
            x = X[pm]; f = x[c].astype(bool)
            rows.append({"p": name, "per": per, "n": int(f.sum()), "loss_share": f[x["loss"]].mean(),
                         "win_share": f[~x["loss"]].mean(),
                         "w_with": (~x.loc[f, "loss"]).mean() if f.any() else math.nan,
                         "w_without": (~x.loc[~f, "loss"]).mean() if (~f).any() else math.nan,
                         "a_with": x.loc[f, "net_base"].mean() if f.any() else math.nan,
                         "a_without": x.loc[~f, "net_base"].mean()})
    R = pd.DataFrame(rows)
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    L += ["## Each pattern", "", _table(R, [
        ("p", "pattern", str), ("per", "period", str), ("n", "trades with it", str), ("loss_share", "in losers", _pct),
        ("win_share", "in winners", _pct), ("w_with", "win % with", _pct), ("w_without", "win % without", _pct),
        ("a_with", "avg R with", f2), ("a_without", "avg R without", f2)]), ""]
    cons = []
    for c, name in NEW.items():
        a = R[(R["p"] == name) & (R["per"] == "2022 - Oct 2025")].iloc[0]
        b = R[(R["p"] == name) & (R["per"] == "holdout")].iloc[0]
        if a["n"] >= 10 and b["n"] >= 3 and a["w_with"] <= a["w_without"] - 0.05 and b["w_with"] <= b["w_without"] - 0.05:
            cons.append(name)
    L += ["## Marks losers in both periods", "", *(f"- {c}" for c in cons), "" if cons else "- none", ""]
    old = ["ema200_near", "falling_highs", "second_try", "unconfirmed_4h"]
    newc = [NEW[c] for c in NEW]
    lo = X[X["loss"]]
    expl_old = lo[old].any(axis=1)
    expl_new = lo[[c for c, nm in NEW.items() if nm in cons]].any(axis=1) if cons else pd.Series(False, index=lo.index)
    wi = X[~X["loss"]]
    w_old = wi[old].any(axis=1)
    w_new = wi[[c for c, nm in NEW.items() if nm in cons]].any(axis=1) if cons else pd.Series(False, index=wi.index)
    L += ["## How selective the markers are (a marker that also flags most winners explains nothing)", "",
          f"- earlier markers (EMA 200 in the way, falling 4h highs, second try, no 4h confirmation): flag "
          f"{int(expl_old.sum())} of {len(lo)} losers and {int(w_old.sum())} of {len(wi)} winners",
          f"- new markers above: flag {int(expl_new.sum())} of {len(lo)} losers and {int(w_new.sum())} of {len(wi)} winners",
          f"- either: {int((expl_old | expl_new).sum())} losers and {int((w_old | w_new).sum())} winners", ""]
    path = out_dir / "defs_review.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
