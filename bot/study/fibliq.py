"""
Liquidity + Fibonacci execution for the v3.1 ETH signals (the signal = the spot; this decides entry, stop, target).

All levels are known at the signal time (only candles closed before it):
  leg        1h chart, last 150 candles: long = lowest low -> highest high after it (short mirrored)
  Fibonacci  retracements 0.382 / 0.5 / 0.618 / 0.786 of the leg; extensions 1.272 / 1.618 from the leg start
  liquidity  untaken swing lows / highs (15m and 1h for the stop side; 1h, 4h, 1D for the target side), i.e.
             confirmed swings that price has not traded through since
Entry  E0 market at the signal (as now) | E1 limit at Fib 0.382 | E2 limit at Fib 0.5 (filled only if price trades 0.02%
       through within 48h of the signal; otherwise no trade)
Stop   S0 the setup's own stop (as now) | S1 below the first untaken liquidity beyond Fib 0.618 (else below the leg start)
       | S2 below Fib 0.786;  0.1% beyond the level
Target T0 the setup's own (2:1 breakouts, 3:1 bounces, in the new risk) | T1 the first untaken liquidity beyond the leg
       end (0.05% in front of it) | T2 extension 1.272 | T3 extension 1.618
Taken only if reward:risk >= 1.2 at the entry price. One position per move: signals at the same time and direction
are merged (the A+ one kept). Time limit 60 signal candles after the fill. Costs: market 0.09% / limit 0.02% per side,
actual funding. Choice of combination: research only (trades 2022 - Oct 2025), >= 60 trades, profitable in >= 3 of 4
years, best t-score; the holdout is the honest test.
"""
from __future__ import annotations

import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import C_LMT, C_MKT, LIMIT_BUFFER, MAX_TF_BARS, _funding_cum, account, stats
from .concepts import Bars
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
FIVE = pd.Timedelta(minutes=5)
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
PRIORITY = {"A+ breakout": 0, "breakout": 1, "1D bounce": 2}
ENTRIES, STOPS, TARGETS = ["E0", "E1", "E2"], ["S0", "S1", "S2"], ["T0", "T1", "T2", "T3"]
NAMES = {"E0": "market at signal", "E1": "limit at Fib 0.382", "E2": "limit at Fib 0.5",
         "S0": "setup's own stop", "S1": "below liquidity past Fib 0.618", "S2": "below Fib 0.786",
         "T0": "setup's own R target", "T1": "next untaken liquidity", "T2": "Fib extension 1.272",
         "T3": "Fib extension 1.618"}
LEG_BARS, FILL_WINDOW, BUF = 150, pd.Timedelta(hours=48), 0.001


class Swings:
    def __init__(self, df5u: pd.DataFrame, rule: str):
        b = Bars(resample(df5u, rule))
        self.b = b
        self.ct = b.ct.dt.tz_convert(None).to_numpy()
        self.sh = np.array([(i, p, cf) for i, p, cf in b.sh], dtype=float).reshape(-1, 3)
        self.sl = np.array([(i, p, cf) for i, p, cf in b.sl], dtype=float).reshape(-1, 3)

    def n_closed(self, t) -> int:
        return int(np.searchsorted(self.ct, np.datetime64(t), side="right"))

    def untaken(self, t, side: str, lookback: int = LEG_BARS) -> np.ndarray:
        """Prices of confirmed swing highs ('H') / lows ('L') not traded through by time t."""
        n = self.n_closed(t)
        arr = self.sh if side == "H" else self.sl
        m = (arr[:, 2] < n) & (arr[:, 0] >= n - lookback)
        out = []
        for i, p, _ in arr[m]:
            i = int(i)
            seg = self.b.h[i + 1:n] if side == "H" else self.b.l[i + 1:n]
            if not len(seg) or (seg.max() <= p if side == "H" else seg.min() >= p):
                out.append(p)
        return np.array(out)


