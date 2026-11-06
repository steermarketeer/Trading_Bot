"""
The textbook top (trader, 22 Nov 2024 review of the 15m): "3 tops failed, the trendline broke, retested, and the price
falls." Three failed pushes at a cap (bot/study/three_failures.py, audited) followed by a break of the rising line through
the swing lows (bot/study/trendline_retest.py, audited), then the retest. Mirrored for bottoms. Six coins, 15m / 1h / 4h.

  textbook break   a trendline break (first close >= 0.25 ATR beyond the line) with a three-failures trigger of the same
                   side (cap above the break close) in the 30 candles before it, or at most 2 candles after it (the close
                   below the last push's low and the line break are usually the same event) and before the retest.
                   "right from the break" is measured only with the trigger at or before the break (no lookahead).
  strict textbook  the three tops are three consecutive CONFIRMED swing highs (K = 5) within max(0.25%, 0.5 ATR) of each
                   other, at least 8 candles from the first to the third, no close above their cap in between, the third
                   top at most 20 candles before the break and confirmed by the retest; "right from the break" only with
                   the third top confirmed at or before the break.
  other break      every other trendline break (the control: same line definition, no three tops before it)
  retest           the first candle back within 0.25 ATR of the extended line (20-candle window); rejected = it closes back
                   on the broken side; strict = after the price first moved >= 1 ATR away from the line
  fair test        from the break candle / the rejected retest candle: 1.5 ATR further from the line before 1.5 ATR back
                   within 30 candles (50% = coin flip; bot/study/indicator_learn.outcome)
  trade            short at the open after the rejected retest; stop 0.1% above the retest candle's high; target 2R, or the
                   measured move (the cap minus the pattern's base, projected down from the base) when it is >= 1.2R;
                   5m replay with costs and funding (funding for ETH only). 60 candles maximum.
Research 2022 - Oct 2025, holdout Nov 2025 on, calendar-month bootstrap for the 90% intervals.
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
from .indicator_learn import outcome
from .mtf import resample
from .sr2_run import _pct, _table
from .three_failures import setups
from .trendline_retest import breaks

HOLDOUT = pd.Timestamp("2025-11-01")
START = pd.Timestamp("2022-01-01")
W_TOPS, MAXB = 30, 60
TFS = (("15m", "15min"), ("1h", "1h"), ("4h", "4h"))


def triple_tops(t: TF, side: int) -> np.ndarray:
    """Rows (i3, cf3, cap) in oriented terms: three consecutive confirmed swing highs within max(0.25%, 0.5 ATR), spanning
    >= 8 candles, with no close above the cap between the first top and the third top's confirmation."""
    c = t.c if side > 0 else -t.c
    pts = t.sh if side > 0 else [(i, -p, cf) for i, p, cf in t.sl]
    arr = np.array(pts, float).reshape(-1, 3)
    out = []
    for k in range(2, len(arr)):
        (i1, p1, _), (i2, p2, _), (i3, p3, cf3) = arr[k - 2], arr[k - 1], arr[k]
        i1, i3, cf3 = int(i1), int(i3), int(cf3)
        cap = max(p1, p2, p3)
        tol = max(0.0025 * abs(cap), 0.5 * t.a[i3]) if np.isfinite(t.a[i3]) else 0.0025 * abs(cap)
        if cap - min(p1, p2, p3) > tol or i3 - i1 < 8:
            continue
        if np.any(c[i1:min(cf3, t.n - 1) + 1] > cap):
            continue
        out.append((i3, cf3, cap))
    return np.array(out, float).reshape(-1, 3)


