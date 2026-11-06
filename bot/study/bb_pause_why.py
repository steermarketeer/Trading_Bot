"""
Why does the middle-band hold after a pump pump again, and why does it sometimes fail? (And why does a failure dump?)

Events (1h, 4h, 1D; mirrored for dumps), as in bot/study/bb_pause.py concept(): a pump close beyond the outer band,
>= 3 sideways candles with every close above the middle band (no touch, no new pump), then the first touch of the middle
band (low <= middle + 0.25 ATR) at candle q. Decided at q's close.
  hold  = q closes above the middle band: claim the trend resumes.  fail = q closes at / below it: claim a dump.
  Outcome (fair, symmetric): 1.5 ATR in the claimed direction before 1.5 ATR against, within 30 candles (a coin flip =
  50%). And the trader's far target: a new high above everything so far (hold) / the sideways low (fail) before a close
  0.5 ATR beyond the middle band (a failure level that does not depend on the touch candle). Because the distances to the
  target and to the failure level differ from case to case (and conditions like a long wick change them), each condition
  is also compared WITHIN groups of the same timeframe x distance to the target x distance to the failure level
  (quintiles), with a shuffle test inside the groups: only that column says whether the condition itself matters.
Conditions at q's close (all from candles <= q):
  pump      pump size: the leg into the pump >= 4 ATR; the pump close > 0.5 ATR beyond the band; volume on the pump >= 2x
  sideways  length >= 6 candles; tight (high-low of the sideways <= 2 ATR); bands contracted during it (width at q <=
            0.8 x at the pump); volume dried up (sideways average <= 0.6 x the pump's volume); a higher high made during
            the sideways (above the pump candle's high); 3+ rejections at the top (high reaches the upper band, close back
            inside); equal highs at the top (two sideways highs within 0.25 ATR: buy-side liquidity left above)
  touch     a wick rejection (close in the top half of the candle); deep (low > 0.25 ATR below the middle band); swept the
            sideways low (low below the lowest sideways low) and still closed above the middle; touch volume >= 1.5x the
            sideways average; RSI 40-50 at the touch; RSI < 40
  context   middle band rising (vs 5 candles ago); higher timeframe above its EMA 50; daily above its EMA 200
  liquidity (from Dec 2021) open interest rose > 5% from the pump close to the touch (new positions piled in); the account
            long/short ratio at the touch above its 30-day median (the crowd leaning long)
Each condition: fair-test rate when present vs absent, the time-shift noise test (400 shifts, clustering kept), and the
holdout. Research 2020 - Oct 2025 (open-interest conditions: Dec 2021 - Oct 2025).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .defs import TF
from .indicator_deep import shift_pvalue
from .indicator_learn import outcome
from .indicators import ema, rsi
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
HTF = {"1h": "4h", "4h": "1D", "1D": "1W"}
WIN = 30


def load_metrics(data_dir, symbol):
    p = Path(data_dir) / "metrics" / f"{symbol}_metrics_5m.csv"
    m = pd.read_csv(p, usecols=["create_time", "sum_open_interest", "count_long_short_ratio"])
    m["create_time"] = pd.to_datetime(m["create_time"]).dt.as_unit("ns")
    m = m.dropna().sort_values("create_time").reset_index(drop=True)
    m["ls_med"] = m["count_long_short_ratio"].rolling(288 * 30, min_periods=288 * 10).median()
    return m


def at(m, t):
    """Last metrics snapshot at or before time t (or None)."""
    k = int(np.searchsorted(m["create_time"].to_numpy(), np.datetime64(pd.Timestamp(t)), side="right")) - 1
    return None if k < 0 else m.iloc[k]


def events(t: TF, ht: TF, d1: TF, m, tf: str) -> list[dict]:
    rows = []
    he50 = ema(pd.Series(ht.c), 50).to_numpy(float)
    d200 = ema(pd.Series(d1.c), 200).to_numpy(float)
    r_all = rsi(pd.Series(t.c)).to_numpy(float)
    Y = outcome(t)                                                       # fair test: +1.5 ATR before -1.5 ATR
    for side in (1, -1):
        c, h, l, o = (t.c, t.h, t.l, t.o) if side > 0 else (-t.c, -t.l, -t.h, -t.o)
        up, mid = (t.up, t.mid) if side > 0 else (-t.lo, -t.mid)
        hup = ht.up if side > 0 else -ht.lo
        r = r_all if side > 0 else 100 - r_all
        bw = (t.up - t.lo) / t.mid
        a = t.a
        v = t.v
        j = 25
        while j < t.n - 1:
            if not (np.isfinite(a[j]) and c[j] > up[j]):
                j += 1; continue
            k = j
            q = k + 1
            while q < t.n and q - k <= 20 and c[q] > mid[q] and not (l[q] <= mid[q] + 0.25 * a[q]) and not c[q] > up[q]:
                q += 1
            if q >= t.n - 1 or q - k > 20:
                j = q; continue
            if c[q] > up[q] and not (l[q] <= mid[q] + 0.25 * a[q]):
                j = q; continue                                          # a new pump: restart from it
            nside = q - k - 1
            if nside < 3:
                j = q if c[q] > up[q] else q + 1; continue
            # ---- the event at q
            held = c[q] > mid[q]
            sw = slice(k + 1, q)
            top = max(h[max(0, k - 20):q + 1].max(), h[q])
            sw_low = l[sw].min()
            end = min(t.n, q + 1 + WIN)
            if q + WIN >= t.n:
                j = q + 1; continue                                      # window would be cut by the data end
            # far outcome with a failure level that does NOT depend on the touch candle: 0.5 ATR beyond the middle band
            fail_lvl = mid[q] - 0.5 * a[q] if held else mid[q] + 0.5 * a[q]
            succ = False
            for z in range(q + 1, end):
                if held:
                    if h[z] > top:
                        succ = True; break
                    if c[z] < fail_lvl:
                        break
                else:
                    if l[z] < sw_low:
                        succ = True; break
                    if c[z] > fail_lvl:
                        break
            d_target = ((top - c[q]) if held else (c[q] - sw_low)) / a[q]
            d_fail = ((c[q] - fail_lvl) if held else (fail_lvl - c[q])) / a[q]
            leg0 = l[max(0, k - 20):k + 1].min()
            sw_highs = h[sw]
            eqh = bool(len(sw_highs) >= 2 and np.any(np.abs(sw_highs[:, None] - sw_highs[None, :])[np.triu_indices(len(sw_highs), 1)] <= 0.25 * a[q]))
            rej = int(np.sum((h[sw] >= up[sw]) & (c[sw] <= up[sw])))
            hj = ht.closed_before(t.ct[q]) - 1
            dj = d1.closed_before(t.ct[q]) - 1
            rng = h[q] - l[q]
            f = {"pump: leg into the pump >= 4 ATR": (h[k] - leg0) / a[k] >= 4,
                 "pump: close > 0.5 ATR beyond the band": (c[k] - up[k]) / a[k] > 0.5,
                 "pump: volume >= 2x": v[k] >= 2 * v[max(0, k - 20):k].mean(),
                 "sideways: 6+ candles": nside >= 6,
                 "sideways: tight (range <= 2 ATR)": (h[sw].max() - l[sw].min()) / a[q] <= 2,
                 "sideways: bands contracted (width <= 0.8x the pump's)": bw[q] <= 0.8 * bw[k],
                 "sideways: volume dried up (<= 0.6x the pump's)": v[sw].mean() <= 0.6 * v[k],
                 "sideways: a higher high than the pump candle": h[sw].max() > h[k],
                 "sideways: 3+ rejections at the upper band": rej >= 3,
                 "sideways: equal highs at the top (liquidity above)": eqh,
                 "touch: wick rejection (close in the top half)": rng > 0 and (c[q] - l[q]) >= 0.5 * rng,
                 "touch: deep (> 0.25 ATR below the middle band)": (mid[q] - l[q]) / a[q] > 0.25,
                 "touch: swept the sideways low": l[q] < sw_low,
                 "touch: volume >= 1.5x the sideways average": v[q] >= 1.5 * v[sw].mean(),
                 "touch: RSI 40-50": 40 <= r[q] <= 50,
                 "touch: RSI < 40": r[q] < 40,
                 "context: middle band rising": mid[q] > mid[q - 5],
                 "context: higher timeframe above its EMA 50": ((ht.c[hj] - he50[hj]) * side > 0) if hj >= 0 and np.isfinite(he50[hj]) else None,
                 "context: higher timeframe at / above its upper band": (((ht.h[hj] if side > 0 else -ht.l[hj]) >= hup[hj])
                                                                       if hj >= 0 and np.isfinite(hup[hj]) else None),
                 "context: daily above its EMA 200": ((d1.c[dj] - d200[dj]) * side > 0) if dj >= 0 and np.isfinite(d200[dj]) else None}
            mk, mq = at(m, t.ct[k]), at(m, t.ct[q])
            ok_m = mk is not None and mq is not None and pd.Timestamp(t.ct[q]) - mq["create_time"] < pd.Timedelta(hours=2) \
                and np.isfinite(mq["ls_med"]) and mk["sum_open_interest"] > 0 and mq["sum_open_interest"] > 0
            if ok_m:
                oi_up = mq["sum_open_interest"] / mk["sum_open_interest"] - 1 > 0.05
                ls = mq["count_long_short_ratio"]
                crowd = (ls > mq["ls_med"]) if side > 0 else (ls < mq["ls_med"])
                f["liquidity: open interest rose > 5% during the sideways"] = bool(oi_up)
                f["liquidity: crowd leaning with the pump (long/short ratio above its 30-day median)"] = bool(crowd)
            else:
                f["liquidity: open interest rose > 5% during the sideways"] = None
                f["liquidity: crowd leaning with the pump (long/short ratio above its 30-day median)"] = None
            claim = side if held else -side                              # in price terms: held = the trend's way
            yq = Y[q]
            fair = np.nan if not np.isfinite(yq) else (yq if claim > 0 else 1 - yq)
            rows.append({"tf": tf, "time": pd.Timestamp(t.ot[q]), "side": side, "held": bool(held), "right": fair,
                         "far": float(succ), "d_target": d_target, "d_fail": d_fail,
                         **{kk: (None if vv is None else bool(vv)) for kk, vv in f.items()}})
            j = q if c[q] > up[q] else q + 1                             # a touch that is also a pump starts a new sequence
    return rows


def run_bb_pause_why(cfg: Config, out_dir: Path) -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    tfs = {k: TF(resample(df5u, k)) for k in ("1h", "4h", "1D", "1W")}
    m = load_metrics(cfg.data_dir, cfg.symbol)
    E = pd.DataFrame([r for tf in ("1h", "4h", "1D") for r in events(tfs[tf], tfs[HTF[tf]], tfs["1D"], m, tf)])
    late = {"1h": pd.Timedelta(hours=30), "4h": pd.Timedelta(hours=120), "1D": pd.Timedelta(days=30)}
    E = E[E["right"].notna()].reset_index(drop=True)
    E["hold"] = E["time"] >= HOLDOUT
    E["res"] = ~E["hold"] & (E["time"].dt.year >= 2020) & (E["time"] < HOLDOUT - E["tf"].map(late))
    E.to_pickle(ROOT / "results" / "bb_pause_why.pkl")
    conds = [c for c in E.columns if ":" in c]
    L = ["# Why the middle-band hold pumps again, and why it sometimes fails", "",
         "Pump -> 3+ sideways closes above the middle band -> first touch of the middle band. **Hold** = the touch closes above "
         "the middle band; **fail** = at / below it. Mirrored for dumps. Outcomes: the **fair test** (1.5 ATR either way, coin "
         "flip 50%) and the trader's **far target** (hold: a new high above everything so far; fail: the sideways low; before a "
         "close 0.5 ATR beyond the middle band, within 30 candles). The far-target difference is shown raw and **at the same "
         "distances** (within groups of the same timeframe, distance to the target and distance to the failure level); only "
         "the same-distance column removes the geometry. **real** = p < 0.01 at the same distances and the holdout points the "
         "same way.", ""]
    for kind, hm in (("hold -> does it pump again?", True), ("fail -> does it dump?", False)):
        for scope, sm in (("1h + 4h + 1D together", None), ("4h", "4h"), ("1D", "1D")):
            g = E[E["held"] == hm] if sm is None else E[(E["held"] == hm) & (E["tf"] == sm)]
            res, hol = g[g["res"]].sort_values("time"), g[g["hold"]]
            L += [f"## {kind} · {scope}: {len(res)} cases 2020 - Oct 2025, **right {res['right'].mean():.0%}** (fair test); "
                  f"holdout {len(hol)}, right {hol['right'].mean():.0%}" if len(hol) else
                  f"## {kind} · {scope}: {len(res)} cases, right {res['right'].mean():.0%}", "",
                  f"Far target (the trader's definition): {res['far'].mean():.0%} "
                  + ("made a new high above everything so far before a close 0.5 ATR below the middle band" if hm else
                     "took out the sideways low before a close 0.5 ATR above the middle band") + ".", ""]
            L += cond_table(res, hol, conds)
    path = out_dir / "bb_pause_why.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


def strat_test(g: pd.DataFrame, cn: str, n_perm: int = 400):
    """Difference in 'far' (condition present minus absent) within groups of the same timeframe x distance to the target
    (quintile) x distance to the failure level (quintile), weighted by group size; p by shuffling the condition within the
    groups. Removes the geometry: a condition that only moves the close nearer the target or further from the failure level
    shows nothing here."""
    x = g[g[cn].notna()].copy()
    if len(x) < 60:
        return np.nan, np.nan
    x["cnd"] = x[cn].astype(bool)
    x["s"] = x["tf"] + "|" + x.groupby("tf")["d_target"].transform(lambda v: pd.qcut(v.rank(method="first"), 5, labels=False)).astype(str) \
        + "|" + x.groupby("tf")["d_fail"].transform(lambda v: pd.qcut(v.rank(method="first"), 5, labels=False)).astype(str)
    y = x["far"].to_numpy(float)
    grp = x["s"].to_numpy()
    idx = [np.nonzero(grp == u)[0] for u in np.unique(grp)]

    def diff(cv):
        num = den = 0.0
        for ii in idx:
            cc = cv[ii]
            if cc.all() or not cc.any():
                continue
            num += len(ii) * (y[ii][cc].mean() - y[ii][~cc].mean()); den += len(ii)
        return num / den if den else np.nan

    cv = x["cnd"].to_numpy()
    obs = diff(cv)
    if not np.isfinite(obs):
        return np.nan, np.nan
    rng = np.random.default_rng(3)
    cnt = 0
    for _ in range(n_perm):
        cp = cv.copy()
        for ii in idx:
            cp[ii] = rng.permutation(cp[ii])
        cnt += abs(diff(cp)) >= abs(obs) - 1e-12
    return obs, (cnt + 1) / (n_perm + 1)


def cond_table(res, hol, conds) -> list[str]:
    tab = []
    for cn in conds:
        a_, a0 = res[res[cn] == True], res[res[cn] == False]  # noqa: E712
        b_, b0 = hol[hol[cn] == True], hol[hol[cn] == False]  # noqa: E712
        if len(a_) < 15 or len(a0) < 15:
            continue
        d_fair = a_["right"].mean() - a0["right"].mean()
        pv_fair = shift_pvalue(res, cn) if len(res) >= 60 else np.nan
        d_far = a_["far"].mean() - a0["far"].mean()
        d_st, pv_st = strat_test(res, cn)
        d_h = (b_["far"].mean() - b0["far"].mean()) if len(b_) >= 5 and len(b0) >= 5 else np.nan
        real = ""
        if pv_st == pv_st and pv_st < 0.01 and d_h == d_h and np.sign(d_h) == np.sign(d_st):
            real = "yes"
        elif pv_st == pv_st and pv_st < 0.05 and (d_h != d_h or np.sign(d_h) == np.sign(d_st)):
            real = "likely"
        tab.append({"c": cn, "n": len(a_), "df": d_fair, "pf": pv_fair, "dfar": d_far, "dst": d_st, "pst": pv_st,
                    "nh": len(b_), "dh": d_h, "real": real})
    T = pd.DataFrame(tab).sort_values("dst") if tab else pd.DataFrame()
    if not len(T):
        return []
    f2 = lambda v: "" if v != v else f"{v * 100:+.0f} pts"  # noqa: E731
    fp = lambda v: "not tested (n < 60)" if v != v else f"{v:.3f}"  # noqa: E731
    return [_table(T, [("c", "condition at the touch", str), ("n", "cases with it", str),
                       ("df", "fair test: difference", f2), ("pf", "fair test: noise", fp),
                       ("dfar", "far target: raw difference", f2), ("dst", "far target: same distances", f2),
                       ("pst", "same distances: noise", fp), ("nh", "holdout cases with it", str),
                       ("dh", "holdout far difference (raw)", f2),
                       ("real", "real (p<0.01 at same distances, holdout agrees) / likely (p<0.05)", str)]), ""]

if __name__ == "__main__":
    from ..config import load_config
    print(run_bb_pause_why(load_config(ROOT / "config.yaml"), ROOT / "reports"))
