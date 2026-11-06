"""
Does the price test the extreme of a pump / dump before the sideways resolves?  (trader's concept, 22 Nov 2024 review)

Definitions (close-based, per timeframe, mirrored for dumps; ATR = 14-candle ATR of the last closed candle):
  impulse   at candle p: H = highest high of the last K=6 candles (made at p or p-1), L0 = lowest low of those candles
            before H, leg = H - L0 >= A x ATR (A = 2), and the close of p in the top 30% of the leg.
  sideways  the next S=3 candles close neither above H nor below L0 (a close above H within them = immediate
            continuation, below L0 = immediate reversal; both counted separately).
  follow    from p+1: the sideways resolves at the first close above H (up) or below L0 (down), at most N=40 candles.
  tested    the price first pulls back at least 1 ATR from H (a candle's low <= H - 1 ATR) and a LATER candle's high comes
            back to H - 0.25 ATR before the resolution: "sweep" (high above H, close below it), "touch" (high within
            0.25 ATR, not above H) or "break" (the return is the close above H itself). Without the pullback a close
            above H is "no pullback" (continued directly); the candle after p opens at the close of p, so a test without
            a pullback first would be no test at all.
  retrace   the deepest pullback before the first test, as a share of the leg.
  retest    "retest of the price" (trader): the price first trades at least 0.5 ATR above the impulse close C_p (the price the
            pump closed at, e.g. 3,358 on 21 Nov 2024) and a LATER candle's low comes back to C_p before the resolution;
            held = that candle closes no more than 0.25 ATR below C_p,
            failed = a close further below (the project's 0.25 ATR convention for a break).
            Also the retest of the midpoint of the leg and of the origin L0 (touch with a close above it).
  rsi       RSI 14 of the timeframe's closes (mirrored for dumps): at p, at the retest, and at the up-resolution candle.
            "RSI cooled" = RSI at the retest at least 5 points below RSI at p while the price is still above the origin.
Every window (any leg size, same close position) is measured the same way; legs < 1.5 ATR are the control for
"the price is simply near the high". Six coins, 4h and 1D, 2022 - Oct 2025 chosen, holdout shown once. Significance:
calendar-month bootstrap pooled across coins (the coins move together).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .bb_pause_coins import COINS, month_boot
from .defs import TF
from .indicators import rsi
from .levels import _level_table, strong_levels
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
START = pd.Timestamp("2022-01-01")                                      # research period start (the data begins 2019/20)
K, A, S, N, TOL = 6, 2.0, 3, 40, 0.25


def windows(t: TF, side: int, coin: str, tf: str, table: pd.DataFrame | None = None) -> list[dict]:
    """table = the coin's swing table (levels.py) for the 'at a strong level' flag: a strong S/R zone known at p within
    0.5 ATR of the impulse extreme (the year's high in the 22 Nov 2024 review)."""
    h, l, c = (t.h, t.l, t.c) if side > 0 else (-t.l, -t.h, -t.c)
    a = t.a
    r = rsi(pd.Series(t.c)).to_numpy(float)
    r = r if side > 0 else 100 - r
    out = []
    p = 20
    while p < t.n - S - 1:
        atr = a[p - 1]
        if not np.isfinite(atr) or atr <= 0:
            p += 1
            continue
        lo = p - K + 1
        iH = lo + int(np.argmax(h[lo:p + 1]))
        if iH < p - 1:
            p += 1
            continue
        H = h[iH]
        iL = lo + int(np.argmin(l[lo:iH + 1]))
        L0 = l[iL]
        leg = H - L0
        if leg <= 0 or c[p] < H - 0.3 * leg:
            p += 1
            continue
        row = {"coin": coin, "tf": tf, "side": "pump" if side > 0 else "dump", "time": pd.Timestamp(t.ct[p]),
               "leg_atr": leg / atr, "impulse": leg >= A * atr, "pos_atr": (H - c[p]) / atr, "rsi_p": r[p],
               "hold": pd.Timestamp(t.ct[p]) >= HOLDOUT, "at_level": False}
        if table is not None and leg >= A * atr:
            lv = strong_levels(table, pd.Timestamp(t.ct[p]).tz_localize("UTC"))
            Hp = H if side > 0 else -H                                   # back to price
            row["at_level"] = bool(len(lv)) and bool(np.any(np.abs(lv - Hp) <= 0.5 * atr))
        imm = None
        for q in range(p + 1, p + 1 + S):
            if c[q] > H:
                imm = ("up", q); break
            if c[q] < L0:
                imm = ("down", q); break
        if imm is not None:
            row.update(sideways=False, res="immediate " + imm[0], tested="", n_res=imm[1] - p)
            out.append(row)
            p = imm[1] + 1
            continue
        tested, qt, res, ri, lowest = "", None, "none", None, np.inf
        Cp, M = c[p], (H + L0) / 2
        rt = {"close": None, "mid": None, "origin": None}              # first retest candle per level
        first = ""                                                      # which came first: the high test or the close retest
        away_hi = away_cl = False                                       # pulled back >= 1 ATR from H / traded >= 0.5 ATR above C_p
        for q in range(p + 1, min(t.n, p + 1 + N)):
            if c[q] > H:
                res, ri = "up", q
                if not tested:
                    tested, qt = ("break" if away_hi else "no pullback"), q
                    first = first or ("break" if away_hi else "no pullback")
                break
            if c[q] < L0:
                res, ri = "down", q
                break
            if not tested:
                if away_hi and h[q] >= H - TOL * atr:
                    tested, qt = ("sweep" if h[q] > H else "touch"), q
                    first = first or "high"
                else:
                    lowest = min(lowest, l[q])
            for lv, X in (("close", Cp), ("mid", M), ("origin", L0)):
                if rt[lv] is None and l[q] <= X and (lv != "close" or away_cl):
                    rt[lv] = q
                    if lv == "close":
                        first = first or "retest"
            away_hi = away_hi or l[q] <= H - 1.0 * atr
            away_cl = away_cl or h[q] >= Cp + 0.5 * atr
        row.update(sideways=True, res=res, tested=tested, n_res=(ri - p) if ri else np.nan,
                   n_test=(qt - p) if qt else np.nan, first=first or "neither",
                   retrace=((H - lowest) / leg) if np.isfinite(lowest) else 0.0,
                   rsi_up=r[ri] if res == "up" else np.nan,
                   test_end=pd.Timestamp(t.ct[ri]) if ri else pd.Timestamp(t.ct[min(t.n - 1, p + N)]))
        for lv, X in (("close", Cp), ("mid", M), ("origin", L0)):
            q = rt[lv]
            row[f"rt_{lv}"] = q is not None
            row[f"rt_{lv}_held"] = (c[q] >= X - TOL * atr) if q is not None else np.nan
            row[f"rt_{lv}_n"] = (q - p) if q is not None else np.nan
            row[f"rt_{lv}_rsi"] = r[q] if q is not None else np.nan
        out.append(row)
        p = (ri if ri else min(t.n - 1, p + N)) + 1
    return out


def build(cfg: Config) -> pd.DataFrame:
    rows = []
    for sym in COINS:
        df5u, _ = load_klines_5m(cfg.data_dir, sym)
        table = _level_table(df5u)
        for tf in ("4h", "1D"):
            t = TF(resample(df5u, tf))
            for side in (1, -1):
                rows += windows(t, side, sym.replace("USDT", ""), tf, table)
        print(sym, len(rows), flush=True)
    return pd.DataFrame(rows)


def summarize(W: pd.DataFrame, label: str) -> list[str]:
    f2 = lambda v: "" if v != v else f"{v:.1f}"  # noqa: E731
    L = [f"## {label}", ""]
    tab = []
    for (tf, side), g in W.groupby(["tf", "side"]):
        for per, m in (("2022 - Oct 2025", (g["time"] >= START) & ~g["hold"] & (g["test_end"].fillna(g["time"]) < HOLDOUT)), ("holdout", g["hold"])):
            e = g[m & g["impulse"]]
            sw = e[e["sideways"]]
            tst = sw[sw["tested"] != ""]
            ctrl = g[m & (g["leg_atr"] < 1.5) & g["sideways"]]
            mb = month_boot(sw.assign(x=(sw["tested"] != "").astype(float)), "x") if len(sw) >= 20 else (np.nan,) * 4
            tab.append({"tf": tf, "side": side, "per": per, "n": len(e), "sw": sw.shape[0] / max(1, len(e)),
                        "imm_up": (e["res"] == "immediate up").mean() if len(e) else np.nan,
                        "imm_dn": (e["res"] == "immediate down").mean() if len(e) else np.nan,
                        "tested": (sw["tested"] != "").mean() if len(sw) else np.nan,
                        "lo": mb[1], "hi": mb[2],
                        "ctrl": (ctrl["tested"] != "").mean() if len(ctrl) else np.nan, "nc": len(ctrl),
                        "sweep": (sw["tested"] == "sweep").mean() if len(sw) else np.nan,
                        "touch": (sw["tested"] == "touch").mean() if len(sw) else np.nan,
                        "brk": (sw["tested"] == "break").mean() if len(sw) else np.nan,
                        "up": (sw["res"] == "up").mean() if len(sw) else np.nan,
                        "dn": (sw["res"] == "down").mean() if len(sw) else np.nan,
                        "n_test": tst["n_test"].median() if len(tst) else np.nan,
                        "retr": tst["retrace"].median() if len(tst) else np.nan})
    L += [_table(pd.DataFrame(tab), [("tf", "tf", str), ("side", "move", str), ("per", "period", str), ("n", "impulses", str),
                                      ("sw", "went sideways", _pct), ("imm_up", "continued at once", _pct), ("imm_dn", "reversed at once", _pct),
                                      ("tested", "extreme tested before the range resolved", _pct), ("lo", "90% low", _pct), ("hi", "90% high", _pct),
                                      ("ctrl", "same for small legs (< 1.5 ATR)", _pct), ("nc", "control n", str),
                                      ("sweep", "first test = sweep", _pct), ("touch", "= touch", _pct), ("brk", "= direct break", _pct),
                                      ("up", "resolved up", _pct), ("dn", "resolved down", _pct),
                                      ("n_test", "candles to the test (median)", f2), ("retr", "retrace before the test (median share of the leg)", _pct)]), ""]
    # what the test says about the resolution
    tab = []
    for (tf, side), g in W.groupby(["tf", "side"]):
        for per, m in (("2022 - Oct 2025", (g["time"] >= START) & ~g["hold"] & (g["test_end"].fillna(g["time"]) < HOLDOUT)), ("holdout", g["hold"])):
            sw = g[m & g["impulse"] & g["sideways"]]
            for kind in ("sweep", "touch", "break", "no pullback", ""):
                x = sw[sw["tested"] == kind]
                if len(x) < 5:
                    continue
                tab.append({"tf": tf, "side": side, "per": per, "kind": kind or "pulled back, never tested", "n": len(x),
                            "up": (x["res"] == "up").mean(), "dn": (x["res"] == "down").mean(), "none": (x["res"] == "none").mean(),
                            "n_res": x["n_res"].median()})
    # retest of the price
    tab2 = []
    for (tf, side), g in W.groupby(["tf", "side"]):
        for per, m in (("2022 - Oct 2025", (g["time"] >= START) & ~g["hold"] & (g["test_end"].fillna(g["time"]) < HOLDOUT)), ("holdout", g["hold"])):
            sw = g[m & g["impulse"] & g["sideways"]]
            if len(sw) < 10:
                continue
            row = {"tf": tf, "side": side, "per": per, "n": len(sw),
                   "f_high": (sw["first"] == "high").mean(), "f_ret": (sw["first"] == "retest").mean(),
                   "f_brk": (sw["first"] == "break").mean(), "f_np": (sw["first"] == "no pullback").mean(),
                   "f_no": (sw["first"] == "neither").mean()}
            for lv in ("close", "mid", "origin"):
                x = sw[sw[f"rt_{lv}"] == True]  # noqa: E712
                held = x[x[f"rt_{lv}_held"] == True]  # noqa: E712
                fail = x[x[f"rt_{lv}_held"] == False]  # noqa: E712
                row[f"{lv}_rt"] = (sw[f"rt_{lv}"] == True).mean()  # noqa: E712
                row[f"{lv}_held_up"] = (held["res"] == "up").mean() if len(held) >= 5 else np.nan
                row[f"{lv}_fail_up"] = (fail["res"] == "up").mean() if len(fail) >= 5 else np.nan
                row[f"{lv}_no_up"] = (sw.loc[sw[f"rt_{lv}"] != True, "res"] == "up").mean() if (sw[f"rt_{lv}"] != True).sum() >= 5 else np.nan  # noqa: E712
            cl = sw[sw["rt_close"] == True]  # noqa: E712
            cooled = cl[(cl["rt_close_rsi"] <= cl["rsi_p"] - 5)]
            warm = cl[(cl["rt_close_rsi"] > cl["rsi_p"] - 5)]
            row["cool_up"] = (cooled["res"] == "up").mean() if len(cooled) >= 5 else np.nan
            row["warm_up"] = (warm["res"] == "up").mean() if len(warm) >= 5 else np.nan
            row["n_cool"], row["n_warm"] = len(cooled), len(warm)
            up = sw[sw["res"] == "up"]
            row["rsi_lower_at_break"] = (up["rsi_up"] < up["rsi_p"]).mean() if len(up) >= 5 else np.nan
            tab2.append(row)
    L += ["### Retest of the price (the impulse close), the midpoint and the origin", "",
          "first = what happened first in the sideways (after the price moved away): the high was tested, the impulse close was retested, a break after a pullback, a continuation without any 1 ATR pullback, or neither (reversed / timed out).", "",
          _table(pd.DataFrame(tab2), [("tf", "tf", str), ("side", "move", str), ("per", "period", str), ("n", "sideways impulses", str),
                                     ("f_high", "high tested first", _pct), ("f_ret", "close retested first", _pct), ("f_brk", "broke first", _pct), ("f_np", "continued without a pullback", _pct), ("f_no", "neither", _pct),
                                     ("close_rt", "close retested", _pct), ("close_held_up", "held -> continued", _pct), ("close_fail_up", "closed below -> continued", _pct), ("close_no_up", "never retested -> continued", _pct),
                                     ("mid_rt", "midpoint retested", _pct), ("mid_held_up", "held -> continued", _pct), ("mid_fail_up", "failed -> continued", _pct),
                                     ("origin_rt", "origin retested", _pct), ("origin_held_up", "held -> continued", _pct),
                                     ("cool_up", "retest with RSI cooled >= 5 -> continued", _pct), ("n_cool", "n", str), ("warm_up", "RSI not cooled -> continued", _pct), ("n_warm", "n", str),
                                     ("rsi_lower_at_break", "continuations with RSI lower at the break than at the impulse", _pct)]), ""]
    tab3 = []
    for (tf, side), g in W.groupby(["tf", "side"]):
        for per, m in (("2022 - Oct 2025", (g["time"] >= START) & ~g["hold"] & (g["test_end"].fillna(g["time"]) < HOLDOUT)), ("holdout", g["hold"])):
            sw = g[m & g["impulse"] & g["sideways"]]
            for at in (True, False):
                x = sw[sw["at_level"] == at]
                swp, tch = x[x["tested"] == "sweep"], x[x["tested"] == "touch"]
                if len(x) < 10:
                    continue
                tab3.append({"tf": tf, "side": side, "per": per, "at": "at a strong level" if at else "elsewhere", "n": len(x),
                             "up": (x["res"] == "up").mean(), "tested": (x["tested"] != "").mean(),
                             "swp_n": len(swp), "swp_up": (swp["res"] == "up").mean() if len(swp) >= 5 else np.nan,
                             "swp_dn": (swp["res"] == "down").mean() if len(swp) >= 5 else np.nan,
                             "tch_n": len(tch), "tch_up": (tch["res"] == "up").mean() if len(tch) >= 5 else np.nan})
    L += ["### Is the extreme at a strong S/R level (within 0.5 ATR)?  The sweep as an exit signal lives or dies here", "",
          _table(pd.DataFrame(tab3), [("tf", "tf", str), ("side", "move", str), ("per", "period", str), ("at", "extreme", str), ("n", "sideways impulses", str),
                                      ("up", "continued", _pct), ("tested", "extreme tested", _pct), ("swp_n", "sweeps", str), ("swp_up", "sweep -> continued", _pct),
                                      ("swp_dn", "sweep -> reversed", _pct), ("tch_n", "touches", str), ("tch_up", "touch -> continued", _pct)]), ""]
    L += ["### After the first test of the high, how did the range resolve?", "",
          _table(pd.DataFrame(tab), [("tf", "tf", str), ("side", "move", str), ("per", "period", str), ("kind", "first test", str), ("n", "n", str),
                                     ("up", "continued (close beyond the extreme)", _pct), ("dn", "reversed (close beyond the origin)", _pct),
                                     ("none", "neither in 40 candles", _pct), ("n_res", "candles to resolve (median)", f2)]), ""]
    return L


def run_sideways_test(cfg: Config, out_dir: Path, rebuild: bool = True) -> Path:
    if rebuild:
        W = build(cfg)
        W.to_pickle(ROOT / "results" / "sideways_test.pkl")
    else:
        W = pd.read_pickle(ROOT / "results" / "sideways_test.pkl")
    L = ["# After a pump or dump: is the extreme tested before the sideways resolves?", "",
         "Trader's concept (22 Nov 2024 review): after a pump the price goes sideways and the high gets tested first, mostly. "
         "Definitions in the module docstring (impulse >= 2 ATR in 6 candles, close in the top 30%; sideways = 3 candles without a "
         "close beyond the extreme or the origin; tested = a high within 0.25 ATR of the extreme before a close beyond it or "
         "beyond the origin). **Control**: the same measurement on windows whose leg is < 1.5 ATR (no impulse) at the same close "
         "position. 90% interval from a calendar-month bootstrap pooled across the six coins.", ""]
    L += summarize(W, "Six coins (BTC, ETH, BNB, SOL, XRP, DOGE)")
    L += summarize(W[W["coin"] == "ETH"], "ETH only")
    # geometry control at the same close position
    tab = []
    bins = [0, 0.25, 0.5, 1.0, 2.0, np.inf]
    R = W[(W["time"] >= START) & ~W["hold"] & (W["test_end"] < HOLDOUT) & W["sideways"]].copy()
    R["pos"] = pd.cut(R["pos_atr"], bins, right=False)
    for (tf, pos), g in R.groupby(["tf", "pos"], observed=True):
        i_, c_ = g[g["impulse"]], g[g["leg_atr"] < 1.5]
        if len(i_) >= 20 and len(c_) >= 20:
            tab.append({"tf": tf, "pos": str(pos), "ni": len(i_), "ti": (i_["tested"] != "").mean(), "nc": len(c_), "tc": (c_["tested"] != "").mean(),
                        "ui": (i_["res"] == "up").mean(), "uc": (c_["res"] == "up").mean()})
    L += ["## Same close position, impulse vs small leg (six coins, 2022 - Oct 2025)", "",
          "If the test rate is the same at the same distance from the high, the concept is proximity, not the pump.", "",
          _table(pd.DataFrame(tab), [("tf", "tf", str), ("pos", "close below the extreme (ATR)", str), ("ni", "impulses", str), ("ti", "tested", _pct),
                                     ("nc", "small legs", str), ("tc", "tested", _pct), ("ui", "impulse resolved up", _pct), ("uc", "small leg resolved up", _pct)]), "",
          "## Reading", "",
          "- **The extreme is tested first, mostly: yes.** After a pump of >= 2 ATR that goes sideways, the high is revisited "
          "(after a pullback of at least 1 ATR) before the range resolves in 75% of daily cases and 77% of 4h cases (90% "
          "intervals 69 - 80%), dumps 72 - 74%; the holdout agrees (68 - 86%). Small legs at the same distance test "
          "56 - 74%, so part of it is proximity and part is the pump.",
          "- **The test of the high is not the exit.** After a sweep (wick above the high, close back below) the range still "
          "resolves UP 70 - 74% of the time (daily pumps 74%, 4h 72%; holdout 65 - 73%); a touch 69 - 70%. At a strong S/R "
          "level it is the same (daily pumps 74%, 4h 69%). The 16 Dec 2024 sweep of 4,099 was the 1-in-5 case, not the rule. "
          "The exit study confirms it: exiting after a sweep of the trade's high earns +0.62R vs +0.88R.",
          "- **The retest of the price is the key: supported.** The price comes back to the pump's close (after first trading "
          "0.5 ATR above it) in about half the sideways cases. When that retest HOLDS (close no more than 0.25 ATR below) "
          "the range resolves up 72% (daily pumps) and 71% (4h); when it closes below, 55 - 56%; with no retest at all, 54 - 55%. "
          "Dumps mirror it (63 - 70% vs 42 - 48%). The holdout agrees (daily pumps 87% vs 30%, 4h 66% vs 46%). A held retest of "
          "the pump's close is the best continuation marker in this study.",
          "- **RSI cooling at the retest does not help.** A retest with RSI at least 5 points below the impulse RSI continues "
          "54 - 56%, one with RSI still warm 70 - 71%: the slow, cooled retest is the weaker one. In continuations the RSI at "
          "the break is lower than at the impulse only 25 - 30% of the time. So 'RSI 70 at 3,358, then RSI 60 with the price "
          "well above' is the minority picture; most continuations break with a higher RSI.",
          "- **What it means for the bot:** hold through the sideways; do not exit on the test of the high; a held retest of "
          "the pump's close is the signal to stay (or to add); a failed retest (close below) is a coin flip. The 'pulled back, "
          "never tested -> reversed' row is true by construction (the only other way out of the range is down) and is not a finding.", "",
          "Audit: round 29b, independent re-implementation of all 14,597 windows (six coins, 4h + 1D, both sides) with zero "
          "mismatches; one result-impacting issue found and fixed (the research rows included 2019 - 2021 data under a "
          "'2022 - Oct 2025' label; now filtered, shares moved by up to 4 points); tables reproduced after the fix."]
    path = out_dir / "sideways_test.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    import sys

    from ..config import load_config
    print(run_sideways_test(load_config(ROOT / "config.yaml"), ROOT / "reports", rebuild="--report-only" not in sys.argv))