def strict_flags(cfg: Config, E: pd.DataFrame) -> pd.DataFrame:
    """Add tops_strict / tops_strict_pre to the break table (a second pass over the data; no break detection rerun)."""
    E = E.copy()
    E["tops_strict"], E["tops_strict_pre"] = False, False
    for sym in COINS:
        coin = sym.replace("USDT", "")
        df5u, _ = load_klines_5m(cfg.data_dir, sym)
        for tf, rule in TFS:
            t = TF(resample(df5u, rule))
            for side in (1, -1):
                c = t.c if side > 0 else -t.c
                tt = triple_tops(t, side)
                m = (E["coin"] == coin) & (E["tf"] == tf) & (E["side"] == side)
                if not m.any() or not len(tt):
                    continue
                js = np.searchsorted(t.ot, E.loc[m, "time"].to_numpy().astype("datetime64[ns]"))
                waits = E.loc[m, "wait"].to_numpy(float)
                st, sp = [], []
                for j, w in zip(js, waits):
                    rt = j + int(w) if np.isfinite(w) else 10 ** 9
                    ok = (tt[:, 0] < j) & (j - tt[:, 0] <= 20) & (tt[:, 1] <= min(j + 5, rt)) & (tt[:, 2] > c[j])
                    st.append(bool(ok.any()))
                    sp.append(bool((ok & (tt[:, 1] <= j)).any()))
                E.loc[m, "tops_strict"], E.loc[m, "tops_strict_pre"] = st, sp
        print("strict", sym, flush=True)
    return E


def build(cfg: Config) -> pd.DataFrame:
    rows = []
    for sym in COINS:
        df5u, _ = load_klines_5m(cfg.data_dir, sym)
        df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
        t5 = df5n["open_time"].to_numpy()
        O, H, L_, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
        ft, fc = _funding_cum(cfg) if sym == "ETHUSDT" else (np.array([], dtype="datetime64[ns]"), np.array([0.0]))
        for tf, rule in TFS:
            t = TF(resample(df5u, rule))
            y = outcome(t)
            ot = t.ot if hasattr(t, "ot") else pd.to_datetime(resample(df5u, rule)["open_time"], utc=True).dt.tz_convert(None).to_numpy()
            step = int(pd.Timedelta(rule) / pd.Timedelta(minutes=5))
            for side in (1, -1):
                h, l, c = (t.h, t.l, t.c) if side > 0 else (-t.l, -t.h, -t.c)
                trig = np.array([(j, cap) for j, cap, _, _ in setups(t, side)], float).reshape(-1, 2)
                for b in breaks(t, side, y, sym.replace("USDT", ""), tf):
                    j = int(np.searchsorted(ot, np.datetime64(b["time"])))
                    rt_i = (j + int(b["wait"])) if b["retest"] else 10 ** 9
                    m = (trig[:, 0] >= j - W_TOPS) & (trig[:, 0] <= min(j + 2, rt_i)) & (trig[:, 1] > c[j]) if len(trig) else np.zeros(0, bool)
                    tops = bool(m.any())
                    tops_pre = bool((m & (trig[:, 0] <= j)).any()) if len(trig) else False
                    cap = float(trig[m, 1].max()) if tops else np.nan
                    rec = {**b, "tops": tops, "tops_pre": tops_pre, "cap": cap, "net2": np.nan, "netm": np.nan, "rr_m": np.nan, "stop_pct": np.nan}
                    # the trade at the rejected retest (first retest, rejected)
                    if b["retest"] and b["result"] == "rejected":
                        rt = j + int(b["wait"])
                        if rt + 1 < t.n:
                            d = -side                                       # rising line broken down -> short
                            ct = t.ct[rt]
                            i0 = int(np.searchsorted(t5, ct))
                            end = min(len(t5), i0 + MAXB * step)
                            if i0 < len(t5) and end > i0 + 1:
                                e = O[i0]
                                s = (h[rt] if side > 0 else -h[rt]) * (1 + 0.001 * side)     # 0.1% beyond the retest extreme (price)
                                risk = (e - s) * d
                                if risk > 0:
                                    base_o = l[max(0, j - 20):j + 1].min()                 # the pattern's base (oriented)
                                    base = base_o if side > 0 else -base_o
                                    cap_p = (cap if side > 0 else -cap) if tops else np.nan
                                    tg_m = np.nan
                                    if tops:
                                        tg_m = base + d * abs(cap_p - base)
                                        if (tg_m - e) * d < 1.2 * risk:
                                            tg_m = e + d * 2 * risk
                                    for key, tg in (("net2", e + d * 2 * risk), ("netm", tg_m)):
                                        if not np.isfinite(tg):
                                            continue
                                        o_, hh, ll, cc = (O, H, L_, C) if d > 0 else (-O, -L_, -H, -C)
                                        e_, s_, tg_ = d * e, d * s, d * tg
                                        buf = LIMIT_BUFFER * abs(e)
                                        hs = np.nonzero(ll[i0:end] <= s_)[0]
                                        ht = np.nonzero(hh[i0:end] >= tg_ + buf)[0]
                                        xs = i0 + hs[0] if len(hs) else end
                                        xt = i0 + ht[0] if len(ht) else end
                                        if xs <= xt and xs < end:
                                            R = ((o_[xs] - e_) if (xs > i0 and o_[xs] <= s_) else (s_ - e_)) / risk; xi, kind = xs, "stop"
                                        elif xt < end:
                                            R = (tg_ - e_) / risk; xi, kind = xt, "target"
                                        else:
                                            R = (cc[end - 1] - e_) / risk; xi, kind = end - 1, "time"
                                        x_t = t5[xi] + np.timedelta64(5, "m")
                                        a_ = np.searchsorted(ft, t5[i0], side="right"); b_ = np.searchsorted(ft, x_t, side="left")
                                        fund = (fc[b_] - fc[a_]) * d if b_ > a_ else 0.0
                                        sp = risk / abs(e)
                                        rec[key] = R - (C_MKT + (C_LMT if kind == "target" else C_MKT) + fund) / sp
                                        rec["stop_pct"] = sp
                                        if key == "netm":
                                            rec["rr_m"] = abs(tg - e) / risk
                    rows.append(rec)
        print(sym, len(rows), flush=True)
    E = pd.DataFrame(rows)
    E["hold"] = E["time"] >= HOLDOUT
    E["res"] = ~E["hold"] & (E["time"] >= START) & (E["time"] < HOLDOUT - pd.Timedelta(days=3))
    return E


