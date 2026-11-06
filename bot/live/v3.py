"""
Strategy v3 - paper trading (no exchange orders).

Rules (frozen from the research period, see reports/strategy_v2.md + failure_liquidity.md):
  BREAKOUT (2:1)  concept breakout (zone/trendline break, liquidity run, BOS, range break) on 2h / 4h / 1D
                  - certainty >= 7 from the frozen scoring model (2h model; pooled 4h + 1D model)
                  - stop >= 0.6% away; ATR% not in the bottom 20% of research trades of that timeframe
                  - BTC 4h close vs EMA20 in the trade direction; 6h MACD histogram in the trade direction
                  - clean risk zone: no confirmed swing (1h + own TF) between entry and stop, no equal-high/low
                    pool within 0.5 ATR of the stop
                  - A+ = low-volume path to the target (volume-profile LVN share above the research median)
  BOUNCE (5:1)    1D strong zone tested >= 4 times, bounce confirmed by the next daily candle; stop = v3.1 zone stop
                  (lowest of the tests - 0.25 ATR, bot/study/level_tests.py); target 5 : 1 (the user's choice after
                  reports/ratio_sweep.md: bounces improve with the ratio up to 5 : 1 in both periods; the sweep's own
                  t-score pick on 2022 - Oct 2025 was 2.5 : 1)
  NOT YET LIVE    the research-chosen version (reports/fixes.md) adds the journal filters (skip an untaken double /
                  triple top ahead; skip 3+ rejections at the resistance ahead), one position per move, and the bounce
                  stop below the 1h-leg Fib 0.786. These live only in bot/study/fixes.py so far; the live bounce stop
                  differs from the studied one (median 0.89x), and on the live stop the 5 : 1 holdout does not improve
                  on 3 : 1 (+0.58R vs +0.65R). Wire them here before paper trading (docs/architecture.md, build order).
Risk: A+ 4%, breakout 2%, bounce 2% of equity per trade, leverage capped at 5x. Entry = open of the candle after
the signal; stop / target as defined; max holding 60 candles of the trade's timeframe. Fills simulated on 5m data.
"""
from __future__ import annotations

import hashlib
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from ..study.concepts import add_confluence, detect_events
from ..study.failure_liquidity import liquidity_features, swing_tables
from ..study.flow import flow_features, load_flow
from ..study.indicators import ema
from ..study.level_tests import tests_for
from ..study.mtf import resample
from ..study.scoring import FAMILIES, Model
from ..study.smalltf import COST_TAKER
from ..study.sr2 import add_mtf_features

MODEL_DIR = ROOT / "models" / "v3"
HOLDOUT = pd.Timestamp("2025-11-01", tz="UTC")
RISK = {"A+ breakout": 0.04, "breakout": 0.02, "1D bounce": 0.02}
TARGET = {"A+ breakout": 2.0, "breakout": 2.0, "1D bounce": 5.0}   # bounces 5 : 1 since the ratio sweep (reports/ratio_sweep.md)
LEV_CAP = 5.0
MAX_TF_BARS = 60
FIVE = pd.Timedelta(minutes=5)


# ----------------------------------------------------------------------------- freezing
def _prep_scoring_frame(ev: pd.DataFrame) -> pd.DataFrame:
    ev = ev.copy()
    ev["decision_time"] = pd.to_datetime(ev["decision_time"], utc=True)
    ev["is_1D"] = (ev["tf"] == "1D").astype(int)
    ev["tl_touches_f"] = ev["tl_touches"].fillna(0) if "tl_touches" in ev else 0.0
    if "f_bvol" not in ev:
        ev["f_bvol"] = np.nan
    ev["bar"] = ev["tf"].map(pd.Timedelta)
    return ev


