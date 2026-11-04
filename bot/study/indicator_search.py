"""
Which indicators would have caught the failed trades?

Tests every hint (90 from mtf.py + ~180 new ones from mtf2.py) on the same study trades.
Selection uses the RESEARCH period only, with three guards against luck:
  1. Benjamini-Hochberg false-discovery control across all hints (q < 0.10)
  2. the effect must point the same way in BOTH halves of the research period
  3. redundant hints (that flag mostly the same trades) are dropped
The holdout period is used once, at the end, to check the combined filter.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from ..data import load_klines_5m
from .mtf import hint_columns
from .mtf2 import context_hints, load_funding_table, tf_hints2

SPLIT_DAY = "2023-01-01"   # research half 1 < SPLIT_DAY <= research half 2
MIN_WARNED = 30            # in the research period
MIN_WARNED_HALF = 10       # in each half
Q_MAX = 0.10
MAX_OVERLAP = 0.5          # phi correlation above which two hints are treated as the same


def two_prop_z(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """z and two-sided p for H0: p1 == p2 (pooled)."""
    if n1 == 0 or n2 == 0:
        return math.nan, math.nan
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return math.nan, math.nan
    z = (k1 / n1 - k2 / n2) / se
    return z, math.erfc(abs(z) / math.sqrt(2))


def bh_qvalues(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (NaN stays NaN)."""
    p = np.asarray(p, float)
    q = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    m = len(pv)
    if m == 0:
        return q
    order = np.argsort(pv)
    ranked = pv[order] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(ranked, 1.0)
    q[ok] = out
    return q


def _fail(x: pd.DataFrame) -> float:
    return float((x["outcome"] == "loss").mean()) if len(x) else math.nan


def _diff(x: pd.DataFrame, col: str) -> tuple[int, float]:
    w = x[col] < 0
    if w.sum() == 0 or (~w).sum() == 0:
        return int(w.sum()), math.nan
    return int(w.sum()), _fail(x[w]) - _fail(x[~w])


def evaluate_hints(res: pd.DataFrame, hold: pd.DataFrame, cols: list[str], new_cols: set[str]) -> pd.DataFrame:
    h1, h2 = res[res["day"] < SPLIT_DAY], res[res["day"] >= SPLIT_DAY]
    rows = []
    for col in cols:
        w = res[col] < 0
        nw, nn = int(w.sum()), int((~w).sum())
        kw = int((res.loc[w, "outcome"] == "loss").sum())
        kn = int((res.loc[~w, "outcome"] == "loss").sum())
        z, p = two_prop_z(kw, nw, kn, nn)
        n1, d1 = _diff(h1, col)
        n2, d2 = _diff(h2, col)
        nh, dh = _diff(hold, col)
        tf, _, name = col.partition("_") if not col.startswith("ctx_") else ("context", "", col[4:])
        rows.append({
            "column": col, "timeframe": tf, "hint": name, "new": col in new_cols,
            "n_warned": nw, "fail_if_warned": kw / nw if nw else math.nan, "fail_if_not": kn / nn if nn else math.nan,
            "diff": (kw / nw - kn / nn) if nw and nn else math.nan, "z": z, "p": p,
            "r_if_warned": res.loc[w, "r"].mean() if nw else math.nan, "r_if_not": res.loc[~w, "r"].mean(),
            "n_half1": n1, "diff_half1": d1, "n_half2": n2, "diff_half2": d2,
            "n_hold": nh, "diff_hold": dh,
            "testable": nw >= MIN_WARNED and nn >= MIN_WARNED and n1 >= MIN_WARNED_HALF and n2 >= MIN_WARNED_HALF,
        })
    t = pd.DataFrame(rows)
    t["q"] = np.nan
    ok = t["testable"]
    t.loc[ok, "q"] = bh_qvalues(t.loc[ok, "p"].to_numpy())
    same_way = (np.sign(t["diff_half1"]) == np.sign(t["diff"])) & (np.sign(t["diff_half2"]) == np.sign(t["diff"]))
    t["verdict"] = "not enough trades"
    t.loc[ok, "verdict"] = "noise"
    t.loc[ok & same_way & (t["diff"] > 0), "verdict"] = "weak (consistent, not significant)"
    t.loc[ok & same_way & (t["diff"] < 0), "verdict"] = "weak inverse"
    t.loc[ok & same_way & (t["diff"] > 0) & (t["q"] < Q_MAX), "verdict"] = "CATCHES FAILURES"
    t.loc[ok & same_way & (t["diff"] < 0) & (t["q"] < Q_MAX), "verdict"] = "INVERSE (warning = better trades)"
    return t.sort_values(["verdict", "z"], ascending=[True, False])


