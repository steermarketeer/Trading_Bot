"""
Why do v3.1 trades fail? Liquidation map + low-volume study (every losing trade gets a reason).

Idea: price travels to where leveraged traders will be liquidated, and it travels fastest where volume is thin.

Estimated liquidation map (no open-interest history is available here, so it is built from volume; known only
from candles CLOSED before the entry):
  every 1h candle of the last 30 days opens positions at its typical price: longs = taker-buy volume,
  shorts = taker-sell volume, spread over leverage 10x / 25x / 50x / 100x (shares 35 / 35 / 20 / 10 %).
  liquidation price: long p*(1 - 1/L + 0.4%), short p*(1 + 1/L - 0.4%)  (0.4% ~ maintenance margin + fees).
  A level is removed once price has traded through it (those traders are already liquidated).
  Weights are a share of the 30-day volume.
Per trade (in R from the entry; "own side" = traders positioned like us, whose liquidations sit beyond our stop):
  own_beyond_stop  own-side liquidations 0-1R beyond our stop       (the stop-hunt magnet)
  own_in_risk      own-side liquidations between entry and stop
  opp_to_target    opposite-side liquidations between entry and target (the fuel for our move)
  pull             opp_to_target / (own_in_risk + own_beyond_stop)  (< 1: the bigger magnet is against us)
  thin_stop        volume (30-day profile) between entry and 1.5R beyond... the stop side vs a typical price bin
  thin_target      the same between entry and target
After the trade (diagnosis only, never used for a decision): did a stopped trade come back to the entry / target
within the time limit (stop hunt), how deep the hunt went, did it end at the biggest liquidation cluster.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..ml.targets import MAX_TF_BARS, account, label_paths, _funding_cum, stats
from .flow import load_flow
from .sr2_run import _pct, _table

LEV = np.array([10.0, 25.0, 50.0, 100.0])
LEV_SHARE = np.array([0.35, 0.35, 0.20, 0.10])
MM = 0.004
WINDOW_H = 720
HOLDOUT = pd.Timestamp("2025-11-01")
FIVE = pd.Timedelta(minutes=5)
TGT = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 3.0}
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
BIN = 0.25  # R


def _hourly(fl: pd.DataFrame) -> pd.DataFrame:
    g = fl.set_index("open_time").resample("1h", label="left", closed="left")
    h = pd.DataFrame({"high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "volume": g["volume"].sum(), "buy": g["taker_buy_base"].sum()}).dropna()
    h["tp"] = (h["high"] + h["low"] + h["close"]) / 3
    return h.reset_index()


def liq_levels(hb: dict, entry_time: pd.Timestamp, mode: str = "volume"):
    """Untaken long / short liquidation levels (price, weight) known at entry_time.
    mode "volume": positions = taker buy / sell volume of each 1h candle (estimate).
    mode "oi":     positions = real open-interest INCREASE of each 1h candle (Binance, USD), split long / short by
                   that candle's taker-buy share; open-interest decreases shrink all earlier positions pro rata.
    Weights are a share of the 30-day volume ("volume") or of the open interest at entry ("oi")."""
    n = int(np.searchsorted(hb["t"], (entry_time - pd.Timedelta(hours=1)).to_datetime64(), side="right"))
    k0 = max(0, n - WINDOW_H)
    if n - k0 < 100:
        return None
    L, H, TP, V, B = (hb[x][k0:n] for x in ("low", "high", "tp", "volume", "buy"))
    suf_min = np.r_[np.minimum.accumulate(L[::-1])[::-1][1:], np.inf]
    suf_max = np.r_[np.maximum.accumulate(H[::-1])[::-1][1:], -np.inf]
    if mode == "oi":
        oi = hb["oi"][k0 - 1:n] if k0 > 0 else np.r_[np.nan, hb["oi"][k0:n]]
        if np.isnan(oi[1:]).mean() > 0.2:
            return None
        oi = pd.Series(oi).ffill().to_numpy()
        d_oi = np.diff(oi)
        keep = np.where(d_oi < 0, oi[1:] / oi[:-1], 1.0)               # share of positions left after closes
        keep = np.where(np.isfinite(keep), keep, 1.0)
        later = np.r_[np.cumprod(keep[::-1])[::-1][1:], 1.0]           # product over candles AFTER k
        opened = np.where(d_oi > 0, d_oi, 0.0) * later
        share = np.where(V > 0, B / V, 0.5)
        lw_tot, sw_tot, tot = opened * TP * share, opened * TP * (1 - share), oi[-1] * TP[-1]  # ETH -> USD
    else:
        lw_tot, sw_tot, tot = B, V - B, V.sum()
    lv = TP[:, None] * (1 - 1 / LEV + MM)[None, :]
    sv = TP[:, None] * (1 + 1 / LEV - MM)[None, :]
    lw = np.nan_to_num(lw_tot)[:, None] * LEV_SHARE[None, :]
    sw = np.nan_to_num(sw_tot)[:, None] * LEV_SHARE[None, :]
    la = suf_min[:, None] > lv
    sa = suf_max[:, None] < sv
    return (lv[la], lw[la] / tot), (sv[sa], sw[sa] / tot)


def load_oi_hourly(data_dir, symbol: str, hours: pd.Series) -> np.ndarray:
    """Binance open interest (ETH) at each 1h candle's CLOSE (last 5m snapshot at or before open + 1h)."""
    p = Path(data_dir) / "metrics" / f"{symbol}_metrics_5m.csv"
    m = pd.read_csv(p, usecols=["create_time", "sum_open_interest"])
    m["create_time"] = pd.to_datetime(m["create_time"]).dt.as_unit("ns")
    m = m.dropna().sort_values("create_time")
    q = pd.DataFrame({"close": (pd.to_datetime(hours) + pd.Timedelta(hours=1)).dt.as_unit("ns")})
    r = pd.merge_asof(q, m, left_on="close", right_on="create_time", direction="backward",
                      tolerance=pd.Timedelta(minutes=30))
    return r["sum_open_interest"].to_numpy(float)


