"""
The trader's Bollinger-middle idea, tested on every v3.1 ETH trade (one position per move):
aggressive buyers defend the 1h Bollinger middle band (SMA 20).
  X  exit: after entry, the first 1h candle that CLOSES beyond the 1h middle band (below it for longs) before the trade
     has reached +1R -> exit at the next open.
  E  entry: after the signal, wait up to 24h for a 1h candle that touches the middle band and closes back on our side
     (the defence) -> enter at the next open; same stop and target PRICES as the signal (skip if the reward:risk drops
     under 1.2 or the stop / target was hit first). No defence within 24h -> no trade.
  E+X both. Same costs and fills as everywhere. Lessons came from holdout trades: 2022 - Oct 2025 is the clean test.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import C_LMT, C_MKT, LIMIT_BUFFER, MAX_TF_BARS, _funding_cum, account, stats
from .indicators import bollinger
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
FIVE = pd.Timedelta(minutes=5)
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
PRIORITY = {"A+ breakout": 0, "breakout": 1, "1D bounce": 2}


def run_bbmid(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t5 = df5n["open_time"].to_numpy()
    O, H, Lw, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    h1 = resample(df5u, "1h")
    h1t = pd.to_datetime(h1["open_time"], utc=True).dt.tz_convert(None).to_numpy()
    mid = bollinger(h1["close"])[0].to_numpy(float)
    H1h, H1l, H1c = (h1[x].to_numpy(float) for x in ("high", "low", "close"))
    ft, fc = _funding_cum(cfg)
    A = pd.read_pickle(ROOT / "results" / "coins_v31.pkl")
    S = A[A["coin"] == "ETH"].copy()
    S["prio"] = S["setup"].map(PRIORITY)
    S = S.sort_values(["entry_time", "direction", "prio"]).drop_duplicates(["entry_time", "direction"]).reset_index(drop=True)
    rows = []
    for k, r in S.iterrows():
        d, risk0 = int(r["direction"]), float(r["risk"])
        st = int(np.searchsorted(t5, pd.Timestamp(r["entry_time"]).to_datetime64()))
        bpt = int(pd.Timedelta(r["tf"]) / FIVE)
        sg = (lambda v: v) if d > 0 else (lambda v: -v)
        o, h, l, c = (O, H, Lw, C) if d > 0 else (-O, -Lw, -H, -C)
        e0 = o[st]
        S0, T0 = e0 - risk0, e0 + TGT[r["setup"]] * risk0          # signal stop / target prices (normalised)
        for mode in ("base", "X", "E", "E+X"):
            i0, e = st, e0
            if "E" in mode.split("+")[0] and mode.startswith("E"):
                # wait for a 1h defence of the middle band within 24h
                j = int(np.searchsorted(h1t, t5[st]))
                found = None
                for jj in range(j, min(len(h1t) - 1, j + 24)):
                    lo_, cl_, md = (H1l[jj], H1c[jj], mid[jj]) if d > 0 else (-H1h[jj], -H1c[jj], -mid[jj])
                    a5 = int(np.searchsorted(t5, h1t[jj])); b5 = a5 + 12
                    if (l[st:b5] <= S0).any() or (h[st:b5] >= T0).any():
                        break
                    if lo_ <= md and cl_ > md:
                        found = b5
                        break
                if found is None or found >= len(o):
                    continue
                i0, e = found, o[found]
                if e <= S0 or (T0 - e) / (e - S0) < 1.2:
                    continue
            s, tg = S0, T0
            risk = e - s
            end = min(len(o), i0 + MAX_TF_BARS * bpt)
            buf = LIMIT_BUFFER * abs(e)
            kind = None
            for i in range(i0, end):
                if i > i0 and o[i] <= s:
                    R, kind, xi = (o[i] - e) / risk, "stop", i; break
                if l[i] <= s:
                    R, kind, xi = (s - e) / risk, "stop", i; break
                if h[i] >= tg + buf:
                    R, kind, xi = (tg - e) / risk, "target", i; break
                if mode.endswith("X") and (i - i0) % 12 == 11:          # a 1h candle closed (entries on hour boundaries)
                    jj = int(np.searchsorted(h1t, t5[i - 11]))
                    cl_, md = (H1c[jj], mid[jj]) if d > 0 else (-H1c[jj], -mid[jj])
                    if h[i0:i + 1].max() < e + risk and cl_ < md and i + 1 < end:
                        R, kind, xi = (o[i + 1] - e) / risk, "middle-band exit", i + 1; break
            if kind is None:
                R, kind, xi = (c[end - 1] - e) / risk, "time", end - 1
            x_t = pd.Timestamp(t5[xi]) + FIVE
            a_ = np.searchsorted(ft, t5[i0], side="right"); b_ = np.searchsorted(ft, x_t.to_datetime64(), side="left")
            sp = risk / abs(e)
            cost = C_MKT + (C_LMT if kind == "target" else C_MKT) + ((fc[b_] - fc[a_]) * d if b_ > a_ else 0.0)
            rows.append({"sig": k, "mode": mode, "setup": r["setup"], "hold": bool(r["entry_time"] >= HOLDOUT),
                         "net": R - cost / sp, "kind": kind, "stop_pct": sp, "decision_time": pd.Timestamp(t5[i0]),
                         "exit_time": x_t, "rr": (tg - e) / risk})
    R_ = pd.DataFrame(rows)
    R_.to_pickle(ROOT / "results" / "bbmid.pkl")
    wk = {False: (HOLDOUT - pd.Timestamp("2022-01-01")).days / 7, True: (S["entry_time"].max() - HOLDOUT).days / 7}
    names = {"base": "v3.1 now (one position per move)", "X": "X · exit on a 1h close through the middle band (before +1R)",
             "E": "E · enter only after the 1h middle band is defended", "E+X": "E + X"}
    L = ["# Bollinger middle band: do aggressive buyers defend it?", "",
         "Every v3.1 ETH trade, one position per move. **win % = profit after all costs.** The idea came from the journal "
         "(holdout trades), so **2022 - Oct 2025 is the clean test**.", ""]
    rows = []
    for m in ("base", "X", "E", "E+X"):
        for hold, per in ((False, "2022 - Oct 2025 (clean test)"), (True, "holdout")):
            x = R_[(R_["mode"] == m) & (R_["hold"] == hold)].reset_index(drop=True)
            s_ = stats(x["net"].to_numpy())
            eq, mdd = account(x, "net", "exit_time", RISK) if len(x) else (math.nan, math.nan)
            rows.append({"m": names[m], "per": per, **s_, "pw": s_["n"] / wk[hold], "eq": eq, "mdd": mdd, "rr": x["rr"].mean()})
    f2 = lambda v: f"{v:+.2f}"  # noqa: E731
    L += ["## Results", "", _table(pd.DataFrame(rows), [
        ("m", "rule", str), ("per", "period", str), ("n", "trades", str), ("pw", "per week", lambda v: f"{v:.2f}"),
        ("win", "win %", _pct), ("avg", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("rr", "avg reward:risk", lambda v: f"{v:.2f}"), ("eq", "account", lambda v: f"{v:.2f}x"),
        ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    rows = []
    for m in ("base", "X", "E", "E+X"):
        for setup in TGT:
            for hold, per in ((False, "2022-25"), (True, "holdout")):
                x = R_[(R_["mode"] == m) & (R_["hold"] == hold) & (R_["setup"] == setup)]
                s_ = stats(x["net"].to_numpy())
                rows.append({"m": m, "setup": setup, "per": per, **s_})
    L += ["## Per setup", "", _table(pd.DataFrame(rows), [("m", "rule", str), ("setup", "setup", str), ("per", "period", str),
                                                         ("n", "trades", str), ("win", "win %", _pct), ("avg", "avg R", f2)]), ""]
    path = out_dir / "bbmid.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
