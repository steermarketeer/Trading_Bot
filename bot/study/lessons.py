"""
The trader's journal lessons as exact rules, tested on every v3.1 ETH trade (one position per move).

L1  15m failure exit (trader's lesson from h039): after entry, track the 15m candles. Peak = highest high since entry;
    neckline = lowest low after the peak. A second push that does NOT make a new high (a double top or lower high, at least
    within 0.5R of the peak) followed by a 15m CLOSE below the neckline and below the 15m EMA 50 = buyers are done ->
    exit at the next open (market). Mirrored for shorts.
L1F same, and also take the opposite trade from there: stop just beyond the second top, target = the nearest untaken
    15m / 1h liquidity on the other side (at least 1.2 : 1).
L2  no long breakout into a falling market at a ceiling: skip a breakout when the daily close is on the wrong side of the
    daily EMA 200 AND a strong S/R zone or untaken 4h swing sits between the entry and the target (mirrored for shorts).
L3  falling highs: skip a long breakout when the last three confirmed 4h swing highs are each lower (shorts: rising lows).
L4  no second try: skip a trade when a trade in the same direction lost in the last 7 days with an entry within 1% of
    this one (that loss closed before this entry).
All levels and indicators use only candles closed at the decision. Costs as everywhere (market 0.09%, limit target 0.02%,
funding). NOTE: L1-L4 came from reviewing holdout trades, so 2022 - Oct 2025 is the clean test.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import C_LMT, C_MKT, LIMIT_BUFFER, MAX_TF_BARS, _funding_cum, account, stats
from .concepts import Bars
from .indicators import ema
from .levels import _level_table, strong_levels
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
FIVE = pd.Timedelta(minutes=5)
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
PRIORITY = {"A+ breakout": 0, "breakout": 1, "1D bounce": 2}


def _cost(limit_exit: bool, frac_funding: float) -> float:
    return C_MKT + (C_LMT if limit_exit else C_MKT) + frac_funding


def replay(sig, ctx, mode: str):
    """mode: 'base' or 'L1' or 'L1F'. Returns list of legs (net R in the ORIGINAL trade's risk units, exit time, kind)."""
    t5, O, H, Lw, C, m15, fund = ctx["t5"], ctx["O"], ctx["H"], ctx["L"], ctx["C"], ctx["m15"], ctx["fund"]
    d, risk = int(sig["direction"]), float(sig["risk"])
    st = int(np.searchsorted(t5, pd.Timestamp(sig["entry_time"]).to_datetime64()))
    bpt = int(pd.Timedelta(sig["tf"]) / FIVE)
    end = min(len(O), st + MAX_TF_BARS * bpt)
    o, h, l, c = (O, H, Lw, C) if d > 0 else (-O, -Lw, -H, -C)
    e = o[st]
    s, tg = e - risk, e + TGT[sig["setup"]] * risk
    buf = LIMIT_BUFFER * abs(e)
    peak, neck, second, legs = -np.inf, np.inf, False, []
    e50 = m15["e50"] if d > 0 else -m15["e50"]
    ft, fc = fund

    def fund_frac(i0, i1, dd):
        a = np.searchsorted(ft, t5[i0], side="right")
        b = np.searchsorted(ft, (pd.Timestamp(t5[i1]) + FIVE).to_datetime64(), side="left")
        return (fc[b] - fc[a]) * dd if b > a else 0.0

    i = st
    while i < end:
        if i > st and o[i] <= s:
            R, kind = (o[i] - e) / risk, "stop"
            break
        if l[i] <= s:
            R, kind = (s - e) / risk, "stop"
            break
        if h[i] >= tg + buf:
            R, kind = (tg - e) / risk, "target"
            break
        # 15m candle closes at the end of every third 5m candle (entries are on hour boundaries)
        tight = mode == "L1b"
        active = (not tight) or ((i - st) < 288 and peak < e + 1.0 * risk)
        if mode != "base" and active and (i - st) % 3 == 2:
            j = i - 2
            h15, l15, c15 = h[j:i + 1].max(), l[j:i + 1].min(), c[i]
            k15 = int(np.searchsorted(m15["t"], t5[j]))       # this 15m candle
            if h15 > peak:                                       # new high: start over
                peak, neck, second = h15, np.inf, False
            elif not second:
                tol = 0.15 if tight else 0.5
                if np.isfinite(neck) and (peak - neck) >= 0.25 * risk and h15 >= peak - tol * risk and h15 > neck:
                    second = True                                # a second push that failed to make a new high
                else:
                    neck = min(neck, l15)                        # the pullback low after the peak (the neckline)
            if second:
                if c15 < neck and c15 < e50[k15]:
                    x = i + 1
                    if x >= end:
                        R, kind, i = (c[end - 1] - e) / risk, "time", end - 1
                        break
                    R, kind = (o[x] - e) / risk, "15m failure exit"
                    i = x
                    break
        i += 1
    else:
        R, kind, i = (c[end - 1] - e) / risk, "time", end - 1
    sp = risk / abs(e)
    legs.append({"net": R - _cost(kind == "target", fund_frac(st, i, d)) / sp, "exit_time": pd.Timestamp(t5[i]) + FIVE,
                 "kind": kind, "R_gross": R})
    if mode == "L1F" and kind == "15m failure exit":
        # opposite trade from the exit: stop just beyond the peak, target = nearest untaken liquidity the other way
        x = i
        ent2 = o[x]
        stop2 = peak + 0.1 * risk                         # in normalised space the flip is a SHORT: stop above the peak
        liq = ctx["liq_below"](pd.Timestamp(t5[x]), d)    # untaken lows (longs) / highs (shorts), real prices
        liq = np.array([v if d > 0 else -v for v in liq])
        below = liq[liq < ent2 - 0.0005 * abs(ent2)]
        if len(below):
            tg2 = below.max() + 0.0005 * abs(ent2)
            r2 = stop2 - ent2
            if r2 > 0 and (ent2 - tg2) / r2 >= 1.2:
                end2 = min(len(O), x + MAX_TF_BARS * bpt)
                res = None
                for k in range(x, end2):
                    if k > x and o[k] >= stop2:
                        res = ((ent2 - o[k]) / r2, k, "stop"); break
                    if h[k] >= stop2:
                        res = ((ent2 - stop2) / r2, k, "stop"); break
                    if l[k] <= tg2 - buf:
                        res = ((ent2 - tg2) / r2, k, "target"); break
                if res is None:
                    res = ((ent2 - c[end2 - 1]) / r2, end2 - 1, "time")
                R2, k2, kind2 = res
                sp2 = r2 / abs(ent2)
                net2 = R2 - _cost(kind2 == "target", fund_frac(x, k2, -d)) / sp2
                legs.append({"net": net2, "flip_net_R": net2,
                             "flip_stop_pct": sp2, "exit_time": pd.Timestamp(t5[k2]) + FIVE, "kind": "flip " + kind2,
                             "R_gross": R2})
    return legs


def run_lessons(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t5 = df5n["open_time"].to_numpy()
    b15 = resample(df5u, "15min")
    m15 = {"t": pd.to_datetime(b15["open_time"], utc=True).dt.tz_convert(None).to_numpy(),
           "e50": ema(b15["close"], 50).to_numpy(float)}
    # liquidity for the flip target: untaken 15m / 1h swings known at time t
    sw = {}
    for tf, rule in (("15m", "15min"), ("1h", "1h"), ("4h", "4h")):
        b = Bars(resample(df5u, rule))
        sw[tf] = (b, b.ct.dt.tz_convert(None).to_numpy())

    def untaken(tf, t, side, lookback=150):
        b, ct = sw[tf]
        n = int(np.searchsorted(ct, np.datetime64(t), side="right"))
        pts = b.sl if side == "L" else b.sh
        out = []
        for i, p, cf in pts:
            if cf < n and i >= n - lookback:
                seg = b.l[i + 1:n] if side == "L" else b.h[i + 1:n]
                if not len(seg) or (seg.min() >= p if side == "L" else seg.max() <= p):
                    out.append(p)
        return out

    def liq_below(t, d):
        side = "L" if d > 0 else "H"
        return untaken("15m", t, side) + untaken("1h", t, side)

    ctx = {"t5": t5, "O": df5n["open"].to_numpy(float), "H": df5n["high"].to_numpy(float),
           "L": df5n["low"].to_numpy(float), "C": df5n["close"].to_numpy(float), "m15": m15,
           "fund": _funding_cum(cfg), "liq_below": liq_below}
    A = pd.read_pickle(ROOT / "results" / "coins_v31.pkl")
    S = A[A["coin"] == "ETH"].copy()
    S["prio"] = S["setup"].map(PRIORITY)
    S = S.sort_values(["entry_time", "direction", "prio"]).drop_duplicates(["entry_time", "direction"]).reset_index(drop=True)
    S["family"] = np.where(S["setup"] == "1D bounce", "bounce", "breakout")
    # ---- entry filters (known at entry)
    d1 = resample(df5u, "1D")
    d1["ct"] = pd.to_datetime(d1["close_time"], utc=True).dt.tz_convert(None)
    d1["e200"] = ema(d1["close"], 200)
    q = pd.merge_asof(S[["entry_time"]].assign(_r=np.arange(len(S))).sort_values("entry_time"),
                      d1[["ct", "close", "e200"]].sort_values("ct"), left_on="entry_time", right_on="ct",
                      direction="backward").sort_values("_r")
    S["d1_wrong_side"] = ((q["close"].to_numpy() - q["e200"].to_numpy()) * S["direction"].to_numpy()) < 0
    table = _level_table(df5u)
    blocked, falling = [], []
    b4, ct4 = sw["4h"]
    for _, r in S.iterrows():
        e, d, rk = float(r["px"]), int(r["direction"]), float(r["risk"])
        tg = e + d * TGT[r["setup"]] * rk
        z = strong_levels(table, pd.Timestamp(r["entry_time"]).tz_localize("UTC"))
        hi4 = untaken("4h", r["entry_time"], "H" if d > 0 else "L")
        lv = np.r_[z, hi4]
        rel = (lv - e) * d
        blocked.append(bool(((rel > 0.15 * rk) & (rel < (tg - e) * d)).any()))
        n = int(np.searchsorted(ct4, np.datetime64(r["entry_time"]), side="right"))
        pts = [p for i, p, cf in (b4.sh if d > 0 else b4.sl) if cf < n][-3:]
        falling.append(len(pts) == 3 and ((pts[0] > pts[1] > pts[2]) if d > 0 else (pts[0] < pts[1] < pts[2])))
    S["ceiling"], S["falling_highs"] = blocked, falling
    # ---- replay base / L1 / L1F
    out = {}
    for mode in ("base", "L1", "L1F", "L1b"):
        rows = []
        for k, r in S.iterrows():
            legs = replay(r, ctx, mode)
            for g in legs:
                rows.append({"sig": k, **g})
        out[mode] = pd.DataFrame(rows)
    base = out["base"].groupby("sig").first()
    S["net_base"], S["exit_base"] = base["net"], base["exit_time"]
    l1 = out["L1"].groupby("sig").first()
    S["net_L1"], S["exit_L1"], S["kind_L1"] = l1["net"], l1["exit_time"], l1["kind"]
    l1b = out["L1b"].groupby("sig").first()
    S["net_L1b"], S["exit_L1b"], S["kind_L1b"] = l1b["net"], l1b["exit_time"], l1b["kind"]
    # L4: a same-direction LOSS (closed before this entry) within 7 days and 1% of price
    skip4 = []
    for k, r in S.iterrows():
        prev = S[(S.index < k) & (S["direction"] == r["direction"]) & (S["exit_base"] < r["entry_time"]) &
                 (S["entry_time"] >= r["entry_time"] - pd.Timedelta(days=7)) & (S["net_base"] <= 0) &
                 ((S["px"] - r["px"]).abs() / r["px"] <= 0.01)]
        skip4.append(len(prev) > 0)
    S["second_try"] = skip4
    S["stop_pct"] = S["risk"] / S["px"]
    S["hold"] = S["entry_time"] >= HOLDOUT
    S["decision_time"] = S["entry_time"]
    flips = out["L1F"][out["L1F"]["kind"].str.startswith("flip")].set_index("sig")
    S.to_pickle(ROOT / "results" / "lessons.pkl")
    flips.to_pickle(ROOT / "results" / "lessons_flips.pkl")

    brk = S["family"] == "breakout"
    rules = {
        "v3.1 now (one position per move)": (pd.Series(True, index=S.index), "net_base", "exit_base"),
        "L1 15m failure exit": (pd.Series(True, index=S.index), "net_L1", "exit_L1"),
        "L1b 15m double top in the first 24h, before +1R": (pd.Series(True, index=S.index), "net_L1b", "exit_L1b"),
        "L1b + L4": (~S["second_try"], "net_L1b", "exit_L1b"),
        "L2 skip breakouts under daily EMA200 with a ceiling before target": (~(brk & S["d1_wrong_side"] & S["ceiling"]), "net_base", "exit_base"),
        "L3 skip breakouts against falling 4h highs": (~(brk & S["falling_highs"]), "net_base", "exit_base"),
        "L4 skip the second try at a failed level": (~S["second_try"], "net_base", "exit_base"),
        "L1 + L2 + L3 + L4": (~(brk & S["d1_wrong_side"] & S["ceiling"]) & ~(brk & S["falling_highs"]) & ~S["second_try"],
                              "net_L1", "exit_L1"),
    }
    wk = {False: (HOLDOUT - pd.Timestamp("2022-01-01")).days / 7, True: (S["entry_time"].max() - HOLDOUT).days / 7}
    L = ["# Your journal lessons as rules: tested on every v3.1 ETH trade", "",
         "One position per move. **win % = profit after all costs.** The lessons came from holdout trades (h039, h030, h029), "
         "so **2022 - Oct 2025 is the clean test**; the holdout is shown but is no longer untouched.", ""]
    rows = []
    for name, (keep, ncol, xcol) in rules.items():
        for hold, per in ((False, "2022 - Oct 2025 (clean test)"), (True, "holdout (lessons came from here)")):
            x = S[keep & (S["hold"] == hold)].rename(columns={ncol: "net_", xcol: "exit_"})
            s_ = stats(x["net_"].to_numpy())
            eq, mdd = account(x.reset_index(drop=True), "net_", "exit_", RISK) if len(x) else (math.nan, math.nan)
            rows.append({"rule": name, "per": per, **s_, "pw": s_["n"] / wk[hold], "eq": eq, "mdd": mdd})
    f2 = lambda v: f"{v:+.2f}"  # noqa: E731
    L += ["## Results", "", _table(pd.DataFrame(rows), [
        ("rule", "rule", str), ("per", "period", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
        ("win", "win %", _pct), ("avg", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("eq", "account", lambda v: f"{v:.2f}x"), ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    # L1 detail: what the exit did to winners and losers
    rows = []
    for col, nm in (("L1", "L1 (first version)"), ("L1b", "L1b (first 24h, true double top)")):
      for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
        x = S[S["hold"] == hold]
        ex = x[f"kind_{col}"] == "15m failure exit"
        rows.append({"per": f"{nm}, {per}", "n": int(ex.sum()), "share": ex.mean(),
                     "was_loss": int((ex & (x["net_base"] <= 0)).sum()), "was_win": int((ex & (x["net_base"] > 0)).sum()),
                     "saved": float((x.loc[ex, f"net_{col}"] - x.loc[ex, "net_base"]).sum())})
    L += ["## L1 in detail: trades the 15m failure exit closed early", "", _table(pd.DataFrame(rows), [
        ("per", "period", str), ("n", "trades exited early", str), ("share", "share of trades", _pct),
        ("was_loss", "would have lost anyway", str), ("was_win", "would have won", str),
        ("saved", "R gained (+) / lost (−) in total", f2)]), ""]
    if len(flips):
        fl = flips.join(S[["hold"]])
        rows = []
        for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
            x = fl[fl["hold"] == hold]
            s_ = stats(x["flip_net_R"].to_numpy())
            rows.append({"per": per, **s_})
        L += ["## L1F: the opposite trade after a 15m failure (to the liquidity on the other side)", "",
              _table(pd.DataFrame(rows), [("per", "period", str), ("n", "flip trades", str), ("win", "win %", _pct),
                                          ("avg", "avg R (own risk)", f2), ("pf", "profit factor", lambda v: f"{v:.2f}")]), ""]
    rows = []
    for hold, per in ((False, "2022 - Oct 2025"), (True, "holdout")):
        x = S[S["hold"] == hold]
        for name, m in (("L2 under daily EMA200 + ceiling", brk & x["d1_wrong_side"] & x["ceiling"]),
                        ("L3 falling 4h highs", brk & x["falling_highs"]), ("L4 second try", x["second_try"])):
            m = m.reindex(x.index).fillna(False).astype(bool)
            rows.append({"rule": name, "per": per, "n": int(m.sum()), "w_skip": (x.loc[m, "net_base"] > 0).mean() if m.any() else math.nan,
                         "w_keep": (x.loc[~m, "net_base"] > 0).mean()})
    L += ["## Filters: win % of the trades each rule removes vs keeps", "", _table(pd.DataFrame(rows), [
        ("rule", "rule", str), ("per", "period", str), ("n", "trades removed", str), ("w_skip", "win % of removed", _pct),
        ("w_keep", "win % of kept", _pct)]), ""]
    path = out_dir / "lessons.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