def validate_map(hb: dict, data_dir, mode: str) -> dict:
    """Does the map predict REAL liquidations? Per UTC day (Coinalyze, Binance ETHUSDT perp): liquidation weight the
    map had in that day's range at 00:00 vs actual long / short liquidations (USD). Spearman correlations, also
    for the day's range alone (a map must beat 'big moves liquidate more')."""
    a = pd.read_csv(Path(data_dir) / "coinalyze" / "eth_liq_daily.csv", parse_dates=["time"])
    a = a[a["market"] == "binance_usdt"].set_index("time")
    hdf = pd.DataFrame({"t": hb["t"], "high": hb["high"], "low": hb["low"]}).set_index("t")
    day = hdf.resample("1D").agg({"high": "max", "low": "min"}).dropna()
    rows = []
    for t, r in day.iterrows():
        if t not in a.index:
            continue
        lv = liq_levels(hb, pd.Timestamp(t), mode)
        if lv is None:
            continue
        (lp, lw), (sp, sw) = lv
        mid = hb["tp"][max(0, int(np.searchsorted(hb["t"], t.to_datetime64())) - 1)]
        rows.append({"pred_long": lw[lp >= r["low"]].sum(), "pred_short": sw[sp <= r["high"]].sum(),
                     "down": mid - r["low"], "up": r["high"] - mid,
                     "act_long": a.at[t, "l"], "act_short": a.at[t, "s"]})
    v = pd.DataFrame(rows)
    sp_ = lambda x, y: float(v[x].rank().corr(v[y].rank()))  # noqa: E731
    return {"days": len(v), "long_map": sp_("pred_long", "act_long"), "long_move": sp_("down", "act_long"),
            "short_map": sp_("pred_short", "act_short"), "short_move": sp_("up", "act_short")}


