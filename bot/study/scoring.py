"""
Combined decision score: main concepts first, technical indicators second -> a certainty from 1 to 10.

Two families (each gets its own model, because different things matter for them):
  reversal : zone_bounce, tl_bounce, liq_sweep, choch
  breakout : zone_break, tl_break, liq_run, bos, range_break

Layer 1 - main concepts (always in the model):
  which concept fired, confluence with each other concept (same direction, last 3 candles), number of
  agreeing concepts, chart structure with/against, weekly & daily trend with/against, timeframe,
  trendline touches.
Layer 2 - indicators chosen per family from the research-period indicator study:
  breakout: momentum & volume in the break direction (MACD, EMA20 distance, Bollinger position, RSI, DI,
            2h/4h volume climax, 2h slope / DI / CMF, 4h rate of change)
  reversal: touch & bounce volume, volume / RSI divergence, EMA200 side, ADX < 20 (quiet market), RSI

Model: L2-regularised logistic regression (transparent: every factor gets a weight). Target: win at 1R.
Certainty = predicted win probability x 10, rounded (7/10 = model expects ~70% wins).
Walk-forward: each test year is scored by a model trained only on earlier years (gap = 62 candles);
the holdout (from 2025-11-01) is scored once by the model trained on all research data.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from .concepts_run import NAMES
from .sr2_run import COST_FRAC, _pct, _r, _table, winrates

HOLDOUT = pd.Timestamp("2025-11-01", tz="UTC")
YEARS = ["2022", "2023", "2024", "2025"]
FAMILIES = {
    "reversal": ["zone_bounce", "tl_bounce", "liq_sweep", "choch"],
    "breakout": ["zone_break", "tl_break", "liq_run", "bos", "range_break"],
}
CONCEPT_COLS = ["c_zone_bounce", "c_tl_bounce", "c_liq_sweep", "c_bos", "c_choch", "c_tl_break", "c_zone_break",
                "c_liq_run", "c_count", "structure_with", "m_1W_trend", "m_1D_trend", "m_1W_supertrend",
                "is_1D", "tl_touches_f"]
INDICATORS = {
    "breakout": ["f_macd", "f_d_e20", "f_bb_pos", "f_rsi", "f_di", "m_2h_climax", "m_4h_climax", "m_2h_slope",
                 "m_2h_di", "m_2h_cmf", "m_4h_roc_against", "f_vol", "f_range"],
    "reversal": ["f_vol", "f_bvol", "f_vol_div", "f_rsi_div", "f_d_e200", "m_1D_adx_weak", "f_rsi", "f_close_pos",
                 "f_vol_approach"],
}
TEXT = {
    "c_count": "number of concepts agreeing", "structure_with": "chart structure with the trade",
    "m_1W_trend": "weekly trend (close vs EMA50) with the trade", "m_1D_trend": "daily trend with the trade",
    "m_1W_supertrend": "weekly Supertrend with the trade", "is_1D": "daily chart (vs 4h)",
    "tl_touches_f": "trendline touches", "f_bvol": "bounce candle volume", "f_vol": "event candle volume",
    "f_vol_div": "volume divergence", "f_rsi_div": "RSI divergence", "f_d_e200": "distance from EMA200 (our side +)",
    "m_1D_adx_weak": "daily ADX < 20 (quiet market)", "f_rsi": "RSI in trade direction",
    "f_close_pos": "candle closed near our end", "f_vol_approach": "volume into the event",
    "f_macd": "MACD histogram our way", "f_d_e20": "distance from EMA20 our way", "f_bb_pos": "Bollinger position our way",
    "f_di": "DI spread our way", "m_2h_climax": "2h volume climax our way", "m_4h_climax": "4h volume climax our way",
    "m_2h_slope": "2h EMA20 slope our way", "m_2h_di": "2h DI our way", "m_2h_cmf": "2h money flow our way",
    "m_4h_roc_against": "4h momentum our way", "f_range": "event candle size",
}


def _text(c):
    if c.startswith("ev_"):
        return f"concept: {NAMES.get(c[3:], c[3:])}"
    if c.startswith("c_") and c != "c_count":
        return f"confluence: {NAMES.get(c[2:], c[2:])}"
    return TEXT.get(c, c)


def load_events() -> pd.DataFrame:
    parts = []
    for tf in ("4h", "1D"):
        e = pd.read_pickle(ROOT / "results" / f"concept_events_{tf}.pkl")
        e["tf"] = tf
        parts.append(e)
    ev = pd.concat(parts, ignore_index=True)
    ev["decision_time"] = pd.to_datetime(ev["decision_time"], utc=True)
    ev["is_1D"] = (ev["tf"] == "1D").astype(int)
    ev["tl_touches_f"] = ev.get("tl_touches", pd.Series(np.nan, index=ev.index)).fillna(0)
    ev["f_bvol"] = ev.get("f_bvol", pd.Series(np.nan, index=ev.index))
    ev["bar"] = ev["tf"].map(pd.Timedelta)
    ev["cost_r"] = COST_FRAC * ev["entry"] / ev["risk"]
    return ev


def design(ev: pd.DataFrame, family: str) -> tuple[pd.DataFrame, list[str]]:
    cols = list(CONCEPT_COLS) + INDICATORS[family]
    X = ev[cols].astype(float).copy()
    for e_name in FAMILIES[family][1:]:              # concept one-hots (first one = reference)
        X[f"ev_{e_name}"] = (ev["event"] == e_name).astype(float)
    return X, list(X.columns)


class Model:
    def __init__(self, family):
        self.family = family

    def fit(self, ev):
        from sklearn.linear_model import LogisticRegression

        X, self.cols = design(ev, self.family)
        self.med = X.median()
        X = X.fillna(self.med)
        self.mu, self.sd = X.mean(), X.std().replace(0, 1)
        y = (ev["out_1"] == "win").astype(int)
        self.m = LogisticRegression(C=0.3, max_iter=2000).fit((X - self.mu) / self.sd, y)
        return self

    def predict(self, ev):
        X, _ = design(ev, self.family)
        X = X[self.cols].fillna(self.med)
        return self.m.predict_proba((X - self.mu) / self.sd)[:, 1]

    def weights(self):
        return pd.DataFrame({"factor": self.cols, "weight": self.m.coef_[0]}).sort_values("weight", ascending=False)


def certainty(p: np.ndarray) -> np.ndarray:
    return np.clip(np.round(p * 10), 1, 10).astype(int)


def walk_forward(ev: pd.DataFrame, family: str) -> pd.DataFrame:
    fam = ev[ev["event"].isin(FAMILIES[family]) & ev["out_1"].isin(["win", "loss", "timeout"])]
    research = fam[fam["decision_time"] < HOLDOUT - fam["bar"] * 62]
    scored = []
    for yr in YEARS:
        start, end = pd.Timestamp(f"{yr}-01-01", tz="UTC"), pd.Timestamp(f"{int(yr) + 1}-01-01", tz="UTC")
        train = research[research["decision_time"] < start - research["bar"] * 62]
        test = research[(research["decision_time"] >= start) & (research["decision_time"] < end)]
        if len(train) < 300 or len(test) == 0:
            continue
        m = Model(family).fit(train)
        scored.append(test.assign(p=m.predict(test), period=yr))
    final = Model(family).fit(research)
    hold = fam[fam["decision_time"] >= HOLDOUT]
    if len(hold):
        scored.append(hold.assign(p=final.predict(hold), period="holdout"))
    out = pd.concat(scored) if scored else pd.DataFrame()
    out["certainty"] = certainty(out["p"].to_numpy()) if len(out) else []
    out.attrs["weights"] = final.weights()
    return out


def loss_reasons(t: pd.DataFrame) -> dict:
    lost = t[t["out_1"] == "loss"]
    if not len(lost):
        return {}
    return {"n": len(lost),
            "fast": (lost["bars_1"] <= 2).mean(),
            "right_first": (lost["mfe_1"] >= 0.5).mean(),
            "gap": (lost["r_1"] < -1.05).mean()}


def compare_losses(t: pd.DataFrame, family: str) -> pd.DataFrame:
    """Among high-certainty trades: how do losers differ from winners on every input?"""
    X, cols = design(t, family)
    y = t["out_1"] == "win"
    rows = []
    for c in cols:
        x = X[c]
        if x.notna().sum() < 20 or x.nunique() < 2:
            continue
        rows.append({"factor": c, "winners": x[y].mean(), "losers": x[~y].mean(),
                     "gap_sd": (x[y].mean() - x[~y].mean()) / (x.std() or 1)})
    return pd.DataFrame(rows).sort_values("gap_sd", key=abs, ascending=False)


def run_scoring(cfg: Config, out_dir: Path) -> Path:
    ev = load_events()
    L = ["# Combined score: main concepts + indicators -> certainty 1-10", "",
         "Every trade gets a **certainty from 1 to 10** = the model's expected win probability at a 1R target x 10. "
         "The model weighs the main concepts first (which concept, confluence, structure, weekly/daily trend) and then "
         "the indicators that helped that kind of trade. **Every number below is out-of-sample:** each year (2022-2025) "
         "is scored by a model trained only on earlier years, and the holdout (from 2025-11-01) by the model trained on "
         "all research data. Win rates are before costs; avg R is after costs. At 1R the after-cost break-even is "
         "about 52% on 1D and 55% on 4h.", ""]
    for family in ("reversal", "breakout"):
        s = walk_forward(ev, family)
        if s.empty:
            continue
        s.to_pickle(ROOT / "results" / f"scored_{family}.pkl")
        L += [f"## {family.capitalize()} trades ({', '.join(NAMES[e] for e in FAMILIES[family])})", ""]
        # calibration: certainty vs actual win rate
        res = s[s["period"] != "holdout"]
        hold = s[s["period"] == "holdout"]
        rows = []
        for cert in range(1, 11):
            a, b = res[res["certainty"] == cert], hold[hold["certainty"] == cert]
            if len(a) + len(b) == 0:
                continue
            rows.append({"cert": f"{cert}/10", "a_n": len(a), "a_win": (a["out_1"] == "win").mean() if len(a) else math.nan,
                         "b_n": len(b), "b_win": (b["out_1"] == "win").mean() if len(b) else math.nan})
        L += ["### Is the certainty honest? (predicted vs actual)", "",
              "A 6/10 trade should win about 60% of the time.", "",
              _table(pd.DataFrame(rows), [("cert", "certainty", str), ("a_n", "trades 2022-25", str),
                                          ("a_win", "actual win @1R 2022-25", _pct), ("b_n", "holdout trades", str),
                                          ("b_win", "actual win @1R holdout", _pct)]), ""]
        # trade only above a certainty
        rows = []
        for cmin in (1, 5, 6, 7):
            for per, g in (("2022-25", res), ("holdout", hold)):
                gg = g[g["certainty"] >= cmin]
                weeks = max((gg["decision_time"].max() - gg["decision_time"].min()).days / 7, 1) if len(gg) > 1 else math.nan
                rows.append({"rule": "all trades" if cmin == 1 else f"certainty >= {cmin}", "period": per,
                             **winrates(gg), "per_week": len(gg) / weeks if weeks == weeks else math.nan})
        L += ["### Taking only confident trades", "",
              _table(pd.DataFrame(rows), [("rule", "rule", str), ("period", "period", str), ("n", "trades", str),
                                          ("per_week", "trades/week", lambda x: "-" if pd.isna(x) else f"{x:.1f}"),
                                          ("win_1", "win @1R", _pct), ("win_1.5", "win @1.5R", _pct),
                                          ("win_2", "win @2R", _pct), ("r_1", "avg R @1R after costs", _r),
                                          ("r_2", "avg R @2R after costs", _r)]), ""]
        # per year at certainty >= 6
        rows = [{"period": per, **winrates(g[g["certainty"] >= 6])} for per, g in s.groupby("period")]
        L += ["### Certainty >= 6, year by year", "",
              _table(pd.DataFrame(rows), [("period", "year", str), ("n", "trades", str), ("win_1", "win @1R", _pct),
                                          ("win_2", "win @2R", _pct), ("r_1", "avg R @1R after costs", _r)]), ""]
        # weights
        w = s.attrs["weights"].copy()
        w["factor"] = w["factor"].map(_text)
        L += ["### What the score is made of (weights of the final model; + raises certainty, - lowers it)", "",
              _table(w, [("factor", "factor", str), ("weight", "weight", lambda x: f"{x:+.2f}")]), ""]
        # losses that remain
        conf = res[res["certainty"] >= 6]
        lr = loss_reasons(conf)
        if lr:
            L += ["### Why do confident trades still lose? (certainty >= 6, 2022-25)", "",
                  f"- {lr['n']} losses. **{lr['fast']:.0%} failed within 2 candles**; **{lr['right_first']:.0%} went at "
                  f"least +0.5R our way first**; {lr['gap']:.0%} gapped through the stop.", ""]
            cl = compare_losses(conf, family).head(8)
            cl["factor"] = cl["factor"].map(_text)
            L += ["Biggest differences between winners and losers among these trades (gap in standard deviations):", "",
                  _table(cl, [("factor", "factor", str), ("winners", "avg for winners", lambda x: f"{x:.2f}"),
                              ("losers", "avg for losers", lambda x: f"{x:.2f}"),
                              ("gap_sd", "gap", lambda x: f"{x:+.2f}")]), ""]
    path = out_dir / "scoring.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
