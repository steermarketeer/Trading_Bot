"""
The middle-band hold after a pump, on every coin we have (BTC, ETH, BNB, SOL, XRP, DOGE), 4h and daily: more cases,
above all on the daily where the concept looked strongest on ETH alone (61%, 44 cases).

Events and outcomes exactly as bot/study/bb_pause_why.py (pump -> 3+ sideways closes above the middle band -> first touch;
hold / fail; the fair 1.5 ATR test; the trader's far target with a failure level 0.5 ATR beyond the middle band). Coins
move together, so events on the same dates are not independent: confidence intervals and p-values come from a bootstrap
that resamples whole calendar months (all coins' events in a month stay together). Conditions are compared at the same
distances (groups: timeframe x distance quintiles, pooled across coins; distances are in ATR). The open-interest conditions are ETH only.
Research 2020 - Oct 2025 (each coin from its first data), holdout Nov 2025 on.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .bb_pause_why import HTF, events, load_metrics, strat_test
from .defs import TF
from .mtf import resample
from .sr2_run import _pct, _table

HOLDOUT = pd.Timestamp("2025-11-01")
COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]
LATE = {"4h": pd.Timedelta(hours=120), "1D": pd.Timedelta(days=30)}


def month_boot(g: pd.DataFrame, col: str, n: int = 2000, seed: int = 1):
    """Mean of col with a 90% interval and the share of resamples at or below 50% (one-sided p for 'above a coin flip')."""
    if g.empty:
        return np.nan, np.nan, np.nan, np.nan
    mon = g["time"].dt.to_period("M")
    groups = [x[col].to_numpy(float) for _, x in g.groupby(mon)]
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n):
        pick = rng.integers(0, len(groups), len(groups))
        v = np.concatenate([groups[i] for i in pick])
        means.append(v.mean())
    means = np.array(means)
    return g[col].mean(), np.quantile(means, 0.05), np.quantile(means, 0.95), float((means <= 0.5).mean())


def strat_boot(res: pd.DataFrame, cn: str, n: int = 400, min_mixed: int = 60, seed: int = 4):
    """Far-target difference (condition present minus absent) at the same distances: groups of timeframe x distance to
    the target (quintile) x distance to the failure level (quintile), pooled across coins (distances are in ATR), weighted
    by group size, needing >= min_mixed rows in groups that contain both cases. Two-sided p from a bootstrap of whole
    calendar months (coins move together, so a month's cases stay together)."""
    obs, _ = strat_test(res, cn, n_perm=0, min_mixed=min_mixed)
    if obs != obs:
        return np.nan, np.nan
    mon = res["time"].dt.to_period("M")
    groups = [x for _, x in res.groupby(mon)]
    rng = np.random.default_rng(seed)
    ds = []
    for _ in range(n):
        smp = pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))], ignore_index=True)
        d, _ = strat_test(smp, cn, n_perm=0, min_mixed=min_mixed)
        if d == d:
            ds.append(d)
    ds = np.array(ds)
    if len(ds) < n // 2:
        return obs, np.nan
    p = 2 * min((ds <= 0).mean(), (ds >= 0).mean())
    return obs, min(1.0, max(p, 1 / len(ds)))


