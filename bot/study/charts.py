"""
Multi-timeframe chart pack for one trade: 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1D, 1W.

Each chart: candles + EMA20/EMA50 + Bollinger(20,2) + Ichimoku cloud, volume, MACD(12,26,9), RSI(14).
Black dashed line = entry (00:00 UTC after the signal day); grey dashed = the candle where the
stop / 5x liquidation / target was first touched (found on 5m data).
Blue = entry price, green dotted = target (+2 ATR), red dotted = stop (-1 ATR).
Indicators are computed on the full history, then the window around the trade is shown.
Everything left of the entry line is what was knowable at entry.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .indicators import bollinger, ema, ichimoku, macd, rsi
from .mtf import TIMEFRAMES, resample

BEFORE = {"1W": 80, "1D": 120}
DEFAULT_BEFORE = 150
MAX_AFTER = 120


def _hint_text(trade: pd.Series, tf: str) -> str:
    names = [("trend", "EMA50"), ("macd", "MACD"), ("macd_fade", "MACD fade"), ("rsi_ext", "RSI ext"),
             ("cloud", "cloud"), ("supertrend", "Supertrend"), ("adx_weak", "ADX<20"), ("di", "DI")]
    parts = []
    for key, label in names:
        col = f"{tf}_{key}"
        if col in trade.index and not pd.isna(trade[col]):
            v = int(trade[col])
            if key == "adx_weak":
                parts.append(f"{label}: {'yes' if v < 0 else 'no'}")
            else:
                parts.append(f"{label}: {'AGAINST' if v < 0 else 'with' if v > 0 else '-'}")
    return " | ".join(parts)


def exit_moment(df5: pd.DataFrame, trade: pd.Series, leverage: float = 5.0, mmr: float = 0.005):
    """First 5m candle after entry that touched the stop / liquidation (losses) or the target (wins)."""
    et = pd.Timestamp(trade["entry_time"])
    end = et + pd.Timedelta(days=float(trade["days_to_exit"]))
    w = df5[(df5["open_time"] >= et) & (df5["open_time"] < end)]
    d, e, a = int(trade["direction"]), float(trade["entry"]), float(trade["atr14"])
    if trade["outcome"] == "loss":
        stop = e - d * a
        liq = e * (1 - d * (1 / leverage - mmr))
        level, kind = (min(stop, liq), "liquidated" if liq < stop else "stop") if d < 0 else \
                      (max(stop, liq), "liquidated" if liq > stop else "stop")
        hit = w[w["high"] >= level] if d < 0 else w[w["low"] <= level]
    elif trade["outcome"] == "win":
        level, kind = e + d * 2 * a, "target"
        hit = w[w["low"] <= level] if d < 0 else w[w["high"] >= level]
    else:
        return end, "timeout"
    return (hit["open_time"].iloc[0], kind) if len(hit) else (end, kind)


def plot_tf(df5: pd.DataFrame, trade: pd.Series, tf: str, rule: str, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    b = resample(df5, rule).reset_index(drop=True)
    e20, e50 = ema(b["close"], 20), ema(b["close"], 50)
    mid, bu, bl = bollinger(b["close"])
    _, _, ctop, cbot, _, _ = ichimoku(b)
    line, sig = macd(b["close"])
    hist = line - sig
    r = rsi(b["close"])

    et = pd.Timestamp(trade["entry_time"])
    xt, exit_kind = exit_moment(df5, trade)                    # exact 5m candle of the exit
    i_entry = int((b["close_time"] <= et).sum())               # first candle opening at/after entry
    i_exit = int((b["open_time"] <= xt).sum()) - 1             # candle containing the exit
    before = BEFORE.get(tf, DEFAULT_BEFORE)
    lo_i = max(0, i_entry - before)
    hi_i = min(len(b), max(i_exit + max(5, (i_exit - i_entry) // 4), i_entry + 8), i_entry + MAX_AFTER)
    s = slice(lo_i, hi_i)
    seg = b.iloc[s]
    x = np.arange(len(seg))
    k_entry, k_exit = i_entry - lo_i, i_exit - lo_i

    fig, (ax, axv, axm, axr) = plt.subplots(4, 1, figsize=(15, 9), sharex=True,
                                            gridspec_kw={"height_ratios": [5, 1, 1.4, 1.4]})
    up = (seg["close"] >= seg["open"]).to_numpy()
    w = 0.7
    ax.vlines(x, seg["low"], seg["high"], color="#666", linewidth=0.7, zorder=2)
    ax.bar(x[up], (seg["close"] - seg["open"]).to_numpy()[up], bottom=seg["open"].to_numpy()[up],
           color="#26a69a", width=w, zorder=3)
    ax.bar(x[~up], (seg["close"] - seg["open"]).to_numpy()[~up], bottom=seg["open"].to_numpy()[~up],
           color="#ef5350", width=w, zorder=3)
    ax.plot(x, e20.iloc[s], color="#ff9800", linewidth=1.1, label="EMA20")
    ax.plot(x, e50.iloc[s], color="#3f51b5", linewidth=1.3, label="EMA50")
    ax.plot(x, bu.iloc[s], color="#9e9e9e", linewidth=0.7, linestyle="--", label="Bollinger 20,2")
    ax.plot(x, bl.iloc[s], color="#9e9e9e", linewidth=0.7, linestyle="--")
    ct, cb = ctop.iloc[s].to_numpy(), cbot.iloc[s].to_numpy()
    ax.fill_between(x, cb, ct, color="#80cbc4", alpha=0.25, label="Ichimoku cloud", zorder=1)
    d = int(trade["direction"])
    entry, a = float(trade["entry"]), float(trade["atr14"])
    ax.axhline(entry, color="#1e88e5", linewidth=1, label="entry")
    ax.axhline(entry + d * 2 * a, color="#2e7d32", linestyle=":", linewidth=1.4, label="target +2 ATR")
    ax.axhline(entry - d * 1 * a, color="#c62828", linestyle=":", linewidth=1.4, label="stop -1 ATR")
    lv = entry * (1 - d * (1 / 5 - 0.005))
    ax.axhline(lv, color="#000", linestyle="-.", linewidth=0.8, label="5x liquidation")
    for axx in (ax, axv, axm, axr):
        axx.axvline(k_entry - 0.5, color="black", linestyle="--", linewidth=1.2)
        if 0 <= k_exit < len(seg):
            axx.axvline(k_exit, color="#757575", linestyle="--", linewidth=1)
    ax.legend(loc="upper left", fontsize=7, ncol=4)
    lo_y = min(seg["low"].min(), entry - abs(2 * a))
    hi_y = max(seg["high"].max(), entry + abs(2 * a))
    ax.set_ylim(lo_y * 0.98, hi_y * 1.02)

    axv.bar(x, seg["volume"], color=np.where(up, "#26a69a", "#ef5350"), width=w)
    axv.set_ylabel("vol", fontsize=8)
    hseg = hist.iloc[s].to_numpy()
    axm.bar(x, hseg, color=np.where(hseg >= 0, "#26a69a", "#ef5350"), width=w)
    axm.plot(x, line.iloc[s], color="#1e88e5", linewidth=0.9)
    axm.plot(x, sig.iloc[s], color="#ff9800", linewidth=0.9)
    axm.set_ylabel("MACD", fontsize=8)
    axr.plot(x, r.iloc[s], color="#7e57c2", linewidth=1)
    axr.axhline(70, color="#c62828", linewidth=0.6, linestyle="--")
    axr.axhline(30, color="#2e7d32", linewidth=0.6, linestyle="--")
    axr.set_ylim(0, 100)
    axr.set_ylabel("RSI", fontsize=8)

    n_ticks = 8
    idx = np.linspace(0, len(seg) - 1, n_ticks).astype(int)
    fmt = "%Y-%m-%d" if tf in ("1D", "1W", "12h", "8h", "6h") else "%m-%d %H:%M"
    axr.set_xticks(idx)
    axr.set_xticklabels([seg["open_time"].iloc[i].strftime(fmt) for i in idx], fontsize=8)

    side = "SHORT" if d < 0 else "LONG"
    fig.suptitle(
        f"{tf}  |  {side} signal {trade['day']} ({trade['signals']}), entry {et:%Y-%m-%d %H:%M} UTC @ {entry:,.2f}  "
        f"->  {exit_kind.upper()} {xt:%Y-%m-%d %H:%M} UTC (grey line)  |  weekly trend: {trade['weekly_trend']}\n"
        f"at entry on {tf}: {_hint_text(trade, tf)}", fontsize=10)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)


def chart_pack(df5: pd.DataFrame, trade: pd.Series, out_dir: Path) -> list[Path]:
    files = []
    for k, (tf, rule) in enumerate(TIMEFRAMES.items()):
        p = out_dir / f"{k:02d}_{tf}.png"
        plot_tf(df5, trade, tf, rule, p)
        files.append(p)
    return files


def plot_levels(df5: pd.DataFrame, tf: str, rule: str, entry_time: pd.Timestamp, exit_time: pd.Timestamp,
                direction: int, entry: float, stop: float, target: float, title: str, path: Path,
                ref_level: float | None = None, before: int | None = None) -> None:
    """Chart one trade with explicit entry / stop / target on one timeframe (same indicator panels)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    b = resample(df5, rule).reset_index(drop=True)
    e20, e50 = ema(b["close"], 20), ema(b["close"], 50)
    _, bu, bl = bollinger(b["close"])
    _, _, ctop, cbot, _, _ = ichimoku(b)
    line, sig = macd(b["close"])
    hist = line - sig
    r = rsi(b["close"])
    et, xt = pd.Timestamp(entry_time), pd.Timestamp(exit_time)
    i_entry = int((b["close_time"] <= et).sum())
    i_exit = int((b["open_time"] < xt).sum()) - 1
    nb = before or BEFORE.get(tf, DEFAULT_BEFORE)
    lo_i = max(0, i_entry - nb)
    hi_i = min(len(b), max(i_exit + 15, i_entry + 15), i_entry + MAX_AFTER)
    s = slice(lo_i, hi_i)
    seg = b.iloc[s]
    x = np.arange(len(seg))
    k_entry, k_exit = i_entry - lo_i, i_exit - lo_i
    fig, (ax, axv, axm, axr) = plt.subplots(4, 1, figsize=(15, 9), sharex=True,
                                            gridspec_kw={"height_ratios": [5, 1, 1.4, 1.4]})
    up = (seg["close"] >= seg["open"]).to_numpy()
    ax.vlines(x, seg["low"], seg["high"], color="#666", linewidth=0.7, zorder=2)
    ax.bar(x[up], (seg["close"] - seg["open"]).to_numpy()[up], bottom=seg["open"].to_numpy()[up], color="#26a69a", width=0.7, zorder=3)
    ax.bar(x[~up], (seg["close"] - seg["open"]).to_numpy()[~up], bottom=seg["open"].to_numpy()[~up], color="#ef5350", width=0.7, zorder=3)
    ax.plot(x, e20.iloc[s], color="#ff9800", linewidth=1.1, label="EMA20")
    ax.plot(x, e50.iloc[s], color="#3f51b5", linewidth=1.3, label="EMA50")
    ax.plot(x, bu.iloc[s], color="#9e9e9e", linewidth=0.7, linestyle="--", label="Bollinger 20,2")
    ax.plot(x, bl.iloc[s], color="#9e9e9e", linewidth=0.7, linestyle="--")
    ax.fill_between(x, cbot.iloc[s].to_numpy(), ctop.iloc[s].to_numpy(), color="#80cbc4", alpha=0.25, label="Ichimoku cloud", zorder=1)
    ax.axhline(entry, color="#1e88e5", linewidth=1, label=f"entry {entry:,.2f}")
    ax.axhline(target, color="#2e7d32", linestyle=":", linewidth=1.4, label=f"target 2:1 {target:,.2f}")
    ax.axhline(stop, color="#c62828", linestyle=":", linewidth=1.4, label=f"stop {stop:,.2f}")
    if ref_level is not None:
        ax.axhline(ref_level, color="#8e24aa", linestyle="-.", linewidth=1, label=f"broken level {ref_level:,.2f}")
    for axx in (ax, axv, axm, axr):
        axx.axvline(k_entry - 0.5, color="black", linestyle="--", linewidth=1.2)
        if 0 <= k_exit < len(seg):
            axx.axvline(k_exit, color="#757575", linestyle="--", linewidth=1)
    ax.legend(loc="upper left", fontsize=7, ncol=4)
    span = [seg["low"].min(), seg["high"].max(), stop, target]
    pad = (max(span) - min(span)) * 0.04
    ax.set_ylim(min(span) - pad, max(span) + pad)
    axv.bar(x, seg["volume"], color=np.where(up, "#26a69a", "#ef5350"), width=0.7)
    axv.set_ylabel("vol", fontsize=8)
    hs = hist.iloc[s].to_numpy()
    axm.bar(x, hs, color=np.where(hs >= 0, "#26a69a", "#ef5350"), width=0.7)
    axm.plot(x, line.iloc[s], color="#1e88e5", linewidth=0.9)
    axm.plot(x, sig.iloc[s], color="#ff9800", linewidth=0.9)
    axm.set_ylabel("MACD", fontsize=8)
    axr.plot(x, r.iloc[s], color="#7e57c2", linewidth=1)
    axr.axhline(70, color="#c62828", linewidth=0.6, linestyle="--")
    axr.axhline(30, color="#2e7d32", linewidth=0.6, linestyle="--")
    axr.set_ylim(0, 100)
    axr.set_ylabel("RSI", fontsize=8)
    idx = np.linspace(0, len(seg) - 1, 8).astype(int)
    fmt = "%Y-%m-%d" if tf in ("1D", "1W") else "%m-%d %H:%M"
    axr.set_xticks(idx)
    axr.set_xticklabels([seg["open_time"].iloc[i].strftime(fmt) for i in idx], fontsize=8)
    fig.suptitle(f"{tf}  |  {title}", fontsize=10)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)
