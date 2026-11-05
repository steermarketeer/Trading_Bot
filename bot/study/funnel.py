"""Which v3 rule removes the most trades? Funnel + drop-one test, 2022 onward (win % after costs at 2:1, candle data)."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .failure_liquidity import liquidity_features, swing_tables
from .indicators import ema
from .level_tests import tests_for
from .mtf import resample
from .sr2_run import _pct, _table

COST = 0.0018
START = pd.Timestamp("2022-01-01")


def run_funnel(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    params = json.loads((ROOT / "models" / "v3" / "params.json").read_text())
    parts = []
    for f, tfs in (("scored_breakout_2h.pkl", ["2h"]), ("scored_breakout.pkl", ["4h", "1D"])):
        d = pd.read_pickle(ROOT / "results" / f)
        d.attrs = {}
        parts.append(d[d["tf"].isin(tfs)])
    b = pd.concat(parts, ignore_index=True)
    b["decision_time"] = pd.to_datetime(b["decision_time"], utc=True).dt.tz_convert(None)
    b = b[(b["decision_time"] >= START) & b["out_2"].isin(["win", "loss", "timeout"])].reset_index(drop=True)
    b["net"] = b["r_2"] - COST * b["entry"] / b["risk"]
    b["win"] = b["net"] > 0
    btc5, _ = load_klines_5m(cfg.data_dir, cfg.btc_symbol)
    b4 = resample(btc5, "4h")
    b4["side"] = np.sign(b4["close"] - ema(b4["close"], 20))
    b4["close_time"] = pd.to_datetime(b4["close_time"], utc=True).dt.tz_convert(None).dt.as_unit("ns")
    t = b.assign(_r=np.arange(len(b)), _t=b["decision_time"].dt.as_unit("ns")).sort_values("_t")
    m = pd.merge_asof(t, b4[["close_time", "side"]], left_on="_t", right_on="close_time", direction="backward").sort_values("_r")
    R = {
        "certainty 7/10+": b["certainty"] >= 7,
        "stop >= 0.6%": (b["risk"] / b["entry"]) >= 0.006,
        "not the quietest 20%": (b["atr"] / b["entry"]) >= b["tf"].map(params["atr_q20"]),
        "BTC 4h agrees": (m["side"].to_numpy() * b["direction"].to_numpy()) > 0,
        "6h MACD agrees": b["m_6h_macd"] > 0,
    }
    cheap = pd.DataFrame(R)
    fails = (~cheap).sum(axis=1)
    need = fails <= 1  # liquidity needed only where at most one cheap rule fails
    sub = b[need].copy()
    sub["T"], sub["atr_px"] = 2.0, sub["atr"]
    lq = liquidity_features(sub, swing_tables(df5u), df5n)
    clean = pd.Series(False, index=b.index)
    clean.loc[sub.index] = ((lq["liq_in_risk"] == 0) & (lq["pool_near_stop"] == 0)).to_numpy()
    R["clean risk zone"] = clean
    allr = pd.DataFrame(R)
    weeks = (b["decision_time"].max() - START).days / 7
    L = ["# Which rule removes the most trades?", "",
         f"Breakouts on 2h / 4h / 1D since 2022 ({len(b):,} main-rule breakout events, ~{len(b) / weeks:.0f} per week). "
         "win % = profit after costs at 2:1 (candle data).", "", "## Funnel: rules applied one after another", ""]
    rows, mask = [], pd.Series(True, index=b.index)
    rows.append({"step": "all main-rule breakouts", "left": int(mask.sum()), "pw": mask.sum() / weeks,
                 "win": b.loc[mask, "win"].mean(), "removed": 0, "win_removed": math.nan})
    for name, r in R.items():
        rem = mask & ~r
        mask = mask & r
        rows.append({"step": f"+ {name}", "left": int(mask.sum()), "pw": mask.sum() / weeks,
                     "win": b.loc[mask, "win"].mean(), "removed": int(rem.sum()),
                     "win_removed": b.loc[rem, "win"].mean() if rem.any() else math.nan})
    L += [_table(pd.DataFrame(rows), [("step", "rule", str), ("removed", "trades removed", str),
                                      ("win_removed", "win % of removed trades", _pct), ("left", "trades left", str),
                                      ("pw", "per week", lambda v: f"{v:.2f}"), ("win", "win % of the rest", _pct)]), ""]
    full = allr.all(axis=1)
    rows = [{"drop": "none (v3 breakouts)", "n": int(full.sum()), "pw": full.sum() / weeks, "win": b.loc[full, "win"].mean(),
             "avg": b.loc[full, "net"].mean()}]
    for name in R:
        mk = allr.drop(columns=name).all(axis=1)
        rows.append({"drop": name, "n": int(mk.sum()), "pw": mk.sum() / weeks, "win": b.loc[mk, "win"].mean(),
                     "avg": b.loc[mk, "net"].mean()})
    L += ["## Drop one rule at a time (all other rules kept)", "",
          _table(pd.DataFrame(rows), [("drop", "rule dropped", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
                                      ("win", "win %", _pct), ("avg", "avg R", lambda v: f"{v:+.2f}")]), ""]
    # bounces
    lt = tests_for(df5u, "1D")
    lt = lt[pd.to_datetime(lt["time"], utc=True).dt.tz_convert(None) >= START]
    tr = lt[lt.get("traded", pd.Series(False, index=lt.index)).fillna(False).astype(bool)].copy()
    tr["net"] = tr["r_3"] - COST * tr["entry"] / tr["risk"]
    wk = (pd.to_datetime(lt["time"]).max() - pd.to_datetime(lt["time"]).min()).days / 7
    rows = [{"step": "strong-zone touches (1D)", "n": len(lt), "pw": len(lt) / wk, "win": math.nan},
            {"step": "+ held at close", "n": int(lt["held"].sum()), "pw": lt["held"].sum() / wk, "win": math.nan},
            {"step": "+ confirmation candle (traded)", "n": len(tr), "pw": len(tr) / wk, "win": (tr["net"] > 0).mean()},
            {"step": "+ 4th test or later", "n": int((tr["test_n"] >= 4).sum()), "pw": (tr["test_n"] >= 4).sum() / wk,
             "win": (tr.loc[tr["test_n"] >= 4, "net"] > 0).mean()}]
    L += ["## 1D bounces funnel (3:1)", "",
          _table(pd.DataFrame(rows), [("step", "rule", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
                                      ("win", "win % (3:1)", _pct)]), "",
          f"Bounces on the 1st-3rd test: win {(tr.loc[tr['test_n'] < 4, 'net'] > 0).mean():.0%}, "
          f"avg {tr.loc[tr['test_n'] < 4, 'net'].mean():+.2f} R vs 4th+: avg {tr.loc[tr['test_n'] >= 4, 'net'].mean():+.2f} R.", ""]
    path = out_dir / "funnel.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