def run_bb_pause_coins(cfg: Config, out_dir: Path) -> Path:
    rows = []
    empty_m = pd.DataFrame({"create_time": pd.Series(dtype="datetime64[ns]"), "sum_open_interest": pd.Series(dtype=float),
                            "count_long_short_ratio": pd.Series(dtype=float), "ls_med": pd.Series(dtype=float)})
    for sym in COINS:
        df5u, _ = load_klines_5m(cfg.data_dir, sym)
        tfs = {k: TF(resample(df5u, k)) for k in ("4h", "1D", "1W")}
        m = load_metrics(cfg.data_dir, sym) if sym == "ETHUSDT" else empty_m
        for tf in ("4h", "1D"):
            for r in events(tfs[tf], tfs[HTF[tf]], tfs["1D"], m, tf):
                r["coin"] = sym.replace("USDT", "")
                rows.append(r)
        print(sym, len(rows), flush=True)
    E = pd.DataFrame(rows)
    E = E[E["right"].notna()].reset_index(drop=True)
    E["hold"] = E["time"] >= HOLDOUT
    E["res"] = ~E["hold"] & (E["time"].dt.year >= 2020) & (E["time"] < HOLDOUT - E["tf"].map(LATE))
    E["tf_c"] = E["coin"] + "-" + E["tf"]                               # coin-timeframe label (not used as a stratum)
    E.to_pickle(ROOT / "results" / "bb_pause_coins.pkl")
    L = ["# The middle-band hold after a pump, on six coins (4h and daily)", "",
         "Same events and outcomes as `reports/bb_pause_why.md`. **right** = the fair test (1.5 ATR either way; a coin flip = "
         "50%). **far** = the trader's definition (hold: a new high above everything so far; fail: the sideways low; before a "
         "close 0.5 ATR beyond the middle band; its rate mostly reflects how far the target and the failure level are, so it is not "
         "an edge). 90% intervals and **p** from a bootstrap of whole calendar months (coins move together). Research 2020 - Oct "
         "2025, holdout Nov 2025 on.", ""]
    rows = []
    for tf in ("1D", "4h"):
        for kind, hm in (("hold -> pump again", True), ("fail -> dump", False)):
            for coin in ["all six"] + [c.replace("USDT", "") for c in COINS]:
                g = E[(E["tf"] == tf) & (E["held"] == hm)]
                if coin != "all six":
                    g = g[g["coin"] == coin]
                res, hol = g[g["res"]], g[g["hold"]]
                mu, lo, hi, p = month_boot(res, "right")
                rows.append({"tf": tf, "kind": kind, "coin": coin, "n": len(res), "right": mu, "lo": lo, "hi": hi,
                             "p": p if coin == "all six" else np.nan, "far": res["far"].mean() if len(res) else np.nan,
                             "nh": len(hol), "rh": hol["right"].mean() if len(hol) else np.nan})
    T = pd.DataFrame(rows)
    f1 = lambda v: "" if v != v else f"{v:.0%}"  # noqa: E731
    L += ["## Does the close at the middle band tell the direction?", "", _table(T, [
        ("tf", "timeframe", str), ("kind", "event", str), ("coin", "coin", str), ("n", "cases 2020-25", str),
        ("right", "right (fair test)", f1), ("lo", "90% low", f1), ("hi", "90% high", f1),
        ("p", "chance it is not above 50%", lambda v: "" if v != v else f"{v:.3f}"), ("far", "far target reached", f1),
        ("nh", "holdout cases", str), ("rh", "holdout right", f1)]), ""]
    conds = [c for c in E.columns if ":" in c and not c.startswith("liquidity")]
    n_tests, pvals = [0], []
    cond_lines = []
    for tf in ("1D", "4h"):
        for kind, hm in (("hold -> pump again", True), ("fail -> dump", False)):
            g = E[(E["tf"] == tf) & (E["held"] == hm)].copy()
            res, hol = g[g["res"]].sort_values("time"), g[g["hold"]]
            tab = []
            for cn in conds:
                a_, a0 = res[res[cn] == True], res[res[cn] == False]  # noqa: E712
                if len(a_) < 20 or len(a0) < 20:
                    continue
                d, pv = strat_boot(res, cn)
                n_tests[0] += 1
                pvals.append(pv)
                dh = strat_test(hol, cn, n_perm=0, min_n=20, min_mixed=20)[0]
                tab.append({"c": cn, "n": len(a_), "raw": a_["far"].mean() - a0["far"].mean(), "d": d, "pv": pv, "dh": dh,
                            "fair": a_["right"].mean() - a0["right"].mean()})
            if tab:
                D = pd.DataFrame(tab).sort_values("d")
                f2 = lambda v: "" if v != v else f"{v * 100:+.0f} pts"  # noqa: E731
                cond_lines += [f"## {tf} · {kind}: conditions, all coins ({len(res)} cases)", "",
                      _table(D, [("c", "condition", str), ("n", "cases with it", str), ("fair", "fair test: difference", f2),
                                 ("raw", "far: raw difference", f2), ("d", "far: same distances", f2),
                                 ("pv", "noise (month bootstrap)", lambda v: "not tested (too few mixed rows)" if v != v else f"{v:.3f}"),
                                 ("dh", "holdout, same distances", f2)]), ""]
    pv = np.array([x for x in pvals if x == x])
    m = len(pv)
    bh = 0
    if m:
        srt = np.sort(pv)
        ok = srt <= 0.05 * np.arange(1, m + 1) / m
        bh = int(np.nonzero(ok)[0].max() + 1) if ok.any() else 0
    L += [f"## Conditions at the same distances (all coins pooled; groups of timeframe x distance quintiles; p by a bootstrap of "
          f"calendar months)", "",
          f"**{m} conditions were tested across these tables; {int((pv < 0.05).sum())} have p < 0.05 (about {0.05 * m:.0f} expected "
          f"by chance); {bh} survive a false-discovery correction (Benjamini-Hochberg, 5%).** These conditions were first searched on "
          f"ETH, which is part of the pool, so this is not an independent replication.", ""] + cond_lines
    L += ["Audit: rounds 15 - 16 (see docs/concepts/bollinger_middle_band_hold.md)."]
    path = out_dir / "bb_pause_coins.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_bb_pause_coins(load_config(ROOT / "config.yaml"), ROOT / "reports"))