def trade_features(tr: pd.DataFrame, hb: dict, fl5: pd.DataFrame, mode: str = "volume") -> pd.DataFrame:
    t5 = fl5["open_time"].to_numpy()
    TP5, V5 = fl5["tp"].to_numpy(float), fl5["volume"].to_numpy(float)
    rows = []
    for idx, r in tr.iterrows():
        e, rk, d, T = float(r["px"]), float(r["risk"]), int(r["direction"]), TGT[r["setup"]]
        lv = liq_levels(hb, pd.Timestamp(r["decision_time"]), mode)
        out = {"trade": idx}
        if lv is None:
            rows.append(out)
            continue
        (lp, lw), (sp, sw) = lv
        own_p, own_w, opp_p, opp_w = (lp, lw, sp, sw) if d > 0 else (sp, sw, lp, lw)
        own_r, opp_r = (own_p - e) * d / rk, (opp_p - e) * d / rk
        out["own_in_risk"] = own_w[(own_r < 0) & (own_r >= -1)].sum()
        out["own_beyond_stop"] = own_w[(own_r < -1) & (own_r >= -2)].sum()
        out["own_within_3r"] = own_w[(own_r < 0) & (own_r >= -3)].sum()
        out["opp_to_target"] = opp_w[(opp_r > 0) & (opp_r <= T)].sum()
        out["opp_within_3r"] = opp_w[(opp_r > 0) & (opp_r <= 3)].sum()
        out["pull"] = out["opp_to_target"] / max(out["own_in_risk"] + out["own_beyond_stop"], 1e-9)
        # heaviest own-side cluster beyond the stop (0.25R bins, 1-3R below entry)
        b = np.floor(own_r[(own_r < -1) & (own_r >= -3)] / BIN)
        if len(b):
            ws = pd.Series(own_w[(own_r < -1) & (own_r >= -3)]).groupby(b).sum()
            out["own_cluster_r"], out["own_cluster_w"] = (ws.idxmax() + 0.5) * BIN, ws.max()
        else:
            out["own_cluster_r"], out["own_cluster_w"] = math.nan, 0.0
        # volume profile, last 30 days of 5m candles before the entry
        end = int(np.searchsorted(t5, np.datetime64(pd.Timestamp(r["decision_time"])), side="left"))
        st = max(0, end - WINDOW_H * 12)
        pr = (TP5[st:end] - e) * d / rk
        vb = pd.Series(V5[st:end]).groupby(np.floor(pr / BIN)).sum()
        vb = vb[(vb.index >= -12) & (vb.index < 16)]
        typ = vb.median() if len(vb) else math.nan
        stop_bins = vb.reindex(np.arange(-6, 0), fill_value=0.0)        # entry .. 1.5R beyond the stop
        tgt_bins = vb.reindex(np.arange(0, int(T / BIN)), fill_value=0.0)
        out["thin_stop"] = stop_bins.mean() / typ if typ > 0 else math.nan
        out["thin_target"] = tgt_bins.mean() / typ if typ > 0 else math.nan
        rows.append(out)
    return pd.DataFrame(rows).set_index("trade")


