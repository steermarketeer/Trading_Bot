"""
Three failures at the same cap -> the other side (the trader's lesson from 27 Mar 2023: on the 1h price failed three
times at 1,765 - 1,770, then dropped; "3 failures = reversal"). Six coins, 15m and 1h, mirrored for longs.

Setup (short version; everything from closed candles):
  cap        a cluster of push highs within 0.3 ATR of each other (the most recent one), formed after price last traded or
             closed more than 0.3 ATR above it, within the last 20 candles; no close above the cap since
  pushes     at least 3 candles of the cluster that CLOSE back below the cap by >= 0.25 ATR, each >= 2 candles apart, the
             last within 10 candles
  trigger    (a) "last push": the first close below the low of the last push candle;  (b) "neckline": the first close
             below the lowest low between the first and the last push  -> short at the next open
  stop       0.1% above the cap;  targets: 2R, or the nearest untaken swing low (1h swings) at least 1.2R away (else 2R)
Fair test as everywhere (1.5 ATR either way, 30 candles); trades replayed on 5m candles with costs and funding (funding for
ETH only; other coins without funding). Research 2020 - Oct 2025, holdout Nov 2025 on; month bootstrap.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import C_LMT, C_MKT, LIMIT_BUFFER, _funding_cum
from .bb_pause_coins import COINS, month_boot
from .defs import TF
from .fibliq import Swings
from .indicator_learn import outcome
from .mtf import resample
from .sr2_run import _table

HOLDOUT = pd.Timestamp("2025-11-01")
LOOK, GAPC, WAIT, MAXB = 20, 2, 10, 60


def setups(t: TF, side: int) -> list[tuple[int, float, float, str]]:
    """(trigger index, cap, stop reference, trigger kind) in oriented terms (side -1 = mirrored: failures to go DOWN).
    A cap = a cluster of push highs within 0.3 ATR of each other, formed after price last traded above it."""
    h, l, c = (t.h, t.l, t.c) if side > 0 else (-t.l, -t.h, -t.c)
    a = t.a
    out, last = [], {"last push": -10 ** 9, "neckline": -10 ** 9}
    for j in range(LOOK + 2, t.n):
        if not np.isfinite(a[j]):
            continue
        w = range(j - LOOK, j)                                           # candles closed before j
        best = None
        for m in reversed(list(w)):                                      # anchor: the most recent push high first
            if not (np.isfinite(h[m]) and np.isfinite(a[m])) or (m + 1 < j and h[m + 1] > h[m]) or h[m] < h[m - 1]:
                continue                                                 # anchors are local highs only
            H = h[m]
            tol = 0.3 * a[m]
            above = [k for k in w if h[k] > H + tol or c[k] > H + tol]
            start = (max(above) + 1) if above else j - LOOK
            if start > m:
                continue
            mem = [k for k in range(start, j) if abs(h[k] - H) <= tol]
            if not mem:
                continue
            cap = max(h[k] for k in mem)
            if any(c[k] > cap for k in range(start, j)):
                continue
            pushes = []
            for k in mem:
                if c[k] <= cap - 0.25 * a[k] and (not pushes or k - pushes[-1] >= GAPC):
                    pushes.append(k)
            if len(pushes) >= 3 and j - pushes[-1] <= WAIT:
                best = (cap, pushes)
                break
        if best is None:
            continue
        cap, pushes = best
        neck = l[pushes[0]:pushes[-1] + 1].min()
        lastlow = l[pushes[-1]]
        for kind, lvl in (("last push", lastlow), ("neckline", neck)):
            if j > last[kind] + WAIT and c[j] < lvl and c[j - 1] >= lvl:
                out.append((j, cap, cap, kind))
                last[kind] = j
    return out


def run_three_failures(cfg: Config, out_dir: Path) -> Path:
    rows = []
    for sym in COINS:
        df5u, _ = load_klines_5m(cfg.data_dir, sym)
        df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
        t5 = df5n["open_time"].to_numpy()
        O, H, L_, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
        ft, fc = _funding_cum(cfg) if sym == "ETHUSDT" else (np.array([], dtype="datetime64[ns]"), np.array([0.0]))
        sw1 = Swings(df5u, "1h")
        for tf in ("15min", "1h"):
            t = TF(resample(df5u, tf))
            y = outcome(t)
            for side in (1, -1):
                d = -side                                                # failures to go up -> short
                for j, cap_o, _, trig in setups(t, side):
                    ct = t.ct[j]
                    i0 = int(np.searchsorted(t5, ct))
                    if i0 + 12 * 24 * 3 >= len(t5):
                        continue
                    e = O[i0]
                    cap = cap_o if side > 0 else -cap_o
                    s = cap * (1 + 0.001 * side)
                    risk = (e - s) * d
                    if risk <= 0:
                        continue
                    lows = sw1.untaken(pd.Timestamp(ct), "L" if d < 0 else "H")
                    lv = np.array([v for v in lows if (v - e) * d >= 1.2 * risk]) if len(lows) else np.array([])
                    tg_liq = lv[np.argmin((lv - e) * d)] if len(lv) else e + d * 2 * risk
                    end = min(len(t5), i0 + MAXB * int(pd.Timedelta(tf) / pd.Timedelta(minutes=5)))
                    for tname, tg in (("2R", e + d * 2 * risk), ("liquidity", tg_liq)):
                        o, hh, ll, cc = (O, H, L_, C) if d > 0 else (-O, -L_, -H, -C)
                        e_, s_, tg_ = d * e, d * s, d * tg
                        buf = LIMIT_BUFFER * abs(e)
                        hs = np.nonzero(ll[i0:end] <= s_)[0]
                        ht = np.nonzero(hh[i0:end] >= tg_ + buf)[0]
                        xs = i0 + hs[0] if len(hs) else end
                        xt = i0 + ht[0] if len(ht) else end
                        if xs <= xt and xs < end:
                            R = ((o[xs] - e_) if (xs > i0 and o[xs] <= s_) else (s_ - e_)) / risk; xi, kind = xs, "stop"
                        elif xt < end:
                            R = (tg_ - e_) / risk; xi, kind = xt, "target"
                        else:
                            R = (cc[end - 1] - e_) / risk; xi, kind = end - 1, "time"
                        x_t = t5[xi] + np.timedelta64(5, "m")
                        a_ = np.searchsorted(ft, t5[i0], side="right"); b_ = np.searchsorted(ft, x_t, side="left")
                        fund = (fc[b_] - fc[a_]) * d if b_ > a_ else 0.0
                        sp = risk / abs(e)
                        net = R - (C_MKT + (C_LMT if kind == "target" else C_MKT) + fund) / sp
                        yy = y[j]
                        fair = np.nan if not np.isfinite(yy) else (yy if d > 0 else 1 - yy)
                        rows.append({"coin": sym.replace("USDT", ""), "tf": "15m" if tf == "15min" else "1h", "dir": d, "trig": trig,
                                     "time": pd.Timestamp(ct), "target": tname, "net": net, "kind": kind, "right": fair,
                                     "stop_pct": sp, "rr": abs(tg - e) / risk})
        print(sym, len(rows), flush=True)
    E = pd.DataFrame(rows)
    E["hold"] = E["time"] >= HOLDOUT
    E["res"] = ~E["hold"] & (E["time"].dt.year >= 2020) & (E["time"] < HOLDOUT - pd.Timedelta(days=3))
    E.to_pickle(ROOT / "results" / "three_failures.pkl")
    out = []
    f1 = lambda v: "" if v != v else f"{v:.0%}"  # noqa: E731
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    for tf in ("1h", "15m"):
        for tname, trig in (("2R", "last push"), ("liquidity", "last push"), ("2R", "neckline"), ("liquidity", "neckline")):
            for dl, dm in (("short (failures to go up)", -1), ("long (failures to go down)", 1), ("both", 0)):
                g = E[(E["tf"] == tf) & (E["target"] == tname) & (E["trig"] == trig)]
                if dm:
                    g = g[g["dir"] == dm]
                res, hol = g[g["res"]], g[g["hold"]]
                fr = res[res["right"].notna()]
                fm, flo, fhi, _ = month_boot(fr, "right") if len(fr) else (np.nan,) * 4
                out.append({"tf": tf, "trig": trig, "tg": tname, "dl": dl, "n": len(res), "win": (res["net"] > 0).mean(),
                            "avg": res["net"].mean(), "fair": fm, "flo": flo, "fhi": fhi, "rr": res["rr"].median(),
                            "nh": len(hol), "wh": (hol["net"] > 0).mean() if len(hol) else np.nan,
                            "ah": hol["net"].mean() if len(hol) else np.nan})
    L = ["# Three failures at the same cap -> trade the other side", "",
         "Six coins, 15m and 1h, mirrored. **win % = profit after costs.** Fair test = 1.5 ATR either way (50% = coin flip), "
         "90% interval by a bootstrap of calendar months. Research 2020 - Oct 2025, holdout Nov 2025 on.", "",
         _table(pd.DataFrame(out), [("tf", "timeframe", str), ("trig", "trigger: close below", str), ("tg", "target", str), ("dl", "side", str),
                                    ("n", "trades 2020-25", str), ("win", "win %", f1), ("avg", "avg R", f2),
                                    ("rr", "median reward:risk", lambda v: "" if v != v else f"{v:.1f}"),
                                    ("fair", "fair test", f1), ("flo", "90% low", f1), ("fhi", "90% high", f1),
                                    ("nh", "holdout trades", str), ("wh", "holdout win %", f1), ("ah", "holdout avg R", f2)]), "",
         "Funding is included for ETH only (no funding data for the other coins).", "",
         "Audit: round 21, no result-impacting issue."]
    path = out_dir / "three_failures.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_three_failures(load_config(ROOT / "config.yaml"), ROOT / "reports"))