def plan(sig: pd.Series, sw: dict) -> dict | None:
    """Fibonacci leg + liquidity levels at the signal (direction-normalised: long = +1)."""
    t, d = pd.Timestamp(sig["entry_time"]), int(sig["direction"])
    h1 = sw["1h"]
    n = h1.n_closed(t)
    if n < LEG_BARS:
        return None
    hh, ll = h1.b.h[n - LEG_BARS:n], h1.b.l[n - LEG_BARS:n]
    if d > 0:
        k0 = int(np.argmin(ll)); k1 = k0 + int(np.argmax(hh[k0:]))
        a, z = ll[k0], hh[k1]
    else:
        k0 = int(np.argmax(hh)); k1 = k0 + int(np.argmin(ll[k0:]))
        a, z = hh[k0], ll[k1]
    L = (z - a) * d
    if L <= 0 or k1 == k0:
        return None
    ret = lambda r: z - d * r * L  # noqa: E731
    ext = lambda r: a + d * r * L  # noqa: E731
    stop_side, tgt_side = ("L", "H") if d > 0 else ("H", "L")
    liq_stop = np.concatenate([sw["15m"].untaken(t, stop_side), sw["1h"].untaken(t, stop_side)])
    liq_tgt = np.concatenate([sw[x].untaken(t, tgt_side) for x in ("1h", "4h", "1D")])
    f618 = ret(0.618)
    beyond = liq_stop[(liq_stop - f618) * d < 0]                       # past the 0.618, toward the leg start
    s1_level = beyond[np.argmax(beyond * d)] if len(beyond) else a      # the nearest one past 0.618
    ahead = liq_tgt[(liq_tgt - z) * d > 0]
    t1 = ahead[np.argmin(ahead * d)] if len(ahead) else np.nan
    return {"a": a, "z": z, "L": L, "f382": ret(0.382), "f5": ret(0.5), "f786": ret(0.786),
            "s1": s1_level, "t1": t1, "x1272": ext(1.272), "x1618": ext(1.618)}


def simulate(sig: pd.Series, p: dict, O, H, Lw, C, t5, fund) -> list[dict]:
    d = int(sig["direction"])
    st = int(np.searchsorted(t5, pd.Timestamp(sig["entry_time"]).to_datetime64()))
    bpt = int(pd.Timedelta(sig["tf"]) / FIVE)
    win_end = st + int(FILL_WINDOW / FIVE)
    if st >= len(t5) or win_end + MAX_TF_BARS * bpt > len(O):
        return []
    sgn = (lambda v: v) if d > 0 else (lambda v: -v)
    o, h, l, c = (O, H, Lw, C) if d > 0 else (-O, -Lw, -H, -C)
    e0 = o[st]
    own_stop = e0 - float(sig["risk"])
    lv = {k: sgn(v) for k, v in p.items() if k in ("f382", "f5", "f786", "s1", "t1", "x1272", "x1618", "a", "z")}
    rows = []
    ft, fc = fund
    for E, S, T in itertools.product(ENTRIES, STOPS, TARGETS):
        if E == "E0":
            i0, px, limit = st, e0, False
        else:
            lim = lv["f382"] if E == "E1" else lv["f5"]
            if lim >= e0:                                   # price already below the level: buy at market
                i0, px, limit = st, e0, False
            else:
                hit = np.flatnonzero(l[st:win_end] <= lim - LIMIT_BUFFER * abs(lim))
                if not len(hit):
                    continue
                i0, px, limit = st + int(hit[0]), lim, True
        stop = {"S0": own_stop, "S1": lv["s1"] - BUF * abs(px), "S2": lv["f786"] - BUF * abs(px)}[S]
        if stop >= px:
            continue
        risk = px - stop
        tg = {"T0": px + TGT[sig["setup"]] * risk, "T1": lv["t1"] - 0.0005 * abs(px) if np.isfinite(lv["t1"]) else np.nan,
              "T2": lv["x1272"], "T3": lv["x1618"]}[T]
        if not np.isfinite(tg) or (tg - px) / risk < 1.2:
            continue
        end = i0 + MAX_TF_BARS * bpt
        R, xi, kind = _run(o, h, l, c, i0, px, stop, tg, limit, end)
        x_t = pd.Timestamp(t5[xi]) + FIVE
        a_ = np.searchsorted(ft, t5[i0], side="right")
        b_ = np.searchsorted(ft, x_t.to_datetime64(), side="left")
        sp = risk / abs(px)
        cost = (C_LMT if limit else C_MKT) + (C_LMT if kind == "target" else C_MKT) + ((fc[b_] - fc[a_]) * d if b_ > a_ else 0.0)
        rows.append({"combo": f"{E}-{S}-{T}", "net": R - cost / sp, "rr": (tg - px) / risk, "stop_pct": sp,
                     "decision_time": pd.Timestamp(t5[i0]), "exit_time": x_t})
    return rows