def after_stop(tr: pd.DataFrame, df5n: pd.DataFrame) -> pd.DataFrame:
    """Diagnosis only: what price did after a stop-out."""
    t5 = df5n["open_time"].to_numpy()
    O, H, Lw, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    rows = []
    for idx, r in tr.iterrows():
        T = TGT[r["setup"]]
        out = {"trade": idx}
        if r[f"hit_{T:g}"] == 1 or r[f"R_{T:g}"] > -0.999:
            rows.append(out)
            continue
        d, e, rk = int(r["direction"]), float(r["px"]), float(r["risk"])
        bpt = int(pd.Timedelta(r["tf"]) / FIVE)
        st = int(np.searchsorted(t5, pd.Timestamp(r["decision_time"]).to_datetime64()))
        end = st + MAX_TF_BARS * bpt
        xi = int(np.searchsorted(t5, (pd.Timestamp(r[f"exit_{T:g}"]) - FIVE).to_datetime64()))
        h, l = H[xi + 1:end], Lw[xi + 1:end]                          # candles AFTER the stop candle
        l_stop = Lw[xi] if d > 0 else -H[xi]
        if d < 0:
            h, l = -l, -h
            e = -e
        back_e = np.flatnonzero(h >= e)
        out["came_back_entry"] = int(len(back_e) > 0)
        out["came_back_target"] = int((h >= e + T * rk).any())
        upto = back_e[0] + 1 if len(back_e) else len(l)
        low = min(l_stop, l[:upto].min()) if upto > 0 else l_stop
        out["hunt_depth_r"] = (e - rk - low) / rk                     # how far beyond the stop before turning
        sc = int(np.searchsorted(t5, (pd.Timestamp(r[f"exit_{T:g}"]) - FIVE).to_datetime64()))
        cl = C[sc] if d > 0 else -C[sc]
        out["wick_stop"] = int(cl > e - rk)                             # stop candle closed back on our side
        rows.append(out)
    return pd.DataFrame(rows).set_index("trade")


def reasons(X: pd.DataFrame, cut: dict) -> pd.DataFrame:
    """Pre-trade reasons (all known at the entry). Thresholds = research terciles / fixed values."""
    R = pd.DataFrame(index=X.index)
    R["liquidation magnet just beyond the stop"] = X["own_beyond_stop"] >= cut["own_beyond_stop"]
    R["bigger liquidation magnet against us"] = X["pull"] < 1
    R["thin volume toward the stop"] = X["thin_stop"] < 0.7
    R["little liquidation fuel to the target"] = X["opp_to_target"] <= cut["opp_to_target"]
    R["higher timeframe against (1D structure / weekly trend / 1D pattern)"] = \
        (X["st_1D"] < 0) | (X["wtrend"] < 0) | (X["pat_1D"] < 0)
    R["stop inside normal noise (< 1 ATR)"] = X["x_atr_r"] > 1
    return R


