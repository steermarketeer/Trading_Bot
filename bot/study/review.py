"""
Trade review pack: every losing v3.1 ETH trade on 15m / 1h / 4h / 1D, for the trader to annotate.

Each timeframe panel (only information known at entry is drawn left of the black entry line):
  candles, EMA20 / EMA50, strong S/R zones known at entry (purple bands), trendlines through the last two confirmed
  swing highs / lows (orange / teal), untaken liquidity = confirmed swing highs / lows not yet traded through at
  entry (dashed grey to the entry), entry (blue), stop (red), target (green), exit candle (grey dashed);
  volume, MACD(12,26,9), RSI(14).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT, Config
from ..data import load_klines_5m
from .concepts import Bars
from .indicators import macd
from .levels import _level_table, strong_levels
from .mtf import resample

TFS = [("15m", "15min"), ("1h", "1h"), ("4h", "4h"), ("1D", "1D")]
BEFORE, AFTER_MIN, AFTER_MAX = 100, 12, 90
from ..live.v3 import TARGET as TGT          # one source of truth for the targets
FIVE = pd.Timedelta(minutes=5)


class TFData:
    def __init__(self, df5u: pd.DataFrame, rule: str):
        self.bars = Bars(resample(df5u, rule))
        b = self.bars
        self.ct = b.ct.dt.tz_convert(None).to_numpy()
        self.ot = b.ot.dt.tz_convert(None).to_numpy()
        line, sig = macd(pd.Series(b.c))
        self.ml, self.ms = line.to_numpy(float), sig.to_numpy(float)


def _panel(fig, spec, d: TFData, tf: str, t: pd.Series, zones: np.ndarray):
    b = d.bars
    et, xt = pd.Timestamp(t["entry_time"]).to_datetime64(), pd.Timestamp(t["exit_time"]).to_datetime64()
    i_e = int(np.searchsorted(d.ct, et, side="right"))           # first candle opening at / after entry
    i_x = max(i_e, int(np.searchsorted(d.ot, xt, side="right")) - 1)
    lo = max(0, i_e - BEFORE)
    hi = min(b.n, max(i_x + AFTER_MIN, i_e + AFTER_MIN), i_e + AFTER_MAX)
    x = np.arange(lo, hi)
    gs = spec.subgridspec(4, 1, height_ratios=[5, 1, 1.3, 1.3], hspace=0.05)
    ax = fig.add_subplot(gs[0])
    axv, axm, axr = (fig.add_subplot(gs[k], sharex=ax) for k in (1, 2, 3))
    o, h, l, c = b.o[lo:hi], b.h[lo:hi], b.l[lo:hi], b.c[lo:hi]
    up = c >= o
    ax.vlines(x, l, h, color="#666", linewidth=0.6, zorder=2)
    ax.bar(x[up], (c - o)[up], bottom=o[up], color="#26a69a", width=0.7, zorder=3)
    ax.bar(x[~up], (c - o)[~up], bottom=o[~up], color="#ef5350", width=0.7, zorder=3)
    ax.plot(x, b.e20[lo:hi], color="#ff9800", linewidth=0.9, label="EMA20")
    ax.plot(x, b.e50[lo:hi], color="#3f51b5", linewidth=1.1, label="EMA50")
    e, s, g = float(t["entry"]), float(t["stop"]), float(t["target"])
    ymin, ymax = min(l.min(), s, g), max(h.max(), s, g)
    pad = (ymax - ymin) * 0.04
    for z in zones:
        if ymin - pad <= z <= ymax + pad:
            ax.axhspan(z * 0.9985, z * 1.0015, color="#8e24aa", alpha=0.18, zorder=1)
    # swings confirmed before the entry
    sh = [(i, p) for i, p, cf in b.sh if cf < i_e and i >= lo - 60]
    sl = [(i, p) for i, p, cf in b.sl if cf < i_e and i >= lo - 60]
    for pts, col in ((sh, "#ef6c00"), (sl, "#00897b")):
        if len(pts) >= 2:
            (i1, p1), (i2, p2) = pts[-2], pts[-1]
            xs = np.array([i1, hi - 1])
            ax.plot(xs, p1 + (p2 - p1) / (i2 - i1) * (xs - i1), color=col, linewidth=1.1, alpha=0.9)
    for pts, side in ((sh, 1), (sl, -1)):
        for i, p in pts[-8:]:
            seg = h[max(0, i + 1 - lo):i_e - lo] if side > 0 else l[max(0, i + 1 - lo):i_e - lo]
            taken = (seg.max() > p) if side > 0 and len(seg) else ((seg.min() < p) if len(seg) else False)
            if not taken and i >= lo:
                ax.hlines(p, i, i_e - 0.5, color="#616161", linestyle=(0, (2, 2)), linewidth=0.8)
                ax.plot(i, p, marker="v" if side > 0 else "^", color="#616161", markersize=4)
    ax.axhline(e, color="#1e88e5", linewidth=1)
    ax.axhline(s, color="#c62828", linestyle=":", linewidth=1.4)
    ax.axhline(g, color="#2e7d32", linestyle=":", linewidth=1.4)
    for a_ in (ax, axv, axm, axr):
        a_.axvline(i_e - 0.5, color="black", linestyle="--", linewidth=1.1)
        if i_x < hi:
            a_.axvline(i_x, color="#757575", linestyle="--", linewidth=1)
        a_.tick_params(labelsize=7)
    ax.set_ylim(ymin - pad, ymax + pad)
    beyond = "" if i_x < hi else "  (exit later, off chart)"
    ax.set_title(f"{tf}{beyond}", fontsize=10, loc="left", fontweight="bold")
    axv.bar(x, b.v[lo:hi], color=np.where(up, "#26a69a", "#ef5350"), width=0.7)
    hist = (d.ml - d.ms)[lo:hi]
    axm.bar(x, hist, color=np.where(hist >= 0, "#26a69a", "#ef5350"), width=0.7)
    axm.plot(x, d.ml[lo:hi], color="#1e88e5", linewidth=0.8)
    axm.plot(x, d.ms[lo:hi], color="#ff9800", linewidth=0.8)
    axr.plot(x, b.r[lo:hi], color="#7e57c2", linewidth=0.9)
    for lv, col in ((70, "#c62828"), (30, "#2e7d32")):
        axr.axhline(lv, color=col, linewidth=0.5, linestyle="--")
    axr.set_ylim(0, 100)
    for a_, lab in ((axv, "vol"), (axm, "MACD"), (axr, "RSI")):
        a_.set_ylabel(lab, fontsize=7)
    for a_ in (ax, axv, axm):
        plt_hide = a_.get_xaxis()
        plt_hide.set_visible(False)
    idx = np.linspace(lo, hi - 1, 6).astype(int)
    fmt = "%m-%d" if tf == "1D" else "%m-%d %H:%M"
    axr.set_xticks(idx)
    axr.set_xticklabels([pd.Timestamp(d.ot[i]).strftime(fmt) for i in idx], fontsize=7)


def after_stop_note(t: pd.Series, df5n: pd.DataFrame) -> str:
    t5 = df5n["open_time"].to_numpy()
    H, L = df5n["high"].to_numpy(float), df5n["low"].to_numpy(float)
    xi = int(np.searchsorted(t5, pd.Timestamp(t["exit_time"]).to_datetime64()))
    end = min(len(t5), xi + int(pd.Timedelta(days=30) / FIVE))
    d, e, g = int(t["direction"]), float(t["entry"]), float(t["target"])
    h, l = H[xi:end], L[xi:end]
    back = (h >= e).any() if d > 0 else (l <= e).any()
    tgt = (h >= g).any() if d > 0 else (l <= g).any()
    return ("after the stop, price reached our TARGET within 30 days" if tgt else
            "after the stop, price came back to our entry within 30 days" if back else
            "after the stop, price did not come back to our entry within 30 days")


def build_review(cfg: Config, out_dir: Path, which: str = "holdout") -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    A = pd.read_pickle(ROOT / "results" / "coins_v31.pkl")
    T = A[(A["coin"] == "ETH") & (A["net"] <= 0)].copy()
    T = T[T["hold"]] if which == "holdout" else T[~T["hold"]]
    T = T.sort_values("entry_time").reset_index(drop=True)
    T["entry"] = T["px"]
    T["stop"] = T["entry"] - T["direction"] * T["risk"]
    T["target"] = T["entry"] + T["direction"] * T["setup"].map(TGT) * T["risk"]
    df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
    df5n = df5u.assign(open_time=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
    data = {tf: TFData(df5u, rule) for tf, rule in TFS}
    table = _level_table(df5u)
    out = out_dir / "review" / which
    out.mkdir(parents=True, exist_ok=True)
    meta = []
    for k, t in T.iterrows():
        tid = f"{which[0]}{k + 1:03d}"
        zones = strong_levels(table, pd.Timestamp(t["entry_time"]).tz_localize("UTC"))
        fig = plt.figure(figsize=(18, 11))
        outer = fig.add_gridspec(2, 2, hspace=0.18, wspace=0.08)
        for j, (tf, _) in enumerate(TFS):
            _panel(fig, outer[j // 2, j % 2], data[tf], tf, t, zones)
        side = "LONG" if t["direction"] > 0 else "SHORT"
        fig.suptitle(f"{tid}  {side} {t['setup']} ({t['tf']} signal)  entry {t['entry_time']:%Y-%m-%d %H:%M} UTC "
                     f"@ {t['entry']:,.2f}   stop {t['stop']:,.2f}   target {t['target']:,.2f}   "
                     f"result {t['net']:+.2f}R\n", fontsize=12, fontweight="bold")
        fig.text(0.5, 0.935, "black dashed = entry   grey dashed = exit   blue = entry price   red dotted = stop   "
                 "green dotted = target   purple bands = S/R zones   orange / teal = trendlines (last 2 swing highs / "
                 "lows)   grey dashes + triangles = untaken liquidity   EMA20 orange, EMA50 blue",
                 ha="center", fontsize=9, color="#444")
        p = out / f"{tid}.png"
        fig.savefig(p, dpi=72, bbox_inches="tight")
        plt.close(fig)
        meta.append({"id": tid, "img": f"{tid}.png", "side": side, "setup": t["setup"], "tf": t["tf"],
                     "entry_time": f"{t['entry_time']:%Y-%m-%d %H:%M}", "exit_time": f"{t['exit_time']:%Y-%m-%d %H:%M}",
                     "entry": round(float(t["entry"]), 2), "stop": round(float(t["stop"]), 2),
                     "target": round(float(t["target"]), 2), "result_r": round(float(t["net"]), 2),
                     "after": after_stop_note(t, df5n),
                     "certainty": None if pd.isna(t.get("certainty")) else int(t["certainty"])})
        print(tid, flush=True)
    (out / "trades.json").write_text(json.dumps(meta, indent=1))
    return out


# ----------------------------------------------------------------------------- one trade, large charts
BIG_BEFORE = {"15m": 90, "1h": 90, "4h": 90, "1D": 110}


def plot_big(df5u: pd.DataFrame, tf: str, rule: str, t: dict, zones: np.ndarray, path: Path, liqmap=None,
             marks: list | None = None) -> dict:
    """One timeframe, full width, readable. Returns the indicator readings at the entry (last closed candle)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from .indicators import bollinger, ema

    d = TFData(df5u, rule)
    b = d.bars
    close = pd.Series(b.c)
    e20, e50, e200 = ema(close, 20).to_numpy(), ema(close, 50).to_numpy(), ema(close, 200).to_numpy()
    bm, bu, bl = (x.to_numpy() for x in bollinger(close))
    vavg = pd.Series(b.v).rolling(20).mean().to_numpy()
    et, xt = pd.Timestamp(t["entry_time"]).to_datetime64(), pd.Timestamp(t["exit_time"]).to_datetime64()
    i_e = int(np.searchsorted(d.ct, et, side="right"))
    i_x = max(i_e, int(np.searchsorted(d.ot, xt, side="right")) - 1)
    lo = max(0, i_e - BIG_BEFORE[tf])
    hi = min(b.n, max(i_x + 15, i_e + 15), i_e + 60)
    x = np.arange(lo, hi)
    fig = plt.figure(figsize=(14, 17))
    gs = fig.add_gridspec(4, 2, height_ratios=[8, 1.4, 1.8, 1.8], width_ratios=[10, 1.6], hspace=0.07, wspace=0.03)
    ax = fig.add_subplot(gs[0, 0])
    axv, axm, axr = (fig.add_subplot(gs[k, 0], sharex=ax) for k in (1, 2, 3))
    axl = fig.add_subplot(gs[0, 1], sharey=ax) if liqmap is not None else None
    o, h, l, c = b.o[lo:hi], b.h[lo:hi], b.l[lo:hi], b.c[lo:hi]
    up = c >= o
    ax.fill_between(x, bl[lo:hi], bu[lo:hi], color="#90a4ae", alpha=0.08, zorder=0)
    ax.plot(x, bu[lo:hi], color="#546e7a", linewidth=1.3, label="Bollinger upper")
    ax.plot(x, bm[lo:hi], color="#546e7a", linewidth=1.1, linestyle="--", label="Bollinger middle (SMA 20)")
    ax.plot(x, bl[lo:hi], color="#546e7a", linewidth=1.3, label="Bollinger lower")
    ax.vlines(x, l, h, color="#555", linewidth=0.8, zorder=2)
    ax.bar(x[up], (c - o)[up], bottom=o[up], color="#26a69a", width=0.72, zorder=3)
    ax.bar(x[~up], (c - o)[~up], bottom=o[~up], color="#ef5350", width=0.72, zorder=3)
    ax.plot(x, e20[lo:hi], color="#fb8c00", linewidth=1.4, label="EMA 20")
    ax.plot(x, e50[lo:hi], color="#1e88e5", linewidth=1.6, label="EMA 50")
    ax.plot(x, e200[lo:hi], color="#8e24aa", linewidth=1.8, label="EMA 200")
    e, s, g = t["entry"], t["stop"], t["target"]
    ymin, ymax = min(l.min(), s, e), max(h.max(), s, e)
    rng0 = ymax - ymin
    target_off = not (ymin - 0.3 * rng0 <= g <= ymax + 0.3 * rng0)          # a far target would squash the candles
    if not target_off:
        ymin, ymax = min(ymin, g), max(ymax, g)
    pad = (ymax - ymin) * 0.05
    last_lab = -np.inf
    for z in sorted(zones):
        if ymin - pad <= z <= ymax + pad:
            ax.axhspan(z * 0.998, z * 1.002, color="#ab47bc", alpha=0.16, zorder=1)
            if z - last_lab >= 0.035 * (ymax - ymin):                         # keep labels apart
                ax.text(hi - 1, z, f"S/R {z:,.0f} ", ha="right", va="center", fontsize=12, color="#7b1fa2",
                        bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.75))
                last_lab = z
    sh = [(i, p) for i, p, cf in b.sh if cf < i_e and i >= lo - 80]
    sl = [(i, p) for i, p, cf in b.sl if cf < i_e and i >= lo - 80]
    for pts, col, name in ((sh, "#e65100", "trendline (highs)"), (sl, "#00796b", "trendline (lows)")):
        if len(pts) >= 2:
            (i1, p1), (i2, p2) = pts[-2], pts[-1]
            xs = np.array([max(i1, lo), hi - 1])
            ax.plot(xs, p1 + (p2 - p1) / (i2 - i1) * (xs - i1), color=col, linewidth=1.5, label=name)
    liq = []
    for pts, side in ((sh, 1), (sl, -1)):
        for i, p in pts[-10:]:
            seg = h[max(0, i + 1 - lo):i_e - lo] if side > 0 else l[max(0, i + 1 - lo):i_e - lo]
            taken = len(seg) and ((seg.max() > p) if side > 0 else (seg.min() < p))
            if not taken and i >= lo:
                ax.hlines(p, i, i_e - 0.5, color="#424242", linestyle=(0, (3, 2)), linewidth=1)
                ax.plot(i, p, marker="v" if side > 0 else "^", color="#424242", markersize=6)
                ax.text(i, p, f" liq {p:,.0f}", fontsize=13, color="#424242",
                        va="bottom" if side > 0 else "top")
                liq.append((side, p))
    # equal highs / lows: two untaken swings within 0.15% = stops resting there
    for side in (1, -1):
        ps = sorted(p for sd, p in liq if sd == side)
        for p1, p2 in zip(ps, ps[1:]):
            if abs(p2 - p1) / p1 <= 0.0015:
                m_ = (p1 + p2) / 2
                ax.axhspan(m_ * 0.9993, m_ * 1.0007, color="#ffca28", alpha=0.45, zorder=1.4)
                ax.text(i_e - 1, m_, f"EQUAL {'HIGHS' if side > 0 else 'LOWS'} {m_:,.0f}: stops rest here ",
                        ha="right", va="bottom" if side > 0 else "top", fontsize=13, fontweight="bold", color="#bf360c")
    # estimated liquidation levels (real open interest), in their own panel on the right (same price scale)
    if axl is not None:
        (lp, lw), (sp_, sw_) = liqmap
        edges = np.linspace(ymin - pad, ymax + pad, 80)
        hl, _ = np.histogram(lp, bins=edges, weights=lw)
        hs, _ = np.histogram(sp_, bins=edges, weights=sw_)
        mids = (edges[:-1] + edges[1:]) / 2
        hgt = (edges[1] - edges[0]) * 0.9
        axl.barh(mids, hl * 100, height=hgt, color="#e53935", alpha=0.7, label="longs liquidated")
        axl.barh(mids, hs * 100, height=hgt, color="#43a047", alpha=0.7, label="shorts liquidated")
        axl.axhline(e, color="#1565c0", linewidth=1.1)
        axl.axhline(s, color="#c62828", linewidth=1.1, linestyle=(0, (4, 2)))
        axl.axhline(g, color="#2e7d32", linewidth=1.1, linestyle=(0, (4, 2)))
        axl.set_title("liquidations at entry\n(est. from open interest)", fontsize=14)
        axl.tick_params(labelleft=False, labelsize=7)
        axl.set_xlabel("% of open interest", fontsize=13)
        axl.legend(loc="upper right", fontsize=12)
        axl.grid(alpha=0.15)
    # Fibonacci: the last leg in the trade direction inside the window, using only candles closed before entry.
    # Long: lowest low of the window -> highest high after it; retracements measured down from that high,
    # extensions up from the low (short: mirrored).
    dirn = int(t.get("direction", 1))
    pre_h, pre_l = b.h[lo:i_e], b.l[lo:i_e]
    fib = {}
    if len(pre_h) > 5:
        if dirn > 0:
            k0 = int(np.argmin(pre_l)); k1 = k0 + int(np.argmax(pre_h[k0:]))
            f_lo, f_hi = pre_l[k0], pre_h[k1]
            start, end_ = lo + k0, lo + k1
            lv_of = lambda r: f_hi - r * (f_hi - f_lo)  # noqa: E731
            ext_of = lambda r: f_lo + r * (f_hi - f_lo)  # noqa: E731
        else:
            k0 = int(np.argmax(pre_h)); k1 = k0 + int(np.argmin(pre_l[k0:]))
            f_hi, f_lo = pre_h[k0], pre_l[k1]
            start, end_ = lo + k0, lo + k1
            lv_of = lambda r: f_lo + r * (f_hi - f_lo)  # noqa: E731
            ext_of = lambda r: f_hi - r * (f_hi - f_lo)  # noqa: E731
        ax.plot([start, end_], [f_lo, f_hi] if dirn > 0 else [f_hi, f_lo], color="#f9a825", linewidth=1.2,
                linestyle=(0, (1, 1)), label="Fibonacci leg")
        for r_ in (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0):
            v = lv_of(r_)
            fib[f"ret_{r_:g}"] = float(v)
            ax.hlines(v, start, hi - 1, color="#f9a825", linewidth=1.0 if r_ in (0.5, 0.618) else 0.7,
                      linestyle="-" if r_ in (0.5, 0.618) else "--", alpha=0.9, zorder=1.5)
            if ymin - pad <= v <= ymax + pad:
                ax.text(lo + 0.6 * (hi - lo), v, f"Fib {r_:g}  {v:,.0f}", fontsize=12, color="#e65100", va="bottom",
                        bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.75))
        for r_ in (1.272, 1.618):
            v = ext_of(r_)
            fib[f"ext_{r_:g}"] = float(v)
            if ymin - pad <= v <= ymax + pad:
                ax.hlines(v, end_, hi - 1, color="#f57f17", linewidth=0.9, linestyle="-.")
                ax.text(lo + 0.6 * (hi - lo), v, f"Fib ext {r_:g}  {v:,.0f}", fontsize=12, color="#e65100", va="bottom",
                        bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.75))
        fib["leg"] = (float(f_lo), float(f_hi), pd.Timestamp(d.ot[start]).strftime("%d %b %Y %H:%M"),
                      pd.Timestamp(d.ot[end_]).strftime("%d %b %Y %H:%M"))
    if target_off:
        ax.text(lo + 1, ymax + pad * 0.4, f" target {g:,.2f} is above the chart \u2191 " if (g - e) > 0 else f" target {g:,.2f} is below the chart \u2193 ",
                fontsize=14, color="#2e7d32", fontweight="bold", va="top",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="#2e7d32", lw=0.8), zorder=6)
    for lv, col, name in ((e, "#1565c0", "entry"), (s, "#c62828", "stop")) + (() if target_off else ((g, "#2e7d32", "target"),)):
        ax.axhline(lv, color=col, linewidth=1.3, linestyle="-" if name == "entry" else (0, (4, 2)))
        ax.text(lo + 1, lv, f" {name} {lv:,.2f} ", ha="left", va="center", fontsize=15, color=col, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=col, lw=0.8, alpha=0.9), zorder=6)
    for a_ in (ax, axv, axm, axr):
        a_.axvline(i_e - 0.5, color="black", linestyle="--", linewidth=1.3)
        if i_x < hi:
            a_.axvline(i_x, color="#616161", linestyle=":", linewidth=1.3)
        a_.grid(alpha=0.15)
    ax.text(i_e - 0.5, ymax + pad * 0.6, " ENTRY", fontsize=15, fontweight="bold")
    for mt, mlab, mcol in (marks or []):
        k_ = int(np.searchsorted(d.ot, pd.Timestamp(mt).to_datetime64(), side="right")) - 1
        if lo <= k_ < hi:
            for a_ in (ax, axv, axm, axr):
                a_.axvline(k_, color=mcol, linestyle="-.", linewidth=1.6)
            ax.text(k_, ymin + (ymax - ymin) * 0.5, f" {mlab}", fontsize=14, color=mcol, fontweight="bold", rotation=90,
                    va="center", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=mcol, lw=0.8, alpha=0.9))
    if i_x < hi:
        ax.text(i_x, ymin - pad * 0.6, " EXIT (" + str(t.get("exit_label", "stop")) + ")", fontsize=15, color="#616161",
                fontweight="bold")
    ax.set_ylim(ymin - pad, ymax + pad)
    for a_ in (ax, axv, axm, axr):
        a_.tick_params(axis="y", labelsize=13)
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0), fontsize=13, ncol=6, frameon=False)
    off = "" if i_x < hi else "   (exit is later, beyond the right edge)"
    ax.set_title(f"{tf} chart{off}", fontsize=20, loc="left", fontweight="bold", pad=58)
    axv.bar(x, b.v[lo:hi], color=np.where(up, "#26a69a", "#ef5350"), width=0.72)
    axv.plot(x, vavg[lo:hi], color="#424242", linewidth=1, label="20-candle average")
    axv.legend(loc="upper left", fontsize=13)
    hist = (d.ml - d.ms)[lo:hi]
    axm.bar(x, hist, color=np.where(hist >= 0, "#26a69a", "#ef5350"), width=0.72)
    axm.plot(x, d.ml[lo:hi], color="#1e88e5", linewidth=1, label="MACD 12,26")
    axm.plot(x, d.ms[lo:hi], color="#fb8c00", linewidth=1, label="signal 9")
    axm.legend(loc="upper left", fontsize=13)
    axr.plot(x, b.r[lo:hi], color="#6a1b9a", linewidth=1.2)
    for lv in (70, 50, 30):
        axr.axhline(lv, color="#9e9e9e", linewidth=0.7, linestyle="--")
    axr.set_ylim(0, 100)
    for a_, lab in ((axv, "Volume"), (axm, "MACD"), (axr, "RSI 14")):
        a_.set_ylabel(lab, fontsize=15)
    for a_ in (ax, axv, axm):
        a_.tick_params(labelbottom=False)
    idx = np.linspace(lo, hi - 1, 6).astype(int)
    fmt = "%d %b %Y" if tf == "1D" else "%d %b %Y\n%H:%M"
    axr.set_xticks(idx)
    axr.set_xticklabels([pd.Timestamp(d.ot[i]).strftime(fmt) for i in idx], fontsize=14)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    j = i_e - 1                                                     # last candle closed at entry
    return {"tf": tf, "close": float(b.c[j]), "ema20": float(e20[j]), "ema50": float(e50[j]), "ema200": float(e200[j]),
            "bb_up": float(bu[j]), "bb_lo": float(bl[j]), "rsi": float(b.r[j]), "macd_hist": float((d.ml - d.ms)[j]),
            "vol_vs_avg": float(b.v[j] / vavg[j]) if vavg[j] > 0 else None,
            "liq_below": sorted([p for sd, p in liq if sd < 0 and p < e], reverse=True)[:3],
            "liq_above": sorted([p for sd, p in liq if sd > 0 and p > e])[:3], "fib": fib}