def _run(o, h, l, c, i0, e, s, tg, limit_entry, end):
    risk = e - s
    buf = LIMIT_BUFFER * abs(e)
    j0 = i0
    if limit_entry:
        if l[i0] <= s:
            return (s - e) / risk, i0, "stop"
        j0 = i0 + 1
    for i in range(j0, end):
        if i > j0 and o[i] <= s:
            return (o[i] - e) / risk, i, "stop"
        if l[i] <= s:
            return (s - e) / risk, i, "stop"
        if h[i] >= tg + buf:
            return (tg - e) / risk, i, "target"
    return (c[end - 1] - e) / risk, end - 1, "time"


def run_fibliq(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t5 = df5n["open_time"].to_numpy()
    O, H, Lw, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    fund = _funding_cum(cfg)
    sw = {tf: Swings(df5u, rule) for tf, rule in (("15m", "15min"), ("1h", "1h"), ("4h", "4h"), ("1D", "1D"))}
    A = pd.read_pickle(ROOT / "results" / "coins_v31.pkl")
    S = A[A["coin"] == "ETH"].copy()
    S["prio"] = S["setup"].map(PRIORITY)
    S = S.sort_values(["entry_time", "direction", "prio"]).drop_duplicates(["entry_time", "direction"]).reset_index(drop=True)
    rows = []
    for k, sig in S.iterrows():
        p = plan(sig, sw)
        if p is None:
            continue
        for r in simulate(sig, p, O, H, Lw, C, t5, fund):
            rows.append({"sig": k, "setup": sig["setup"], "family": "bounce" if sig["setup"] == "1D bounce" else "breakout",
                         "hold": bool(sig["entry_time"] >= HOLDOUT), "year": sig["entry_time"].year, **r})
    R = pd.DataFrame(rows)
    R.to_pickle(ROOT / "results" / "fibliq_trades.pkl")
    res_ok = ~R["hold"] & (R["exit_time"] < HOLDOUT)
    tab, chosen = [], {}
    for fam in ("breakout", "bounce"):
        for combo, g in R[R["family"] == fam].groupby("combo"):
            r_ = g[res_ok.loc[g.index]]
            h_ = g[g["hold"]]
            yrs = sum(1 for y in (2022, 2023, 2024, 2025) if r_.loc[r_["year"] == y, "net"].mean() > 0)
            tsc = r_["net"].mean() / (r_["net"].std(ddof=1) / math.sqrt(len(r_))) if len(r_) > 2 and r_["net"].std() > 0 else 0
            tab.append({"family": fam, "combo": combo, "n_r": len(r_), "w_r": (r_["net"] > 0).mean(), "a_r": r_["net"].mean(),
                        "t": tsc, "years": yrs, "n_h": len(h_), "w_h": (h_["net"] > 0).mean() if len(h_) else math.nan,
                        "a_h": h_["net"].mean() if len(h_) else math.nan, "rr": g["rr"].mean()})
    T = pd.DataFrame(tab)
    for fam in ("breakout", "bounce"):
        ok = T[(T["family"] == fam) & (T["n_r"] >= 60) & (T["years"] >= 3)].sort_values("t", ascending=False)
        chosen[fam] = ok.iloc[0]["combo"] if len(ok) else None
    base = {"breakout": "E0-S0-T0", "bounce": "E0-S0-T0"}
    desc = lambda c: " · ".join(NAMES[x] for x in c.split("-"))  # noqa: E731
    wk = {False: (HOLDOUT - pd.Timestamp("2022-01-01")).days / 7, True: (R["exit_time"].max() - HOLDOUT).days / 7}
    L = ["# Liquidity + Fibonacci execution for the v3.1 signals", "",
         "The v3.1 signal is the spot; entry, stop and target come from Fibonacci and untaken liquidity known at the signal. "
         "One position per move. **win % = profit after all costs.** The combination is chosen on 2022 - Oct 2025 only; "
         "the holdout (Nov 2025 - Oct 2026) is the honest test.", ""]
    rows = []
    for fam in ("breakout", "bounce"):
        for label, combo in (("current (v3.1)", base[fam]), ("chosen on research", chosen[fam])):
            if combo is None:
                rows.append({"fam": fam, "label": label, "combo": "nothing qualified"})
                continue
            r = T[(T["family"] == fam) & (T["combo"] == combo)].iloc[0].to_dict()
            rows.append({"fam": fam, "label": label, "combo": desc(combo), **r})
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    L += ["## Current vs chosen", "", _table(pd.DataFrame(rows).fillna(math.nan), [
        ("fam", "setup", str), ("label", "", str), ("combo", "entry · stop · target", str),
        ("n_r", "trades 2022-25", lambda v: "" if v != v else f"{int(v)}"), ("w_r", "win %", _pct), ("a_r", "avg R", f2),
        ("n_h", "trades holdout", lambda v: "" if v != v else f"{int(v)}"), ("w_h", "win % holdout", _pct),
        ("a_h", "avg R holdout", f2), ("rr", "avg reward:risk", lambda v: "" if v != v else f"{v:.2f}")]), ""]
    rows = []
    for name, sel in (("current (v3.1, one position per move)", {"breakout": base["breakout"], "bounce": base["bounce"]}),
                      ("chosen liquidity + Fibonacci", chosen)):
        for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
            parts = [R[(R["family"] == f) & (R["combo"] == c) & (R["hold"] == hold)] for f, c in sel.items() if c]
            x = pd.concat(parts).reset_index(drop=True) if parts else R.iloc[:0]
            s_ = stats(x["net"].to_numpy())
            eq, mdd = account(x, "net", "exit_time", RISK) if len(x) else (math.nan, math.nan)
            rows.append({"name": name, "per": per, **s_, "pw": s_["n"] / wk[hold], "eq": eq, "mdd": mdd})
    L += ["## Account (A+ 4%, others 2%, max 5x)", "", _table(pd.DataFrame(rows), [
        ("name", "strategy", str), ("per", "period", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
        ("win", "win %", _pct), ("avg", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("eq", "account", lambda v: f"{v:.2f}x"), ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    for fam in ("breakout", "bounce"):
        x = T[T["family"] == fam].sort_values("t", ascending=False).copy()
        x["combo"] = x["combo"].map(desc)
        L += [f"## Every combination: {fam}s (sorted by research t-score)", "", _table(x, [
            ("combo", "entry · stop · target", str), ("n_r", "trades 2022-25", str), ("w_r", "win %", _pct),
            ("a_r", "avg R", f2), ("t", "t-score", lambda v: f"{v:.2f}"), ("years", "good years /4", str),
            ("n_h", "holdout trades", str), ("w_h", "holdout win %", _pct), ("a_h", "holdout avg R", f2),
            ("rr", "avg R:R", lambda v: f"{v:.2f}")]), ""]
    path = out_dir / "fibliq.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