def run_liquidation_study(cfg: Config, out_dir: Path, mode: str = "oi") -> Path:
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    fl = load_flow(cfg.data_dir, cfg.symbol)
    hb_df = _hourly(fl)
    hb = {"t": hb_df["open_time"].to_numpy()} | {c: hb_df[c].to_numpy(float) for c in ("low", "high", "tp", "volume", "buy")}
    hb["oi"] = load_oi_hourly(cfg.data_dir, cfg.symbol, hb_df["open_time"])
    val = {m: validate_map(hb, cfg.data_dir, m) for m in ("volume", "oi")}
    X = pd.read_pickle(ROOT / "results" / "ml_targets.pkl")
    X.attrs = {}
    F = trade_features(X, hb, fl, mode)
    A = after_stop(X, df5n)
    X = X.drop(columns=[c for c in list(F.columns) + list(A.columns) if c in X.columns]).join(F).join(A)
    X["loss"] = X["net_fixed"] <= 0
    res = ~X["hold"]
    cut = {"own_beyond_stop": X.loc[res, "own_beyond_stop"].quantile(2 / 3),
           "opp_to_target": X.loc[res, "opp_to_target"].quantile(1 / 3)}
    R = reasons(X, cut)
    X.join(R).to_pickle(ROOT / "results" / f"liquidation_study_{mode}.pkl")
    loss, win = X["loss"], ~X["loss"]
    L = ["# Why trades fail: liquidations and thin volume", "",
         f"All {len(X)} v3.1 trades (2022 - Oct 2026; {int(loss.sum())} losers after costs). Liquidation map built "
         + ("from REAL Binance open interest (5m, increases = new positions, split long/short by taker buys)"
            if mode == "oi" else "from volume (estimate)") + ", using only candles closed before entry.", "",
         "## 0. Does the map predict real liquidations? (Coinalyze, Binance ETHUSDT, per day)", "",
         "Spearman rank correlation with actual liquidations (USD). 'move only' = the day's move alone; "
         "a useful map must beat it.", "",
         _table(pd.DataFrame([{"map": k, **v} for k, v in val.items()]), [
             ("map", "map built from", str), ("days", "days", str),
             ("long_map", "long liqs: map", lambda v: f"{v:.2f}"), ("long_move", "long liqs: move only", lambda v: f"{v:.2f}"),
             ("short_map", "short liqs: map", lambda v: f"{v:.2f}"),
             ("short_move", "short liqs: move only", lambda v: f"{v:.2f}")]), ""]
    # 1. what happened after the stop
    st = X[X["came_back_entry"].notna()]
    L += ["## 1. What price did after stopping us out", "",
          f"- stopped trades: **{len(st)}**",
          f"- price came back to our entry within the time limit: **{st['came_back_entry'].mean():.0%}**",
          f"- price went on to reach our original target: **{st['came_back_target'].mean():.0%}** "
          "(we were right on direction, wrong on the stop)",
          f"- stop candle closed back on our side (wick stop): **{st['wick_stop'].mean():.0%}**",
          f"- median hunt depth beyond our stop before turning back: **{st.loc[st['came_back_entry'] == 1, 'hunt_depth_r'].median():.2f}R**", ""]
    hb_ok = st["came_back_entry"] == 1
    near = (st["hunt_depth_r"] + 1 - (-st["own_cluster_r"])).abs() <= 0.5   # hunt extreme within 0.5R of the cluster
    L += [f"- of the hunts that came back, the turn happened within 0.5R of the biggest estimated long/short "
          f"liquidation cluster in **{near[hb_ok].mean():.0%}** of cases", ""]
    # 2. reasons: losers vs winners
    rows = []
    for c in R.columns:
        for per, pm in (("research", res), ("holdout", ~res)):
            rows.append({"reason": c, "period": per, "loss_share": R.loc[loss & pm, c].mean(),
                         "win_share": R.loc[win & pm, c].mean(),
                         "win_if": (~X.loc[pm & R[c], "loss"]).mean(), "win_not": (~X.loc[pm & ~R[c], "loss"]).mean(),
                         "n_if": int((pm & R[c]).sum())})
    L += ["## 2. Reasons known BEFORE the trade: how often in losers vs winners", "",
          "A reason only explains losses if it is clearly more common in losers than in winners.", "",
          _table(pd.DataFrame(rows), [("reason", "reason", str), ("period", "period", str),
                                      ("loss_share", "in losers", _pct), ("win_share", "in winners", _pct),
                                      ("n_if", "trades with it", str), ("win_if", "win % with", _pct),
                                      ("win_not", "win % without", _pct)]), ""]
    # 3. primary reason per loser
    known = R.columns.tolist()
    n_reasons = R[loss].sum(axis=1)
    L += ["## 3. Every losing trade: how many reasons it had", "",
          _table(pd.DataFrame({"k": n_reasons.value_counts().sort_index().index,
                               "n": n_reasons.value_counts().sort_index().values}),
                 [("k", "reasons found", str), ("n", "losing trades", str)]), "",
          f"Winners with 0 reasons: {(R[win].sum(axis=1) == 0).mean():.0%}; losers with 0 reasons: "
          f"{(n_reasons == 0).mean():.0%}.", ""]
    # 4. avoid rules
    rows = []
    for per, pm in (("research", res), ("holdout", ~res)):
        base = X[pm]
        s = stats(base["net_fixed"].to_numpy())
        eq, mdd = account(base, "net_fixed", "exit_fixed", RISK)
        rows.append({"period": per, "rule": "v3.1 (no change)", **s, "eq": eq, "mdd": mdd})
        for c in known:
            g = base[~R.loc[base.index, c]]
            s = stats(g["net_fixed"].to_numpy())
            eq, mdd = account(g, "net_fixed", "exit_fixed", RISK)
            rows.append({"period": per, "rule": f"skip: {c}", **s, "eq": eq, "mdd": mdd})
        liq = R["liquidation magnet just beyond the stop"] & R["thin volume toward the stop"]
        g = base[~liq.loc[base.index]]
        s = stats(g["net_fixed"].to_numpy())
        eq, mdd = account(g, "net_fixed", "exit_fixed", RISK)
        rows.append({"period": per, "rule": "skip: liquidation magnet beyond stop AND thin volume toward it", **s,
                     "eq": eq, "mdd": mdd})
    L += ["## 4. If we skip trades with each reason (win % after costs)", "", _table(pd.DataFrame(rows), [
        ("period", "period", str), ("rule", "rule", str), ("n", "trades", str), ("win", "win %", _pct),
        ("avg", "avg R", lambda v: f"{v:+.2f}"), ("pf", "profit factor", lambda v: f"{v:.2f}"),
        ("eq", "account", lambda v: f"{v:.2f}x"), ("mdd", "worst drop", lambda v: f"-{v:.0%}")]), ""]
    # 5. per-setup view of the liquidation reason
    rows = []
    c = "liquidation magnet just beyond the stop"
    for per, pm in (("research", res), ("holdout", ~res)):
        for s_ in TGT:
            g = X[pm & (X["setup"] == s_)]
            rows.append({"period": per, "setup": s_, "n": len(g), "w_if": (~g.loc[R.loc[g.index, c], "loss"]).mean(),
                         "n_if": int(R.loc[g.index, c].sum()), "w_not": (~g.loc[~R.loc[g.index, c], "loss"]).mean()})
    L += ["## 5. Liquidation magnet beyond the stop, per setup", "", _table(pd.DataFrame(rows), [
        ("period", "period", str), ("setup", "setup", str), ("n", "trades", str), ("n_if", "with magnet", str),
        ("w_if", "win % with", _pct), ("w_not", "win % without", _pct)]), ""]
    cols = ["decision_time", "setup", "tf", "direction", "net_fixed", "came_back_entry", "came_back_target",
            "hunt_depth_r", "wick_stop", "own_beyond_stop", "pull", "thin_stop", "opp_to_target"]
    X.loc[loss, cols].join(R[loss]).to_csv(out_dir / f"losing_trades_reasons_{mode}.csv")
    L += wider_stop_section(X, df5n, _funding_cum(cfg))
    L += setup_fair_section(X)
    path = out_dir / f"liquidation_failures_{mode}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