def pick_independent(res: pd.DataFrame, cands: pd.DataFrame) -> list[str]:
    picked: list[str] = []
    for col in cands.sort_values("z", ascending=False)["column"]:
        x = (res[col] < 0).astype(float)
        if x.std() == 0:
            continue
        if all(abs(np.corrcoef(x, (res[p] < 0).astype(float))[0, 1]) < MAX_OVERLAP for p in picked):
            picked.append(col)
    return picked


def _stats(x: pd.DataFrame) -> dict:
    return {"trades": len(x), "win": (x["outcome"] == "win").mean() if len(x) else math.nan,
            "fail": _fail(x), "avg_r": x["r"].mean() if len(x) else math.nan,
            "margin_5x": x["margin_ret"].mean() if len(x) else math.nan}


def _pct(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.0%}"


def _pp(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:+.0f} pts"


def _r(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.2f}"


def _m(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.1%}"


def _table(df, cols):
    head = "| " + " | ".join(c[1] for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = ["| " + " | ".join(f(r[c]) for c, _, f in cols) + " |" for _, r in df.iterrows()]
    return "\n".join([head, sep, *body])


HINT_TEXT = {
    "adx_weak": "ADX < 20 (no trend)", "di": "-DI/+DI against", "stoch_ext": "Stochastic stretched",
    "cci_ext": "CCI beyond +/-100", "willr_ext": "Williams %R stretched", "mfi_ext": "MFI stretched",
    "obv": "OBV vs its EMA20 against", "cmf": "Chaikin Money Flow against", "vwap": "below/above VWAP(20)",
    "supertrend": "Supertrend against", "psar": "Parabolic SAR against", "keltner_ext": "outside Keltner",
    "donch_room": "<1 ATR to the 20-candle extreme", "vol_expand": "ATR14 > 1.5x ATR50",
    "climax": "volume climax against", "candle": "reversal candle against", "roc_against": "10-candle momentum against",
    "funding": "funding crowded on our side", "btc_daily": "BTC daily trend against", "btc_weekly": "BTC weekly trend against",
    "ethbtc": "ETH/BTC trend against", "room_1d": "daily swing level before target", "room_1w": "weekly swing level before target",
    "sma200_ext": "far from SMA200", "weekend": "weekend entry",
    "trend": "close vs EMA50 against", "slope": "EMA20 slope against", "macd": "MACD histogram against",
    "macd_fade": "MACD momentum fading", "rsi_ext": "RSI stretched", "cloud": "Ichimoku cloud against",
    "bb_ext": "outside Bollinger", "stretch": ">2 ATR from EMA20", "diverge": "RSI divergence",
}


def run_indicator_search(cfg: Config, out_dir: Path, holdout_start: str = "2025-11-01", max_days: int = 20) -> Path:
    trades = pd.read_csv(out_dir / "trades_with_hints.csv")
    eth5, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    btc5, _ = load_klines_5m(cfg.data_dir, cfg.btc_symbol)
    new_tf = tf_hints2(eth5, trades)
    new_ctx = context_hints(trades, eth5, btc5, load_funding_table(cfg.data_dir, cfg.symbol))
    t = pd.concat([trades, new_tf, new_ctx], axis=1)
    new_cols = set(new_tf.columns) | set(new_ctx.columns)
    cols = hint_columns() + list(new_tf.columns) + list(new_ctx.columns)
    t.to_csv(out_dir / "trades_with_all_hints.csv", index=False)

    cut = (pd.Timestamp(holdout_start) - pd.Timedelta(days=max_days)).strftime("%Y-%m-%d")
    res, hold = t[t["day"] < cut], t[t["day"] >= holdout_start]
    ev = evaluate_hints(res, hold, cols, new_cols)
    ev.to_csv(out_dir / "indicator_hints.csv", index=False)

    catch = ev[ev["verdict"] == "CATCHES FAILURES"]
    picked = pick_independent(res, catch)
    inverse = ev[ev["verdict"].str.startswith("INVERSE")]

    def apply(x, cols_):
        if not cols_:
            return x
        return x[~(x[cols_] < 0).any(axis=1)]

    base_b = ["1W_macd_fade"]
    variants = [
        ("every trade", []),
        ("skip weekly MACD fade (earlier filter B)", base_b),
    ]
    if picked:
        variants += [("skip if ANY selected indicator warns", picked),
                     ("B + selected indicators", sorted(set(base_b + picked)))]
    vrows = []
    for name, cs in variants:
        r_, h_ = _stats(apply(res, cs)), _stats(apply(hold, cs))
        vrows.append({"variant": name, **{f"r_{k}": v for k, v in r_.items()}, **{f"h_{k}": v for k, v in h_.items()}})
    for col in inverse["column"]:  # reverse findings: keep ONLY the trades where the state was present
        row = ev.set_index("column").loc[col]
        nm = f"only when {HINT_TEXT.get(row['hint'], col)} ({row['timeframe']})"
        r_, h_ = _stats(res[res[col] < 0]), _stats(hold[hold[col] < 0])  # empty -> NaN, printed as "-"
        vrows.append({"variant": nm, **{f"r_{k}": v for k, v in r_.items()}, **{f"h_{k}": v for k, v in h_.items()}})
    vt = pd.DataFrame(vrows)

    losses = res[res["outcome"] == "loss"]
    wins = res[res["outcome"] == "win"]
    caught = (losses[picked] < 0).any(axis=1).mean() if picked else 0.0
    wins_lost = (wins[picked] < 0).any(axis=1).mean() if picked else 0.0

    n_tested = int(ev["testable"].sum())
    label = ev.assign(what=[HINT_TEXT.get(h, h) for h in ev["hint"]])
    L = [
        "# Which indicators would have caught the failures?",
        "",
        f"Same trades as the failure analysis. Research: signals before {cut}, split into two halves at {SPLIT_DAY}. "
        f"Holdout: from {holdout_start} (used only in section 3).",
        "",
        f"- Hints tested: **{len(cols)}** ({len(new_cols)} new + 90 from before); **{n_tested}** had enough trades "
        f"(>= {MIN_WARNED} warned, >= {MIN_WARNED_HALF} in each half).",
        f"- A hint **catches failures** only if (1) trades it warned about failed more often, with a false-discovery-controlled "
        f"q < {Q_MAX:.2f} across all {n_tested} tests, and (2) that was true in **both** halves of the research period.",
        "- *pts* = percentage points of extra fail rate when the hint warned.",
        "- Trades overlap in time, so the real uncertainty is somewhat larger than the statistics assume. The two-halves "
        "rule and the holdout check are there to catch that.",
        "",
        "## 1. Indicators that catch failures",
        "",
    ]
    if catch.empty:
        L += ["**None** passed all checks.", ""]
    else:
        L += [_table(label[label["verdict"] == "CATCHES FAILURES"].sort_values("z", ascending=False), [
            ("timeframe", "TF", str), ("what", "indicator warning", str), ("new", "new?", lambda b: "new" if b else ""),
            ("n_warned", "warned", str), ("fail_if_warned", "fail if warned", _pct), ("fail_if_not", "fail if not", _pct),
            ("diff", "extra fail", _pp), ("diff_half1", "half 1", _pp), ("diff_half2", "half 2", _pp),
            ("q", "q", lambda x: f"{x:.3f}"), ("column", "id", lambda c: "**picked**" if c in picked else "overlaps")]), ""]
        L += [f"**Picked** = kept after removing overlaps (phi correlation >= {MAX_OVERLAP} with a stronger one): "
              f"{', '.join(picked)}.", "",
              f"Together the picked indicators flag **{caught:.0%} of research failures**, but also **{wins_lost:.0%} "
              "of research wins** (the price of filtering).", ""]

    L += ["## 2. Reverse signals: a 'warning' that came before BETTER trades", ""]
    if inverse.empty:
        L += ["None.", ""]
    else:
        L += [_table(label[label["verdict"].str.startswith("INVERSE")].sort_values("z"), [
            ("timeframe", "TF", str), ("what", "indicator state", str), ("n_warned", "trades", str),
            ("fail_if_warned", "fail if present", _pct), ("fail_if_not", "fail if not", _pct),
            ("diff_half1", "half 1", _pp), ("diff_half2", "half 2", _pp), ("q", "q", lambda x: f"{x:.3f}")]),
              "", "Trades did better when these were present. Directional ones (e.g. weekly Supertrend against the trade) "
              "point to mean reversion: buying weakness / selling strength. Direction-free ones (e.g. ADX < 20) describe "
              "market conditions where these signals work better: quiet, non-trending markets.", ""]

    L += ["## 3. If we had used them: win rate", "",
          "Research = where the indicators were chosen (optimistic). **Holdout = never used for choosing: the honest number.**", "",
          _table(vt, [("variant", "rule", str),
                      ("r_trades", "research trades", lambda x: str(int(x))), ("r_win", "win", _pct),
                      ("r_fail", "fail", _pct), ("r_avg_r", "avg R", _r), ("r_margin_5x", "margin/trade @5x", _m),
                      ("h_trades", "holdout trades", lambda x: str(int(x))), ("h_win", "win", _pct),
                      ("h_fail", "fail", _pct), ("h_avg_r", "avg R", _r), ("h_margin_5x", "margin/trade @5x", _m)]),
          "", "Note: the holdout has only ~120 trades, so a few percentage points either way is within luck.", ""]

    near = label[label["verdict"].str.startswith("weak (")].sort_values("z", ascending=False).head(15)
    L += ["## 4. Consistent but not significant (watch list)", "",
          "Pointed the right way in both halves but didn't clear the bar. More data (4h trades, forward shadow) may confirm them.", "",
          _table(near, [("timeframe", "TF", str), ("what", "indicator warning", str), ("new", "new?", lambda b: "new" if b else ""),
                        ("n_warned", "warned", str), ("diff", "extra fail", _pp), ("diff_half1", "half 1", _pp),
                        ("diff_half2", "half 2", _pp), ("q", "q", lambda x: "-" if pd.isna(x) else f"{x:.2f}")]),
          "", f"Everything (all {len(cols)} hints with all numbers): `indicator_hints.csv`.",
          "",
          "## Indicator settings",
          "",
          "ADX/DI 14 (Wilder) · Stochastic 14,3 (80/20) · CCI 20 (+/-100) · Williams %R 14 (-20/-80) · MFI 14 (80/20) · "
          "OBV vs EMA20 · CMF 20 · rolling VWAP 20 · Supertrend 10,3 · Parabolic SAR 0.02/0.2 · Keltner EMA20 +/- 2xATR10 · "
          "Donchian 20 · ATR14 vs ATR50 · volume climax 3x 20-avg · engulfing / shooting star / hammer · ROC 10 · "
          "funding avg of 3 >= 0.03% or < 0 · BTC EMA50 daily + weekly trend · ETH/BTC vs EMA50 · swing levels "
          "(daily K=5, 120d; weekly K=3, 2y) · SMA200 x1.4 / x0.7 · weekend.",
          ]
    path = out_dir / "indicator_analysis.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
