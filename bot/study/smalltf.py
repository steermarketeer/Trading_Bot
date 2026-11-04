"""
Going down to smaller charts: more trades, compounding.

For each timeframe (1h, 2h, 4h, 1D) and certainty level, trades are replayed on 5m candles with four exits:
  1:1, 1.5:1, 2:1 fixed targets, and "half at 1R, stop to entry, rest at 2R".
Costs in two cases:
  market orders : 0.04% taker fee + 5 bps slippage per side  (0.18% round trip) - realistic default
  limit orders  : 0.02% maker fee per side, no slippage       (0.04% round trip) - best case, fills not guaranteed
Account simulation: trades taken in time order, several may be open at once; each risks a fixed % of equity at
entry (position = risk% / stop distance, capped at 5x equity); profit/loss is booked at the exit time.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .sr2_run import _pct, _r, _table

FIVE = pd.Timedelta(minutes=5)
MAX_TF_BARS = 60
COST_TAKER = 2 * (0.0004 + 0.0005)
COST_MAKER = 2 * 0.0002
RULES = ["1:1", "1.5:1", "2:1", "half@1R+2R"]
HOLDOUT = pd.Timestamp("2025-11-01")


def _first(mask, start=0):
    if start >= len(mask):
        return -1
    idx = np.flatnonzero(mask[start:])
    return int(idx[0]) + start if len(idx) else -1


def exits(o, h, l, c, entry, risk):
    """Long representation. Returns {rule: (R before costs, exit index)}."""
    n = len(o)
    stop0 = entry - risk
    hit_s = l <= stop0
    i_s = _first(hit_s)

    def sfill(i, lv):
        return min(o[i], lv) if i > 0 else lv

    def tfill(i, lv):
        return max(o[i], lv) if i > 0 else lv

    out = {}
    for name, T in (("1:1", 1.0), ("1.5:1", 1.5), ("2:1", 2.0)):
        tg = entry + T * risk
        i_t = _first(h >= tg)
        if i_s >= 0 and (i_t < 0 or i_s <= i_t):
            out[name] = ((sfill(i_s, stop0) - entry) / risk, i_s)
        elif i_t >= 0:
            out[name] = ((tfill(i_t, tg) - entry) / risk, i_t)
        else:
            out[name] = ((c[-1] - entry) / risk, n - 1)
    i_1 = _first(h >= entry + risk)
    if i_1 < 0 or (i_s >= 0 and i_s <= i_1):
        out["half@1R+2R"] = out["1:1"]
    else:
        tg = entry + 2 * risk
        i_be, i_t = _first(l <= entry, i_1 + 1), _first(h >= tg, i_1 + 1)
        if i_be >= 0 and (i_t < 0 or i_be <= i_t):
            out["half@1R+2R"] = (0.5 + 0.5 * (sfill(i_be, entry) - entry) / risk, i_be)
        elif i_t >= 0:
            out["half@1R+2R"] = (0.5 + 0.5 * (tfill(i_t, tg) - entry) / risk, i_t)
        else:
            out["half@1R+2R"] = (0.5 + 0.5 * (c[-1] - entry) / risk, n - 1)
    return out


def replay(trades: pd.DataFrame, df5: pd.DataFrame) -> pd.DataFrame:
    t5 = df5["open_time"].to_numpy()
    O, H, Lw, C = (df5[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    rows = []
    for _, t in trades.iterrows():
        bpt = int(pd.Timedelta(t["tf"]) / FIVE)
        ts = pd.Timestamp(t["decision_time"]).tz_convert(None).to_datetime64()
        start = int(np.searchsorted(t5, ts))
        if start >= len(t5) or t5[start] != ts:
            continue
        end = start + MAX_TF_BARS * bpt
        if end > len(O):
            continue
        d = int(t["direction"])
        o, h, l, c = O[start:end], H[start:end], Lw[start:end], C[start:end]
        if d < 0:
            o, h, l, c = -o, -l, -h, -c
        risk = float(t["risk"])
        ex = exits(o, h, l, c, o[0], risk)
        stop_pct = risk / abs(o[0])
        row = {"decision_time": pd.Timestamp(t["decision_time"]).tz_convert(None), "tf": t["tf"],
               "event": t["event"], "certainty": t["certainty"], "period": t["period"], "stop_pct": stop_pct,
               "family": t["family"]}
        for name, (r, idx) in ex.items():
            row[f"R_{name}"] = r
            row[f"exit_{name}"] = row["decision_time"] + FIVE * (idx + 1)
        rows.append(row)
    return pd.DataFrame(rows)


def stats(x: pd.DataFrame, rule: str, cost: float) -> dict:
    if not len(x):
        return {"n": 0, "win": math.nan, "avg": math.nan}
    net = x[f"R_{rule}"] - cost / x["stop_pct"]
    return {"n": len(x), "win": (net > 0).mean(), "avg": net.mean()}


def account(x: pd.DataFrame, rule: str, cost: float, risk_frac: float, lev_cap: float = 5.0) -> dict:
    """Concurrent positions; each sized on equity at entry; P&L booked at exit."""
    if not len(x):
        return {}
    ev = []
    for i, t in x.iterrows():
        ev.append((t["decision_time"], 0, i))
        ev.append((t[f"exit_{rule}"], 1, i))
    ev.sort()
    eq, open_size = 1.0, {}
    curve = [(x["decision_time"].min(), 1.0)]
    for ts, kind, i in ev:
        t = x.loc[i]
        if kind == 0:
            lev = min(risk_frac / t["stop_pct"], lev_cap)
            open_size[i] = eq * lev  # notional
        else:
            notional = open_size.pop(i)
            move = (t[f"R_{rule}"] * t["stop_pct"]) - cost
            eq = max(eq + notional * move, 0.0)
            curve.append((ts, eq))
            if eq <= 0:
                break
    s = pd.Series([v for _, v in curve], index=pd.DatetimeIndex([k for k, _ in curve])).sort_index()
    s = s[~s.index.duplicated(keep="last")]
    wk = s.resample("W-MON", label="left", closed="left").last().ffill()
    wr = wk.pct_change().dropna()
    return {"final": float(s.iloc[-1]), "max_dd": float((s / s.cummax() - 1).min()),
            "avg_week": float(wr.mean()) if len(wr) else math.nan,
            "median_week": float(wr.median()) if len(wr) else math.nan,
            "weeks_20": float((wr >= 0.20).mean()) if len(wr) else math.nan,
            "losing_weeks": float((wr < 0).mean()) if len(wr) else math.nan, "weeks": len(wr)}


def run_smalltf(cfg: Config, out_dir: Path) -> Path:
    df5, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5["open_time"] = pd.to_datetime(df5["open_time"], utc=True).dt.tz_convert(None)
    sets = []
    for tag in ("_1h", "_2h", ""):
        f = ROOT / "results" / f"scored_breakout{tag}.pkl"
        if f.exists():
            sets.append(pd.read_pickle(f).assign(family="breakout"))
        f = ROOT / "results" / f"scored_reversal{tag}.pkl"
        if f.exists():
            sets.append(pd.read_pickle(f).assign(family="reversal"))
    allt = pd.concat(sets, ignore_index=True)
    allt = allt[allt["certainty"] >= 6]
    rp = replay(allt, df5)
    rp.to_pickle(ROOT / "results" / "smalltf_replay.pkl")
    rp["hold"] = rp["decision_time"] >= HOLDOUT
    L = ["# Smaller charts: more trades, 1:1 vs 1.5:1 vs 2:1", "",
         "Trades = concept events scored by the certainty model **trained separately for each timeframe on earlier "
         "years only** (2022-25 walk-forward) or on all research data (holdout, from 2025-11-01). Every trade replayed on "
         "5-minute candles. *win* = profit after costs. *avg R* after costs.", "",
         "Costs: **market orders 0.18%** round trip (realistic) vs **limit orders 0.04%** (best case; limit entries on "
         "breakouts often don't fill, so treat this as an upper bound).", ""]
    order = {"1h": 0, "2h": 1, "4h": 2, "1D": 3}
    rows = []
    for (tf, fam, cmin), _ in [((tf, fam, c), None) for tf in ("1h", "2h", "4h", "1D")
                               for fam in ("breakout", "reversal") for c in (6, 7)]:
        x = rp[(rp["tf"] == tf) & (rp["family"] == fam) & (rp["certainty"] >= cmin)]
        if not len(x):
            continue
        for per, g in (("2022-25", x[~x["hold"]]), ("holdout", x[x["hold"]])):
            if not len(g):
                continue
            span = max((g["decision_time"].max() - g["decision_time"].min()).days / 7, 1)
            row = {"tf": tf, "fam": fam, "cert": f">= {cmin}", "period": per, "n": len(g), "per_week": len(g) / span}
            for rule in RULES:
                a, b = stats(g, rule, COST_TAKER), stats(g, rule, COST_MAKER)
                row[f"win_{rule}"], row[f"avg_{rule}"], row[f"mk_{rule}"] = a["win"], a["avg"], b["avg"]
            rows.append(row)
    T = pd.DataFrame(rows).sort_values(["fam", "cert", "tf", "period"], key=lambda s: s.map(order) if s.name == "tf" else s)
    for fam in ("breakout", "reversal"):
        t = T[T["fam"] == fam]
        L += [f"## {fam.capitalize()} trades", "",
              _table(t, [("tf", "TF", str), ("cert", "certainty", str), ("period", "period", str), ("n", "trades", str),
                         ("per_week", "trades/wk", lambda v: f"{v:.1f}"),
                         *[(f"win_{r}", f"win {r}", _pct) for r in RULES],
                         *[(f"avg_{r}", f"avg R {r} (market)", _r) for r in RULES],
                         ("mk_half@1R+2R", "avg R half@1R+2R (limit)", _r)]), ""]
    # account simulation: all breakout trades certainty >= 7 across timeframes where avg R (market, research) > 0
    L += ["## Account simulation (compounding, positions can overlap, leverage capped at 5x)", ""]
    for label, pick in (("Breakouts certainty >= 7, all timeframes", (rp["family"] == "breakout") & (rp["certainty"] >= 7)),
                        ("Breakouts certainty >= 7, 4h + 1D only", (rp["family"] == "breakout") & (rp["certainty"] >= 7)
                         & rp["tf"].isin(["4h", "1D"]))):
        x = rp[pick].reset_index(drop=True)
        rows = []
        for per, g in (("2022-25", x[~x["hold"]]), ("holdout", x[x["hold"]])):
            g = g.reset_index(drop=True)
            for rule in ("1:1", "half@1R+2R", "2:1"):
                for rf in (0.01, 0.02, 0.05):
                    a = account(g, rule, COST_TAKER, rf)
                    if a:
                        rows.append({"period": per, "rule": rule, "risk": f"{rf:.0%}", "n": len(g), **a})
        A = pd.DataFrame(rows)
        L += [f"### {label}", "",
              _table(A, [("period", "period", str), ("rule", "exit", str), ("risk", "risk / trade", str),
                         ("n", "trades", str), ("final", "end equity (x start)", lambda v: f"{v:,.2f}x"),
                         ("median_week", "median week", lambda v: f"{v:+.1%}"),
                         ("avg_week", "avg week", lambda v: f"{v:+.1%}"),
                         ("weeks_20", "weeks >= +20%", _pct), ("losing_weeks", "losing weeks", _pct),
                         ("max_dd", "max drawdown", lambda v: f"{v:.0%}")]), ""]
    path = out_dir / "smalltf_study.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
