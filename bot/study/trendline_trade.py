"""
Is there a TRADE at the trendline retest? (The trader: "at the retest the trade exists".) Six coins, 1h and 4h, both
directions. Separate from the Bollinger studies.

Breaks and retests exactly as bot/study/trendline_retest.py (line through the last two confirmed swing lows, rising;
mirrored for falling lines through swing highs; break = first close beyond the line by >= 0.25 ATR; retest = a later
candle within 20 whose high comes back within 0.25 ATR of the line).
  RETEST trade  the first retest candle CLOSES back on the broken side (rejected) -> enter at the next open (after the close), in the break's
                direction; stop 0.1% beyond the retest candle's extreme (its high for a rising line broken down)
  BREAK trade   the comparison: enter at the next open after the break candle; stop 0.1% beyond the line + 0.25 ATR at the
                break candle (where a retest that fails would go)
  strict        only retests after price first moved >= 1 ATR away (the real retests)
Targets: 2R, 3R, and a liquidity target if it is >= 1.2R away, else 2R: for the RETEST trade the break's low before the
retest (the extreme between the break and the retest: the liquidity it left, known at the retest entry); for the BREAK
trade only the break candle's own extreme (known at its entry). Exits on 5m candles, stop first; 60 candles max; costs: market in,
limit target / market stop and time exit, funding for ETH only (other coins: no funding data). **win % = profit after costs.**
Research 2020 - Oct 2025, holdout Nov 2025 on.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import C_LMT, C_MKT, LIMIT_BUFFER, _funding_cum, stats
from .bb_pause_coins import COINS
from .defs import TF
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
WIN, MAXB = 20, 60


def events(t: TF, side: int):
    """Yield (break j, retest k or None, strict, line value at j, line value at k, extreme between) in ORIENTED terms."""
    if side > 0:
        h, l, c, pts = t.h, t.l, t.c, t.sl
    else:
        h, l, c, pts = -t.l, -t.h, -t.c, [(i, -p, cf) for i, p, cf in t.sh]
    arr = np.array(pts, float).reshape(-1, 3)
    a = t.a
    used = set()
    for j in range(30, t.n - WIN - 1):
        if not np.isfinite(a[j]):
            continue
        k1 = int(np.searchsorted(arr[:, 2], j - 1, side="right"))
        if k1 < 2:
            continue
        (i1, p1, _), (i2, p2, _) = arr[k1 - 2], arr[k1 - 1]
        if not p2 > p1 or (i1, i2) in used:
            continue
        sl_ = (p2 - p1) / (i2 - i1)
        line = lambda x: p1 + sl_ * (x - i1)  # noqa: E731
        if not (c[j] < line(j) - 0.25 * a[j] and c[j - 1] >= line(j - 1) - 0.25 * a[j - 1]):
            continue
        if np.any(c[int(i2) + 1:j - 1] < np.array([line(x) for x in range(int(i2) + 1, j - 1)]) - 0.25 * a[int(i2) + 1:j - 1]):
            used.add((i1, i2)); continue
        used.add((i1, i2))
        run = (line(j) - l[j]) / a[j]
        away = run >= 1.0
        rt, strict, ext = None, False, l[j]
        for k in range(j + 1, j + 1 + WIN):
            if h[k] >= line(k) - 0.25 * a[k]:
                rt, strict = k, away
                break
            ext = min(ext, l[k])
            run = max(run, (line(k) - l[k]) / a[j])
            away = away or run >= 1.0
        yield j, rt, strict, line(j), (line(rt) if rt is not None else np.nan), ext


def replay(M, i0, end, d, e, s, tg):
    O, H, L, C = M["O"], M["H"], M["L"], M["C"]
    o, h, l, c = (O, H, L, C) if d > 0 else (-O, -L, -H, -C)
    e_, s_, tg_ = d * e, d * s, d * tg
    risk = e_ - s_
    buf = LIMIT_BUFFER * abs(e)
    hs = np.nonzero(l[i0:end] <= s_)[0]
    ht = np.nonzero(h[i0:end] >= tg_ + buf)[0]
    xs = i0 + hs[0] if len(hs) else end
    xt = i0 + ht[0] if len(ht) else end
    if xs <= xt and xs < end:
        return ((o[xs] - e_) if (xs > i0 and o[xs] <= s_) else (s_ - e_)) / risk, xs, "stop"
    if xt < end:
        return (tg_ - e_) / risk, xt, "target"
    return (c[end - 1] - e_) / risk, end - 1, "time"


def run_trendline_trade(cfg: Config, out_dir: Path) -> Path:
    rows = []
    for sym in COINS:
        df5u, _ = load_klines_5m(cfg.data_dir, sym)
        df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
        M = {"t5": df5n["open_time"].to_numpy(), **{k: df5n[x].to_numpy(float) for k, x in
                                                   (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"))}}
        ft, fc = _funding_cum(cfg) if sym == "ETHUSDT" else (np.array([], dtype="datetime64[ns]"), np.array([0.0]))
        t5 = M["t5"]
        for tf in ("1h", "4h"):
            t = TF(resample(df5u, tf))
            bpt = int(pd.Timedelta(tf) / pd.Timedelta(minutes=5))
            for side in (1, -1):
                d = -side                                                # a rising line broken down -> short
                hh_o = t.h if side > 0 else -t.l                         # oriented highs (toward the line)
                cc_o = t.c if side > 0 else -t.c
                for j, k, strict, lj, lk, ext in events(t, side):
                    plans = []
                    # the break trade
                    i0 = int(np.searchsorted(t5, t.ct[j]))
                    stop_o = lj + 0.25 * t.a[j]                          # oriented: above the line for a short
                    bc_ext = t.l[j] if side > 0 else -t.h[j]                 # known at the break entry (no lookahead)
                    plans.append(("break", i0, stop_o, bc_ext, False))
                    if k is not None and cc_o[k] < lk:                   # rejected retest
                        plans.append(("retest", int(np.searchsorted(t5, t.ct[k])), hh_o[k], ext, strict))
                    for kind, i0, stop_o, ext_o, st in plans:
                        if i0 + MAXB * bpt >= len(t5):
                            continue
                        e = M["O"][i0]
                        # stop_o is in oriented prices: real for side +1 (a short: stop above), negated for side -1
                        # (a long: the real stop is -stop_o, below the line), then 0.1% further out
                        stop = stop_o * 1.001 if side > 0 else (-stop_o) * 0.999
                        risk = (e - stop) * d
                        if risk <= 0:
                            continue
                        liq = (ext_o if side > 0 else -ext_o) if ext_o == ext_o else np.nan
                        tg_liq = liq if (liq == liq and (liq - e) * d >= 1.2 * risk) else e + d * 2 * risk
                        end = min(len(t5), i0 + MAXB * bpt)
                        for tname, tg in (("2R", e + d * 2 * risk), ("3R", e + d * 3 * risk), ("liquidity", tg_liq)):
                            R, xi, xk = replay(M, i0, end, d, e, stop, tg)
                            x_t = t5[xi] + np.timedelta64(5, "m")
                            a_ = np.searchsorted(ft, t5[i0], side="right"); b_ = np.searchsorted(ft, x_t, side="left")
                            fund = (fc[b_] - fc[a_]) * d if b_ > a_ else 0.0
                            sp = risk / abs(e)
                            net = R - (C_MKT + (C_LMT if xk == "target" else C_MKT) + fund) / sp
                            rows.append({"coin": sym.replace("USDT", ""), "tf": tf, "dir": d, "trade": kind, "strict": st,
                                         "target": tname, "time": pd.Timestamp(t5[i0]), "net": net, "kind": xk,
                                         "stop_pct": sp, "rr": abs(tg - e) / risk})
        print(sym, len(rows), flush=True)
    E = pd.DataFrame(rows)
    E["hold"] = E["time"] >= HOLDOUT
    E["res"] = ~E["hold"] & (E["time"].dt.year >= 2020) & (E["time"] < HOLDOUT - pd.Timedelta(days=12))
    E.to_pickle(ROOT / "results" / "trendline_trade.pkl")
    out = []
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    for tf in ("4h", "1h"):
        for lab, m in (("break (enter at the break)", lambda x: x["trade"] == "break"),
                       ("retest (rejected retest)", lambda x: x["trade"] == "retest"),
                       ("retest, strict (after 1 ATR away)", lambda x: (x["trade"] == "retest") & x["strict"])):
            for tname in ("2R", "3R", "liquidity"):
                g = E[(E["tf"] == tf) & (E["target"] == tname)]
                g = g[m(g)]
                for per, pm in (("2020 - Oct 2025", g["res"]), ("holdout", g["hold"])):
                    x = g[pm]
                    s_ = stats(x["net"].to_numpy())
                    out.append({"tf": tf, "lab": lab, "tg": tname, "per": per, **s_, "stop": x["stop_pct"].median(),
                                "rr": x["rr"].median()})
    L = ["# A trade at the trendline retest? (vs entering at the break)", "",
         "Six coins, 1h and 4h, both directions. **win % = profit after costs.** Stops: retest = 0.1% beyond the retest "
         "candle's extreme; break = 0.1% beyond the line + 0.25 ATR. Research 2020 - Oct 2025, holdout Nov 2025 on. Funding "
         "is included for ETH only.", "",
         _table(pd.DataFrame(out), [("tf", "timeframe", str), ("lab", "entry", str), ("tg", "target", str), ("per", "period", str),
                                    ("n", "trades", str), ("win", "win %", _pct), ("avg", "avg R", f2),
                                    ("pf", "profit factor", lambda v: "" if v != v else f"{v:.2f}"),
                                    ("stop", "median stop", lambda v: "" if v != v else f"{v:.2%}"),
                                    ("rr", "median reward:risk", lambda v: "" if v != v else f"{v:.1f}")]), "",
         "Audit: round 20 (the break trade's liquidity target used information from after its entry; fixed).", ""]
    path = out_dir / "trendline_trade.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_trendline_trade(load_config(ROOT / "config.yaml"), ROOT / "reports"))
