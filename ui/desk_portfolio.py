"""
Portfolio views over shadow paper strategies — equal / agreement-only / S2-primary.

Does not place orders. Used by SHADOW DESK for correlation & risk clarity.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SHADOW = ROOT / "shadow"
MODELS = ROOT / "models"

FOLDERS = {
    "s1": "s1_both_align_no_stop",
    "s2": "s2_both_cool7_stable7",
    "s3": "s3_both_btc_confirm",
}

WINNER_FILES = {
    "s1": MODELS / "htf_v4_winner.json",
    "s2": MODELS / "htf_v5_winner.json",
    "s3": MODELS / "htf_v6_s3_winner.json",
}


def _read_signals(folder: str) -> pd.DataFrame:
    path = SHADOW / folder / "signals.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
    except Exception:
        try:
            df = pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame()
    return df


def _read_trades(folder: str) -> pd.DataFrame:
    path = SHADOW / folder / "trades.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def closed_trades_summary() -> pd.DataFrame:
    rows = []
    for sid, folder in FOLDERS.items():
        df = _read_trades(folder)
        if df.empty:
            continue
        nets = df["net_return"].astype(float)
        rows.append({
            "id": sid.upper(),
            "n_trades": int(len(df)),
            "sum_net": float(nets.sum()),
            "avg_net": float(nets.mean()),
            "win_rate": float((nets > 0).mean()),
            "equity_from_trades": float((1.0 + nets).prod()),
            "last_exit": str(df["exit_time"].iloc[-1]) if "exit_time" in df.columns else None,
        })
    return pd.DataFrame(rows)


def daily_side_equity() -> pd.DataFrame:
    """One row per day with S1/S2/S3 side + equity."""
    frames = []
    for sid, folder in FOLDERS.items():
        df = _read_signals(folder)
        if df.empty or "day" not in df.columns:
            continue
        tmp = df.copy()
        sort_col = "ts_utc" if "ts_utc" in tmp.columns else tmp.columns[0]
        tmp = tmp.sort_values(sort_col).groupby("day", as_index=False).tail(1)
        tmp["strategy_id"] = sid.upper()
        if "side" not in tmp.columns:
            tmp["side"] = None
        tmp["side"] = tmp["side"].fillna("flat").astype(str).replace({"nan": "flat", "None": "flat"})
        cols = ["day", "strategy_id", "side", "equity", "price", "regime", "action"]
        frames.append(tmp[[c for c in cols if c in tmp.columns]])
    if not frames:
        return pd.DataFrame()
    long = pd.concat(frames, ignore_index=True)
    sides = long.pivot_table(index="day", columns="strategy_id", values="side", aggfunc="last")
    eqs = long.pivot_table(index="day", columns="strategy_id", values="equity", aggfunc="last")
    eqs = eqs.add_prefix("eq_")
    px = long.groupby("day")["price"].last() if "price" in long.columns else None
    reg = long.groupby("day")["regime"].last() if "regime" in long.columns else None
    out = sides.join(eqs, how="outer")
    if px is not None:
        out["close"] = px
    if reg is not None:
        out["regime"] = reg
    out = out.reset_index().sort_values("day")
    return out


def _agree_label(row: pd.Series) -> str:
    vals = []
    for c in ("S1", "S2", "S3"):
        if c in row.index and pd.notna(row[c]):
            v = str(row[c]).lower()
            if v not in ("nan", "none", ""):
                vals.append(v)
    active = [v for v in vals if v != "flat"]
    if not active:
        return "all_flat"
    if len(set(active)) == 1 and len(active) == len(vals):
        return f"all_agree_{active[0]}"
    if len(set(active)) == 1:
        return f"active_agree_{active[0]}"
    if len(active) == 1:
        return "one_active"
    return "disagree"


def portfolio_curves(daily: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Build equity curves:
      equal — average of S1/S2/S3 equity levels (paper sleeves, independent)
      s2_primary — S2 equity only
      agreement_2of3 — compound daily returns only when >=2 strategies share same non-flat side
    """
    d = daily if daily is not None else daily_side_equity()
    if d.empty:
        return pd.DataFrame()
    d = d.sort_values("day").copy()
    for c in ("S1", "S2", "S3"):
        if c not in d.columns:
            d[c] = "flat"
    for c in ("eq_S1", "eq_S2", "eq_S3"):
        if c not in d.columns:
            d[c] = 1.0
        d[c] = d[c].astype(float).ffill().fillna(1.0)

    d["equal"] = d[["eq_S1", "eq_S2", "eq_S3"]].mean(axis=1)
    d["s2_primary"] = d["eq_S2"]

    # daily returns per sleeve
    for sid in ("S1", "S2", "S3"):
        d[f"ret_{sid}"] = d[f"eq_{sid}"].pct_change().fillna(0.0)

    agree_rets = []
    eq = 1.0
    for _, row in d.iterrows():
        sides = {sid: str(row[sid]).lower() for sid in ("S1", "S2", "S3")}
        active = {k: v for k, v in sides.items() if v != "flat"}
        if len(active) >= 2 and len(set(active.values())) == 1:
            # average returns of active agreeing sleeves
            rets = [float(row[f"ret_{k}"]) for k in active]
            r = sum(rets) / len(rets)
        else:
            r = 0.0  # cash
        eq *= 1.0 + r
        agree_rets.append(eq)
    d["agreement_2of3"] = agree_rets
    d["agreement"] = d.apply(_agree_label, axis=1)
    return d


