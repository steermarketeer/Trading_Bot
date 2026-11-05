"""More ETH trades: 6h / 12h charts and certainty-6 breakouts, all with the v3 filters; win % per timeframe."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .failure_liquidity import liquidity_features, swing_tables
from .flow import flow_features, load_flow
from .indicators import ema
from .mtf import resample
from .smalltf import COST_TAKER
from .sr2_run import _pct, _r, _table
from .strategy_eval import build_rows
from .strategy_v2 import simulate

HOLDOUT = pd.Timestamp("2025-11-01")
FILES = {"2h": "scored_breakout_2h.pkl", "4h": "scored_breakout.pkl", "1D": "scored_breakout.pkl",
         "6h": "scored_breakout_6h.pkl", "12h": "scored_breakout_12h.pkl"}


def load(tf):
    d = pd.read_pickle(ROOT / "results" / FILES[tf])
    d.attrs = {}
    d = d[(d["tf"] == tf) & (d["certainty"] >= 6)].copy()
    d["entry_time"] = pd.to_datetime(d["decision_time"], utc=True).dt.tz_convert(None)
    d["hold"] = d["entry_time"] >= HOLDOUT
    return d


def run_more_trades(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    btc5, _ = load_klines_5m(cfg.data_dir, cfg.btc_symbol)
    b4 = resample(btc5, "4h")
    b4["side"] = np.sign(b4["close"] - ema(b4["close"], 20))
    b4["close_time"] = pd.to_datetime(b4["close_time"], utc=True).dt.tz_convert(None).dt.as_unit("ns")
    fl = load_flow(cfg.data_dir, cfg.symbol)
    sw = swing_tables(df5u)
    lvn_med = float(pd.read_pickle(ROOT / "results" / "boost_A_flow.pkl").pipe(lambda a: a.loc[~a["hold"], "n_vp_lvn_share"].median()))
    parts = []
    for tf in ("2h", "4h", "6h", "12h", "1D"):
        d = load(tf)
        keep = ["tf", "event", "direction", "hold", "certainty", "entry", "risk", "entry_time", "f_atr_pct", "m_6h_macd", "atr"]
        r = build_rows(d, df5n, (2.0,), keep)
        q20 = r.loc[~r["hold"] & (r["certainty"] >= 7), "atr_pct"].quantile(0.2) if "atr_pct" in r else None
        r["atr_pct"] = r["atr"] / r["entry"]
        q20 = r.loc[~r["hold"] & (r["certainty"] >= 7), "atr_pct"].quantile(0.2)
        r = r[(r["stop_pct"] >= 0.006) & (r["atr_pct"] >= q20)].reset_index(drop=True)
        t = r.assign(_r=np.arange(len(r)), _t=r["decision_time"].dt.as_unit("ns")).sort_values("_t")
        m = pd.merge_asof(t, b4[["close_time", "side"]], left_on="_t", right_on="close_time", direction="backward").sort_values("_r")
        r["btc_4h"] = m["side"].to_numpy() * r["direction"].to_numpy()
        r = r[(r["btc_4h"] > 0) & (r["m_6h_macd"] > 0)].reset_index(drop=True)
        r["T"], r["atr_px"] = 2.0, r["atr"]
        r = pd.concat([r, liquidity_features(r, sw, df5n)], axis=1)
        r = r[(r["liq_in_risk"] == 0) & (r["pool_near_stop"] == 0)].reset_index(drop=True)
        ff = flow_features(r.assign(atr_ref=r["atr"]), fl)
        r["lvn"] = ff["n_vp_lvn_share"].to_numpy()
        r["setup"] = np.where(r["lvn"] > lvn_med, "A+ breakout (2:1)", "breakout (2:1)")
        r["net"] = r["R_2:1"] - COST_TAKER / r["stop_pct"]
        parts.append(r)
    B = pd.concat(parts, ignore_index=True)
    B = B[B["decision_time"] >= pd.Timestamp("2022-01-01")]
    B.to_pickle(ROOT / "results" / "more_trades_breakouts.pkl")
    span = {"research": (B.loc[~B["hold"], "decision_time"].max() - pd.Timestamp("2022-01-01")).days / 7,
            "holdout": (B.loc[B["hold"], "decision_time"].max() - HOLDOUT).days / 7}
    L = ["# More ETH trades: 6h / 12h charts and 6/10 breakouts (all v3 filters)", "",
         "Breakouts at 2:1 after the v3 filters (stop >= 0.6%, not the quietest 20%, BTC 4h + 6h MACD agree, clean "
         "risk zone). Replayed on 5-minute candles, market-order costs. Research 2022 - Oct 2025, holdout Nov 2025 on.", ""]
    rows = []
    for tf in ("2h", "4h", "6h", "12h", "1D"):
        for cert, cm in (("7+", B["certainty"] >= 7), ("6", B["certainty"] == 6)):
            for per, pm in (("research", ~B["hold"]), ("holdout", B["hold"])):
                g = B[(B["tf"] == tf) & cm & pm]
                rows.append({"tf": tf, "cert": cert, "period": per, "n": len(g), "pw": len(g) / span[per],
                             "win": (g["net"] > 0).mean() if len(g) else math.nan, "avg": g["net"].mean() if len(g) else math.nan})
    L += ["## Breakouts per timeframe and certainty", "",
          _table(pd.DataFrame(rows), [("tf", "chart", str), ("cert", "certainty", str), ("period", "period", str),
                                      ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
                                      ("win", "win % (2:1)", _pct), ("avg", "avg R", _r)]), ""]
    bnc = pd.read_pickle(ROOT / "results" / "boost_B.pkl")
    bnc = bnc[bnc["decision_time"] >= pd.Timestamp("2022-01-01")].copy()
    bnc["setup"], bnc["R"], bnc["exit"] = "1D 4th-test bounce (3:1)", bnc["R_3:1"], bnc["exit_3:1"]
    bnc["net"] = bnc["R"] - COST_TAKER / bnc["stop_pct"]
    B["R"], B["exit"] = B["R_2:1"], B["exit_2:1"]
    risk = {"A+ breakout (2:1)": 0.04, "breakout (2:1)": 0.02, "1D 4th-test bounce (3:1)": 0.02}
    variants = {
        "v3 now: 2h/4h/1D at 7+": (B["tf"].isin(["2h", "4h", "1D"])) & (B["certainty"] >= 7),
        "+ 6h and 12h at 7+": B["certainty"] >= 7,
        "+ 6h/12h at 7+, + 6/10 on 4h/6h/12h/1D": (B["certainty"] >= 7) | (B["tf"].isin(["4h", "6h", "12h", "1D"])),
        "everything: all charts, 6+": B["certainty"] >= 6,
    }
    rows = []
    for name, m in variants.items():
        allt = pd.concat([B[m], bnc], ignore_index=True)
        for per, pm in (("research", ~allt["hold"]), ("holdout", allt["hold"])):
            g = allt[pm].sort_values("decision_time").reset_index(drop=True)
            gb = g[g["setup"] != "1D 4th-test bounce (3:1)"]
            s = simulate(g[["decision_time", "exit", "setup", "stop_pct", "R"]].assign(), risk)
            rows.append({"variant": name, "period": per, "n": len(g), "pw": len(g) / span[per],
                         "win": (g["net"] > 0).mean(), "win_b": (gb["net"] > 0).mean(), "avg": g["net"].mean(),
                         "final": s["final"], "dd": s["max_dd"], "month": s["avg_month"]})
    L += ["## Whole strategy (breakouts + 1D 4th-test bounces), risk A+ 4% / others 2%, cap 5x", "",
          _table(pd.DataFrame(rows), [("variant", "version", str), ("period", "period", str), ("n", "trades", str),
                                      ("pw", "trades/week", lambda v: f"{v:.1f}"), ("win", "win % all", _pct),
                                      ("win_b", "win % breakouts", _pct), ("avg", "avg R", _r),
                                      ("final", "account (x)", lambda v: f"{v:,.2f}x"), ("dd", "max drawdown", lambda v: f"{v:.0%}"),
                                      ("month", "avg month", lambda v: f"{v:+.1%}")]), ""]
    path = out_dir / "more_trades.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
