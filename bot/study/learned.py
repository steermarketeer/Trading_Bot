"""
What the indicator / Bollinger studies taught, applied to the current best version (v3.1 + journal filters + bounce stop
below the 0.786 + strong breaking candle). Rules were written from the general studies (docs/indicators.md) BEFORE
looking at these trades; nothing is tuned on them. Everything at the entry uses candles closed at the entry.

Entry filters (skip the trade):
  R1 weak band touch    the last 4h candle reached the outer band in the trade's direction with a wick against the
                        trade (close in the far half of the candle) while BandWidth is not above 3 candles ago
  R2 fading momentum    a long with 4h RSI < 30 / a short with 4h RSI > 70 (the "buy oversold" idea lost every year)
  R3 squeeze vs trend   the last 4h candle is a squeeze breakout (BandWidth in the lowest 20% of 120 candles 5 candles
                        before, close beyond the band) against the daily trend (daily close vs daily EMA 50)
  R4 thin breakout      breakouts only: breaking-candle volume below its 20-candle average
  R5 against the regime the daily close is on the wrong side of the daily EMA 200 (shown for information)
  R6 breakout volume below 2x     breakouts: the breaking candle's volume < 2x its 20-candle average (deep study)
  R7 RSI divergence at a breakout the last 4h candle makes a 30-candle high with RSI > 60 but below the RSI peak of
                                  candles j-30 .. j-6 (momentum fading)
  R8 shallow pullback             1D bounces: in the last 4h up-leg (confirmed swing low -> highest high, > 3 ATR) the
                                  pullback since the high retraced < 0.45 of the leg (the 0.382 pullbacks failed)
Exit:
  X  1D bounces only: a 4h candle within 3 days touches the 4h middle band (low <= middle + 0.25 ATR) -> exit at the
     next open (the pullback that marked the weak bounces)
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import MAX_TF_BARS, _funding_cum, account, stats
from .defs import TF
from .indicators import ema, rsi
from .mtf import resample
from .pullback import booked, replay
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}


def run_learned(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t5 = df5n["open_time"].to_numpy()
    M = {"t5": t5, "fund": _funding_cum(cfg), **{k: df5n[x].to_numpy(float) for k, x in
                                                 (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}}
    t4, d1 = TF(resample(df5u, "4h")), TF(resample(df5u, "1D"))
    tfs = {"2h": TF(resample(df5u, "2h")), "4h": t4, "1D": d1}
    r4 = rsi(pd.Series(t4.c)).to_numpy(float)
    bw = (t4.up - t4.lo) / t4.mid
    rank = pd.Series(bw).rolling(120, min_periods=60).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True).to_numpy()
    de50, de200 = (ema(pd.Series(d1.c), k).to_numpy(float) for k in (50, 200))
    T, _ = pd.read_pickle(ROOT / "results" / "manager_states.pkl")
    T = T[(T["src"] == "v31") & T["filtered"] & (T["variant"] == "S786") & T["BQ"]].copy()
    rows = []
    for r in T.itertuples():
        et = pd.Timestamp(r.decision_time); d = int(r.d)
        j = t4.closed_before(et) - 1
        jd = d1.closed_before(et) - 1
        h, l, c = (t4.h[j], t4.l[j], t4.c[j]) if d > 0 else (-t4.l[j], -t4.h[j], -t4.c[j])
        band = t4.up[j] if d > 0 else -t4.lo[j]
        out_c = (t4.c[j] > t4.up[j]) if d > 0 else (t4.c[j] < t4.lo[j])
        f = {"R1": bool(h >= band and (c - l) < 0.5 * (h - l) and bw[j] <= bw[j - 3]),
             "R2": bool((r4[j] < 30) if d > 0 else (r4[j] > 70)),
             "R3": bool(np.isfinite(rank[j - 5]) and rank[j - 5] <= 0.2 and out_c and (d1.c[jd] - de50[jd]) * d < 0),
             "R4": False,
             "R5": bool((d1.c[jd] - de200[jd]) * d < 0)}
        f["R6"] = f["R7"] = f["R8"] = False
        if r.setup != "1D bounce":
            tb = tfs[{2: "2h", 4: "4h", 24: "1D"}[int(round(r.tf_h))]]
            jb = tb.closed_before(et) - 1
            vavg = tb.v[max(0, jb - 20):jb].mean()
            f["R4"] = bool(tb.v[jb] < vavg)
            f["R6"] = bool(tb.v[jb] < 2 * vavg)
            rr = r4 if d > 0 else 100 - r4                                   # 4h RSI, oriented
            hh = t4.h if d > 0 else -t4.l
            prev_peak = np.nanmax(rr[j - 30:j - 5])
            f["R7"] = bool(hh[j] >= np.max(hh[j - 30:j]) and rr[j] > 60 and prev_peak > rr[j])
        else:
            # how deep the pullback was in the last 4h up-leg (confirmed swing low -> highest high since), at the entry
            lows = [(i, p) for i, p, cf in (t4.sl if d > 0 else t4.sh) if cf <= j]
            if lows:
                i_lo, p_lo = lows[-1]
                seg = t4.h[i_lo:j + 1] if d > 0 else t4.l[i_lo:j + 1]
                p_hi = seg.max() if d > 0 else seg.min()
                i_hi = i_lo + int(np.argmax(seg) if d > 0 else np.argmin(seg))
                if i_hi < j:                                                     # candles after the high only
                    after = t4.l[i_hi + 1:j + 1].min() if d > 0 else t4.h[i_hi + 1:j + 1].max()
                else:
                    after = p_hi                                                 # no pullback yet: depth 0
                leg = (p_hi - p_lo) * d
                if leg > 3 * t4.a[j]:
                    depth = (p_hi - after) * d / leg
                    f["R8"] = bool(depth < 0.45)
        net_x, exit_x, kind_x = r.net, r.exit_time, r.kind
        if r.setup == "1D bounce":
            j0 = t4.closed_before(et)
            for k in range(j0, min(t4.n, j0 + 18)):
                ct = np.datetime64(pd.Timestamp(t4.ct[k]))
                if ct >= np.datetime64(r.exit_time):
                    break
                touch = (t4.l[k] <= t4.mid[k] + 0.25 * t4.a[k]) if d > 0 else (t4.h[k] >= t4.mid[k] - 0.25 * t4.a[k])
                if touch:
                    fx = int(np.searchsorted(t5, ct))
                    R, xi, kind = replay(M, int(r.i0), int(r.end), d, r.e, r.s, r.tg, fx)
                    net_x, exit_x = booked(M, int(r.i0), xi, kind, d, R, r.sp)
                    kind_x = kind
                    break
        rows.append({"setup": r.setup, "entry_time": r.entry_time, "decision_time": et, "exit_time": r.exit_time,
                     "net": r.net, "net_x": net_x, "exit_x": exit_x, "kind_x": kind_x, "stop_pct": r.sp, "d": d,
                     "hold": et >= HOLDOUT, **f})
    D = pd.DataFrame(rows)
    D.to_pickle(ROOT / "results" / "learned.pkl")
    res = ~D["hold"] & (D["exit_time"] < HOLDOUT)
    names = {"R1": "R1 weak band touch at entry", "R2": "R2 fading momentum (buy RSI < 30 / sell RSI > 70)",
             "R3": "R3 squeeze breakout against the daily trend", "R4": "R4 breakout on thin volume",
             "R5": "R5 against the daily EMA 200 (information)",
             "R6": "R6 breakout volume below 2x (2x proven to help; 1-2x failing is not proven)",
             "R7": "R7 bearish RSI divergence at a breakout (4h)",
             "R8": "R8 1D bounce after only a shallow 4h pullback (< 0.45 of the leg)"}
    rows = []
    for key, nm in names.items():
        for per, pm in (("2022 - Oct 2025", res), ("holdout", D["hold"])):
            g = D[pm]; sk = g[g[key]]; kp = g[~g[key]]
            rows.append({"rule": nm, "per": per, "skipped": len(sk), "sk_loss": int((sk["net"] <= 0).sum()),
                         "sk_win": int((sk["net"] > 0).sum()), "sk_r": sk["net"].sum(), "n": len(kp),
                         "w": (kp["net"] > 0).mean(), "a": kp["net"].mean()})
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    base = []
    for nm, col, msk in (("current best version", "net", None), ("+ R1 + R2 + R3 + R4 (all learned filters)", "net", ["R1", "R2", "R3", "R4"]),
                         ("+ R6 + R7 + R8 (deep-study filters)", "net", ["R6", "R7", "R8"]),
                         ("+ exit X (bounce touches the 4h middle band)", "net_x", None)):
        for per, pm in (("2022 - Oct 2025", res), ("holdout", D["hold"])):
            g = D[pm]
            if msk:
                g = g[~g[msk].any(axis=1)]
            s_ = stats(g[col].to_numpy())
            gg = g.assign(setup=g["setup"]).reset_index(drop=True)
            eq, dd = account(gg, col, "exit_x" if col == "net_x" else "exit_time", RISK)
            base.append({"v": nm, "per": per, **s_, "eq": eq, "dd": dd})
    L = ["# What the indicator studies taught, applied to the current best version", "",
         "Rules written from the general studies (docs/indicators.md) before looking at these trades. "
         "**win % = profit after costs.** 2022 - Oct 2025 and the holdout (Nov 2025 on).", "",
         _table(pd.DataFrame(base), [("v", "version", str), ("per", "period", str), ("n", "trades", str), ("win", "win %", _pct),
                                     ("avg", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}"),
                                     ("eq", "account", lambda v: f"{v:.2f}x"), ("dd", "worst drop", lambda v: f"-{v:.0%}")]), "",
         "## Each rule: which trades it would skip", "",
         _table(pd.DataFrame(rows), [("rule", "rule", str), ("per", "period", str), ("skipped", "skipped", str),
                                     ("sk_loss", "of them losers", str), ("sk_win", "of them winners", str),
                                     ("sk_r", "R of the skipped trades", f2), ("n", "trades kept", str),
                                     ("w", "win % kept", _pct), ("a", "avg R kept", f2)]), ""]
    path = out_dir / "learned.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_learned(load_config(ROOT / "config.yaml"), ROOT / "reports"))