def portfolio_summary(curves: pd.DataFrame | None = None) -> pd.DataFrame:
    c = curves if curves is not None else portfolio_curves()
    if c.empty:
        return pd.DataFrame()
    rows = []
    for name, col in [
        ("equal_weight", "equal"),
        ("s2_primary", "s2_primary"),
        ("agreement_2of3", "agreement_2of3"),
        ("s1_only", "eq_S1"),
        ("s3_only", "eq_S3"),
    ]:
        if col not in c.columns:
            continue
        series = c[col].astype(float)
        ret = float(series.iloc[-1] / series.iloc[0] - 1.0) if len(series) else 0.0
        peak = series.cummax()
        dd = float(((series - peak) / peak).min()) if len(series) else 0.0
        rows.append({
            "portfolio": name,
            "final_equity": float(series.iloc[-1]),
            "total_return": ret,
            "max_dd": dd,
            "note": {
                "equal_weight": "avg of 3 sleeves (shows correlation drag)",
                "s2_primary": "most distinct rules (cool7/stable7)",
                "agreement_2of3": "only risk-on when 2+ agree same side",
                "s1_only": "both_align_no_stop",
                "s3_only": "both_btc_confirm (often ~S1)",
            }.get(name, ""),
        })
    return pd.DataFrame(rows)


def s1_s3_correlation_note(curves: pd.DataFrame | None = None) -> str:
    c = curves if curves is not None else portfolio_curves()
    if c.empty or "ret_S1" not in c.columns or "ret_S3" not in c.columns:
        return "Not enough data to compare S1 vs S3."
    corr = float(c["ret_S1"].corr(c["ret_S3"]))
    same = float((c["S1"] == c["S3"]).mean()) if "S1" in c.columns else None
    msg = (
        f"S1 vs S3 daily equity-return correlation ~ **{corr:.2f}**. "
        "They often take the same side and lose/win together — treat S3 as BTC-filter twin of S1, "
        "not full independent size."
    )
    if same is not None:
        msg += f" Same-side/flat match rate ~ **{same:.0%}** of days."
    return msg


def load_wf_context() -> pd.DataFrame:
    rows = []
    labels = {"s1": "S1 both_align_no_stop", "s2": "S2 both_cool7_stable7", "s3": "S3 both_btc_confirm"}
    for sid, path in WINNER_FILES.items():
        if not path.exists():
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        w = raw.get("winner", {})
        wf = raw.get("walkforward", {})
        rows.append({
            "id": sid.upper(),
            "strategy": w.get("name") or labels.get(sid),
            "stop_pct": w.get("stop_pct"),
            "wf_edged": wf.get("edged"),
            "wf_oos_ret": wf.get("compounded_oos_ret"),
            "wf_median_pf": wf.get("median_pf"),
            "wf_worst_dd": wf.get("worst_dd"),
            "status": raw.get("status"),
        })
    return pd.DataFrame(rows)
