"""
Two-layer model.

Candidates = every main-rule event on 2h / 4h / 1D (zone bounce / break, trendline bounce / break, liquidity sweep / run,
BOS, CHoCH, range break) + 1D level-test bounces (any test count). Outcome = trade at 2:1 (entry next open, the
concept's stop), win = profit after costs.

LAYER 1 - main rules only (bot/ml/context.py + which concept, timeframe, concept confluence, level test count):
          learns WHICH main-rule trade to take WHEN. Picks trades; nothing else can add one.
LAYER 2 - indicators (~290 multi-timeframe hint states, event-candle features, BTC trend, order flow / volume profile):
          sees only trades layer 1 picked; can VETO them (never add, never flip direction).
Walk-forward: each test year 2022-2025 uses models trained on trades that ended before it (62-day gap); cut-offs
chosen on out-of-fold predictions inside the training data. Holdout (Nov 2025 on) = models trained on all research.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..study.concepts import Bars
from ..study.flow import flow_features, load_flow
from ..study.indicators import ema
from ..study.level_tests import tests_for
from ..study.mtf import hints_at, resample
from ..study.mtf2 import tf_hints2
from ..study.sr2_run import _pct, _r, _table
from .context import build_context

COST = 0.0018
HOLDOUT = pd.Timestamp("2025-11-01")
YEARS = [2022, 2023, 2024, 2025]
GAP = pd.Timedelta(days=62)
EVENTS = ["zone_bounce", "zone_break", "tl_bounce", "tl_break", "liq_sweep", "liq_run", "bos", "choch",
          "range_break", "level_test_bounce"]
NAMES = {"zone_bounce": "S/R zone bounce", "zone_break": "S/R zone breakout", "tl_bounce": "trendline bounce",
         "tl_break": "trendline break", "liq_sweep": "liquidity sweep reversal", "liq_run": "liquidity run",
         "bos": "break of structure", "choch": "change of character", "range_break": "range break",
         "level_test_bounce": "1D level-test bounce"}


def load_candidates(df5u: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for tf in ("2h", "4h", "1D"):
        e = pd.read_pickle(ROOT / "results" / f"concept_events_{tf}.pkl")
        e["tf"] = tf
        parts.append(e)
    ce = pd.concat(parts, ignore_index=True)
    ce["decision_time"] = pd.to_datetime(ce["decision_time"], utc=True).dt.tz_convert(None)
    lt = tests_for(df5u, "1D")
    lt = lt[lt.get("traded", pd.Series(False, index=lt.index)).fillna(False).astype(bool)].copy()
    lt["event"], lt["tf"] = "level_test_bounce", "1D"
    lt["decision_time"] = (pd.to_datetime(lt["time"], utc=True) + pd.Timedelta(days=1)).dt.tz_convert(None)
    lt["out_2"] = np.where(lt["r_2"] >= 2 - 1e-9, "win", np.where(lt["r_2"] <= -1 + 1e-9, "loss", "timeout"))
    bars = Bars(resample(df5u, "1D"))
    fe = pd.DataFrame([bars.features(int(j) + 1, int(d)) for j, d in zip(lt["j"], lt["direction"])], index=lt.index)
    lt = pd.concat([lt.drop(columns=[c for c in fe.columns if c in lt]), fe], axis=1)
    hh = pd.DataFrame({"entry_time": pd.to_datetime(lt["decision_time"]).dt.tz_localize("UTC"), "direction": lt["direction"]},
                      index=lt.index)
    h1 = hints_at(df5u, hh).drop(columns=["entry_time", "direction"])
    h2 = tf_hints2(df5u, hh)
    m = pd.concat([h1, h2], axis=1)
    m.columns = [f"m_{c}" for c in m.columns]
    lt = pd.concat([lt, m], axis=1)
    keep = sorted(set(ce.columns) & set(lt.columns) | {"test_n", "prev_failed_breaks"})
    cand = pd.concat([ce, lt[[c for c in keep if c in lt.columns]]], ignore_index=True)
    cand = cand[cand["out_2"].isin(["win", "loss", "timeout"]) & (cand["risk"] > 0)].reset_index(drop=True)
    cand["net"] = cand["r_2"] - COST * cand["entry"] / cand["risk"]
    cand["win"] = (cand["net"] > 0).astype(int)
    cand["hold"] = cand["decision_time"] >= HOLDOUT
    return cand


def add_layer2_extras(cand: pd.DataFrame, cfg: Config, df5u: pd.DataFrame) -> pd.DataFrame:
    btc5, _ = load_klines_5m(cfg.data_dir, cfg.btc_symbol)
    b4 = resample(btc5, "4h")
    b4["side"] = np.sign(b4["close"] - ema(b4["close"], 20))
    b4["close_time"] = pd.to_datetime(b4["close_time"], utc=True).dt.tz_convert(None).dt.as_unit("ns")
    t = cand[["decision_time"]].assign(_r=np.arange(len(cand)), _t=cand["decision_time"].dt.as_unit("ns")).sort_values("_t")
    m = pd.merge_asof(t, b4[["close_time", "side"]], left_on="_t", right_on="close_time", direction="backward").sort_values("_r")
    cand["n_btc_4h"] = m["side"].to_numpy() * cand["direction"].to_numpy()
    fl = load_flow(cfg.data_dir, cfg.symbol)
    x = cand.assign(entry_time=cand["decision_time"], atr_ref=cand["atr"])
    ff = flow_features(x, fl)
    return pd.concat([cand, ff], axis=1)


def layer1_cols(df):
    ctx = [c for c in df.columns if c.startswith(("st_", "brk_", "pat_", "ev_", "zone_", "liq_", "pool_")) or
           c in ("at_zone", "wtrend", "vol_regime", "test_n", "prev_failed_breaks", "tl_touches")]
    conc = [c for c in df.columns if c.startswith("c_")]
    return ctx + conc + [f"is_{e}" for e in EVENTS] + ["is_2h", "is_4h", "is_1D", "is_long"]


def layer2_cols(df):
    return [c for c in df.columns if c.startswith(("m_", "f_", "n_"))]


PARAMS = dict(objective="binary", learning_rate=0.03, num_leaves=15, min_data_in_leaf=80, feature_fraction=0.7,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, seed=11)


def fit(X, y, rounds=250):
    import lightgbm as lgb
    return lgb.train(PARAMS, lgb.Dataset(X, y), num_boost_round=rounds)


def oof(X, y, times, n_parts=4):
    """Expanding time-ordered out-of-fold predictions (first part has none)."""
    order = np.argsort(times.to_numpy())
    parts = np.array_split(order, n_parts)
    p = np.full(len(X), np.nan)
    for i in range(1, n_parts):
        tr = np.concatenate(parts[:i])
        m = fit(X.iloc[tr], y.iloc[tr])
        p[parts[i]] = m.predict(X.iloc[parts[i]])
    return p


def pick_cut(p, net, shares=(0.1, 0.2, 0.3, 0.4, 0.5)):
    """Choose the share of top-scored trades with the best average result (min 40 trades)."""
    ok = ~np.isnan(p)
    best, best_thr = -np.inf, None
    for s in shares:
        thr = np.quantile(p[ok], 1 - s)
        sel = ok & (p >= thr)
        if sel.sum() < 40:
            continue
        v = net[sel].mean()
        if v > best:
            best, best_thr = v, thr
    return best_thr


def run_period(train, test, c1, c2):
    y = train["win"]
    m1 = fit(train[c1], y)
    p1_oof = oof(train[c1], y, train["decision_time"])
    thr1 = pick_cut(p1_oof, train["net"].to_numpy())
    sel_tr = train[(p1_oof >= thr1) & ~np.isnan(p1_oof)]
    X2 = sel_tr[c2].assign(p1=p1_oof[(p1_oof >= thr1) & ~np.isnan(p1_oof)])
    m2 = fit(X2, sel_tr["win"], rounds=200) if len(sel_tr) >= 150 else None
    thr2 = None
    if m2 is not None:
        p2_oof = oof(X2, sel_tr["win"], sel_tr["decision_time"], n_parts=3)
        thr2 = pick_cut(p2_oof, sel_tr["net"].to_numpy(), shares=(0.5, 0.6, 0.7, 0.8, 0.9, 1.0))
    p1 = m1.predict(test[c1])
    pick1 = p1 >= thr1
    out = test.assign(p1=p1, layer1=pick1, layer2=pick1)
    if m2 is not None and thr2 is not None and pick1.any():
        p2 = m2.predict(test.loc[pick1, c2].assign(p1=p1[pick1]))
        keep = np.zeros(len(test), bool)
        keep[np.flatnonzero(pick1)] = p2 >= thr2
        out["layer2"] = keep
    return out, m1


def stats(g):
    return {"n": len(g), "win": g["win"].mean() if len(g) else math.nan, "avg": g["net"].mean() if len(g) else math.nan}


def run_two_layer(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    cand = load_candidates(df5u)
    cand = cand[cand["decision_time"] >= pd.Timestamp("2020-06-01")].reset_index(drop=True)
    print(f"candidates: {len(cand)}")
    allev = cand[["decision_time", "tf", "event", "direction"]]
    ctx = build_context(cand, df5u, allev)
    cand = pd.concat([cand, ctx], axis=1)
    for e in EVENTS:
        cand[f"is_{e}"] = (cand["event"] == e).astype(int)
    for tf in ("2h", "4h", "1D"):
        cand[f"is_{tf}"] = (cand["tf"] == tf).astype(int)
    cand["is_long"] = (cand["direction"] > 0).astype(int)
    cand = add_layer2_extras(cand, cfg, df5u)
    cand.to_pickle(ROOT / "results" / "two_layer_candidates.pkl")
    c1, c2 = layer1_cols(cand), layer2_cols(cand)
    res = cand[~cand["hold"]]
    scored = []
    for yr in YEARS:
        start = pd.Timestamp(f"{yr}-01-01")
        train = res[res["decision_time"] < start - GAP]
        test = res[(res["decision_time"] >= start) & (res["decision_time"] < pd.Timestamp(f"{yr + 1}-01-01"))]
        if len(train) < 1000 or test.empty:
            continue
        o, _ = run_period(train, test, c1, c2)
        scored.append(o.assign(period=str(yr)))
    o, m1_final = run_period(res[res["decision_time"] < HOLDOUT - GAP], cand[cand["hold"]], c1, c2)
    scored.append(o.assign(period="holdout"))
    S = pd.concat(scored, ignore_index=True)
    S.to_pickle(ROOT / "results" / "two_layer_scored.pkl")

    L = ["# Two-layer model: main rules decide the trade, indicators can only veto", "",
         f"{len(cand):,} candidate trades from the main rules on 2h / 4h / 1D (all setups allowed), each a 2:1 trade "
         f"with the concept's own stop. win % = profit after costs. Every number below is out-of-sample.", "",
         f"- **Layer 1** ({len(c1)} main-rule inputs: structure on 1h-1W, patterns on 4h/1D/1W, events on other "
         "timeframes, zones, liquidity, weekly trend, volatility regime, which concept) picks the trades.",
         f"- **Layer 2** ({len(c2)} indicator inputs) reviews only those and can veto.", ""]
    rows = []
    for per, g in S.groupby("period"):
        a, b, c = stats(g), stats(g[g["layer1"]]), stats(g[g["layer2"]])
        rows.append({"period": per, "n_all": a["n"], "w_all": a["win"], "a_all": a["avg"],
                     "n1": b["n"], "w1": b["win"], "a1": b["avg"], "n2": c["n"], "w2": c["win"], "a2": c["avg"]})
    for per, gs in (("2022-25 total", S[S["period"] != "holdout"]),):
        a, b, c = stats(gs), stats(gs[gs["layer1"]]), stats(gs[gs["layer2"]])
        rows.append({"period": per, "n_all": a["n"], "w_all": a["win"], "a_all": a["avg"],
                     "n1": b["n"], "w1": b["win"], "a1": b["avg"], "n2": c["n"], "w2": c["win"], "a2": c["avg"]})
    T = pd.DataFrame(rows)
    L += ["## Win % at 2:1", "",
          _table(T, [("period", "period", str), ("n_all", "all candidates", str), ("w_all", "win % all", _pct),
                     ("n1", "layer 1 picks", str), ("w1", "win % layer 1", _pct), ("a1", "avg R layer 1", _r),
                     ("n2", "after layer 2", str), ("w2", "win % layer 1+2", _pct), ("a2", "avg R layer 1+2", _r)]), ""]
    # what layer 1 takes when: per concept
    rows = []
    for e, g in S.groupby("event"):
        rows.append({"event": NAMES.get(e, e), "n": len(g), "w_all": g["win"].mean(), "picked": g["layer1"].mean(),
                     "w1": g.loc[g["layer1"], "win"].mean() if g["layer1"].any() else math.nan,
                     "w2": g.loc[g["layer2"], "win"].mean() if g["layer2"].any() else math.nan,
                     "h_w2": g.loc[g["layer2"] & (g["period"] == "holdout"), "win"].mean()
                     if (g["layer2"] & (g["period"] == "holdout")).any() else math.nan})
    L += ["## Which main-rule trades layer 1 takes (all out-of-sample periods)", "",
          _table(pd.DataFrame(rows).sort_values("w2", ascending=False),
                 [("event", "main-rule setup", str), ("n", "candidates", str), ("w_all", "win % if taken always", _pct),
                  ("picked", "share layer 1 takes", _pct), ("w1", "win % when layer 1 takes it", _pct),
                  ("w2", "win % after layer 2", _pct), ("h_w2", "holdout win % after layer 2", _pct)]), ""]
    # importance + surrogate rules
    imp = pd.DataFrame({"feature": c1, "gain": m1_final.feature_importance("gain")}).sort_values("gain", ascending=False)
    imp["share"] = imp["gain"] / imp["gain"].sum()
    L += ["## What layer 1 looks at most (final model)", "",
          _table(imp.head(20), [("feature", "main-rule input", str), ("share", "share of importance", _pct)]), ""]
    from sklearn.tree import DecisionTreeClassifier, export_text
    r = S[S["period"] != "holdout"]
    tree = DecisionTreeClassifier(max_depth=4, min_samples_leaf=150, random_state=0)
    Xs = r[c1].fillna(-99)
    tree.fit(Xs, r["layer1"].astype(int))
    L += ["## Layer 1 in plain rules (a 4-level decision tree that imitates its picks)", "",
          "```", export_text(tree, feature_names=list(c1), decimals=2), "```", ""]
    path = out_dir / "two_layer.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
