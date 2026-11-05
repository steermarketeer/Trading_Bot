"""
Strategy v2 failures: liquidity vs indicators.

For every trade (breakouts 2:1, A+, 1D bounces 3:1), at the entry time (swings confirmed by then):
  liq_in_risk      number of swing points on OUR stop side (1h + trade timeframe, last 100 candles) lying between the
                   stop and the entry: resting stops inside our risk zone (sweep magnet)
  pool_near_stop   equal lows/highs (2 swings within 0.25 ATR) within 0.5 ATR of our stop, on either side of it
  round_near_stop  a round number (multiple of 50 USDT) within 0.3 ATR of our stop
  liq_in_path      untaken swing points on the TARGET side between entry and the target (obstacles)
Outcome of losers (uses the future, for diagnosis only):
  stop_hunt        after the stop was hit, price still reached the original target within the trade window
  wick_stop        the stop was hit by a wick; that candle (trade timeframe) closed back on our side of the stop
Fix tested: stop placed 0.25 ATR beyond the deepest liquidity (swing / pool / round number) that lies within 1 ATR
beyond the original stop; target = same R multiple of the NEW risk.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .concepts import Bars
from .mtf import resample
from .smalltf import COST_TAKER
from .sr2_run import _pct, _r, _table
from .strategy_eval import replay_one

FIVE = pd.Timedelta(minutes=5)


def trades_v2() -> pd.DataFrame:
    A = pd.read_pickle(ROOT / "results" / "boost_A_flow.pkl")
    B = pd.read_pickle(ROOT / "results" / "boost_B.pkl")
    med = A.loc[~A["hold"], "n_vp_lvn_share"].median()
    a = A[(A["n_btc_4h"] > 0) & (A["m_6h_macd"] > 0)].copy()
    a["setup"] = np.where(a["n_vp_lvn_share"] > med, "A+ breakout", "breakout")
    a["T"], a["R"], a["exit"] = 2.0, a["R_2:1"], a["exit_2:1"]
    b = B.copy()
    b["setup"], b["T"], b["R"], b["exit"] = "1D bounce", 3.0, b["R_3:1"], b["exit_3:1"]
    keep = ["decision_time", "exit", "setup", "tf", "direction", "entry", "risk", "stop_pct", "R", "T", "hold",
            "f_atr_pct"] + [c for c in A.columns if c.startswith(("m_", "n_", "f_")) and c in B.columns]
    keep = list(dict.fromkeys(keep))
    t = pd.concat([a[keep], b[keep]], ignore_index=True)
    t = t[t["decision_time"] >= pd.Timestamp("2022-01-01")].reset_index(drop=True)
    t["atr_px"] = t["f_atr_pct"] * t["entry"]
    t["net"] = t["R"] - COST_TAKER / t["stop_pct"]
    return t


def swing_tables(df5: pd.DataFrame) -> dict:
    out = {}
    for tf in ("1h", "2h", "4h", "6h", "12h", "1D"):
        bars = Bars(resample(df5, tf))
        ct = bars.ct.dt.tz_convert(None).to_numpy()
        hi = [(bars.ot.iloc[i].tz_convert(None), p, ct[cf]) for i, p, cf in bars.sh]
        lo = [(bars.ot.iloc[i].tz_convert(None), p, ct[cf]) for i, p, cf in bars.sl]
        out[tf] = (pd.DataFrame(hi, columns=["formed", "price", "known"]),
                   pd.DataFrame(lo, columns=["formed", "price", "known"]), pd.Timedelta(tf))
    return out


def liquidity_features(t: pd.DataFrame, sw: dict, df5n: pd.DataFrame) -> pd.DataFrame:
    t5 = df5n["open_time"].to_numpy()
    H, Lw = df5n["high"].to_numpy(float), df5n["low"].to_numpy(float)
    rows = []
    for _, r in t.iterrows():
        et, d, e, rk, a = r["decision_time"], int(r["direction"]), r["entry"], r["risk"], r["atr_px"]
        stop, tgt = e - d * rk, e + d * r["T"] * rk
        own, path = [], []
        for tf in ("1h", r["tf"]):
            hi, lo, bar = sw[tf]
            win = et - bar * 100
            stop_side = lo if d > 0 else hi
            tgt_side = hi if d > 0 else lo
            s1 = stop_side[(stop_side["known"] <= et) & (stop_side["formed"] >= win)]["price"].to_numpy()
            s2 = tgt_side[(tgt_side["known"] <= et) & (tgt_side["formed"] >= win)]["price"].to_numpy()
            own.append(s1)
            # untaken = not traded through between its formation and entry
            for _, s in tgt_side[(tgt_side["known"] <= et) & (tgt_side["formed"] >= win)].iterrows():
                i0, i1 = np.searchsorted(t5, np.datetime64(s["formed"])), np.searchsorted(t5, np.datetime64(et))
                seg = H[i0 + 1:i1] if d > 0 else Lw[i0 + 1:i1]
                taken = (seg > s["price"]).any() if d > 0 else (seg < s["price"]).any()
                if not taken:
                    path.append(s["price"])
        own = np.unique(np.concatenate(own)) if own else np.array([])
        path = np.array(path)
        lo_, hi_ = sorted((stop, e))
        liq_in_risk = int(((own > lo_) & (own < hi_)).sum())
        srt = np.sort(own)
        pools = [(srt[i] + srt[i + 1]) / 2 for i in range(len(srt) - 1) if srt[i + 1] - srt[i] <= 0.25 * a]
        pools = np.array(pools)
        pool_near = int((np.abs(pools - stop) <= 0.5 * a).any()) if len(pools) else 0
        rn = round(stop / 50) * 50
        round_near = int(abs(rn - stop) <= 0.3 * a)
        a2, b2 = sorted((e, tgt))
        liq_in_path = int(((path > a2) & (path < b2)).sum()) if len(path) else 0
        # liquidity just beyond the stop (within 1 ATR): candidates for a wider stop
        beyond = own[((stop - own) * d > 0) & ((stop - own) * d <= a)] if len(own) else np.array([])
        extra = list(beyond) + ([rn] if (stop - rn) * d >= 0 and (stop - rn) * d <= a else []) + \
            [p for p in pools if (stop - p) * d >= -0.5 * a and (stop - p) * d <= a]
        if extra:
            deepest = min(extra) if d > 0 else max(extra)
            wide_stop = deepest - d * 0.25 * a
            wide_stop = min(wide_stop, stop) if d > 0 else max(wide_stop, stop)  # never tighter than the original
        else:
            wide_stop = np.nan
        rows.append({"liq_in_risk": liq_in_risk, "pool_near_stop": pool_near, "round_near_stop": round_near,
                     "liq_in_path": liq_in_path, "wide_stop": wide_stop})
    return pd.DataFrame(rows, index=t.index)


def loser_outcomes(t: pd.DataFrame, df5n: pd.DataFrame) -> pd.DataFrame:
    t5 = df5n["open_time"].to_numpy()
    H, Lw, C = (df5n[x].to_numpy(float) for x in ("high", "low", "close"))
    out = []
    for _, r in t.iterrows():
        if r["net"] > 0:
            out.append({"stop_hunt": np.nan, "wick_stop": np.nan})
            continue
        d, e, rk = int(r["direction"]), r["entry"], r["risk"]
        stop, tgt = e - d * rk, e + d * r["T"] * rk
        bpt = int(pd.Timedelta(r["tf"]) / FIVE)
        i0 = int(np.searchsorted(t5, np.datetime64(r["decision_time"])))
        i_ex = int(np.searchsorted(t5, np.datetime64(r["exit"]))) - 1
        end = min(len(t5), i0 + 60 * bpt)
        after = slice(i_ex + 1, end)
        hunt = bool((H[after] >= tgt).any()) if d > 0 else bool((Lw[after] <= tgt).any())
        # close of the trade-timeframe candle that contains the stop-out
        k = i0 + ((i_ex - i0) // bpt + 1) * bpt - 1
        k = min(k, len(C) - 1)
        wick = bool((C[k] - stop) * d > 0)
        out.append({"stop_hunt": float(hunt), "wick_stop": float(wick)})
    return pd.DataFrame(out, index=t.index)


def run_failure_liquidity(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t = trades_v2()
    sw = swing_tables(df5u)
    t = pd.concat([t, liquidity_features(t, sw, df5n), loser_outcomes(t, df5n)], axis=1)
    # alternative: stop beyond liquidity
    O, Hh, Ll, Cc = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    t5 = df5n["open_time"].to_numpy()
    alt = []
    for _, r in t.iterrows():
        if pd.isna(r["wide_stop"]):
            alt.append(r["net"])
            continue
        nrisk = abs(r["entry"] - r["wide_stop"])
        res = replay_one(O, Hh, Ll, Cc, t5, r["decision_time"], r["tf"], int(r["direction"]), nrisk, (r["T"],))
        if res is None:
            alt.append(r["net"])
            continue
        ex, px = res
        alt.append(ex[f"{r['T']:g}:1"][0] - COST_TAKER / (nrisk / px))
    t["net_wide"] = alt
    t.to_pickle(ROOT / "results" / "failure_liquidity.pkl")

    L = ["# Strategy v2 failures: liquidity vs indicators", "",
         "Liquidity measured at entry from swings already confirmed (1h + the trade's timeframe, last 100 candles). "
         "Win % after costs. Research 2022 - Oct 2025, holdout Nov 2025 on.", ""]
    for per, g in (("research", t[~t["hold"]]), ("holdout", t[t["hold"]])):
        lost = g[g["net"] <= 0]
        L += [f"## {per}: {len(g)} trades, {len(lost)} losses", "",
              f"- **{lost['stop_hunt'].mean():.0%} of losses were stop hunts**: stopped out, then price still reached our target.",
              f"- **{lost['wick_stop'].mean():.0%} were wick stops**: the candle that hit our stop closed back on our side.",
              ""]
        rows = []
        for name, col in (("swing liquidity inside our risk zone", "liq_in_risk"),
                          ("equal highs/lows (pool) near our stop", "pool_near_stop"),
                          ("round number near our stop", "round_near_stop"),
                          ("untaken liquidity between entry and target", "liq_in_path")):
            yes, no = g[g[col] > 0], g[g[col] <= 0]
            rows.append({"what": name, "n": len(yes), "win_yes": (yes["net"] > 0).mean(), "win_no": (no["net"] > 0).mean(),
                         "r_yes": yes["net"].mean(), "r_no": no["net"].mean(),
                         "hunt": yes[yes["net"] <= 0]["stop_hunt"].mean()})
        L += ["### Liquidity at entry", "",
              _table(pd.DataFrame(rows), [("what", "liquidity condition", str), ("n", "trades with it", str),
                                          ("win_yes", "win % with", _pct), ("win_no", "win % without", _pct),
                                          ("r_yes", "avg R with", _r), ("r_no", "avg R without", _r),
                                          ("hunt", "losses that were stop hunts", _pct)]), ""]
        # indicators: biggest win% gaps among the main ones
        ind = ["m_6h_macd", "m_4h_supertrend", "m_1D_trend", "m_1W_trend", "m_2h_climax", "n_btc_4h", "n_squeeze",
               "m_6h_macd_fade", "m_1h_rsi_ext", "m_4h_rsi_ext", "m_1D_adx_weak"]
        rows = []
        for col in [c for c in ind if c in g]:
            yes, no = g[g[col] > 0] if not col.endswith(("fade", "rsi_ext")) else g[g[col] < 0], \
                g[~(g[col] > 0)] if not col.endswith(("fade", "rsi_ext")) else g[~(g[col] < 0)]
            if len(yes) < 10 or len(no) < 10:
                continue
            rows.append({"what": col, "n": len(yes), "win_yes": (yes["net"] > 0).mean(), "win_no": (no["net"] > 0).mean(),
                         "gap": (yes["net"] > 0).mean() - (no["net"] > 0).mean()})
        L += ["### Indicators (for comparison: how much they separate winners from losers)", "",
              _table(pd.DataFrame(rows).sort_values("gap", key=abs, ascending=False),
                     [("what", "indicator (present / warning)", str), ("n", "trades", str), ("win_yes", "win % when present", _pct),
                      ("win_no", "win % when not", _pct), ("gap", "gap", lambda v: f"{v * 100:+.0f} pts")]), ""]
        # fix: stop beyond liquidity
        rows = []
        for st, gg in list(g.groupby("setup")) + [("ALL", g)]:
            rows.append({"setup": st, "n": len(gg), "moved": gg["wide_stop"].notna().mean(),
                         "win_now": (gg["net"] > 0).mean(), "win_wide": (gg["net_wide"] > 0).mean(),
                         "r_now": gg["net"].mean(), "r_wide": gg["net_wide"].mean()})
        L += ["### Fix: stop placed beyond the nearby liquidity (target = same R multiple of the new risk)", "",
              _table(pd.DataFrame(rows), [("setup", "setup", str), ("n", "trades", str), ("moved", "stops moved", _pct),
                                          ("win_now", "win % now", _pct), ("win_wide", "win % with wider stop", _pct),
                                          ("r_now", "avg R now", _r), ("r_wide", "avg R wider stop", _r)]), ""]
    path = out_dir / "failure_liquidity.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path
