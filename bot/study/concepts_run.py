"""Concept study runner: win rates per concept, structure / confluence effects, and which indicators help which concept."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .concepts import add_confluence, detect_events
from .indicator_search import bh_qvalues, two_prop_z
from .mtf import resample
from .sr2 import MAX_BARS, add_mtf_features
from .sr2_run import WIN_COLS, _pct, _r, _table, winrates

HOLDOUT = pd.Timestamp("2025-11-01", tz="UTC")
SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
NAMES = {
    "zone_bounce": "S/R zone bounce (confirmed)", "zone_break": "S/R zone breakout",
    "tl_bounce": "trendline bounce (confirmed)", "tl_break": "trendline break",
    "liq_sweep": "liquidity sweep (stop hunt) reversal", "liq_run": "liquidity run (break of equal highs/lows)",
    "bos": "break of structure (continuation)", "choch": "change of character (first reversal break)",
    "range_break": "break of a swing in a range",
}
FEATURE_TEXT = {
    "f_vol": "touch/decision candle volume", "f_vol_prev": "previous candle volume", "f_vol_approach": "volume into the event",
    "f_vol_slope": "volume trend (10 candles)", "f_vol_div": "volume divergence", "f_rsi": "RSI in trade direction",
    "f_rsi_div": "RSI divergence", "f_adx": "ADX", "f_di": "DI spread in trade direction", "f_bb_pos": "Bollinger position",
    "f_d_e20": "distance from EMA20", "f_d_e50": "distance from EMA50", "f_d_e200": "distance from EMA200",
    "f_macd": "MACD histogram in trade direction", "f_macd_turn": "MACD turning our way", "f_body": "candle body our way",
    "f_range": "candle range (ATR)", "f_close_pos": "close position in candle", "f_ret_5": "5-candle return our way",
    "f_ret_20": "20-candle return our way", "f_atr_pct": "volatility (ATR %)", "f_bvol": "bounce candle volume",
    "structure_with": "structure agrees with trade", "tl_touches": "trendline touches", "tl_age": "trendline age",
    "c_count": "number of other concepts agreeing",
}


def _desc(col: str) -> str:
    if col in FEATURE_TEXT:
        return FEATURE_TEXT[col]
    if col.startswith("c_"):
        return f"confluence: {NAMES.get(col[2:], col[2:])} in last 3 candles"
    if col.startswith("m_"):
        tf, _, h = col[2:].partition("_")
        return f"{tf} {h.replace('_', ' ')} (+ = supports)"
    return col


def split(ev: pd.DataFrame, bar: pd.Timedelta):
    t = pd.to_datetime(ev["decision_time"], utc=True)
    return ev[t < HOLDOUT - bar * (MAX_BARS + 2)], ev[t >= HOLDOUT]


def feature_list(ev: pd.DataFrame) -> list[str]:
    skip = {"j", "direction", "atr", "entry", "risk", "ref_level", "structure"}
    return [c for c in ev.columns if (c.startswith(("f_", "m_", "c_")) or c in ("structure_with", "tl_touches", "tl_age"))
            and c not in skip]


def indicator_matrix(res: pd.DataFrame, hold: pd.DataFrame) -> pd.DataFrame:
    """Per event type x feature: win @1R when the feature is 'high' (above median, or > 0 for -1/0/1 states) vs not."""
    rows = []
    for e_name, g in res.groupby("event"):
        g = g[g["out_1"].isin(["win", "loss", "timeout"])]
        gh = hold[(hold["event"] == e_name) & hold["out_1"].isin(["win", "loss", "timeout"])]
        if len(g) < 150:
            continue
        y = g["out_1"] == "win"
        h1 = pd.to_datetime(g["decision_time"], utc=True) < SPLIT
        for col in feature_list(g):
            x = g[col]
            if x.notna().sum() < 100 or x.nunique() < 2:
                continue
            discrete = x.nunique() <= 5
            thr = 0 if discrete else x.median()
            hi = x > thr
            n1, n2 = int(hi.sum()), int((~hi).sum())
            if n1 < 30 or n2 < 30:
                continue
            k1, k2 = int(y[hi].sum()), int(y[~hi].sum())
            z, p = two_prop_z(k1, n1, k2, n2)
            hh = gh[col] > thr if len(gh) else pd.Series(dtype=bool)
            yh = gh["out_1"] == "win" if len(gh) else pd.Series(dtype=bool)
            rows.append({
                "event": e_name, "feature": col, "rule": "> 0" if discrete else f"> {thr:.3g} (median)",
                "n_high": n1, "win_high": k1 / n1, "win_low": k2 / n2, "diff": k1 / n1 - k2 / n2, "z": z, "p": p,
                "half1": y[hi & h1].mean() - y[~hi & h1].mean(), "half2": y[hi & ~h1].mean() - y[~hi & ~h1].mean(),
                "hold_n_high": int(hh.sum()) if len(gh) else 0,
                "hold_win_high": yh[hh].mean() if len(gh) and hh.any() else math.nan,
                "hold_win_low": yh[~hh].mean() if len(gh) and (~hh).any() else math.nan,
            })
    t = pd.DataFrame(rows)
    if t.empty:
        return t
    t["q"] = np.nan
    for e_name, idx in t.groupby("event").groups.items():
        t.loc[idx, "q"] = bh_qvalues(t.loc[idx, "p"].to_numpy())
    same = (np.sign(t["half1"]) == np.sign(t["diff"])) & (np.sign(t["half2"]) == np.sign(t["diff"]))
    t["verdict"] = np.where((t["q"] < 0.10) & same, np.where(t["diff"] > 0, "HELPS", "HURTS"),
                            np.where(same, "consistent", "noise"))
    t["holdout_agrees"] = np.sign(t["hold_win_high"] - t["hold_win_low"]) == np.sign(t["diff"])
    return t


def run_concepts(cfg: Config, out_dir: Path, timeframes=("4h", "1D")) -> Path:
    df5, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    cache = ROOT / "results"
    cache.mkdir(exist_ok=True)
    all_res, all_hold = [], []
    L = ["# Price-action concepts: structure, trendlines, liquidity, S/R zones - and which indicators help each", "",
         "Each concept is detected from swings that were already confirmed. Each event is a trade (entry next open, "
         "stop per concept, targets 1R / 1.5R / 2R). **Win rates are before costs; avg R is after costs.** "
         "*needed @1R after costs* is the real break-even. Research = before 2025-11-01, holdout = after.", ""]
    for tf in timeframes:
        bar = pd.Timedelta(tf)
        ev = detect_events(df5, tf, resample)
        ev = add_confluence(ev)
        ev = add_mtf_features(ev, df5)
        ev["tf"] = tf
        ev.to_pickle(cache / f"concept_events_{tf}.pkl")
        res, hold = split(ev, bar)
        all_res.append(res)
        all_hold.append(hold)
        L += [f"## {tf} chart", "", "### Win rate per concept", ""]
        rows = []
        for e_name in NAMES:
            r_, h_ = res[res["event"] == e_name], hold[hold["event"] == e_name]
            if len(r_) == 0:
                continue
            rows.append({"what": NAMES[e_name], "period": "research", **winrates(r_)})
            rows.append({"what": NAMES[e_name], "period": "holdout", **winrates(h_)})
        L += [_table(pd.DataFrame(rows), [("what", "concept", str), ("period", "period", str), *WIN_COLS]), ""]
        # structure alignment
        rows = []
        for e_name in NAMES:
            for sw, lab in ((1, "with structure"), (0, "range / unclear"), (-1, "against structure")):
                g = res[(res["event"] == e_name) & (res["structure_with"] == sw)]
                if len(g) >= 20:
                    rows.append({"what": NAMES[e_name], "structure": lab, **winrates(g)})
        L += ["### Does chart structure matter? (research)", "",
              _table(pd.DataFrame(rows), [("what", "concept", str), ("structure", "structure", str), *WIN_COLS]), ""]
        # trendline touches
        tl = res[res["event"].isin(["tl_bounce", "tl_break"])].copy()
        if len(tl):
            tl["touch_b"] = tl["tl_touches"].clip(upper=4).map({2: "2 touches", 3: "3 touches", 4: "4+ touches"})
            rows = [{"what": NAMES[e], "touches": k, **winrates(g)} for (e, k), g in tl.groupby(["event", "touch_b"])]
            L += ["### Trendlines: does a line with more touches work better? (research)", "",
                  _table(pd.DataFrame(rows), [("what", "concept", str), ("touches", "line", str), *WIN_COLS]), ""]
        # confluence
        rows = []
        for e_name in NAMES:
            g = res[res["event"] == e_name]
            for cnt, gg in g.groupby(g["c_count"].clip(upper=2)):
                if len(gg) >= 20:
                    rows.append({"what": NAMES[e_name], "conf": {0: "alone", 1: "+1 other concept", 2: "+2 or more"}[cnt],
                                 **winrates(gg)})
        L += ["### Confluence: other concepts agreeing in the last 3 candles (research)", "",
              _table(pd.DataFrame(rows), [("what", "concept", str), ("conf", "confluence", str), *WIN_COLS]), ""]

    res = pd.concat(all_res, ignore_index=True)
    hold = pd.concat(all_hold, ignore_index=True)
    mat = indicator_matrix(res, hold)
    mat.to_csv(out_dir / "concept_indicator_matrix.csv", index=False)
    L += ["## Which indicators help which concept? (4h + 1D pooled, research)", "",
          "For each concept, every indicator/feature is split at its median (or > 0 for with/against states) and the "
          "win rate @1R compared. **HELPS / HURTS** = false-discovery q < 0.10 within that concept AND the same direction "
          "in both research halves. The holdout columns are a later, unseen check.", ""]
    for e_name in NAMES:
        m = mat[(mat["event"] == e_name) & mat["verdict"].isin(["HELPS", "HURTS"])].sort_values("z", ascending=False)
        n_ev = int((res["event"] == e_name).sum())
        if n_ev == 0:
            continue
        L += [f"### {NAMES[e_name]} ({n_ev} research trades)", ""]
        if m.empty:
            L += ["No indicator passed all checks.", ""]
            continue
        m = m.assign(what=m["feature"].map(_desc))
        L += [_table(m.head(15), [("what", "indicator", str), ("rule", "when", str), ("n_high", "trades", str),
                                  ("win_high", "win @1R when true", _pct), ("win_low", "win when not", _pct),
                                  ("verdict", "verdict", str), ("hold_win_high", "holdout: when true", _pct),
                                  ("hold_win_low", "holdout: when not", _pct),
                                  ("holdout_agrees", "holdout agrees", lambda b: "yes" if b else "no")]), ""]
    good = mat[(mat["verdict"] == "HELPS") & mat["holdout_agrees"]]
    if len(good):
        cross = good.groupby("feature")["event"].apply(lambda s: ", ".join(sorted(set(s)))).reset_index()
        cross["n_concepts"] = cross["event"].str.count(",") + 1
        cross = cross.sort_values("n_concepts", ascending=False)
        cross["what"] = cross["feature"].map(_desc)
        L += ["## Indicators that help several concepts (HELPS + holdout agrees)", "",
              _table(cross.head(25), [("what", "indicator", str), ("n_concepts", "concepts", str), ("event", "helps", str)]), ""]
    path = out_dir / "concept_study.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