def run_textbook_top(cfg: Config, out_dir: Path, rebuild: bool = True) -> Path:
    if rebuild:
        E = build(cfg)
        E.to_pickle(ROOT / "results" / "textbook_top.pkl")
    else:
        E = pd.read_pickle(ROOT / "results" / "textbook_top.pkl")
    if "tops_strict" not in E.columns:
        E = strict_flags(cfg, E)
        E.to_pickle(ROOT / "results" / "textbook_top.pkl")
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    tab = []
    for tf, _ in TFS:
        for per, pm in (("2022 - Oct 2025", E["res"]), ("holdout", E["hold"])):
            for lab, tm, tp in (("strict textbook (3 swing highs, then the line breaks)", E["tops_strict"], E["tops_strict_pre"]),
                                ("textbook (3 failed pushes, then the line breaks)", E["tops"], E["tops_pre"]),
                                ("other breaks (no 3 pushes)", ~E["tops"], ~E["tops_pre"])):
                g = E[(E["tf"] == tf) & pm & tm]
                if len(g) < 20:
                    continue
                rj = g[g["result"] == "rejected"]
                fr = rj[rj["after"].notna()]
                fm, flo, fhi, _ = month_boot(fr, "after") if len(fr) >= 20 else (np.nan,) * 4
                gp = E[(E["tf"] == tf) & pm & tp]
                ab = gp[gp["at_break"].notna()]
                bm, blo, bhi, _ = month_boot(ab, "at_break") if len(ab) >= 20 else (np.nan,) * 4
                t2, tm_ = rj[rj["net2"].notna()], rj[rj["netm"].notna()]
                tab.append({"tf": tf, "per": per, "lab": lab, "n": len(g), "np": len(gp), "retest": g["retest"].mean(), "strict": g["retest_far"].mean(),
                            "rej": (g["result"] == "rejected").mean(), "recl": (g["result"] == "reclaimed").mean(),
                            "atb": bm, "blo": blo, "bhi": bhi, "after": fm, "flo": flo, "fhi": fhi, "nr": len(fr),
                            "w2": (t2["net2"] > 0).mean() if len(t2) else np.nan, "a2": t2["net2"].mean() if len(t2) else np.nan,
                            "wm": (tm_["netm"] > 0).mean() if len(tm_) else np.nan, "am": tm_["netm"].mean() if len(tm_) else np.nan,
                            "rrm": tm_["rr_m"].median() if len(tm_) else np.nan, "nt": len(t2)})
    T = pd.DataFrame(tab)
    L = ["# The textbook top: three failed tops, the trendline breaks, the retest fails, the price falls", "",
         "Six coins, 15m / 1h / 4h, mirrored for bottoms. Strict textbook = three consecutive confirmed swing highs at one cap, the line breaking "
         "within 20 candles of the third. Textbook = a trendline break within 30 candles after a three-failures trigger (same side, "
         "cap above the break). Control = every other break of the same line definition. Fair test: 1.5 ATR "
         "further from the line before 1.5 ATR back (50% = coin flip); 90% intervals by a calendar-month bootstrap. "
         "**win % = profit after costs** (funding for ETH only). Research 2022 - Oct 2025, holdout Nov 2025 on.", "",
         _table(T, [("tf", "tf", str), ("per", "period", str), ("lab", "breaks", str), ("n", "n", str), ("retest", "retested", _pct),
                    ("strict", "strict retest", _pct), ("rej", "retest rejected", _pct), ("recl", "line reclaimed", _pct),
                    ("np", "n (tops before the break)", str), ("atb", "right from the break", _pct), ("blo", "90% low", _pct), ("bhi", "90% high", _pct),
                    ("after", "right after the rejected retest", _pct), ("flo", "90% low", _pct), ("fhi", "90% high", _pct), ("nr", "n", str),
                    ("nt", "retest trades", str), ("w2", "win % (2R)", _pct), ("a2", "avg R (2R)", f2),
                    ("wm", "win % (measured move)", _pct), ("am", "avg R (measured move)", f2), ("rrm", "median R:R (measured)", lambda v: "" if v != v else f"{v:.1f}")]), "",
         "## Reading", "",
         "- The loose group (a three-failures trigger within 30 candles) is the base rate: such a trigger exists near 65% of ALL "
         "candles, so 76% of breaks carry one and the loose split (52% vs 51%) says nothing.",
         "- The strict textbook (three confirmed swing highs at one cap, the line breaking within 20 candles of the third): the line is "
         "retested 7 times in 10 and the retest is rejected about half the time, exactly as the textbook draws it. What follows is a coin "
         "flip: 1.5 ATR away before 1.5 ATR back 54% from the break and 53% after the rejected retest on the 15m (intervals 53 - 56%), "
         "51 - 52% in the holdout; 1h 53% / 52%; 4h 59% / 55% on 52 cases (47 - 71%). The short at the rejected retest loses after "
         "costs on every timeframe (-0.75R 15m, -0.39R 1h, -0.28R 4h).",
         "- Nothing was tuned: the 20-candle rule (10 .. 40 candles) and the 30-candle window (10 .. 60) move the 15m result by less "
         "than a point; 2020 - 21 data would not have helped either.",
         "- The three tops add nothing to the line break and the line break adds nothing to the three tops. The pattern describes what a "
         "top looks like once it has happened; it does not say that one is happening. On 22 Nov 2024 the fall came, the same shape "
         "appeared four more times in three days without the fall, and the daily trend decided which was which.",
         "- The descriptive columns of the strict group (retested / rejected) pool cases whose third top was confirmed after the break; "
         "the headline columns are unaffected (after the rejected retest 53.3% pooled vs 53.2% with the top confirmed before the break).", "",
         "Audit: round 30, independent re-implementation of the join, the strict triple-top detector, 200 retest trades and every table "
         "line; zero result-impacting issues."]
    path = out_dir / "textbook_top.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    import sys

    from ..config import load_config
    print(run_textbook_top(load_config(ROOT / "config.yaml"), ROOT / "reports", rebuild="--report-only" not in sys.argv))
