"""
Support / resistance reversal study: when price touches a strong zone, what makes it reverse?

Event  : a candle (4h or 1D) touches a strong zone (bot/study/levels.py) known before that candle opened.
         Support touch: previous close above the zone, candle low reaches zone + 0.25 ATR.
         Resistance touch: mirror. One event per zone per 6 candles.
Decision: at the CLOSE of the touch candle (its volume / wick are known then).
         Reversal trade only if the candle closed back on the zone's side (support: close > level).
Trade  : enter next candle's open; stop = beyond the zone and the touch wick by 0.25 ATR;
         target = entry + 2 x risk; max 60 candles. Same-candle stop+target = loss; gaps fill at open.
Features (all known at the decision close) - see FEATURES.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from ..data import load_klines_5m
from .indicators import atr, ema, macd, rsi
from .indicator_search import bh_qvalues, two_prop_z
from .levels import _level_table, strong_levels
from .mtf import resample
from .patterns import swing_points
from .trend import add_weekly_trend

BAND_ATR = 0.25
STOP_PAD_ATR = 0.25
TARGET_RR = 2.0
MAX_BARS = 60
COOLDOWN = 6
SPLIT_DAY = "2023-01-01"
HOLDOUT = "2025-11-01"

FEATURES = {
    "vol_touch": "touch-candle volume / 20-candle average",
    "vol_approach": "avg volume of the 5 candles into the level / the 5 before them (<0.8 fading, >1.25 rising)",
    "vol_slope": "volume trend over the last 10 candles (fading / flat / rising)",
    "vol_div": "price made a new 20-candle extreme into the level on LOWER volume than the previous extreme",
    "wick": "rejection wick: share of the candle range on the level side (>=0.5 strong)",
    "sweep": "candle pierced the zone level and closed back on the zone's side",
    "rsi": "RSI(14) at the touch: stretched toward the level (<35 at support / >65 at resistance)",
    "rsi_div": "RSI divergence at the touch (price new 20-candle extreme, RSI not)",
    "macd_turn": "MACD histogram turned in the reversal direction on the touch candle",
    "ema50_side": "close vs EMA50 on this timeframe: with the reversal / against",
    "ema200_side": "close vs EMA200 on this timeframe: with the reversal / against",
    "structure": "market structure from the last 2 confirmed swing highs and lows: up / down / range",
    "structure_vs": "structure with or against the reversal direction",
    "speed": "approach speed: ATRs travelled in the 5 candles into the level (fast > 2)",
    "retest": "zone touched in the previous 30 candles (retest) vs first touch",
    "zone_weekly": "zone contains a weekly swing",
    "zone_touches": "number of swings forming the zone (3-4 / 5+)",
    "weekly_trend_vs": "weekly trend with / against the reversal direction",
    "daily_trend_vs": "daily close vs daily EMA50 with / against the reversal direction (4h study only)",
}


def _structure(sh: list, sl: list, t: int, k: int) -> str:
    """Up = higher high & higher low; down = lower high & lower low; using swings confirmed by candle t."""
    hs = [p for i, p, c in sh if c <= t][-2:]
    ls = [p for i, p, c in sl if c <= t][-2:]
    if len(hs) < 2 or len(ls) < 2:
        return "unknown"
    if hs[1] > hs[0] and ls[1] > ls[0]:
        return "up"
    if hs[1] < hs[0] and ls[1] < ls[0]:
        return "down"
    return "range"


def label_trades(b: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    o, h, l, c = (b[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    n = len(b)
    out = []
    for j, d, stop in zip(ev["j"], ev["direction"], ev["stop"]):
        i = j + 1
        if i >= n:
            out.append(("incomplete", math.nan, math.nan, math.nan, math.nan))
            continue
        e = o[i]
        risk = (e - stop) * d
        if risk <= 0:  # opened beyond the stop already: no trade
            out.append(("no_trade", math.nan, math.nan, e, math.nan))
            continue
        tgt = e + d * TARGET_RR * risk
        res, r, bars = None, None, None
        last = min(n - 1, i + MAX_BARS - 1)
        for k in range(i, last + 1):
            if k > i and d * (o[k] - stop) <= 0:
                res, r, bars = "loss", d * (o[k] - e) / risk, k - i + 1
                break
            if k > i and d * (o[k] - tgt) >= 0:
                res, r, bars = "win", d * (o[k] - e) / risk, k - i + 1
                break
            hit_s = (l[k] <= stop) if d > 0 else (h[k] >= stop)
            hit_t = (h[k] >= tgt) if d > 0 else (l[k] <= tgt)
            if hit_s:
                res, r, bars = "loss", -1.0, k - i + 1
                break
            if hit_t:
                res, r, bars = "win", TARGET_RR, k - i + 1
                break
        if res is None:
            if last - i + 1 < MAX_BARS:
                out.append(("incomplete", math.nan, math.nan, e, risk))
                continue
            res, r, bars = "timeout", d * (c[last] - e) / risk, MAX_BARS
        out.append((res, float(r), bars, e, risk))
    lab = pd.DataFrame(out, columns=["outcome", "r", "bars", "entry", "risk"], index=ev.index)
    return pd.concat([ev, lab], axis=1)


def find_touches(df5: pd.DataFrame, rule: str, daily_ctx: pd.DataFrame | None, swing_k: int = 5) -> pd.DataFrame:
    b = resample(df5, rule).reset_index(drop=True)
    table = _level_table(df5)
    a = atr(b, 14)
    r = rsi(b["close"])
    line, sig = macd(b["close"])
    hist = line - sig
    e50, e200 = ema(b["close"], 50), ema(b["close"], 200)
    vol = b["volume"]
    vavg20 = vol.shift(1).rolling(20, min_periods=20).mean()
    v5 = vol.rolling(5, min_periods=5).mean()
    vprev5 = v5.shift(5)
    sh, sl = swing_points(b["high"].to_numpy(float), b["low"].to_numpy(float), swing_k)
    o, h, l, c = (b[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    ot = pd.to_datetime(b["open_time"], utc=True)
    ct = pd.to_datetime(b["close_time"], utc=True)

    last_touch: dict = {}
    zone_cache_key, zones = None, np.array([])
    rows = []
    for j in range(210, len(b)):
        aj = a.iloc[j]
        if not np.isfinite(aj) or aj <= 0:
            continue
        t_open = ot.iloc[j]
        key = int((table["known"] <= t_open).sum())  # zones only change when a new swing is confirmed
        if key != zone_cache_key or t_open.hour == 0:
            zones = strong_levels(table, t_open)  # known before this candle opened
            zone_cache_key = key
        if len(zones) == 0:
            continue
        band = BAND_ATR * aj
        pc = c[j - 1]
        sup = zones[(zones < pc) & (l[j] <= zones + band)]
        res_ = zones[(zones > pc) & (h[j] >= zones - band)]
        for kind, cand in (("support", sup), ("resistance", res_)):
            if len(cand) == 0:
                continue
            L = cand.max() if kind == "support" else cand.min()
            zkey = (kind, round(L, 2))
            if j - last_touch.get(zkey, -10**9) < COOLDOWN:
                continue
            last_touch[zkey] = j
            d = 1 if kind == "support" else -1
            held = c[j] > L if d > 0 else c[j] < L
            rng = h[j] - l[j]
            wick = ((min(o[j], c[j]) - l[j]) if d > 0 else (h[j] - max(o[j], c[j]))) / rng if rng > 0 else 0.0
            stop = (min(l[j], L) - STOP_PAD_ATR * aj) if d > 0 else (max(h[j], L) + STOP_PAD_ATR * aj)
            # volume divergence: new 20-candle extreme on lower volume than the previous extreme
            win = slice(j - 20, j)
            if d > 0:
                new_ext = l[j] <= l[win].min()
                prev_i = j - 20 + int(np.argmin(l[win]))
            else:
                new_ext = h[j] >= h[win].max()
                prev_i = j - 20 + int(np.argmax(h[win]))
            vol_div = bool(new_ext and vol.iloc[j] < vol.iloc[prev_i])
            rsi_div = bool(new_ext and ((r.iloc[j] > r.iloc[prev_i]) if d > 0 else (r.iloc[j] < r.iloc[prev_i])))
            vs = np.polyfit(np.arange(10), vol.iloc[j - 9:j + 1].to_numpy(float), 1)[0] / max(vavg20.iloc[j], 1e-12)
            struct = _structure(sh, sl, j, swing_k)
            zone_sw = table[(table["known"] <= t_open) & (table["formed"] >= t_open - table["lookback"])
                            & (table["price"].between(L * 0.99, L * 1.01))]
            rows.append({
                "j": j, "time": ct.iloc[j], "day": ct.iloc[j].strftime("%Y-%m-%d"), "kind": kind, "direction": d,
                "level": L, "close": c[j], "atr": aj, "held_at_close": bool(held), "stop": stop,
                "vol_touch": vol.iloc[j] / vavg20.iloc[j] if vavg20.iloc[j] > 0 else math.nan,
                "vol_approach": v5.iloc[j - 1] / vprev5.iloc[j - 1] if vprev5.iloc[j - 1] > 0 else math.nan,
                "vol_slope": vs, "vol_div": vol_div, "wick": wick,
                "sweep": bool((l[j] < L) if d > 0 else (h[j] > L)) and bool(held),
                "rsi": r.iloc[j], "rsi_div": rsi_div,
                "macd_turn": bool((hist.iloc[j] > hist.iloc[j - 1]) if d > 0 else (hist.iloc[j] < hist.iloc[j - 1])),
                "ema50_with": bool((c[j] > e50.iloc[j]) if d > 0 else (c[j] < e50.iloc[j])),
                "ema200_with": bool((c[j] > e200.iloc[j]) if d > 0 else (c[j] < e200.iloc[j])),
                "structure": struct,
                "speed": d * (c[j - 5] - (l[j] if d > 0 else h[j])) / aj,
                "retest": any(abs(k2[1] - L) / L < 0.01 and k2[0] == kind and 0 < j - v2 <= 30
                              for k2, v2 in last_touch.items() if k2 != zkey),
                "zone_weekly": bool((zone_sw["tf"] == "1W").any()),
                "zone_touches": int(len(zone_sw)),
            })
    ev = pd.DataFrame(rows)
    if ev.empty:
        return ev
    ev["structure_vs"] = np.where(ev["structure"].isin(["unknown", "range"]), ev["structure"],
                                  np.where((ev["structure"] == "up") == (ev["direction"] > 0), "with", "against"))
    # weekly / daily trend known at the decision close
    dd = resample(df5, "1D").rename(columns={"open_time": "ts"})
    dd["day"] = dd["ts"].dt.strftime("%Y-%m-%d")
    wt = add_weekly_trend(dd)[["close_time", "weekly_trend"]]
    dd["e50"] = ema(dd["close"], 50)
    dd["dside"] = np.sign(dd["close"] - dd["e50"]).where(dd["e50"].notna(), 0)
    left = ev[["time"]].assign(_r=np.arange(len(ev))).sort_values("time")
    left["time"] = left["time"].dt.as_unit("ns")
    for tbl, cols in ((wt, ["weekly_trend"]), (dd[["close_time", "dside"]], ["dside"])):
        tb = tbl.copy()
        tb["close_time"] = pd.to_datetime(tb["close_time"], utc=True).dt.as_unit("ns")
        left = pd.merge_asof(left, tb.sort_values("close_time"), left_on="time", right_on="close_time",
                             direction="backward").drop(columns="close_time")
    left = left.sort_values("_r")
    wt_sign = left["weekly_trend"].map({"Up": 1, "Down": -1}).fillna(0).to_numpy()
    ev["weekly_trend_vs"] = np.where(wt_sign == 0, "flat", np.where(wt_sign * ev["direction"] > 0, "with", "against"))
    ds = left["dside"].fillna(0).to_numpy()
    ev["daily_trend_vs"] = np.where(ds == 0, "flat", np.where(ds * ev["direction"] > 0, "with", "against"))
    held = ev[ev["held_at_close"]]
    lab = label_trades(b, held)
    ev = ev.join(lab[["outcome", "r", "bars", "entry", "risk"]])
    ev.loc[~ev["held_at_close"], "outcome"] = "broke_at_touch"  # closed through the level: no reversal trade
    return ev


def bucketize(ev: pd.DataFrame) -> pd.DataFrame:
    """Readable buckets per feature (thresholds fixed in advance, not tuned)."""
    x = pd.DataFrame(index=ev.index)
    x["vol_touch"] = pd.cut(ev["vol_touch"], [0, 0.7, 1.5, 3, np.inf], labels=["low <0.7x", "normal", "high 1.5-3x", "climax >3x"])
    x["vol_approach"] = pd.cut(ev["vol_approach"], [0, 0.8, 1.25, np.inf], labels=["fading", "steady", "rising"])
    x["vol_slope"] = pd.cut(ev["vol_slope"], [-np.inf, -0.03, 0.03, np.inf], labels=["fading", "flat", "rising"])
    x["vol_div"] = ev["vol_div"].map({True: "yes", False: "no"})
    x["wick"] = pd.cut(ev["wick"], [-0.01, 0.2, 0.5, 1.01], labels=["small", "medium", "strong >=0.5"])
    x["sweep"] = ev["sweep"].map({True: "yes", False: "no"})
    stretched = np.where(ev["direction"] > 0, ev["rsi"] < 35, ev["rsi"] > 65)
    x["rsi"] = np.where(ev["rsi"].isna(), None, np.where(stretched, "stretched", "normal"))
    x["rsi_div"] = ev["rsi_div"].map({True: "yes", False: "no"})
    x["macd_turn"] = ev["macd_turn"].map({True: "yes", False: "no"})
    x["ema50_side"] = ev["ema50_with"].map({True: "with", False: "against"})
    x["ema200_side"] = ev["ema200_with"].map({True: "with", False: "against"})
    x["structure"] = ev["structure"]
    x["structure_vs"] = ev["structure_vs"]
    x["speed"] = pd.cut(ev["speed"], [-np.inf, 1, 2, np.inf], labels=["slow <1", "medium", "fast >2"])
    x["retest"] = ev["retest"].map({True: "retest", False: "first touch"})
    x["zone_weekly"] = ev["zone_weekly"].map({True: "yes", False: "no"})
    x["zone_touches"] = pd.cut(ev["zone_touches"], [0, 4, np.inf], labels=["3-4", "5+"])
    x["weekly_trend_vs"] = ev["weekly_trend_vs"]
    x["daily_trend_vs"] = ev["daily_trend_vs"]
    return x.astype(object).where(x.notna(), None)


def _st(g: pd.DataFrame) -> dict:
    n = len(g)
    return {"n": n, "win": (g["outcome"] == "win").mean() if n else math.nan,
            "fail": (g["outcome"] == "loss").mean() if n else math.nan,
            "avg_r": g["r"].mean() if n else math.nan}


def feature_table(tr: pd.DataFrame, bk: pd.DataFrame) -> pd.DataFrame:
    rows = []
    h1 = tr["day"] < SPLIT_DAY
    for f in bk.columns:
        for val in [v for v in pd.unique(bk[f]) if v is not None]:
            m = bk[f] == val
            if m.sum() < 30 or (~m).sum() < 30:
                continue
            k1 = int((tr.loc[m, "outcome"] == "win").sum())
            k2 = int((tr.loc[~m, "outcome"] == "win").sum())
            z, p = two_prop_z(k1, int(m.sum()), k2, int((~m).sum()))
            s, rest = _st(tr[m]), _st(tr[~m])
            s1, s2 = _st(tr[m & h1]), _st(tr[m & ~h1])
            r1, r2 = _st(tr[~m & h1]), _st(tr[~m & ~h1])
            rows.append({"feature": f, "value": val, **s, "rest_win": rest["win"], "rest_r": rest["avg_r"],
                         "diff_win": s["win"] - rest["win"], "z": z, "p": p,
                         "half1_diff": s1["win"] - r1["win"] if s1["n"] >= 15 else math.nan,
                         "half2_diff": s2["win"] - r2["win"] if s2["n"] >= 15 else math.nan})
    t = pd.DataFrame(rows)
    t["q"] = bh_qvalues(t["p"].to_numpy())
    same = (np.sign(t["half1_diff"]) == np.sign(t["diff_win"])) & (np.sign(t["half2_diff"]) == np.sign(t["diff_win"]))
    t["verdict"] = np.where((t["q"] < 0.10) & same, np.where(t["diff_win"] > 0, "HELPS REVERSAL", "HURTS REVERSAL"),
                            np.where(same, "consistent, not significant", "noise"))
    return t.sort_values("z", ascending=False)


def grid(tr: pd.DataFrame, bk: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    g = pd.concat([tr[["outcome", "r"]], bk[[a, b]]], axis=1).dropna()
    out = g.groupby([a, b], observed=True).agg(
        n=("r", "size"), win=("outcome", lambda s: (s == "win").mean()), avg_r=("r", "mean")).reset_index()
    return out


def trade_return(r: float, risk_pct: float, outcome: str, leverage: float, cost_frac: float,
                 mmr: float = 0.005) -> float:
    """Return on margin at `leverage` (isolated). Liquidation = -100% when the stop sits beyond the
    liquidation price and the trade did not win, or a loss (incl. gaps) moved further than it."""
    liq = 1 / leverage - mmr
    if outcome != "win" and risk_pct >= liq:
        return -1.0
    if r < 0 and -r * risk_pct >= liq:
        return -1.0
    return max(leverage * (r * risk_pct - cost_frac), -1.0)


def sequential_weekly(tr: pd.DataFrame, leverage: float, cost_frac: float, sizing: str = "full",
                      risk_frac: float = 0.10, mmr: float = 0.005) -> dict:
    """
    One position at a time (events during an open trade are skipped), compounding.
    sizing="full": all equity as margin at `leverage`.
    sizing="risk": a stop-out loses `risk_frac` of equity (position = risk_frac / stop distance), capped at `leverage`.
    Trades whose stop is beyond the liquidation price at `leverage` are skipped (can't be placed safely).
    """
    tr = tr.sort_values("time")
    liq = 1 / leverage - mmr
    busy_until = None
    eq = 1.0
    rows = []
    for _, t in tr.iterrows():
        if busy_until is not None and t["time"] < busy_until:
            continue
        risk_pct = t["risk"] / t["entry"]
        if risk_pct >= liq:
            continue
        lev = leverage if sizing == "full" else min(leverage, risk_frac / risk_pct)
        move = t["r"] * risk_pct
        ret = -1.0 if (t["r"] < 0 and -move >= 1 / lev - mmr) else max(lev * (move - cost_frac), -1.0)
        eq *= 1 + ret
        rows.append({"time": t["time"], "ret": ret, "eq": eq})
        busy_until = t["time"] + t["bar_len"] * t["bars"]
        if eq <= 0:
            break
    if not rows:
        return {}
    s = pd.DataFrame(rows).set_index("time")["eq"]
    wk = s.resample("W-MON", label="left", closed="left").last().ffill()
    wr = pd.concat([pd.Series([1.0]), wk.reset_index(drop=True)]).pct_change().dropna()
    path = pd.concat([pd.Series([1.0]), s.reset_index(drop=True)])
    return {"trades": len(rows), "final_equity": float(eq), "weeks": len(wr),
            "avg_week": float(wr.mean()), "median_week": float(wr.median()),
            "share_weeks_20pct": float((wr >= 0.20).mean()), "share_losing_weeks": float((wr < 0).mean()),
            "max_dd": float((path / path.cummax() - 1).min()),
            "liquidations": int((pd.DataFrame(rows)["ret"] <= -1).sum())}


def run_sr_study(cfg: Config, out_dir: Path, leverage: float = 5.0) -> Path:
    df5, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    cost_frac = 2 * (cfg.costs.taker_fee + cfg.costs.slippage_bps / 10_000)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for tf, rule in (("4h", "4h"), ("1D", "1D")):
        ev = find_touches(df5, rule, None)
        ev["bar_len"] = pd.Timedelta(rule)
        ev.to_csv(out_dir / f"sr_touches_{tf}.csv", index=False)
        results[tf] = ev
    return write_report(results, out_dir, leverage, cost_frac)


def _pct(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.0%}"


def _pp(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:+.0f} pts"


def _r(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.2f}"


def _table(df, cols):
    head = "| " + " | ".join(c[1] for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = ["| " + " | ".join(f(r[c]) for c, _, f in cols) + " |" for _, r in df.iterrows()]
    return "\n".join([head, sep, *body])


def write_report(results: dict, out_dir: Path, leverage: float, cost_frac: float) -> Path:
    L = ["# Support / resistance reversal study", "",
         "When price touches a strong zone, what decides whether it reverses or breaks? Zones come from swings "
         "confirmed before the touch (weekly / daily / 4h, >= 3 touches or a weekly swing). Decision at the touch "
         "candle's close; the reversal trade enters the next open with the stop beyond the zone and wick, target 2x risk.",
         f"Research = events before {HOLDOUT} (halves split at {SPLIT_DAY}); holdout = from {HOLDOUT}.", ""]
    for tf, ev in results.items():
        if ev.empty:
            continue
        cut = (pd.Timestamp(HOLDOUT) - ev["bar_len"].iloc[0] * MAX_BARS).strftime("%Y-%m-%d")
        n_all = len(ev)
        held = ev["held_at_close"].mean()
        tr = ev[ev["outcome"].isin(["win", "loss", "timeout"])]
        res, hold = tr[tr["day"] < cut], tr[tr["day"] >= HOLDOUT]
        bk_res, bk_hold = bucketize(res), bucketize(hold)
        ft = feature_table(res, bk_res)
        ft.to_csv(out_dir / f"sr_features_{tf}.csv", index=False)
        base = _st(res)
        L += [f"## {tf} chart", "",
              f"- Zone touches: **{n_all}**. The level held at the touch candle's close **{held:.0%}** of the time "
              f"(close back on the zone's side).",
              f"- Reversal trades (held at close): research **{base['n']}**, win **{_pct(base['win'])}**, fail "
              f"**{_pct(base['fail'])}**, avg **{_r(base['avg_r'])} R** (break-even ~33%).",
              "", "### Which conditions make the reversal work? (research)", "",
              "*diff* = win rate with this condition minus without it. HELPS/HURTS = q < 0.10 across all rows AND the "
              "same direction in both halves.", "",
              _table(ft[ft["verdict"].isin(["HELPS REVERSAL", "HURTS REVERSAL"])], [
                  ("feature", "feature", str), ("value", "value", str), ("n", "trades", str), ("win", "win", _pct),
                  ("rest_win", "win without", _pct), ("diff_win", "diff", _pp), ("avg_r", "avg R", _r),
                  ("half1_diff", "half 1", _pp), ("half2_diff", "half 2", _pp), ("q", "q", lambda x: f"{x:.3f}"),
                  ("verdict", "verdict", str)]) if (ft["verdict"].isin(["HELPS REVERSAL", "HURTS REVERSAL"])).any()
              else "No single condition passed all checks.", ""]
        L += ["### Volume: the key question", "",
              "Win rate of the reversal trade by **volume into the level** (rows) x **volume on the touch candle** "
              "(columns), research period:", ""]
        g = grid(res, bk_res, "vol_approach", "vol_touch")
        if len(g):
            piv_w = g.pivot(index="vol_approach", columns="vol_touch", values="win")
            piv_n = g.pivot(index="vol_approach", columns="vol_touch", values="n")
            cols = list(piv_w.columns)
            hdr = "| volume into level \\ touch volume | " + " | ".join(str(c) for c in cols) + " |"
            sep = "|---|" + "|".join("---" for _ in cols) + "|"
            body = []
            for idx in piv_w.index:
                cells = [f"{_pct(piv_w.loc[idx, c])} (n={int(piv_n.loc[idx, c]) if not pd.isna(piv_n.loc[idx, c]) else 0})"
                         for c in cols]
                body.append(f"| {idx} | " + " | ".join(cells) + " |")
            L += [hdr, sep, *body, ""]
        for a_, b_ in (("vol_slope", "structure_vs"), ("vol_div", "rsi_div"), ("vol_touch", "wick"),
                       ("vol_approach", "weekly_trend_vs")):
            g = grid(res, bk_res, a_, b_)
            if len(g):
                L += [f"{a_} x {b_}:", "", _table(g, [(a_, a_, str), (b_, b_, str), ("n", "trades", str),
                                                      ("win", "win", _pct), ("avg_r", "avg R", _r)]), ""]
        L += ["### Every condition (research)", "",
              _table(ft.sort_values(["feature", "value"]), [
                  ("feature", "feature", str), ("value", "value", str), ("n", "trades", str), ("win", "win", _pct),
                  ("rest_win", "win without", _pct), ("diff_win", "diff", _pp), ("avg_r", "avg R", _r),
                  ("half1_diff", "half 1", _pp), ("half2_diff", "half 2", _pp),
                  ("q", "q", lambda x: "-" if pd.isna(x) else f"{x:.2f}"), ("verdict", "verdict", str)]), ""]
        # rule built from research findings only, then holdout
        helps = ft[ft["verdict"] == "HELPS REVERSAL"]
        hurts = ft[ft["verdict"] == "HURTS REVERSAL"]

        def rule_mask(tr_, bk_):
            m = pd.Series(True, index=tr_.index)
            for _, rw in helps.iterrows():
                m &= bk_[rw["feature"]] == rw["value"]
            for _, rw in hurts.iterrows():
                m &= bk_[rw["feature"]] != rw["value"]
            return m
        variants = [("every reversal trade", None)]
        if len(helps) or len(hurts):
            variants.append(("apply all HELPS (require) + HURTS (avoid)", rule_mask))
        for _, rw in helps.head(3).iterrows():
            variants.append((f"only {rw['feature']} = {rw['value']}",
                             lambda tr_, bk_, f=rw["feature"], v=rw["value"]: bk_[f] == v))
        vrows = []
        for name, fn in variants:
            rm = pd.Series(True, index=res.index) if fn is None else fn(res, bk_res)
            hm = pd.Series(True, index=hold.index) if fn is None else fn(hold, bk_hold)
            a_, b_ = _st(res[rm]), _st(hold[hm])
            for sizing, rf, label in (("full", 0.0, "full margin 5x"), ("risk", 0.10, "risk 10%/trade (<=5x)"),
                                      ("risk", 0.02, "risk 2%/trade (<=5x)")):
                wr = sequential_weekly(res[rm], leverage, cost_frac, sizing=sizing, risk_frac=rf)
                wh = sequential_weekly(hold[hm], leverage, cost_frac, sizing=sizing, risk_frac=rf)
                vrows.append({"rule": name, "sizing": label,
                              "r_n": a_["n"], "r_win": a_["win"], "r_r": a_["avg_r"],
                              "h_n": b_["n"], "h_win": b_["win"], "h_r": b_["avg_r"],
                              "r_final": wr.get("final_equity", math.nan), "r_week": wr.get("median_week", math.nan),
                              "r_20": wr.get("share_weeks_20pct", math.nan), "r_lose": wr.get("share_losing_weeks", math.nan),
                              "r_dd": wr.get("max_dd", math.nan),
                              "h_final": wh.get("final_equity", math.nan), "h_week": wh.get("median_week", math.nan),
                              "h_dd": wh.get("max_dd", math.nan)})
        fx = lambda x: "-" if pd.isna(x) else f"{x:,.2f}x"  # noqa: E731
        fw = lambda x: "-" if pd.isna(x) else f"{x:+.1%}"  # noqa: E731
        fd = lambda x: "-" if pd.isna(x) else f"{x:.0%}"  # noqa: E731
        L += [f"### Turning it into a rule ({tf})", "",
              f"Account simulation at up to **{leverage:g}x**: one trade at a time, compounding, after fees and slippage "
              "(funding not included). Trades whose stop lies beyond the liquidation price are skipped. "
              "*final* = ending equity as a multiple of the start; *median week* = typical week's return.", "",
              _table(pd.DataFrame(vrows), [
                  ("rule", "rule", str), ("sizing", "sizing", str),
                  ("r_n", "research trades", str), ("r_win", "win", _pct), ("r_r", "avg R", _r),
                  ("r_final", "final", fx), ("r_week", "median week", fw), ("r_20", "weeks >= +20%", _pct),
                  ("r_lose", "losing weeks", _pct), ("r_dd", "max drawdown", fd),
                  ("h_n", "holdout trades", str), ("h_win", "holdout win", _pct), ("h_r", "holdout R", _r),
                  ("h_final", "holdout final", fx), ("h_dd", "holdout max DD", fd)]), ""]
    L += ["## Feature definitions", "", *[f"- **{k}**: {v}" for k, v in FEATURES.items()], "",
          "Raw events: `sr_touches_4h.csv`, `sr_touches_1D.csv`; all condition stats: `sr_features_*.csv`."]
    path = out_dir / "sr_study.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