def freeze(cfg: Config) -> dict:
    """Fit the final scoring models on research data exactly as the study did, and store thresholds."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    models = {}
    for key, tfs in (("2h", ("2h",)), ("4h_1D", ("4h", "1D"))):
        parts = []
        for tf in tfs:
            e = pd.read_pickle(ROOT / "results" / f"concept_events_{tf}.pkl")
            e["tf"] = tf
            parts.append(e)
        ev = _prep_scoring_frame(pd.concat(parts, ignore_index=True))
        fam = ev[ev["event"].isin(FAMILIES["breakout"]) & ev["out_1"].isin(["win", "loss", "timeout"])]
        research = fam[fam["decision_time"] < HOLDOUT - fam["bar"] * 62]
        models[key] = Model("breakout").fit(research)
    from ..study.strategy_eval import load_breakouts
    b = load_breakouts()
    q20 = b[~b["hold"]].groupby("tf")["atr_pct"].quantile(0.2).to_dict()
    A = pd.read_pickle(ROOT / "results" / "boost_A_flow.pkl")
    lvn_med = float(A.loc[~A["hold"], "n_vp_lvn_share"].median())
    params = {"atr_q20": q20, "lvn_median": lvn_med, "risk": RISK, "target": TARGET, "lev_cap": LEV_CAP,
              "frozen_at": datetime.now(timezone.utc).isoformat(), "research_end": str(HOLDOUT.date())}
    with open(MODEL_DIR / "models.pkl", "wb") as fh:
        pickle.dump(models, fh)
    (MODEL_DIR / "params.json").write_text(json.dumps(params, indent=2))
    return params


def load_frozen():
    with open(MODEL_DIR / "models.pkl", "rb") as fh:
        models = pickle.load(fh)
    params = json.loads((MODEL_DIR / "params.json").read_text())
    blob = (MODEL_DIR / "models.pkl").read_bytes() + (MODEL_DIR / "params.json").read_bytes()
    return models, params, hashlib.sha256(blob).hexdigest()[:12]


# ----------------------------------------------------------------------------- signals
def generate_signals(cfg: Config, since: pd.Timestamp | None = None, params_override: dict | None = None,
                     return_stage: str | None = None) -> pd.DataFrame:
    """All v3 trades (entry_time, setup, direction, entry, stop, ...) from the full data, frozen rules.
    params_override: replace frozen thresholds (e.g. per-coin atr_q20 / lvn_median) - research use only.
    return_stage="breakouts": return certainty >= 7 breakouts with F1 / F2 columns, before any filter."""
    models, params, _ = load_frozen()
    params = {**params, **(params_override or {})}
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    btc5, _ = load_klines_5m(cfg.data_dir, cfg.btc_symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    t5 = df5n["open_time"].to_numpy()
    O = df5n["open"].to_numpy(float)

    def entry_px(ts):
        ts = pd.Timestamp(ts).tz_convert(None).to_datetime64() if pd.Timestamp(ts).tz else pd.Timestamp(ts).to_datetime64()
        i = int(np.searchsorted(t5, ts))
        return float(O[i]) if i < len(t5) and t5[i] == ts else np.nan

    rows = []
    for tf in ("2h", "4h", "1D"):
        ev = detect_events(df5u, tf, resample, live=True)
        ev = add_confluence(ev)
        ev["tf"] = tf
        ev = ev[ev["event"].isin(FAMILIES["breakout"])]
        if since is not None:
            ev = ev[pd.to_datetime(ev["decision_time"], utc=True) >= since]
        if ev.empty:
            continue
        ev = add_mtf_features(ev.reset_index(drop=True), df5u)
        ev = _prep_scoring_frame(ev)
        m = models["2h"] if tf == "2h" else models["4h_1D"]
        ev["p"] = m.predict(ev)
        ev["certainty"] = np.clip(np.round(ev["p"] * 10), 1, 10).astype(int)
        ev = ev[ev["certainty"] >= params.get("min_certainty", 7)].copy()
        ev["entry"] = [e if np.isfinite(e) else entry_px(t) for e, t in zip(ev["entry"], ev["decision_time"])]
        ev["risk"] = (ev["entry"] - ev["stop"]) * ev["direction"]
        ev["family"] = "breakout"
        rows.append(ev)
    br = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    out = []
    if len(br):
        br["entry_time"] = pd.to_datetime(br["decision_time"], utc=True).dt.tz_convert(None)
        br["stop_pct"] = br["risk"] / br["entry"]
        br["atr_pct"] = br["atr"] / br["entry"]
        ok = br["entry"].notna() & (br["risk"] > 0)
        br.loc[ok, "F1"] = br.loc[ok, "stop_pct"] >= 0.006
        br.loc[ok, "F2"] = br.loc[ok, "atr_pct"] >= br.loc[ok, "tf"].map(params["atr_q20"])
        # BTC 4h trend at entry (candles closed by then)
        b4 = resample(btc5, "4h")
        b4["side"] = np.sign(b4["close"] - ema(b4["close"], 20))
        b4["close_time"] = pd.to_datetime(b4["close_time"], utc=True).dt.tz_convert(None).dt.as_unit("ns")
        mm = pd.merge_asof(br[["entry_time"]].assign(_r=np.arange(len(br)), entry_time=br["entry_time"].dt.as_unit("ns"))
                           .sort_values("entry_time"), b4[["close_time", "side"]], left_on="entry_time",
                           right_on="close_time", direction="backward").sort_values("_r")
        br["btc_4h"] = mm["side"].to_numpy() * br["direction"].to_numpy()
        br["macd_6h"] = br["m_6h_macd"]
        br["pending_entry"] = br["entry"].isna()
        if return_stage == "breakouts":
            return br
        keep = br["pending_entry"] | (ok & br["F1"].astype(bool) & br["F2"].astype(bool))
        keep &= (br["btc_4h"] > 0) & (br["macd_6h"] > 0)
        br = br[keep].copy()
        if len(br):
            filled = br[~br["pending_entry"]].copy()
            if len(filled):
                fl = load_flow(cfg.data_dir, cfg.symbol)
                filled["atr_ref"] = filled["f_atr_pct"] * filled["entry"]
                filled = pd.concat([filled, flow_features(filled, fl)[["n_vp_lvn_share"]]], axis=1)
                filled["decision_time"] = filled["entry_time"]
                filled["T"], filled["atr_px"] = 2.0, filled["atr_ref"]
                liq = liquidity_features(filled, swing_tables(df5u), df5n)
                filled = pd.concat([filled, liq], axis=1)
                filled = filled[(filled["liq_in_risk"] == 0) & (filled["pool_near_stop"] == 0)]
                filled["setup"] = np.where(filled["n_vp_lvn_share"] > params["lvn_median"], "A+ breakout", "breakout")
                out.append(filled)
            pend = br[br["pending_entry"]].copy()
            if len(pend):
                pend["setup"] = "breakout (pending entry checks)"
                out.append(pend)
    # 1D 4th-test bounces
    lt = tests_for(df5u, "1D", live=True)
    if len(lt) and "stop" in lt:
        lt = lt[lt["stop"].notna() & (lt["test_n"] >= 4)].copy()
        lt["entry_time"] = (pd.to_datetime(lt["time"], utc=True) + pd.Timedelta(days=1)).dt.tz_convert(None)
        if since is not None:
            lt = lt[lt["entry_time"] >= since.tz_convert(None)]
        lt["entry"] = [e if np.isfinite(e) else entry_px(t.tz_localize("UTC")) for e, t in zip(lt["entry"], lt["entry_time"])]
        lt["risk"] = (lt["entry"] - lt["stop"]) * lt["direction"]
        lt = lt[lt["entry"].isna() | (lt["risk"] > 0)]
        lt["tf"], lt["setup"], lt["event"], lt["certainty"] = "1D", "1D bounce", "level_4th_test", np.nan
        lt["stop_pct"] = lt["risk"] / lt["entry"]
        lt["pending_entry"] = lt["entry"].isna()
        out.append(lt)
    if not out:
        return pd.DataFrame()
    cols = ["entry_time", "setup", "tf", "event", "direction", "entry", "stop", "risk", "stop_pct", "certainty",
            "pending_entry"]
    sig = pd.concat([o[[c for c in cols if c in o]] for o in out], ignore_index=True)
    sig["target"] = sig["entry"] + sig["direction"] * sig["setup"].map(TARGET).fillna(2.0) * sig["risk"]
    return sig.sort_values("entry_time").reset_index(drop=True)


# ----------------------------------------------------------------------------- fills
def replay(sig: pd.DataFrame, df5n: pd.DataFrame) -> pd.DataFrame:
    """Simulate each trade on 5m data. Status: closed (stop/target/time) or open (mark-to-market)."""
    t5 = df5n["open_time"].to_numpy()
    O, H, Lw, C = (df5n[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    rows = []
    for _, s in sig.iterrows():
        r = s.to_dict()
        if s["pending_entry"] or not np.isfinite(s["entry"]):
            r.update(status="pending", R=np.nan, exit_time=pd.NaT, exit_price=np.nan, reason="")
            rows.append(r)
            continue
        st = int(np.searchsorted(t5, pd.Timestamp(s["entry_time"]).to_datetime64()))
        bpt = int(pd.Timedelta(s["tf"]) / FIVE)
        end = min(len(t5), st + MAX_TF_BARS * bpt)
        d, e, stop, tgt = int(s["direction"]), s["entry"], s["stop"], s["target"]
        status, reason, xp, xi = "open", "", np.nan, None
        for i in range(st, end):
            o_, h_, l_ = O[i], H[i], Lw[i]
            if i > st and d * (o_ - stop) <= 0:
                status, reason, xp, xi = "closed", "stop (gap)", o_, i
                break
            if i > st and d * (o_ - tgt) >= 0:
                status, reason, xp, xi = "closed", "target (gap)", o_, i
                break
            if (l_ <= stop) if d > 0 else (h_ >= stop):
                status, reason, xp, xi = "closed", "stop", stop, i
                break
            if (h_ >= tgt) if d > 0 else (l_ <= tgt):
                status, reason, xp, xi = "closed", "target", tgt, i
                break
        if status == "open" and end - st >= MAX_TF_BARS * bpt:
            status, reason, xp, xi = "closed", "time limit", C[end - 1], end - 1
        if status == "closed":
            R = d * (xp - e) / s["risk"]
            r.update(status="closed", reason=reason, exit_price=xp, exit_time=pd.Timestamp(t5[xi]) + FIVE, R=R)
        else:
            last = C[end - 1] if end > st else e
            r.update(status="open", reason="", exit_price=np.nan, exit_time=pd.NaT,
                     R=d * (last - e) / s["risk"], last_price=last)
        r["net_R"] = r["R"] - COST_TAKER / s["stop_pct"] if np.isfinite(r["R"]) else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def account(tr: pd.DataFrame, start: pd.Timestamp) -> tuple[pd.DataFrame, float, float]:
    """Equity from `start`: closed trades booked at exit; open trades marked to market (unrealized)."""
    t = tr[tr["status"] != "pending"].copy()
    ev = [(r.entry_time, 0, i) for i, r in t.iterrows()] + \
         [(r.exit_time, 1, i) for i, r in t.iterrows() if r.status == "closed"]
    ev.sort()
    eq, notional, curve = 1.0, {}, [(start, 1.0)]
    for ts, kind, i in ev:
        r = t.loc[i]
        if kind == 0:
            notional[i] = eq * min(RISK.get(r.setup, 0.02) / r.stop_pct, LEV_CAP)
        else:
            eq += notional.pop(i) * (r.R * r.stop_pct - COST_TAKER)
            curve.append((ts, eq))
    unreal = sum(n * (t.loc[i, "R"] * t.loc[i, "stop_pct"] - COST_TAKER) for i, n in notional.items())
    return pd.DataFrame(curve, columns=["time", "equity"]), eq, unreal


# ----------------------------------------------------------------------------- runner
def run_shadow_v3(cfg: Config, start: str | None = None, refresh: bool = True, reset: bool = False) -> dict:
    out = ROOT / "shadow_v3"
    out.mkdir(exist_ok=True)
    state_p = out / "state.json"
    if refresh:
        try:
            from ..refresh import refresh_all
            refresh_all(cfg.data_dir, [cfg.symbol, cfg.btc_symbol], 10)
        except Exception as e:  # keep running on stale data, but say so
            print(f"WARN: data refresh failed ({e}); using data on disk")
    _, _, fp = load_frozen()
    if reset or not state_p.exists():
        st = {"forward_from": start or datetime.now(timezone.utc).strftime("%Y-%m-%d"), "fingerprint": fp,
              "created_at": datetime.now(timezone.utc).isoformat()}
        state_p.write_text(json.dumps(st, indent=2))
    st = json.loads(state_p.read_text())
    if st["fingerprint"] != fp:
        raise SystemExit("Frozen v3 model changed since this shadow started. Re-run with --reset.")
    since = pd.Timestamp(st["forward_from"], tz="UTC")
    sig = generate_signals(cfg, since=since - pd.Timedelta(days=3))
    sig = sig[sig["entry_time"] >= since.tz_convert(None)].reset_index(drop=True)
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    tr = replay(sig, df5n)
    curve, eq, unreal = account(tr, since.tz_convert(None))
    closed = tr[tr["status"] == "closed"]
    tr.to_csv(out / "trades.csv", index=False)
    curve.to_csv(out / "equity.csv", index=False)
    summary = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(), "mode": "PAPER_ONLY", "places_orders": False,
        "forward_from": st["forward_from"], "data_until": str(df5n["open_time"].iloc[-1]),
        "trades_closed": int(len(closed)), "open_positions": int((tr["status"] == "open").sum()),
        "pending_signals": int((tr["status"] == "pending").sum()),
        "win_rate": float((closed["net_R"] > 0).mean()) if len(closed) else None,
        "avg_R": float(closed["net_R"].mean()) if len(closed) else None,
        "equity_closed": round(float(eq), 4), "equity_incl_open": round(float(eq + unreal), 4),
        "by_setup": {k: {"n": int(len(g)), "win": float((g["net_R"] > 0).mean())} for k, g in closed.groupby("setup")},
        "open": tr[tr["status"] == "open"][["entry_time", "setup", "tf", "direction", "entry", "stop", "target", "R"]]
        .astype(str).to_dict("records"),
        "fingerprint": fp,
    }
    (out / "latest.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary
