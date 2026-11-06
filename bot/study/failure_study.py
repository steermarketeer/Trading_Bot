"""
Failure study of the chosen version (v3.1 + journal filters + 0.786 bounce stop + bounce target 5 : 1): every loss with
every candidate reason, and whether each reason holds out across ALL trades (losers and winners, both periods).

Reasons known at the entry (actionable):
  ceiling        a strong S/R zone or an untaken 4h swing between entry + 0.15R and the trade's own target
  trendline      a valid trendline against the trade between entry and target (1h or 4h; fixes.trendline_in_way)
  daily against  the daily close on the wrong side of its EMA 200
  weekly no room the weekly is stretched in the trade's direction (at its band, RSI >= 70, or above its older highs)
  vol shock      the signal candle's range >= 2.5 x the ATR before it
  liq at stop    untaken liquidity within 0.5R beyond the stop (defs_review)
  stretched      1h RSI > 70 and close beyond the 1h band in the trade's direction at entry (defs_review)
  vertical day   the daily candle moved > 2 ATR in the trade's direction (defs_review)
  pause against  a daily pump the other way in the last 20 days with every close since on that side of the middle band
  top failure    a top-failure trigger (sweep / failed pushes at a daily or weekly pool; bot/study/topfail) AGAINST the
  against        trade on the 4h within the 48 hours before entry
  3 failures     a three-failures 'last push' trigger against the trade on the 1h within 6 hours before entry
  weak break     breakouts without the strong breaking candle (body >= 60% of its range, range >= 1.5 ATR, volume >= 1.2x
                 its 20-candle average; the audited BQ flag of bot/study/fixes.py)
Reasons seen only after the entry (diagnostic):
  4h against     the first 4h close after entry is back beyond the entry price (defs_review unconfirmed_4h)
  gave back      the trade reached >= +1R and was then stopped (descriptive: by construction every such trade is a loss,
                 so its p-value is not a test; it measures how much of the loss is exit management)
Holds out = among the research trades the win % with the reason is lower than without (Fisher exact test p < 0.05) and
the holdout points the same way. 162 trades: this shows direction, not proof. Research 2022 - Oct 2025, holdout Nov 2025 on.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..live.v3 import TARGET
from ..ml.targets import account, stats
from .defs import TF
from .fibliq import Swings
from .fixes import trendline_in_way
from .indicators import ema, rsi
from .levels import _level_table, strong_levels
from .mtf import resample
from .sr2_run import _pct, _table
from .three_failures import setups as tf_setups
from .topfail import detect

HOLDOUT = pd.Timestamp("2025-11-01")
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
TFN = {2: "2h", 4: "4h", 24: "1D"}
ENTRY_REASONS = ["ceiling", "trendline", "daily against", "weekly no room", "vol shock", "liq at stop", "stretched",
                 "vertical day", "pause against", "top failure against", "3 failures against", "weak break"]
AFTER_REASONS = ["4h against", "gave back"]


def build(cfg: Config) -> pd.DataFrame:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    O, H, L_ = (df5n[x].to_numpy(float) for x in ("open", "high", "low"))
    t5 = df5n["open_time"].to_numpy()
    tf = {k: TF(resample(df5u, k)) for k in ("1h", "2h", "4h", "1D", "1W")}
    t4, d1, w1, h1 = tf["4h"], tf["1D"], tf["1W"], tf["1h"]
    d200 = ema(pd.Series(d1.c), 200).to_numpy(float)
    rw = rsi(pd.Series(w1.c)).to_numpy(float)
    table = _level_table(df5u)
    sw4 = Swings(df5u, "4h")
    pools = {"1D": Swings(df5u, "1D"), "1W": Swings(df5u, "1W")}
    topf = {s: np.array([t4.ct[e.j] for e in detect(t4, pools, s, {"1D": 400, "1W": 104})], dtype="datetime64[ns]") for s in (1, -1)}
    tfail = {s: np.array([h1.ct[j] for j, _, _, k in tf_setups(h1, s) if k == "last push"], dtype="datetime64[ns]") for s in (1, -1)}
    F = pd.read_pickle(ROOT / "results" / "fixes.pkl")
    F = F[(F["entry"] == "now") & (F["exit"] == "none") & (F["fib"] == "S786")].reset_index(drop=True)
    X = pd.read_pickle(ROOT / "results" / "defs_review.pkl").reset_index(drop=True).set_index("entry_time")
    rows = []
    for r in F.itertuples():
        et, d = pd.Timestamp(r.entry_time), int(r.direction)
        x = X.loc[et]
        st = int(np.searchsorted(t5, np.datetime64(et)))
        e = O[st]
        rk = float(x["risk"])
        # the trade's own stop / target under the chosen version (0.786 stop for bounces, 5 : 1)
        s_ = e - d * rk
        if r.setup == "1D bounce":
            s_ = e - d * r.stop_pct * e
        risk = abs(e - s_)
        tg = e + d * TARGET[r.setup] * risk
        o = lambda v: v if d > 0 else -v  # noqa: E731
        j4, jd, jw = t4.closed_before(et) - 1, d1.closed_before(et) - 1, w1.closed_before(et) - 1
        ts = tf[TFN[int(round(pd.Timedelta(r.tf) / pd.Timedelta(hours=1)))]]
        js = ts.closed_before(et) - 1
        lv = np.array(list(strong_levels(table, et.tz_localize("UTC"))) + list(sw4.untaken(et, "H" if d > 0 else "L")))
        ceiling = bool(len(lv) and np.any((o(lv - e) > 0.15 * risk) & (o(tg - lv) > 0)))
        hiw, upw = (w1.h[jw], w1.up[jw]) if d > 0 else (-w1.l[jw], -w1.lo[jw])
        old_hi = (w1.h[jw - 52:jw - 4].max() if d > 0 else -w1.l[jw - 52:jw - 4].min()) if jw >= 52 else np.nan
        rwo = rw[jw] if d > 0 else 100 - rw[jw]
        no_room = (np.isfinite(upw) and hiw >= upw) or (np.isfinite(rwo) and rwo >= 70) or (old_hi == old_hi and o(w1.c[jw]) >= old_hi)
        od = -d
        cc, band_o, mid_o = od * d1.c, od * (d1.up if od > 0 else d1.lo), od * d1.mid
        pumps = [k for k in range(max(0, jd - 20), jd + 1) if np.isfinite(band_o[k]) and cc[k] > band_o[k]]
        pause = bool(pumps) and pumps[-1] < jd and bool(np.all(cc[pumps[-1] + 1:jd + 1] > mid_o[pumps[-1] + 1:jd + 1]))
        et64 = np.datetime64(et)
        tf_ag = topf[1] if d > 0 else topf[-1]                           # top failures (side +1) are against longs
        f3 = tfail[1] if d > 0 else tfail[-1]
        weak = bool(r.setup != "1D bounce" and not r.BQ)                 # the audited strong-breaking-candle flag
        # after-entry: did the trade reach +1R before the stop?
        end = int(np.searchsorted(t5, np.datetime64(pd.Timestamp(r.exit_time))))
        mfe = (o(H[st:end + 1] - e).max() if d > 0 else o(-L_[st:end + 1] + e).max()) / risk if end > st else 0.0
        hi_run = ((H[st:end + 1] - e) if d > 0 else (e - L_[st:end + 1])).max() / risk if end > st else 0.0
        rows.append({"entry_time": et, "setup": r.setup, "dir": "long" if d > 0 else "short", "net": r.net, "kind": r.kind,
                     "exit_time": r.exit_time, "stop_pct": r.stop_pct, "decision_time": r.decision_time, "hold": r.hold,
                     "ceiling": ceiling, "trendline": bool(trendline_in_way(h1, et, e, tg, d) or trendline_in_way(t4, et, e, tg, d)),
                     "daily against": bool(np.isfinite(d200[jd]) and o(d1.c[jd] - d200[jd]) < 0),
                     "weekly no room": bool(no_room), "vol shock": bool((ts.h[js] - ts.l[js]) >= 2.5 * ts.a[js - 1]),
                     "liq at stop": bool(x["liq_under_stop"]), "stretched": bool(x["stretched"]),
                     "vertical day": bool(x["vertical_day"]), "pause against": pause,
                     "top failure against": bool(np.any((tf_ag <= et64) & (tf_ag > et64 - np.timedelta64(48, "h")))),
                     "3 failures against": bool(np.any((f3 <= et64) & (f3 > et64 - np.timedelta64(6, "h")))),
                     "weak break": bool(weak), "4h against": bool(x["unconfirmed_4h"]),
                     "gave back": bool(hi_run >= 1.0 and r.kind == "stop")})
    return pd.DataFrame(rows)


def run_failure_study(cfg: Config, out_dir: Path) -> Path:
    D = build(cfg)
    D.to_pickle(ROOT / "results" / "failure_study.pkl")
    res = ~D["hold"] & (D["exit_time"] < HOLDOUT)
    f2 = lambda v: "" if v != v else f"{v:+.2f}"  # noqa: E731
    rows = []
    for rs in ENTRY_REASONS + AFTER_REASONS:
        for per, pm in (("2022 - Oct 2025", res), ("holdout", D["hold"])):
            g = D[pm]
            w, l = g[g["net"] > 0], g[g["net"] <= 0]
            on, off = g[g[rs]], g[~g[rs]]
            p = np.nan
            if per != "holdout" and len(on) and len(off):
                p = fisher_exact([[int((on["net"] <= 0).sum()), int((on["net"] > 0).sum())],
                                  [int((off["net"] <= 0).sum()), int((off["net"] > 0).sum())]], alternative="greater")[1]
            rows.append({"rs": rs, "per": per, "lshare": l[rs].mean() if len(l) else np.nan, "wshare": w[rs].mean() if len(w) else np.nan,
                         "n": len(on), "won": (on["net"] > 0).mean() if len(on) else np.nan, "aon": on["net"].mean() if len(on) else np.nan,
                         "woff": (off["net"] > 0).mean() if len(off) else np.nan, "aoff": off["net"].mean() if len(off) else np.nan,
                         "p": p, "sumR": on["net"].sum()})
    R = pd.DataFrame(rows)
    # does the reason hold out? research p < 0.05 and holdout win % with < without
    holds = []
    for rs in ENTRY_REASONS + AFTER_REASONS:
        a = R[(R["rs"] == rs) & (R["per"] != "holdout")].iloc[0]
        b = R[(R["rs"] == rs) & (R["per"] == "holdout")].iloc[0]
        hv = (a["p"] == a["p"] and a["p"] < 0.05 and b["won"] == b["won"] and b["woff"] == b["woff"] and b["won"] < b["woff"])
        holds.append({"rs": rs, "holds": "yes" if hv else ("research only" if a["p"] == a["p"] and a["p"] < 0.05 else "")})
    Hd = pd.DataFrame(holds).set_index("rs")["holds"]
    R["holds"] = R["rs"].map(Hd)
    L = ["# Failure study of the chosen version (bounces 5 : 1)", "",
         f"{len(D)} ETH trades: {int(res.sum())} in 2022 - Oct 2025, {int(D['hold'].sum())} in the holdout. **win % = profit after costs.** "
         "For every candidate reason: how many losers vs winners carry it, win % with vs without, Fisher's exact test on "
         "2022-25 (one-sided: the reason lowers the win %), and the holdout. **holds** = p < 0.05 and the holdout agrees; "
         "162 trades show direction, not proof.", "",
         "## Each reason, across all trades", "",
         _table(R, [("rs", "reason", str), ("per", "period", str), ("lshare", "losers with it", _pct), ("wshare", "winners with it", _pct),
                    ("n", "trades with it", str), ("won", "win % with", _pct), ("aon", "avg R with", f2), ("woff", "win % without", _pct),
                    ("aoff", "avg R without", f2), ("sumR", "total R of those trades", f2),
                    ("p", "p (research)", lambda v: "" if v != v else f"{v:.3f}"), ("holds", "holds out", str)]), ""]
    # skip effect for the reasons that hold
    srows = []
    for rs in [k for k, v in Hd.items() if v == "yes" and k in ENTRY_REASONS]:
        for per, pm in (("2022 - Oct 2025", res), ("holdout", D["hold"])):
            for lab, m in (("all trades", pm), (f"skip '{rs}'", pm & ~D[rs])):
                g = D[m].reset_index(drop=True)
                s_ = stats(g["net"].to_numpy()); eq, dd = account(g, "net", "exit_time", RISK) if len(g) else (np.nan, np.nan)
                srows.append({"rs": rs, "per": per, "lab": lab, **s_, "eq": eq, "dd": dd})
    if srows:
        L += ["## If the bot had skipped the reasons that hold out", "", _table(pd.DataFrame(srows), [
            ("rs", "reason", str), ("per", "period", str), ("lab", "", str), ("n", "trades", str), ("win", "win %", _pct),
            ("avg", "avg R", f2), ("pf", "profit factor", lambda v: f"{v:.2f}"), ("eq", "account", lambda v: f"{v:.2f}x"),
            ("dd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    else:
        L += ["## No entry-time reason holds out in both periods.", ""]
    # every loss with its reasons
    Ls = D[D["net"] <= 0].sort_values("net")
    L += ["## Every loss, with its reasons (for the discussion)", "", "| entry | setup | side | R | exit | reasons at entry | after entry |", "|---|---|---|---|---|---|---|"]
    for r in Ls.itertuples():
        rr = ", ".join(k for k in ENTRY_REASONS if D.loc[r.Index, k])
        aa = ", ".join(k for k in AFTER_REASONS if D.loc[r.Index, k])
        L.append(f"| {r.entry_time:%Y-%m-%d %H:%M} | {r.setup} | {r.dir} | {r.net:+.2f} | {r.kind} | {rr or '-'} | {aa or '-'} |")
    L += ["", "Audit: pending."]
    path = out_dir / "failure_study.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    from ..config import load_config
    print(run_failure_study(load_config(ROOT / "config.yaml"), ROOT / "reports"))
