"""Runner + report for the S/R v2 study (see sr2.py)."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .indicator_search import bh_qvalues, two_prop_z
from .mtf import resample
from .sr2 import MAX_BARS, RRS, add_mtf_features, build_events

HOLDOUT = "2025-11-01"
SPLIT_DAY = "2023-01-01"
TEST_YEARS = ["2022", "2023", "2024", "2025"]
EVENT_NAMES = {"reversal_now": "Reversal, enter right after the touch",
               "reversal_bounce": "Reversal, wait for the bounce candle",
               "breakout": "Breakout, trade the break"}


def _pct(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.0%}"


def _r(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.2f}"


def _table(df, cols):
    head = "| " + " | ".join(c[1] for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = ["| " + " | ".join(f(r[c]) for c, _, f in cols) + " |" for _, r in df.iterrows()]
    return "\n".join([head, sep, *body])


COST_FRAC = 0.0018  # round-trip taker fee 0.04% x2 + slippage 5 bps x2, as a fraction of price


def winrates(x: pd.DataFrame) -> dict:
    """Win rates (before costs) + average R AFTER fees/slippage + the after-cost break-even win rate at 1R."""
    out = {"n": len(x)}
    cost_r = COST_FRAC * x["entry"] / x["risk"] if len(x) else pd.Series(dtype=float)
    for rr in RRS:
        col = f"out_{rr:g}"
        ok = x[col].isin(["win", "loss", "timeout"])
        done = x[ok]
        out[f"win_{rr:g}"] = (done[col] == "win").mean() if len(done) else math.nan
        out[f"r_{rr:g}"] = (done[f"r_{rr:g}"] - cost_r[ok]).mean() if len(done) else math.nan
    c = cost_r.median() if len(x) else math.nan
    out["cost_r"] = c
    out["be_1"] = (1 + c) / 2 if not pd.isna(c) else math.nan  # win rate needed at 1R after costs
    return out


WIN_COLS = [("n", "trades", str), ("win_1", "win @1R", _pct), ("be_1", "needed @1R after costs", _pct),
            ("win_1.5", "win @1.5R (b/e 40%+)", _pct), ("win_2", "win @2R (b/e 33%+)", _pct),
            ("r_1", "avg R @1R after costs", _r), ("r_2", "avg R @2R after costs", _r)]


def split(ev: pd.DataFrame, bar: pd.Timedelta):
    cut = (pd.Timestamp(HOLDOUT, tz="UTC") - bar * (MAX_BARS + 2))
    t = pd.to_datetime(ev["decision_time"], utc=True)
    return ev[t < cut], ev[t >= pd.Timestamp(HOLDOUT, tz="UTC")]


def feature_cols(ev: pd.DataFrame) -> list[str]:
    return [c for c in ev.columns if c.startswith("f_") or c.startswith("m_")] + ["touch_n", "bars_since_touch",
                                                                                  "atr_pct"]


def walk_forward(ev: pd.DataFrame, res: pd.DataFrame, hold: pd.DataFrame, bar: pd.Timedelta, top: float = 0.2):
    """LightGBM on target 'win at 1R'. Threshold = top `top` share of out-of-fold predictions on the TRAINING
    data (3-fold time-ordered CV inside train), so no test labels or test predictions are used to choose it."""
    import lightgbm as lgb

    cols = feature_cols(ev)
    params = dict(objective="binary", learning_rate=0.03, num_leaves=15, min_data_in_leaf=50,
                  feature_fraction=0.5, bagging_fraction=0.8, bagging_freq=1, lambda_l2=5.0, verbose=-1, seed=7)

    def fit(train):
        y = (train["out_1"] == "win").astype(int)
        return lgb.train(params, lgb.Dataset(train[cols], y), num_boost_round=200)

    def oof_threshold(train):
        tt = pd.to_datetime(train["decision_time"], utc=True)
        order = np.argsort(tt.to_numpy())
        parts = np.array_split(order, 4)
        preds = []
        for i in range(1, 4):  # expanding: fit on parts[:i], predict parts[i]
            tr_idx = np.concatenate(parts[:i])
            m = fit(train.iloc[tr_idx])
            preds.append(m.predict(train.iloc[parts[i]][cols]))
        return float(np.quantile(np.concatenate(preds), 1 - top))

    done = res[res["out_1"].isin(["win", "loss", "timeout"])]
    tt = pd.to_datetime(done["decision_time"], utc=True)
    folds = []
    sel_all = []
    for yr in TEST_YEARS:
        start = pd.Timestamp(f"{yr}-01-01", tz="UTC")
        end = pd.Timestamp(f"{int(yr) + 1}-01-01", tz="UTC")
        train = done[tt < start - bar * (MAX_BARS + 2)]  # purge: training trades end before the test year
        test = done[(tt >= start) & (tt < end)]
        if len(train) < 500 or len(test) < 50:
            continue
        thr = oof_threshold(train)
        m = fit(train)
        p = m.predict(test[cols])
        sel = test[p >= thr]
        folds.append({"year": yr, "train": len(train), "test": len(test), "picked": len(sel),
                      **{f"all_{k}": v for k, v in winrates(test).items()},
                      **{f"sel_{k}": v for k, v in winrates(sel).items()}})
        sel_all.append(sel)
    # final model on all research, applied once to the holdout
    hold_done = hold[hold["out_1"].isin(["win", "loss", "timeout"])]
    hold_res = {}
    imp = pd.DataFrame()
    if len(done) >= 500:
        thr = oof_threshold(done)
        m = fit(done)
        if len(hold_done):
            p = m.predict(hold_done[cols])
            hsel = hold_done[p >= thr]
            hold_res = {"all": winrates(hold_done), "sel": winrates(hsel)}
        imp = pd.DataFrame({"feature": cols, "gain": m.feature_importance("gain")}).sort_values("gain", ascending=False)
    oos = pd.concat(sel_all) if sel_all else pd.DataFrame(columns=done.columns)
    return pd.DataFrame(folds), oos, hold_res, imp


def why_breaks(res_b: pd.DataFrame) -> pd.DataFrame:
    """Which features differ between breakouts that worked (win @1R) and failed. Median-split each feature."""
    rows = []
    y = (res_b["out_1"] == "win")
    h1 = pd.to_datetime(res_b["decision_time"], utc=True) < pd.Timestamp(SPLIT_DAY, tz="UTC")
    for col in feature_cols(res_b):
        x = res_b[col]
        if x.nunique() < 2:
            continue
        thr = x.median()
        hi = x > thr if x.nunique() > 3 else x > 0
        if hi.sum() < 30 or (~hi).sum() < 30:
            continue
        k1, n1, k2, n2 = int(y[hi].sum()), int(hi.sum()), int(y[~hi].sum()), int((~hi).sum())
        z, p = two_prop_z(k1, n1, k2, n2)
        d1 = y[hi & h1].mean() - y[~hi & h1].mean()
        d2 = y[hi & ~h1].mean() - y[~hi & ~h1].mean()
        rows.append({"feature": col, "split": "> median" if x.nunique() > 3 else "> 0 (supports)",
                     "win_high": k1 / n1, "win_low": k2 / n2, "diff": k1 / n1 - k2 / n2, "z": z, "p": p,
                     "half1": d1, "half2": d2})
    t = pd.DataFrame(rows)
    if t.empty:
        return t
    t["q"] = bh_qvalues(t["p"].to_numpy())
    t["consistent"] = (np.sign(t["half1"]) == np.sign(t["diff"])) & (np.sign(t["half2"]) == np.sign(t["diff"]))
    return t.sort_values("z", key=abs, ascending=False)


def run_sr2(cfg: Config, out_dir: Path, timeframes=("1h", "4h", "1D")) -> Path:
    df5, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = ROOT / "results"
    cache.mkdir(exist_ok=True)
    L = ["# Support / resistance v2: bounce candle, retests, breakouts, 1h / 4h / 1D, and a machine-learning filter", "",
         "**Read the win rates against their break-even:** before costs a 1R target needs >50%, 1.5R >40%, 2R >33%. "
         "Fees + slippage (0.18% round trip) cost a fixed share of each R, so the real 1R break-even is higher: "
         "it's shown as *needed @1R after costs*. **avg R columns are after costs.** "
         "Research = before 2025-11-01; holdout = from 2025-11-01 (never used to choose).",
         ""]
    summary = []
    for tf in timeframes:
        bar = pd.Timedelta(tf)
        ev = build_events(df5, tf, resample)
        ev = add_mtf_features(ev, df5)
        ev.to_pickle(cache / f"sr2_events_{tf}.pkl")
        res, hold = split(ev, bar)
        L += [f"## {tf} chart", ""]
        # overview
        rows = []
        for e_name, label in EVENT_NAMES.items():
            r_, h_ = res[res["event"] == e_name], hold[hold["event"] == e_name]
            rows.append({"what": label, "period": "research", **winrates(r_)})
            rows.append({"what": label, "period": "holdout", **winrates(h_)})
            summary.append({"tf": tf, "what": label, **{f"r_{k}": v for k, v in winrates(r_).items()},
                            **{f"h_{k}": v for k, v in winrates(h_).items()}})
        L += ["### Win rates", "", _table(pd.DataFrame(rows), [("what", "trade", str), ("period", "period", str), *WIN_COLS]), ""]
        # retests
        touches = res[res["event"].isin(["reversal_now", "breakout"])].copy()
        touches["tn"] = touches["touch_n"].clip(upper=4).map({1: "1st", 2: "2nd", 3: "3rd", 4: "4th+"})
        g = touches.groupby("tn").agg(touches=("event", "size"),
                                      held=("event", lambda s: (s == "reversal_now").mean())).reset_index()
        rb = res[res["event"] == "reversal_bounce"].copy()
        rb["tn"] = rb["touch_n"].clip(upper=4).map({1: "1st", 2: "2nd", 3: "3rd", 4: "4th+"})
        g2 = pd.DataFrame([{"tn": k, **winrates(v)} for k, v in rb.groupby("tn")])
        g = g.merge(g2, on="tn", how="left")
        L += ["### Retests: does price come back before breaking?", "",
              "*held* = share of touches where the level held at the candle close. Win rates are for the bounce-confirmed reversal.", "",
              _table(g, [("tn", "touch of the zone", str), ("touches", "touches", str), ("held", "level held", _pct),
                         *WIN_COLS]), ""]
        # bounce candle volume
        rb["bv"] = pd.cut(rb["f_bvol"], [0, 0.7, 1.2, 2, np.inf], labels=["low <0.7x", "normal", "high 1.2-2x", "very high >2x"])
        rb["bvt"] = pd.cut(rb["f_bvol_vs_touch"], [0, 0.7, 1.3, np.inf], labels=["less than touch", "similar", "more than touch"])
        gb = pd.DataFrame([{"bounce volume": k, **winrates(v)} for k, v in rb.groupby("bv", observed=True)])
        gbt = pd.DataFrame([{"bounce vs touch volume": k, **winrates(v)} for k, v in rb.groupby("bvt", observed=True)])
        L += ["### Bounce-candle volume", "", "Volume of the bounce (confirmation) candle vs its 20-candle average:", "",
              _table(gb, [("bounce volume", "bounce volume", str), *WIN_COLS]), "",
              "Bounce-candle volume vs the touch candle's volume:", "",
              _table(gbt, [("bounce vs touch volume", "bounce vs touch", str), *WIN_COLS]), ""]
        # breakouts
        br = res[res["event"] == "breakout"]
        if len(br):
            fb = br["false_break_6"].mean()
            wb = why_breaks(br[br["out_1"].isin(["win", "loss", "timeout"])])
            wb.to_csv(out_dir / f"sr2_breakout_features_{tf}.csv", index=False)
            sig = wb[(wb["q"] < 0.10) & wb["consistent"]].head(15) if len(wb) else wb
            L += ["### Breakouts: why do some breaks hold?", "",
                  f"- {len(br)} breaks; **{fb:.0%} were false breaks** (closed back on the old side within 6 candles).", "",
                  "Features that separate breaks that worked (win @1R) from those that failed (q < 0.10 and same "
                  "direction in both halves):", ""]
            L += [_table(sig, [("feature", "feature", str), ("split", "split", str), ("win_high", "win if high", _pct),
                               ("win_low", "win if low", _pct), ("q", "q", lambda x: f"{x:.3f}")])
                  if len(sig) else "None passed.", ""]
        # machine learning
        for e_name in ("reversal_bounce", "reversal_now", "breakout"):
            sub_r, sub_h = res[res["event"] == e_name], hold[hold["event"] == e_name]
            if len(sub_r) < 800:
                continue
            folds, oos, hres, imp = walk_forward(ev, sub_r, sub_h, bar)
            if folds.empty:
                continue
            L += [f"### Machine-learning filter: {EVENT_NAMES[e_name]} ({tf})", "",
                  f"LightGBM on {len(feature_cols(ev))} features (this timeframe + hint states on 10 timeframes). "
                  "Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the "
                  "top 20% most confident trades, using a cut-off fixed on training data.", "",
                  _table(folds, [("year", "test year", str), ("test", "all trades", str),
                                 ("all_win_1", "all: win @1R", _pct), ("picked", "picked", str),
                                 ("sel_win_1", "picked: win @1R", _pct), ("sel_win_1.5", "picked: win @1.5R", _pct),
                                 ("sel_win_2", "picked: win @2R", _pct), ("sel_r_1", "picked: avg R @1R", _r)]), ""]
            ow = winrates(oos)
            L += [f"**All test years together: picked {ow['n']} trades, win @1R {_pct(ow['win_1'])}, @1.5R "
                  f"{_pct(ow['win_1.5'])}, @2R {_pct(ow['win_2'])}.**", ""]
            if hres:
                L += [f"**Holdout (final model, never seen): all {hres['all']['n']} trades win @1R "
                      f"{_pct(hres['all']['win_1'])}; picked {hres['sel']['n']} trades win @1R "
                      f"{_pct(hres['sel']['win_1'])}, @1.5R {_pct(hres['sel']['win_1.5'])}, @2R "
                      f"{_pct(hres['sel']['win_2'])}.**", ""]
                summary.append({"tf": tf, "what": f"ML picked: {EVENT_NAMES[e_name]}",
                                **{f"r_{k}": v for k, v in ow.items()},
                                **{f"h_{k}": v for k, v in hres["sel"].items()}})
            L += ["Most important features:", "", ", ".join(imp["feature"].head(20)), ""]
    s = pd.DataFrame(summary)
    head = ["## Summary: win % at a 1R target (break-even 50% before costs; see 'needed after costs')", "",
            _table(s, [("tf", "TF", str), ("what", "trade", str), ("r_n", "research trades", lambda x: str(int(x))),
                       ("r_win_1", "research win @1R", _pct), ("r_be_1", "needed after costs", _pct),
                       ("r_r_1", "research avg R after costs", _r),
                       ("h_n", "holdout trades", lambda x: "-" if pd.isna(x) else str(int(x))),
                       ("h_win_1", "holdout win @1R", _pct), ("h_r_1", "holdout avg R after costs", _r)]), ""]
    L = L[:4] + head + L[4:]
    path = out_dir / "sr2_study.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    s.to_csv(out_dir / "sr2_summary.csv", index=False)
    return path