# ----------------------------------------------------------------------------- stops beyond the hunt
STOP_RULES = ["original stop", "stop 0.5R further, same target price", "stop 0.5R further, same R target",
              "stop beyond the liquidation cluster, same target price"]


def wider_stops(X: pd.DataFrame, df5n: pd.DataFrame, fund) -> pd.DataFrame:
    """Replay each trade with the stop moved (decided at entry). Same $ risk: R is in the NEW risk."""
    from ..ml.entry15 import _run
    from ..ml.targets import C_LMT, C_MKT
    t5 = df5n["open_time"].to_numpy()
    O, H, Lw, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    ft, fc = fund
    rows = []
    for idx, r in X.iterrows():
        d, rk, T = int(r["direction"]), float(r["risk"]), TGT[r["setup"]]
        bpt = int(pd.Timedelta(r["tf"]) / FIVE)
        st = int(np.searchsorted(t5, pd.Timestamp(r["decision_time"]).to_datetime64()))
        end = st + MAX_TF_BARS * bpt
        o, h, l, c = O[:end], H[:end], Lw[:end], C[:end]
        if d < 0:
            o, h, l, c = -o, -l, -h, -c
        e = o[st]
        cl = r["own_cluster_r"]
        stops = {STOP_RULES[0]: (e - rk, e + T * rk), STOP_RULES[1]: (e - 1.5 * rk, e + T * rk),
                 STOP_RULES[2]: (e - 1.5 * rk, e + T * 1.5 * rk)}
        if np.isfinite(cl) and (T * rk) / ((-cl + 0.1) * rk) >= 1.2:
            stops[STOP_RULES[3]] = (e + (cl - 0.1) * rk, e + T * rk)
        else:
            stops[STOP_RULES[3]] = stops[STOP_RULES[0]]
        for name, (s, tg) in stops.items():
            R, xi, kind = _run(o, h, l, c, st, e, s, tg, False, end)
            x_t = pd.Timestamp(t5[xi]) + FIVE
            a = np.searchsorted(ft, t5[st], side="right")
            b = np.searchsorted(ft, x_t.to_datetime64(), side="left")
            sp = (e - s) / abs(e)
            cost = C_MKT + (C_LMT if kind == "target" else C_MKT) + ((fc[b] - fc[a]) * d if b > a else 0.0)
            rows.append({"trade": idx, "rule": name, "setup": r["setup"], "hold": bool(r["hold"]),
                         "decision_time": pd.Timestamp(t5[st]), "exit_time": x_t, "stop_pct": sp,
                         "net": R - cost / sp})
    return pd.DataFrame(rows)


