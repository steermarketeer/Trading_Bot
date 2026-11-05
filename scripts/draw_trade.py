"""Draw the four journal charts (15m / 1h / 4h / 1D) for one trade.
usage: PYTHONPATH=. python scripts/draw_trade.py ID "ENTRY_TIME" "EXIT_TIME" ENTRY RISK DIRECTION TARGET_R"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from bot.config import load_config
from bot.data import load_klines_5m
from bot.study.levels import _level_table, strong_levels
from bot.study.review import plot_big, TFS
from bot.study.flow import load_flow
from bot.study.liquidation import _hourly, load_oi_hourly, liq_levels

tid, et, xt, entry, risk, d, tr = sys.argv[1:8]
marks = [(sys.argv[8], sys.argv[9], "#d81b60")] if len(sys.argv) > 9 else None
exit_label = sys.argv[10] if len(sys.argv) > 10 else "stop"
entry, risk, d, tr = float(entry), float(risk), int(d), float(tr)
cfg = load_config()
df5u, _ = load_klines_5m(cfg.data_dir, cfg.symbol)
hb_df = _hourly(load_flow(cfg.data_dir, cfg.symbol))
hb = {"t": hb_df["open_time"].to_numpy()} | {c: hb_df[c].to_numpy(float) for c in ("low", "high", "tp", "volume", "buy")}
hb["oi"] = load_oi_hourly(cfg.data_dir, cfg.symbol, hb_df["open_time"])
t = {"entry_time": pd.Timestamp(et), "exit_time": pd.Timestamp(xt), "entry": entry, "risk": risk, "direction": d}
t["stop"], t["target"] = entry - d * risk, entry + d * tr * risk
t["exit_label"] = exit_label
lm = liq_levels(hb, t["entry_time"], "oi")
z = strong_levels(_level_table(df5u), t["entry_time"].tz_localize("UTC"))
out = Path("reports/review/one")
facts = {}
for k, (tf, rule) in enumerate(TFS):
    facts[tf] = plot_big(df5u, tf, rule, t, z, out / f"{tid}_{k + 1}_{tf}.png", lm, marks)
(lp, lw), (sp, sw) = lm
b = np.arange(np.floor(entry * 0.9 / 10) * 10, entry * 1.1, 10)
hl, _ = np.histogram(lp, bins=b, weights=lw)
hs, _ = np.histogram(sp, bins=b, weights=sw)
facts["liq_bins"] = [(float(b[i]), float(b[i + 1]), round(hl[i] * 100, 2), round(hs[i] * 100, 2))
                     for i in range(len(b) - 1) if hl[i] > 0.0015 or hs[i] > 0.0015]
facts["zones"] = [round(float(v)) for v in z if entry * 0.9 < v < entry * 1.1]
df = df5u.assign(t=pd.to_datetime(df5u["open_time"], utc=True).dt.tz_convert(None))
w = df[(df.t >= t["entry_time"]) & (df.t < t["entry_time"] + pd.Timedelta(days=12))]
w = w.set_index("t")
daily = w.resample("12h").agg({"low": "min", "high": "max"})
facts["path_12h"] = [(str(i), float(r.low), float(r.high)) for i, r in daily.iterrows()]
facts["target_hit"] = str(w[(w.high >= t["target"]) if d > 0 else (w.low <= t["target"])].index.min())
print(json.dumps(facts, default=str, indent=0))
