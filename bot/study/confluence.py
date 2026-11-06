"""
Confluence: all the studied concepts together on the bot's own trades (the research-chosen version: v3.1 + journal
filters + 0.786 bounce stop; 162 ETH trades). No one rule makes an excellent trade, so each concept VOTES for or against
the trade at its entry, with the direction of every vote fixed in advance from the studies (no fitting on these trades).
Everything from candles closed at the entry; oriented to the trade's direction.

For (+1):
  V1 RSI first push         4h RSI crossed above 70 (shorts: below 30) in the last 3 candles, the first time in 50
                            (indicator_deep: 69% vs 54%)
  V2 Bollinger strength      the last 4h candle reached the outer band in the trade's direction with a bulge (width in the
                            top 20% of 120 candles) or RSI > 75, or the daily candle at its band (bollinger.md)
  V3 breakout volume         breakouts: the breaking candle's volume >= 2x its 20-candle average (indicator_deep)
  V4 strong candle + trend   the breaking / signal candle is a displacement (range >= 1.5 ATR, body >= 80%) and the daily
                            close is on the trade's side of its EMA 200 (indicator_deep: 60% vs 43%)
  V5 liquidity close ahead   an untaken 1h swing high (shorts: low) within 1 ATR(1h) ahead of the entry (1h studies)
Against (-1):
  V6 ceiling before target   a resistance / untaken 4h high between the entry and the target (selfreview: 43% vs 68%)
  V7 trendline in the way    a valid trendline against the trade between the entry and the target (fixes.py TL flag)
  V8 weekly has no room      the weekly is stretched in the trade's direction: at its band, RSI >= 70 or above its
                            older highs (bb_pause_weekly W4 - W6; a lead, post hoc)
  V9 three failures against  a 1h three-failures trigger AGAINST the trade in the 6 hours before the entry
  V10 daily pause against    the daily made a pump the other way (a close beyond its outer band) in the last 20 days and
                            every close since stayed on that side of the middle band (the trader's middle-band read; the
                            27 Mar 2023 short went into one)
Score = sum of the votes. Research 2022 - Oct 2025, holdout Nov 2025 on. **win % = profit after costs.**
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import account, stats
from .defs import TF
from .fibliq import Swings
from .indicators import ema, rsi
from .mtf import resample
from .sr2_run import _pct, _table
from .three_failures import setups as tf_setups

HOLDOUT = pd.Timestamp("2025-11-01")
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
TFN = {2: "2h", 4: "4h", 24: "1D"}


def votes(cfg: Config) -> pd.DataFrame:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    tf = {k: TF(resample(df5u, k)) for k in ("1h", "2h", "4h", "1D", "1W")}
    t4, d1, w1, h1 = tf["4h"], tf["1D"], tf["1W"], tf["1h"]
    r4 = rsi(pd.Series(t4.c)).to_numpy(float)
    bw4 = (t4.up - t4.lo) / t4.mid
    rank4 = pd.Series(bw4).rolling(120, min_periods=60).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True).to_numpy()
    d200 = ema(pd.Series(d1.c), 200).to_numpy(float)
    rw = rsi(pd.Series(w1.c)).to_numpy(float)
    sw1 = Swings(df5u, "1h")
    # three-failures triggers on 1h, by direction of the failure ('short' = failures to go up)
    tf_trig = {s: [pd.Timestamp(h1.ct[j]) for j, _, _, k in tf_setups(h1, s) if k == "last push"] for s in (1, -1)}
    tf_trig = {s: np.array(v, dtype="datetime64[ns]") for s, v in tf_trig.items()}
    T, _ = pd.read_pickle(ROOT / "results" / "manager_states.pkl")
    T = T[(T["src"] == "v31") & T["filtered"] & (T["variant"] == "S786")].copy()
    X = pd.read_pickle(ROOT / "results" / "defs_review.pkl").reset_index(drop=True)
    F = pd.read_pickle(ROOT / "results" / "fixes.pkl")
    tl = F[(F["entry"] == "now") & (F["exit"] == "none") & (F["fib"] == "none")].set_index("entry_time")["TL"]
    rows = []
    for r in T.itertuples():
        et, d = pd.Timestamp(r.decision_time), int(r.d)
        x = X.loc[int(r.sig)]
        j4 = t4.closed_before(et) - 1
        jd = d1.closed_before(et) - 1
        jw = w1.closed_before(et) - 1
        jh = h1.closed_before(et) - 1
        o = lambda v: v if d > 0 else -v  # noqa: E731
        rr = r4 if d > 0 else 100 - r4
        v = {}
        # V1
        cross = [k for k in range(j4 - 2, j4 + 1) if rr[k] > 70 >= rr[k - 1]]
        v["V1 RSI first push"] = int(bool(cross) and not (rr[cross[-1] - 50:cross[-1]] > 70).any())
        # V2
        hi4 = t4.h[j4] if d > 0 else -t4.l[j4]
        band4 = t4.up[j4] if d > 0 else -t4.lo[j4]
        hid = d1.h[jd] if d > 0 else -d1.l[jd]
        bandd = d1.up[jd] if d > 0 else -d1.lo[jd]
        v["V2 Bollinger strength"] = int((hi4 >= band4 and ((np.isfinite(rank4[j4]) and rank4[j4] >= 0.8) or rr[j4] > 75))
                                         or hid >= bandd)
        # V3, V4 on the signal candle's own timeframe
        ts = tf[TFN[int(round(r.tf_h))]]
        js = ts.closed_before(et) - 1
        rng = ts.h[js] - ts.l[js]
        v["V3 breakout volume 2x"] = int(r.setup != "1D bounce" and ts.v[js] >= 2 * ts.v[max(0, js - 20):js].mean())
        disp = rng >= 1.5 * ts.a[js] and o(ts.c[js] - ts.o[js]) >= 0.8 * rng
        v["V4 strong candle with the daily trend"] = int(bool(disp) and np.isfinite(d200[jd]) and o(d1.c[jd] - d200[jd]) > 0)
        # V5
        side = "H" if d > 0 else "L"
        lv = sw1.untaken(et, side)
        a1 = h1.a[jh]
        e = r.e
        v["V5 liquidity within 1 ATR ahead"] = int(len(lv) > 0 and np.any((o(lv - e) > 0) & (o(lv - e) <= a1)))
        # V6, V7
        v["V6 ceiling before the target"] = -int(bool(x["ceiling"]))
        tlv = tl.get(pd.Timestamp(r.entry_time), False)
        v["V7 trendline in the way"] = -int(bool(tlv.iloc[0] if hasattr(tlv, "iloc") else tlv))
        # V8 weekly has no room
        hiw = w1.h[jw] if d > 0 else -w1.l[jw]
        upw = w1.up[jw] if d > 0 else -w1.lo[jw]
        cw = o(w1.c[jw])
        old_hi = (w1.h[jw - 52:jw - 4].max() if d > 0 else -w1.l[jw - 52:jw - 4].min()) if jw >= 52 else np.nan
        rwo = rw[jw] if d > 0 else 100 - rw[jw]
        no_room = (np.isfinite(upw) and hiw >= upw) or (np.isfinite(rwo) and rwo >= 70) or (old_hi == old_hi and cw >= old_hi)
        v["V8 weekly has no room"] = -int(bool(no_room))
        # V9 three failures against the trade in the 6 hours before entry: failures to go UP (setups side +1) are against
        # a long; failures to go DOWN (side -1) are against a short
        trig = tf_trig[1] if d > 0 else tf_trig[-1]
        et64 = np.datetime64(et)
        v["V9 three failures against"] = -int(bool(np.any((trig <= et64) & (trig > et64 - np.timedelta64(6, "h")))))
        # V10 daily pause against: a daily pump the OTHER way (od = -d) in the last 20 days, every close since on that
        # side of the middle band
        od = -d
        cc = od * d1.c
        band_o = od * (d1.up if od > 0 else d1.lo)
        mid_o = od * d1.mid
        pumps = [k for k in range(max(0, jd - 20), jd + 1) if np.isfinite(band_o[k]) and cc[k] > band_o[k]]
        pause = bool(pumps) and pumps[-1] < jd and bool(np.all(cc[pumps[-1] + 1:jd + 1] > mid_o[pumps[-1] + 1:jd + 1]))
        v["V10 daily pause against"] = -int(pause)
        rows.append({"setup": r.setup, "entry_time": r.entry_time, "decision_time": et, "exit_time": r.exit_time, "net": r.net,
                     "stop_pct": r.sp, "hold": et >= HOLDOUT, **v})
    D = pd.DataFrame(rows)
    D["score"] = D[[c for c in D.columns if c.startswith("V")]].sum(axis=1)
    return D


def run_confluence(cfg: Config, out_dir: Path) -> Path:
    D = votes(cfg)
    D.to_pickle(ROOT / "results" / "confluence.pkl")
    res = ~D["hold"] & (D["exit_time"] < HOLDOUT)
    vc = [c for c in D.columns if c.startswith("V")]
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    rows = []
    for c in vc:
        for per, pm in (("2022 - Oct 2025", res), ("holdout", D["hold"])):
            g = D[pm]
            on, off = g[g[c] != 0], g[g[c] == 0]
            rows.append({"v": c, "per": per, "n": len(on), "w": (on["net"] > 0).mean() if len(on) else np.nan,
                         "a": on["net"].mean() if len(on) else np.nan, "n0": len(off), "w0": (off["net"] > 0).mean(),
                         "a0": off["net"].mean()})
    srows = []
    for lab, lo, hi in (("score <= -2", -99, -2), ("score -1", -1, -1), ("score 0", 0, 0), ("score +1", 1, 1), ("score >= +2", 2, 99)):
        for per, pm in (("2022 - Oct 2025", res), ("holdout", D["hold"])):
            g = D[pm & (D["score"] >= lo) & (D["score"] <= hi)]
            s_ = stats(g["net"].to_numpy())
            srows.append({"lab": lab, "per": per, **s_})
    arows = []
    for lab, m in (("all trades", D["score"] > -99), ("skip score <= -1", D["score"] >= 0), ("skip score <= -2", D["score"] >= -1)):
        for per, pm in (("2022 - Oct 2025", res), ("holdout", D["hold"])):
            g = D[pm & m].reset_index(drop=True)
            s_ = stats(g["net"].to_numpy())
            eq, dd = account(g, "net", "exit_time", RISK) if len(g) else (np.nan, np.nan)
            arows.append({"lab": lab, "per": per, **s_, "eq": eq, "dd": dd})
    L = ["# Confluence: all the studied concepts voting on the bot's own trades", "",
         "162 ETH trades of the research-chosen version (v3.1 + journal filters + 0.786 bounce stop). Each concept votes +1 "
         "(for) or -1 (against) at the entry; the directions were fixed from the studies before looking at these trades. "
         "**win % = profit after costs.** Small samples: this shows the direction, not proof.", "",
         "## Each vote", "", _table(pd.DataFrame(rows), [
             ("v", "vote", str), ("per", "period", str), ("n", "trades with the vote", str), ("w", "win %", _pct),
             ("a", "avg R", f2), ("n0", "trades without", str), ("w0", "win %", _pct), ("a0", "avg R", f2)]), "",
         "## By total score", "", _table(pd.DataFrame(srows), [
             ("lab", "score", str), ("per", "period", str), ("n", "trades", str), ("win", "win %", _pct), ("avg", "avg R", f2),
             ("pf", "profit factor", lambda v: "" if v != v else f"{v:.2f}")]), "",
         "## Using the score as a filter", "", _table(pd.DataFrame(arows), [
             ("lab", "rule", str), ("per", "period", str), ("n", "trades", str), ("win", "win %", _pct), ("avg", "avg R", f2),
             ("eq", "account", lambda v: "" if v != v else f"{v:.2f}x"), ("dd", "worst drop", lambda v: "" if v != v else f"-{v:.0%}")]), "",
         "Audit: pending."]
    path = out_dir / "confluence.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_confluence(load_config(ROOT / "config.yaml"), ROOT / "reports"))