def wider_stop_section(X, df5n, fund) -> list[str]:
    W = wider_stops(X, df5n, fund)
    rows = []
    for hold, per in ((False, "research"), (True, "holdout")):
        for name in STOP_RULES:
            g = W[(W["hold"] == hold) & (W["rule"] == name)]
            s = stats(g["net"].to_numpy())
            eq, mdd = account(g.reset_index(drop=True), "net", "exit_time", RISK)
            rows.append({"period": per, "rule": name, **s, "eq": eq, "mdd": mdd})
        for setup in TGT:
            for name in STOP_RULES:
                g = W[(W["hold"] == hold) & (W["rule"] == name) & (W["setup"] == setup)]
                s = stats(g["net"].to_numpy())
                rows.append({"period": per, "rule": f"  {setup}: {name}", **s, "eq": math.nan, "mdd": math.nan})
    return ["## 6. Fix: put the stop beyond the hunt (same $ risk, so a smaller position)", "",
            "Decided at the entry. 'same target price' keeps our target; the reward:risk gets smaller.", "",
            _table(pd.DataFrame(rows), [("period", "period", str), ("rule", "stop", str), ("n", "trades", str),
                                        ("win", "win %", _pct), ("avg", "avg R", lambda v: f"{v:+.2f}"),
                                        ("pf", "profit factor", lambda v: f"{v:.2f}"),
                                        ("eq", "account", lambda v: "" if v != v else f"{v:.2f}x"),
                                        ("mdd", "worst drop", lambda v: "" if v != v else f"-{v:.0%}")]), ""]


def setup_fair_section(X: pd.DataFrame) -> list[str]:
    """The 'magnet beyond the stop' weight grows with the stop width (1D bounces have wide stops), so compare it
    fairly: (a) top third WITHIN each setup, (b) weight per 1% of price."""
    res, w = ~X["hold"], ~X["loss"]
    dens = X["own_beyond_stop"] / (X["risk"] / X["px"])
    cut = X[res].groupby("setup")["own_beyond_stop"].quantile(2 / 3)
    flags = {"top third within its own setup": X["own_beyond_stop"] >= X["setup"].map(cut),
             "top third of weight per 1% of price": dens >= dens[res].quantile(2 / 3)}
    rows = []
    for name, f in flags.items():
        for per, pm in (("research", res), ("holdout", ~res)):
            for s_ in ["all"] + list(TGT):
                m = pm & ((X["setup"] == s_) if s_ != "all" else True)
                rows.append({"test": name, "period": per, "setup": s_, "n": int((m & f).sum()),
                             "w_with": w[m & f].mean(), "w_without": w[m & ~f].mean()})
    return ["## 7. Fair check of the liquidation-magnet reason (removing the stop-width effect)", "",
            _table(pd.DataFrame(rows), [("test", "magnet defined as", str), ("period", "period", str),
                                        ("setup", "setup", str), ("n", "trades with magnet", str),
                                        ("w_with", "win % with", _pct), ("w_without", "win % without", _pct)]), ""]
