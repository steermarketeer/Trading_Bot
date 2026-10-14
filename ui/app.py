"""
SHADOW DESK — paper-only monitoring UI for the ETH HTF triple shadow.

Run:
    .\\.venv\\Scripts\\streamlit.exe run ui/app.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

# Allow `import desk_visibility` when Streamlit runs ui/app.py
_UI_DIR = Path(__file__).resolve().parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

import desk_chat as chat  # noqa: E402
import desk_portfolio as port  # noqa: E402
import desk_visibility as vis  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SHADOW = ROOT / "shadow"
ORDERBOOK = ROOT / "data" / "orderbook"
SCRIPT = ROOT / "shadow_htf_v4.py"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)

LIQUIDITY_SYMBOLS = ("ETHUSDT", "BTCUSDT")
DEFAULT_DEPTH_LEVELS = 20

STRATEGY_META = [
    {
        "id": "s1",
        "folder": "s1_both_align_no_stop",
        "title": "Strategy 1",
        "tagline": "Align · cool5 / stable5",
    },
    {
        "id": "s2",
        "folder": "s2_both_cool7_stable7",
        "title": "Strategy 2",
        "tagline": "Stricter cool7 / stable7",
    },
    {
        "id": "s3",
        "folder": "s3_both_btc_confirm",
        "title": "Strategy 3",
        "tagline": "BTC trend confirm",
    },
]


def inject_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
  font-family: 'IBM Plex Sans', sans-serif;
}
.stApp {
  background:
    radial-gradient(1200px 600px at 8% -10%, rgba(46, 139, 126, 0.18), transparent 55%),
    radial-gradient(900px 500px at 100% 0%, rgba(201, 148, 74, 0.12), transparent 50%),
    linear-gradient(165deg, #e8eee9 0%, #d5ddd8 42%, #cfd8d4 100%);
  color: #1a2421;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: 1rem; }

.block-container {
  padding-top: 1.4rem !important;
  padding-bottom: 3rem !important;
  max-width: 1180px;
}

.hero {
  margin: 0 0 1.4rem 0;
  padding: 1.6rem 1.8rem 1.5rem;
  border-radius: 0;
  background:
    linear-gradient(135deg, rgba(26, 36, 33, 0.96) 0%, rgba(33, 52, 48, 0.94) 55%, rgba(28, 58, 52, 0.92) 100%);
  color: #f2f6f4;
  box-shadow: 0 18px 40px rgba(26, 36, 33, 0.18);
  position: relative;
  overflow: hidden;
}
.hero::after {
  content: "";
  position: absolute;
  inset: auto -10% -40% 55%;
  height: 180px;
  background: radial-gradient(circle, rgba(62, 168, 152, 0.35), transparent 65%);
  pointer-events: none;
}
.hero-brand {
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: clamp(2.2rem, 4.5vw, 3.2rem);
  letter-spacing: -0.03em;
  line-height: 1;
  margin: 0 0 0.55rem 0;
}
.hero-line {
  font-size: 1.05rem;
  color: rgba(242, 246, 244, 0.78);
  max-width: 36rem;
  margin: 0 0 1rem 0;
}
.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  align-items: center;
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.7rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  font-family: 'IBM Plex Mono', monospace;
}
.pill-paper {
  background: rgba(62, 168, 152, 0.22);
  color: #9ee0d3;
  border: 1px solid rgba(62, 168, 152, 0.45);
}
.pill-live-off {
  background: rgba(201, 148, 74, 0.18);
  color: #f0d2a0;
  border: 1px solid rgba(201, 148, 74, 0.4);
}
.pill-neutral {
  background: rgba(242, 246, 244, 0.08);
  color: rgba(242, 246, 244, 0.85);
  border: 1px solid rgba(242, 246, 244, 0.16);
}

.strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
  margin-bottom: 1.25rem;
}
@media (max-width: 900px) {
  .strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
.strip-item {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(26, 36, 33, 0.08);
  backdrop-filter: blur(8px);
  padding: 0.95rem 1rem;
}
.strip-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #5c6b66;
  margin-bottom: 0.35rem;
  font-weight: 600;
}
.strip-value {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 1.35rem;
  color: #1a2421;
  letter-spacing: -0.02em;
}
.strip-sub {
  margin-top: 0.2rem;
  font-size: 0.78rem;
  color: #62706b;
  font-family: 'IBM Plex Mono', monospace;
}

.agree-banner {
  margin: 0 0 1.25rem 0;
  padding: 1rem 1.2rem;
  background: rgba(255,255,255,0.62);
  border-left: 4px solid #2e8b7e;
  border: 1px solid rgba(26, 36, 33, 0.08);
  border-left-width: 4px;
  border-left-color: #2e8b7e;
}
.agree-banner.disagree { border-left-color: #c97a4a; }
.agree-banner.active { border-left-color: #3a7ca5; }
.agree-title {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 1.15rem;
  margin: 0 0 0.25rem 0;
}
.agree-sub { color: #5c6b66; font-size: 0.9rem; margin: 0; }

.strat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.9rem;
  margin-bottom: 0.5rem;
}
@media (max-width: 980px) {
  .strat-grid { grid-template-columns: 1fr; }
}
.strat {
  background: rgba(255,255,255,0.68);
  border: 1px solid rgba(26, 36, 33, 0.09);
  padding: 1.05rem 1.1rem 1.15rem;
  min-height: 210px;
}
.strat-top {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: flex-start;
  margin-bottom: 0.7rem;
}
.strat-name {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 1.05rem;
  margin: 0;
}
.strat-code {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.75rem;
  color: #5c6b66;
  margin-top: 0.15rem;
}
.side-chip {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.22rem 0.55rem;
  border-radius: 4px;
  text-transform: uppercase;
}
.side-flat { background: #e4ebe7; color: #4a5853; }
.side-long { background: #d5efe8; color: #1f6b5f; }
.side-short { background: #f5e1d6; color: #8a4a2d; }
.metric-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.55rem 0.8rem;
}
.metric-k {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6a7873;
  font-weight: 600;
}
.metric-v {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.92rem;
  color: #1a2421;
  font-weight: 500;
}
.eq-track {
  margin-top: 0.95rem;
  height: 7px;
  background: rgba(26, 36, 33, 0.08);
  overflow: hidden;
}
.eq-fill {
  height: 100%;
  background: linear-gradient(90deg, #2e8b7e, #4eb8a6);
}
.eq-fill.down {
  background: linear-gradient(90deg, #c97a4a, #e0a078);
}
.section-title {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 1.35rem;
  margin: 1.4rem 0 0.65rem 0;
  letter-spacing: -0.02em;
}
.note {
  color: #5c6b66;
  font-size: 0.9rem;
  margin: 0 0 0.9rem 0;
}
div[data-testid="stTabs"] button {
  font-family: 'Syne', sans-serif;
  font-weight: 600;
}
div[data-testid="stDataFrame"] {
  border: 1px solid rgba(26, 36, 33, 0.08);
}
.stButton > button {
  background: #1a2421 !important;
  color: #f2f6f4 !important;
  border: none !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
  border-radius: 4px !important;
  padding: 0.55rem 1.1rem !important;
}
.stButton > button:hover {
  background: #2e8b7e !important;
  color: #fff !important;
}
.run-box {
  background: rgba(255,255,255,0.68);
  border: 1px solid rgba(26, 36, 33, 0.09);
  padding: 1.2rem 1.3rem;
}
.footer-note {
  margin-top: 2rem;
  font-size: 0.8rem;
  color: #6a7873;
  font-family: 'IBM Plex Mono', monospace;
}
.chat-box {
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(26, 36, 33, 0.1);
  padding: 0.95rem 1.1rem 1.05rem;
  margin: 0 0 1.15rem 0;
}
.chat-title {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 1.05rem;
  margin: 0 0 0.25rem 0;
}
.chat-hint {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.75rem;
  color: #5c6b66;
  margin: 0 0 0.65rem 0;
}
.chat-bubble-user {
  background: rgba(46, 139, 126, 0.12);
  border-radius: 10px 10px 4px 10px;
  padding: 0.65rem 0.8rem;
  margin: 0.35rem 0 0.35rem 15%;
}
.chat-bubble-bot {
  background: rgba(26, 36, 33, 0.05);
  border-radius: 10px 10px 10px 4px;
  padding: 0.65rem 0.8rem;
  margin: 0.35rem 15% 0.35rem 0;
  border-left: 3px solid #2e8b7e;
}
.chat-role {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  color: #5c6b66;
  margin-bottom: 0.25rem;
}

/* Readable typed text in chat + inputs */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input,
[data-testid="stChatInput"] div[contenteditable="true"],
.stTextInput input,
.stTextArea textarea,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
section[data-testid="stChatInput"] textarea {
  color: #1a2421 !important;
  caret-color: #1a2421 !important;
  background-color: #ffffff !important;
  -webkit-text-fill-color: #1a2421 !important;
}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
  color: #5c6b66 !important;
  -webkit-text-fill-color: #5c6b66 !important;
  opacity: 1 !important;
}
[data-testid="stChatInput"] {
  background: transparent !important;
}
[data-testid="stChatInput"] > div {
  background-color: #ffffff !important;
  border: 1px solid rgba(26, 36, 33, 0.18) !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=15)
def load_latest() -> dict | None:
    path = SHADOW / "latest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(ttl=15)
def load_csv(rel: str) -> pd.DataFrame:
    path = SHADOW / rel
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        try:
            return pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame()


@st.cache_data(ttl=15)
def load_run_history() -> pd.DataFrame:
    path = SHADOW / "run_history.jsonl"
    if not path.exists():
        return pd.DataFrame()
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "run_at_utc" in df.columns:
        df = df.sort_values("run_at_utc", ascending=False)
    return df.reset_index(drop=True)


def daily_results_table(limit_days: int = 60) -> pd.DataFrame:
    """One row per market day with S1/S2/S3 action summary."""
    frames = []
    for meta in STRATEGY_META:
        df = load_csv(f"{meta['folder']}/signals.csv")
        if df.empty or "day" not in df.columns:
            continue
        tmp = df.copy()
        tmp["strategy_id"] = meta["id"].upper()
        # last signal of the day wins
        tmp = tmp.sort_values("ts_utc" if "ts_utc" in tmp.columns else tmp.columns[0])
        tmp = tmp.groupby("day", as_index=False).tail(1)
        frames.append(tmp[[
            c for c in ["day", "strategy_id", "action", "side", "price", "regime", "detail", "equity"]
            if c in tmp.columns
        ]])
    if not frames:
        return pd.DataFrame()

    long = pd.concat(frames, ignore_index=True)
    if "side" not in long.columns:
        long["side"] = "flat"
    if "detail" not in long.columns:
        long["detail"] = ""
    long["side"] = long["side"].fillna("flat").astype(str).replace({"nan": "flat", "None": "flat"})
    long["detail"] = long["detail"].fillna("").astype(str).replace({"nan": ""})
    long["summary"] = (
        long["action"].astype(str)
        + " "
        + long["side"]
        + long["detail"].map(lambda d: f" ({d})" if d else "")
    )

    pivot = long.pivot_table(
        index="day",
        columns="strategy_id",
        values="summary",
        aggfunc="last",
    )
    # attach regime/price/equity from S1 when present else any
    meta_cols = []
    for col, src in [("regime", "regime"), ("close", "price"), ("s1_equity", "equity")]:
        if src in long.columns:
            sub = long[long["strategy_id"] == "S1"] if (long["strategy_id"] == "S1").any() else long
            m = sub.groupby("day")[src].last()
            pivot[col] = m
            meta_cols.append(col)

    # agreement from sides that day
    sides = long.pivot_table(index="day", columns="strategy_id", values="side", aggfunc="last")
    def _agree(row):
        vals = [str(v).lower() for v in row.values if pd.notna(v) and str(v).lower() not in ("nan", "none", "")]
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
    if not sides.empty:
        pivot["agreement"] = sides.apply(_agree, axis=1)

    pivot = pivot.reset_index().sort_values("day", ascending=False).head(limit_days)
    prefer = ["day", "agreement", "regime", "close", "S1", "S2", "S3", "s1_equity"]
    cols = [c for c in prefer if c in pivot.columns] + [c for c in pivot.columns if c not in prefer]
    return pivot[cols]


def flatten_run_history(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    # expand strategy statuses into columns when present
    if "strategies" in out.columns:
        for sid in ("s1", "s2", "s3"):
            out[f"{sid}_status"] = out["strategies"].apply(
                lambda xs, sid=sid: next(
                    (x.get("status") for x in (xs or []) if isinstance(x, dict) and x.get("id") == sid),
                    None,
                )
            )
            out[f"{sid}_side"] = out["strategies"].apply(
                lambda xs, sid=sid: next(
                    (x.get("side") for x in (xs or []) if isinstance(x, dict) and x.get("id") == sid),
                    None,
                )
            )
            out[f"{sid}_day"] = out["strategies"].apply(
                lambda xs, sid=sid: next(
                    (x.get("last_processed_day") for x in (xs or []) if isinstance(x, dict) and x.get("id") == sid),
                    None,
                )
            )
    show_cols = [c for c in [
        "run_at_utc", "ok", "error", "agreement", "sides", "n_active",
        "latest_close", "last_processed_day", "processed_days_total",
        "s1_status", "s1_side", "s2_status", "s2_side", "s3_status", "s3_side",
        "mode",
    ] if c in out.columns]
    return out[show_cols]


def list_orderbook_days(symbol: str, levels: int = DEFAULT_DEPTH_LEVELS) -> list[str]:
    if not ORDERBOOK.exists():
        return []
    days = []
    for p in ORDERBOOK.glob(f"{symbol}_depth{levels}_*.csv.gz"):
        # ETHUSDT_depth20_2026-09-30.csv.gz
        stem = p.name.replace(".csv.gz", "")
        day = stem.split("_")[-1]
        days.append(day)
    return sorted(set(days), reverse=True)


@st.cache_data(ttl=30)
def load_orderbook_day(symbol: str, day: str, levels: int = DEFAULT_DEPTH_LEVELS) -> pd.DataFrame:
    path = ORDERBOOK / f"{symbol}_depth{levels}_{day}.csv.gz"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, compression="gzip")
    except Exception:
        try:
            df = pd.read_csv(path, compression="gzip", engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame()
    if df.empty:
        return df
    if "ts_utc" in df.columns:
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True, errors="coerce")
        df = df.dropna(subset=["ts_utc"]).sort_values("ts_utc")
    return df.reset_index(drop=True)


@st.cache_data(ttl=30)
def load_orderbook_recent(symbol: str, max_days: int = 3, levels: int = DEFAULT_DEPTH_LEVELS) -> pd.DataFrame:
    days = list_orderbook_days(symbol, levels)[:max_days]
    frames = [load_orderbook_day(symbol, d, levels) for d in days]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values("ts_utc").reset_index(drop=True)


def snapshot_age_seconds(df: pd.DataFrame) -> float | None:
    if df.empty or "ts_utc" not in df.columns:
        return None
    last = df["ts_utc"].iloc[-1]
    if pd.isna(last):
        return None
    now = pd.Timestamp.now(tz="UTC")
    return max(0.0, (now - last).total_seconds())


def depth_ladder(row: pd.Series, levels: int = 10) -> pd.DataFrame:
    bids, asks = [], []
    for i in range(1, levels + 1):
        bq = row.get(f"bid_qty_{i}")
        aq = row.get(f"ask_qty_{i}")
        bp = row.get(f"bid_px_{i}")
        ap = row.get(f"ask_px_{i}")
        if pd.notna(bq):
            bids.append({"level": i, "side": "bid", "price": bp, "qty": float(bq)})
        if pd.notna(aq):
            asks.append({"level": i, "side": "ask", "price": ap, "qty": float(aq)})
    if not bids and not asks:
        return pd.DataFrame()
    # chart-friendly: negative bid qty for opposing bars
    out_rows = []
    for b in bids:
        out_rows.append({"level": b["level"], "bid_qty": b["qty"], "ask_qty": 0.0, "bid_px": b["price"], "ask_px": None})
    by_level = {r["level"]: r for r in out_rows}
    for a in asks:
        if a["level"] in by_level:
            by_level[a["level"]]["ask_qty"] = a["qty"]
            by_level[a["level"]]["ask_px"] = a["price"]
        else:
            by_level[a["level"]] = {
                "level": a["level"], "bid_qty": 0.0, "ask_qty": a["qty"],
                "bid_px": None, "ask_px": a["price"],
            }
    return pd.DataFrame(by_level.values()).sort_values("level")


def depth_within_bps(row: pd.Series, bps: float = 5.0, levels: int = DEFAULT_DEPTH_LEVELS) -> dict:
    mid = row.get("mid")
    if mid is None or pd.isna(mid) or float(mid) <= 0:
        return {"bid_qty": 0.0, "ask_qty": 0.0}
    mid = float(mid)
    band = mid * (bps / 10_000.0)
    bid_q = ask_q = 0.0
    for i in range(1, levels + 1):
        bp, bq = row.get(f"bid_px_{i}"), row.get(f"bid_qty_{i}")
        ap, aq = row.get(f"ask_px_{i}"), row.get(f"ask_qty_{i}")
        if pd.notna(bp) and pd.notna(bq) and abs(mid - float(bp)) <= band:
            bid_q += float(bq)
        if pd.notna(ap) and pd.notna(aq) and abs(float(ap) - mid) <= band:
            ask_q += float(aq)
    return {"bid_qty": bid_q, "ask_qty": ask_q}


def liquidity_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "ts_utc" not in df.columns:
        return pd.DataFrame()
    x = df.copy()
    x["day"] = x["ts_utc"].dt.strftime("%Y-%m-%d")
    rows = []
    for day, g in x.groupby("day"):
        spr = g["spread_bps"].dropna() if "spread_bps" in g.columns else pd.Series(dtype=float)
        imb = g["imbalance"].dropna() if "imbalance" in g.columns else pd.Series(dtype=float)
        rows.append({
            "day": day,
            "n_snapshots": len(g),
            "avg_spread_bps": float(spr.mean()) if len(spr) else None,
            "max_spread_bps": float(spr.max()) if len(spr) else None,
            "avg_imbalance": float(imb.mean()) if len(imb) else None,
            "pct_spread_gt_0_5bps": float((spr > 0.5).mean() * 100) if len(spr) else None,
            "avg_bid_qty": float(g["bid_qty_sum"].mean()) if "bid_qty_sum" in g.columns else None,
            "avg_ask_qty": float(g["ask_qty_sum"].mean()) if "ask_qty_sum" in g.columns else None,
        })
    return pd.DataFrame(rows).sort_values("day", ascending=False)


@st.cache_data(ttl=120)
def load_market_daily_cached() -> pd.DataFrame:
    return vis.build_market_daily()


@st.cache_data(ttl=30)
def load_ops_health(latest_json: str) -> dict:
    latest = json.loads(latest_json) if latest_json else None
    return vis.ops_health(latest)


@st.cache_data(ttl=60)
def load_decisions(latest_json: str) -> list[dict]:
    latest = json.loads(latest_json) if latest_json else None
    if not latest:
        return []
    daily = load_market_daily_cached()
    return vis.decisions_for_latest(latest, daily)


@st.cache_data(ttl=30)
def load_agreement_timeline(limit_days: int = 60) -> pd.DataFrame:
    return vis.agreement_timeline(limit_days)


@st.cache_data(ttl=30)
def load_regime_strip(limit_days: int = 45) -> pd.DataFrame:
    return vis.regime_price_strip(limit_days)


def render_ops_health(latest: dict | None) -> None:
    health = load_ops_health(json.dumps(latest) if latest else "")
    sched = health.get("scheduler") or {}
    shadow_ok = health.get("shadow_last_ok")
    shadow_badge = "OK" if shadow_ok is True else ("FAIL" if shadow_ok is False else "—")
    sched_badge = "OK" if sched.get("ok") else ("FAIL" if sched.get("available") else "N/A")
    ob = health.get("orderbook_age") or "—"
    kl = health.get("klines_age") or "—"
    st.markdown(
        f"""
<div class="strip">
  <div class="strip-item">
    <div class="strip-label">Shadow last run</div>
    <div class="strip-value" style="font-size:1rem">{health.get("shadow_last_run") or "—"}</div>
    <div class="strip-sub">log ok={shadow_badge} · day {health.get("last_processed") or "—"}</div>
  </div>
  <div class="strip-item">
    <div class="strip-label">Task Scheduler</div>
    <div class="strip-value" style="font-size:1rem">{sched_badge}</div>
    <div class="strip-sub">{sched.get("last_result") or sched.get("error") or "—"} · next {sched.get("next_run") or "—"}</div>
  </div>
  <div class="strip-item">
    <div class="strip-label">Order book age</div>
    <div class="strip-value" style="font-size:1rem">{ob}</div>
    <div class="strip-sub">record_orderbook.py</div>
  </div>
  <div class="strip-item">
    <div class="strip-label">Klines age</div>
    <div class="strip-value" style="font-size:1rem">{kl}</div>
    <div class="strip-sub">ETHUSDT_5m.csv mtime</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_panels(latest: dict | None) -> None:
    if not latest:
        return
    try:
        decisions = load_decisions(json.dumps(latest))
    except Exception as e:
        st.warning(f"Decision panel unavailable: {e}")
        return
    if not decisions:
        st.info("No decision diagnostics yet.")
        return
    cols = st.columns(len(decisions))
    for col, d in zip(cols, decisions):
        with col:
            verd = d.get("verdict", "—")
            side = fmt_side(d.get("side"))
            st.markdown(f"**{(d.get('id') or '').upper()} · {d.get('strategy')}**")
            st.caption(f"{verd} — {d.get('reason')}")
            st.write(f"Side: `{side}` · Regime: `{d.get('regime')}` · Stable: `{d.get('stable')}/{d.get('need_stable')}`")
            gate_rows = [
                {
                    "gate": g["gate"],
                    "pass": "✓" if g["ok"] else "✗",
                    "detail": g["detail"],
                }
                for g in d.get("gates", [])
            ]
            st.dataframe(pd.DataFrame(gate_rows), use_container_width=True, hide_index=True)


def render_open_positions(latest: dict | None) -> None:
    if not latest:
        return
    try:
        decisions = load_decisions(json.dumps(latest))
    except Exception:
        return
    open_rows = []
    for d in decisions:
        if not d.get("side"):
            continue
        u = d.get("unrealized")
        open_rows.append({
            "id": (d.get("id") or "").upper(),
            "strategy": d.get("strategy"),
            "side": d.get("side"),
            "entry_time": d.get("entry_time"),
            "entry_price": d.get("entry_price"),
            "last_close": d.get("close"),
            "unrealized_pct": None if u is None else round(float(u) * 100, 3),
            "days_held": d.get("days_held"),
            "exit_watch": d.get("reason") if d.get("verdict") == "EXIT_PRESSURE" else f"hold · exitSMA{d.get('exit_sma_n')}",
            "regime": d.get("regime"),
        })
    if not open_rows:
        st.caption("No open paper positions.")
        return
    st.dataframe(pd.DataFrame(open_rows), use_container_width=True, hide_index=True)


def render_agreement_timeline() -> None:
    tl = load_agreement_timeline(60)
    if tl.empty:
        st.info("No agreement history yet.")
        return
    # numeric map for chart
    order = {
        "all_flat": 0,
        "one_active": 1,
        "active_agree_long": 2,
        "active_agree_short": 2,
        "all_agree_long": 3,
        "all_agree_short": 3,
        "disagree": 4,
    }
    chart = tl.sort_values("day").copy()
    chart["agree_code"] = chart["agreement"].map(lambda x: order.get(str(x), -1))
    st.line_chart(chart.set_index("day")[["agree_code"]], height=220)
    st.caption("0=all_flat · 1=one_active · 2=active_agree · 3=all_agree · 4=disagree")
    show = tl[["day", "agreement", "regime", "close"] + [c for c in ("S1", "S2", "S3") if c in tl.columns]]
    st.dataframe(show.head(30), use_container_width=True, hide_index=True)


def render_regime_strip() -> None:
    strip = load_regime_strip(45)
    if strip.empty:
        st.info("No regime history yet.")
        return
    chart = strip.sort_values("day").copy()
    if "price" in chart.columns:
        st.line_chart(chart.set_index("day")[["price"]], height=220)
    # color-ish table
    st.dataframe(strip, use_container_width=True, hide_index=True)
    if "regime" in strip.columns:
        counts = strip["regime"].value_counts()
        st.caption("Recent mix: " + ", ".join(f"{k}={v}" for k, v in counts.items()))


def _chat_get_decisions(latest: dict) -> list[dict]:
    return load_decisions(json.dumps(latest))


def _chat_get_health(latest: dict | None) -> dict:
    return load_ops_health(json.dumps(latest) if latest else "")


def _chat_run_shadow() -> tuple[int, str]:
    code, out = run_shadow(None)
    load_latest.clear()
    load_csv.clear()
    load_run_history.clear()
    load_ops_health.clear()
    load_decisions.clear()
    load_agreement_timeline.clear()
    load_regime_strip.clear()
    load_market_daily_cached.clear()
    return code, out


def render_desk_chat(latest: dict | None) -> None:
    st.markdown(
        """
<div class="chat-box">
  <p class="chat-title">Desk chat</p>
  <p class="chat-hint">Rules-first · grounded in shadow data · paper only · optional LLM polish via OPENAI_API_KEY</p>
</div>
        """,
        unsafe_allow_html=True,
    )
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi — ask me anything about the paper desk, e.g. "
                    "“What's our status?”, “Why is S2 flat?”, “Any open positions?”, "
                    "“Is the scheduler healthy?”, or “Run shadow”."
                ),
            }
        ]
    if "chat_pending" not in st.session_state:
        st.session_state.chat_pending = None

    for msg in st.session_state.chat_messages[-40:]:
        role = "user" if msg.get("role") == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg.get("content", ""))
            if msg.get("run_output"):
                with st.expander("Shadow run log"):
                    st.code(msg["run_output"], language="text")

    if st.session_state.chat_pending == "confirm_run":
        st.info("Waiting: reply **confirm run** or **cancel** to proceed with paper shadow.")

    sug = st.columns(5)
    suggestions = [
        "What's our status?",
        "Why is S2 flat?",
        "Any open positions?",
        "Health check",
        "Run shadow",
    ]
    for i, text in enumerate(suggestions):
        with sug[i]:
            if st.button(text, key=f"chat_sug_{i}", use_container_width=True):
                st.session_state.chat_queued = text

    c_clear, _ = st.columns([1, 5])
    with c_clear:
        if st.button("Clear chat", key="chat_clear"):
            st.session_state.chat_messages = [st.session_state.chat_messages[0]]
            st.session_state.chat_pending = None
            st.rerun()

    queued = st.session_state.pop("chat_queued", None)
    typed = st.chat_input("Ask the desk…")
    text = (queued or typed or "").strip()
    if not text:
        return

    st.session_state.chat_messages.append({"role": "user", "content": text})

    fresh_latest = load_latest()
    with st.spinner("Thinking from shadow data…"):
        reply, new_pending, meta = chat.handle_message(
            text,
            pending=st.session_state.chat_pending,
            latest=fresh_latest,
            get_decisions=_chat_get_decisions,
            get_health=_chat_get_health,
            get_timeline=load_agreement_timeline,
            get_strip=load_regime_strip,
            run_shadow_fn=_chat_run_shadow,
        )

    st.session_state.chat_pending = new_pending
    bot_msg: dict = {"role": "assistant", "content": reply}
    if meta.get("run_output"):
        bot_msg["run_output"] = meta["run_output"]
    st.session_state.chat_messages.append(bot_msg)
    st.rerun()


def fmt_side(side) -> str:
    if side is None or (isinstance(side, float) and pd.isna(side)) or side == "" or str(side).lower() == "nan":
        return "FLAT"
    return str(side).upper()


def side_class(side: str) -> str:
    s = side.lower()
    if s == "long":
        return "side-long"
    if s == "short":
        return "side-short"
    return "side-flat"


def agree_class(label: str) -> str:
    if "disagree" in label:
        return "disagree"
    if "flat" in label:
        return ""
    return "active"


def human_agree(label: str) -> str:
    return label.replace("_", " ").upper()


def equity_pct(eq: float | None) -> float:
    if eq is None:
        return 0.0
    return (float(eq) - 1.0) * 100.0


def run_shadow(extra_args: list[str] | None = None) -> tuple[int, str]:
    cmd = [str(PYTHON), str(SCRIPT)]
    if extra_args:
        cmd.extend(extra_args)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        return proc.returncode, out
    except Exception as e:
        return 1, str(e)


def render_hero(latest: dict | None) -> None:
    mode = (latest or {}).get("mode", "SHADOW_PAPER_ONLY")
    places = (latest or {}).get("places_orders", False)
    run_at = (latest or {}).get("run_at_utc", "—")
    st.markdown(
        f"""
<div class="hero">
  <div class="hero-brand">Trading Bot</div>
  <p class="hero-line">ETH futures paper monitor for three walk-forward PASS strategies. Live orders stay off.</p>
  <div class="hero-meta">
    <span class="pill pill-paper">PAPER ONLY</span>
    <span class="pill pill-live-off">LIVE ORDERS: {"ON" if places else "OFF"}</span>
    <span class="pill pill-neutral">{mode}</span>
    <span class="pill pill-neutral">LAST RUN {run_at}</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_strip(latest: dict) -> None:
    agree = latest.get("agreement", {})
    close = latest.get("latest_close")
    strategies = latest.get("strategies", [])
    n_active = agree.get("n_active", 0)
    last_days = [s.get("last_processed_day") for s in strategies if s.get("last_processed_day")]
    last_day = max(last_days) if last_days else "—"
    avg_eq = None
    if strategies:
        avg_eq = sum(float(s.get("equity") or 1) for s in strategies) / len(strategies)
    eq_txt = f"{avg_eq:.4f}" if avg_eq is not None else "—"
    eq_sub = f"{equity_pct(avg_eq):+.2f}% vs start" if avg_eq is not None else ""
    st.markdown(
        f"""
<div class="strip">
  <div class="strip-item">
    <div class="strip-label">Agreement</div>
    <div class="strip-value">{human_agree(agree.get("label", "—"))}</div>
    <div class="strip-sub">{n_active} active position(s)</div>
  </div>
  <div class="strip-item">
    <div class="strip-label">ETH close</div>
    <div class="strip-value">{f"{close:,.2f}" if close else "—"}</div>
    <div class="strip-sub">latest completed day</div>
  </div>
  <div class="strip-item">
    <div class="strip-label">Last day</div>
    <div class="strip-value">{last_day}</div>
    <div class="strip-sub">shadow watermark</div>
  </div>
  <div class="strip-item">
    <div class="strip-label">Avg equity</div>
    <div class="strip-value">{eq_txt}</div>
    <div class="strip-sub">{eq_sub}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_agreement(latest: dict) -> None:
    agree = latest.get("agreement", {})
    label = agree.get("label", "unknown")
    sides = agree.get("sides", {})
    parts = [f"{k.upper()}={fmt_side(v)}" for k, v in sides.items()]
    st.markdown(
        f"""
<div class="agree-banner {agree_class(label)}">
  <p class="agree-title">{human_agree(label)}</p>
  <p class="agree-sub">{" · ".join(parts)}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_strategies(latest: dict) -> None:
    by_id = {s["id"]: s for s in latest.get("strategies", [])}
    cards = []
    for meta in STRATEGY_META:
        s = by_id.get(meta["id"], {})
        side = fmt_side(s.get("side"))
        eq = float(s.get("equity") or 1.0)
        pct = equity_pct(eq)
        width = max(8.0, min(100.0, eq * 100.0))
        fill_cls = "down" if eq < 1 else ""
        btc = " · BTC" if s.get("btc_confirm") else ""
        cards.append(
            f"""
<div class="strat">
  <div class="strat-top">
    <div>
      <p class="strat-name">{meta["title"]}</p>
      <div class="strat-code">{s.get("strategy", meta["folder"])}{btc}</div>
      <div class="strat-code">{meta["tagline"]}</div>
    </div>
    <span class="side-chip {side_class(side)}">{side}</span>
  </div>
  <div class="metric-row">
    <div><div class="metric-k">Equity</div><div class="metric-v">{eq:.4f} ({pct:+.1f}%)</div></div>
    <div><div class="metric-k">Trades</div><div class="metric-v">{s.get("n_trades_closed", 0)}</div></div>
    <div><div class="metric-k">Last day</div><div class="metric-v">{s.get("last_processed_day") or "—"}</div></div>
    <div><div class="metric-k">Status</div><div class="metric-v">{s.get("status") or "—"}</div></div>
    <div><div class="metric-k">Regime</div><div class="metric-v">{s.get("regime") or "—"}</div></div>
    <div><div class="metric-k">Halt / cool</div><div class="metric-v">{"HALTED" if s.get("halted") else "ok"} · cd {s.get("cooldown_left", 0)}</div></div>
  </div>
  <div class="eq-track"><div class="eq-fill {fill_cls}" style="width:{width}%"></div></div>
</div>
            """
        )
    st.markdown(f'<div class="strat-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def all_trades() -> pd.DataFrame:
    frames = []
    for meta in STRATEGY_META:
        df = load_csv(f"{meta['folder']}/trades.csv")
        if df.empty:
            continue
        df = df.copy()
        df.insert(0, "strategy_id", meta["id"].upper())
        if "strategy" not in df.columns:
            df["strategy"] = meta["folder"]
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    if "exit_time" in out.columns:
        out = out.sort_values("exit_time", ascending=False)
    return out


def all_signals(limit: int = 200) -> pd.DataFrame:
    frames = []
    for meta in STRATEGY_META:
        df = load_csv(f"{meta['folder']}/signals.csv")
        if df.empty:
            continue
        df = df.copy()
        if "strategy" not in df.columns:
            df["strategy"] = meta["folder"]
        df.insert(0, "strategy_id", meta["id"].upper())
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    sort_col = "ts_utc" if "ts_utc" in out.columns else out.columns[0]
    out = out.sort_values(sort_col, ascending=False).head(limit)
    return out


def equity_series() -> pd.DataFrame:
    rows = []
    for meta in STRATEGY_META:
        df = load_csv(f"{meta['folder']}/signals.csv")
        if df.empty or "equity" not in df.columns:
            continue
        day_col = "day" if "day" in df.columns else None
        if day_col is None:
            continue
        tmp = df[[day_col, "equity"]].dropna()
        tmp = tmp.rename(columns={day_col: "day"})
        tmp["strategy"] = meta["id"].upper()
        rows.append(tmp)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def render_wf_context() -> None:
    wf = port.load_wf_context()
    v7_path = ROOT / "models" / "htf_v7_stop_winner.json"
    if wf.empty and not v7_path.exists():
        st.info("No walk-forward winner files yet.")
        return
    if not wf.empty:
        show = wf.copy()
        if "wf_oos_ret" in show.columns:
            show["wf_oos_ret"] = show["wf_oos_ret"].apply(
                lambda x: f"{float(x):+.1%}" if pd.notna(x) else "—"
            )
        if "wf_median_pf" in show.columns:
            show["wf_median_pf"] = show["wf_median_pf"].apply(
                lambda x: f"{float(x):.2f}" if pd.notna(x) else "—"
            )
        if "wf_worst_dd" in show.columns:
            show["wf_worst_dd"] = show["wf_worst_dd"].apply(
                lambda x: f"{float(x):.1%}" if pd.notna(x) else "—"
            )
        if "stop_pct" in show.columns:
            show["stop_pct"] = show["stop_pct"].apply(
                lambda x: f"{float(x):.0%}" if pd.notna(x) else "none"
            )
        st.dataframe(show, use_container_width=True, hide_index=True)
    if v7_path.exists():
        try:
            v7 = json.loads(v7_path.read_text(encoding="utf-8"))
            w = v7.get("winner") or {}
            wf7 = v7.get("walkforward") or {}
            st.caption(
                f"v7 stop search: **{v7.get('status')}** — `{w.get('name')}` "
                f"(stop={w.get('stop_pct')}, atr_max={w.get('atr_max')}) · "
                f"edged {wf7.get('edged')} · OOS {float(wf7.get('compounded_oos_ret') or 0):+.1%} · "
                f"medPF {float(wf7.get('median_pf') or 0):.2f}. "
                "Frozen research artifact — not auto-swapped into shadow sleeves."
            )
        except Exception:
            pass


def render_portfolio_views() -> None:
    curves = port.portfolio_curves()
    if curves.empty:
        st.info("No portfolio curves yet — need shadow signals.")
        return
    summary = port.portfolio_summary(curves)
    if not summary.empty:
        show = summary.copy()
        for col in ("final_equity", "total_return", "max_dd"):
            if col in show.columns:
                if col == "final_equity":
                    show[col] = show[col].map(lambda x: f"{float(x):.4f}")
                else:
                    show[col] = show[col].map(lambda x: f"{float(x):+.1%}")
        st.dataframe(show, use_container_width=True, hide_index=True)
    chart = curves.set_index("day")[["equal", "agreement_2of3", "s2_primary"]].copy()
    chart = chart.rename(
        columns={
            "equal": "Equal weight",
            "agreement_2of3": "Agreement 2-of-3",
            "s2_primary": "S2 primary",
        }
    )
    st.line_chart(chart, height=280)
    st.caption(
        "Equal = avg of three paper equities · Agreement = risk-on only when ≥2 share the same non-flat side · "
        "S2 primary = cool7/stable7 sleeve alone."
    )
    st.markdown(port.s1_s3_correlation_note(curves))
    trades = port.closed_trades_summary()
    if not trades.empty:
        st.markdown('<p class="note">Closed paper trades (from trades.csv)</p>', unsafe_allow_html=True)
        tshow = trades.copy()
        for col in ("sum_net", "avg_net", "win_rate", "equity_from_trades"):
            if col not in tshow.columns:
                continue
            if col == "win_rate":
                tshow[col] = tshow[col].map(lambda x: f"{float(x):.0%}")
            elif col == "equity_from_trades":
                tshow[col] = tshow[col].map(lambda x: f"{float(x):.4f}")
            else:
                tshow[col] = tshow[col].map(lambda x: f"{float(x):+.2%}")
        st.dataframe(tshow, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="SHADOW DESK",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()

    latest = load_latest()
    render_hero(latest)
    render_desk_chat(latest)

    if latest is None:
        st.warning("No `shadow/latest.json` yet. Run the shadow script once, or use the Run tab.")
    else:
        render_strip(latest)
        render_agreement(latest)
        st.markdown('<p class="section-title">Ops health</p>', unsafe_allow_html=True)
        render_ops_health(latest)
        st.markdown('<p class="section-title">Why this decision</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="note">Gate checklist for the last processed day — blocked gates explain flat / no entry.</p>',
            unsafe_allow_html=True,
        )
        render_decision_panels(latest)
        st.markdown('<p class="section-title">Open paper positions</p>', unsafe_allow_html=True)
        render_open_positions(latest)
        st.markdown('<p class="section-title">Strategies</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="note">Independent paper sleeves. Closed trades are logged for humans — never fed back as pattern memory.</p>',
            unsafe_allow_html=True,
        )
        render_strategies(latest)

    tab_overview, tab_liq, tab_history, tab_trades, tab_signals, tab_run, tab_policy = st.tabs(
        ["Overview", "Liquidity", "Run history", "Trades", "Signals", "Run shadow", "Policy"]
    )

    with tab_overview:
        st.markdown('<p class="section-title">Walk-forward context</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="note">Frozen research winners that justify the three paper sleeves. Shadow PnL is not the gate — WF is.</p>',
            unsafe_allow_html=True,
        )
        render_wf_context()

        st.markdown('<p class="section-title">Regime + price</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="note">Daily ETH close from S1 signals with regime labels (Bull / Bear / Neutral).</p>',
            unsafe_allow_html=True,
        )
        render_regime_strip()

        st.markdown('<p class="section-title">Agreement timeline</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="note">How S1/S2/S3 align day by day — useful for future live rules (e.g. 2/3 agree).</p>',
            unsafe_allow_html=True,
        )
        render_agreement_timeline()

        st.markdown('<p class="section-title">Equity path (full paper history)</p>', unsafe_allow_html=True)
        eq = equity_series()
        if eq.empty:
            st.info("No signal equity history yet.")
        else:
            pivot = eq.pivot_table(index="day", columns="strategy", values="equity", aggfunc="last")
            pivot = pivot.sort_index()
            # one row per day (last equity that day) — full span, no head truncate
            st.line_chart(pivot, height=320)
            n_days = len(pivot)
            st.caption(
                f"Full signal equity path ({n_days} days, start = 1.0). "
                "Flat stretches in Neutral are expected. Recent drawdowns ≠ WF failure — sample is tiny."
            )

        st.markdown('<p class="section-title">Portfolio views</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="note">How size/risk could look later: equal sleeves, agreement-only, or S2-primary. Paper only.</p>',
            unsafe_allow_html=True,
        )
        render_portfolio_views()

        if latest:
            policy = latest.get("model_policy", {})
            st.markdown('<p class="section-title">Quick facts</p>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Policy", policy.get("name", "—")[:28])
            c2.metric("Places orders", "No" if not latest.get("places_orders") else "YES")
            c3.metric("Strategies", len(latest.get("strategies", [])))

    with tab_liq:
        st.markdown('<p class="section-title">Liquidity desk</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="note">From standalone order-book snapshots '
            "(<code>data/orderbook/</code>). Not wired into S1/S2/S3 entries. "
            "Keep <code>record_orderbook.py</code> running for live updates.</p>",
            unsafe_allow_html=True,
        )
        available = sorted(
            set(list_orderbook_days("ETHUSDT") + list_orderbook_days("BTCUSDT")),
            reverse=True,
        )
        if not available:
            st.warning(
                "No order-book files yet. Start capture with: "
                "`python record_orderbook.py` (ETH+BTC · 5s · depth 20)."
            )
        else:
            csel1, csel2, csel3 = st.columns([1, 1, 1])
            with csel1:
                symbol = st.selectbox("Symbol", list(LIQUIDITY_SYMBOLS), index=0, key="liq_sym")
            with csel2:
                day = st.selectbox("Day", available, index=0, key="liq_day")
            with csel3:
                lookback = st.selectbox("Chart lookback (days)", [1, 2, 3, 5, 7], index=2, key="liq_lb")

            day_df = load_orderbook_day(symbol, day)
            recent = load_orderbook_recent(symbol, max_days=int(lookback))
            age = snapshot_age_seconds(recent if not recent.empty else day_df)

            if day_df.empty and recent.empty:
                st.info(f"No snapshots for {symbol} on {day}.")
            else:
                last = (recent if not recent.empty else day_df).iloc[-1]
                age_txt = "—"
                if age is not None:
                    if age < 120:
                        age_txt = f"{age:.0f}s"
                    elif age < 3600:
                        age_txt = f"{age / 60:.1f}m"
                    else:
                        age_txt = f"{age / 3600:.1f}h stale"

                k1, k2, k3, k4, k5 = st.columns(5)
                k1.metric("Mid", f"{float(last['mid']):,.2f}" if pd.notna(last.get("mid")) else "—")
                k2.metric(
                    "Spread (bps)",
                    f"{float(last['spread_bps']):.3f}" if pd.notna(last.get("spread_bps")) else "—",
                )
                k3.metric(
                    "Imbalance",
                    f"{float(last['imbalance']):+.3f}" if pd.notna(last.get("imbalance")) else "—",
                )
                k4.metric(
                    "Bid / Ask qty",
                    f"{float(last.get('bid_qty_sum') or 0):.2f} / {float(last.get('ask_qty_sum') or 0):.2f}",
                )
                k5.metric("Snapshot age", age_txt)
                if age is not None and age > 300:
                    st.caption("Recorder looks idle (>5 min). Run `python record_orderbook.py` for fresh depth.")

                near = depth_within_bps(last, bps=5.0)
                st.caption(
                    f"Depth within 5 bps of mid — bid {near['bid_qty']:.3f} · ask {near['ask_qty']:.3f} "
                    f"· last ts {last.get('ts_utc')}"
                )

                chart_src = recent if not recent.empty else day_df
                if not chart_src.empty:
                    st.markdown('<p class="section-title">Spread & imbalance</p>', unsafe_allow_html=True)
                    ts_idx = chart_src.set_index("ts_utc")
                    c_a, c_b = st.columns(2)
                    with c_a:
                        if "spread_bps" in ts_idx.columns:
                            st.line_chart(ts_idx[["spread_bps"]].dropna(), height=260)
                            st.caption("Spread (bps) over time")
                    with c_b:
                        if "imbalance" in ts_idx.columns:
                            st.line_chart(ts_idx[["imbalance"]].dropna(), height=260)
                            st.caption("Book imbalance (−1 ask-heavy … +1 bid-heavy)")

                    st.markdown('<p class="section-title">Mid & depth totals</p>', unsafe_allow_html=True)
                    c_c, c_d = st.columns(2)
                    with c_c:
                        if "mid" in ts_idx.columns:
                            st.line_chart(ts_idx[["mid"]].dropna(), height=240)
                            st.caption("Mid price")
                    with c_d:
                        depth_cols = [c for c in ("bid_qty_sum", "ask_qty_sum") if c in ts_idx.columns]
                        if depth_cols:
                            st.line_chart(ts_idx[depth_cols].dropna(), height=240)
                            st.caption("Top-20 size totals (bid vs ask)")

                st.markdown('<p class="section-title">Depth ladder (latest snapshot)</p>', unsafe_allow_html=True)
                ladder_levels = st.slider("Levels to show", 5, 20, 10, key="liq_levels")
                ladder = depth_ladder(last, levels=ladder_levels)
                if ladder.empty:
                    st.info("No depth levels on latest row.")
                else:
                    # opposing horizontal bars via negative bids
                    plot = ladder.set_index("level")[["bid_qty", "ask_qty"]].copy()
                    plot["bid_qty"] = -plot["bid_qty"]
                    st.bar_chart(plot, height=320)
                    st.caption("Bid qty shown negative for mirror view · Ask qty positive")
                    show_l = ladder.copy()
                    st.dataframe(
                        show_l[["level", "bid_px", "bid_qty", "ask_px", "ask_qty"]],
                        use_container_width=True,
                        hide_index=True,
                    )

                st.markdown('<p class="section-title">ETH vs BTC (same day)</p>', unsafe_allow_html=True)
                cmp_cols = st.columns(2)
                for i, sym in enumerate(LIQUIDITY_SYMBOLS):
                    sdf = load_orderbook_day(sym, day)
                    with cmp_cols[i]:
                        if sdf.empty:
                            st.write(f"**{sym}** — no data for {day}")
                        else:
                            r = sdf.iloc[-1]
                            st.write(f"**{sym}**")
                            st.metric("Spread bps", f"{float(r['spread_bps']):.3f}" if pd.notna(r.get("spread_bps")) else "—")
                            st.metric("Imbalance", f"{float(r['imbalance']):+.3f}" if pd.notna(r.get("imbalance")) else "—")
                            st.metric("Mid", f"{float(r['mid']):,.2f}" if pd.notna(r.get("mid")) else "—")

                st.markdown('<p class="section-title">Daily liquidity summary</p>', unsafe_allow_html=True)
                summary = liquidity_daily_summary(load_orderbook_recent(symbol, max_days=14))
                if summary.empty:
                    st.info("Not enough data for daily summary.")
                else:
                    st.dataframe(summary, use_container_width=True, hide_index=True)

    with tab_history:
        st.markdown('<p class="section-title">Shadow run log</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="note">Each invocation of <code>shadow_htf_v4.py</code> appends one row '
            "(success or failure) to <code>shadow/run_history.jsonl</code>.</p>",
            unsafe_allow_html=True,
        )
        runs = load_run_history()
        if runs.empty:
            st.info("No run history yet. Run shadow once (tab or scheduler) to start the log.")
        else:
            n_runs = st.slider("Runs to show", 10, 200, 50, 10, key="hist_runs")
            flat = flatten_run_history(runs.head(n_runs))
            st.dataframe(flat, use_container_width=True, hide_index=True)
            ok_n = int(runs["ok"].sum()) if "ok" in runs.columns else 0
            st.caption(f"Logged runs: {len(runs)} · ok={ok_n} · fail={len(runs) - ok_n}")

        st.markdown('<p class="section-title">Daily strategy results</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="note">Built from signal files — one row per completed market day across S1/S2/S3.</p>',
            unsafe_allow_html=True,
        )
        n_days = st.slider("Days to show", 14, 180, 60, 7, key="hist_days")
        daily = daily_results_table(n_days)
        if daily.empty:
            st.info("No daily signal history yet.")
        else:
            st.dataframe(daily, use_container_width=True, hide_index=True)

    with tab_trades:
        st.markdown('<p class="section-title">Closed paper trades</p>', unsafe_allow_html=True)
        trades = all_trades()
        if trades.empty:
            st.info("No closed trades logged yet.")
        else:
            show = trades.copy()
            if "net_return" in show.columns:
                show["net_return_pct"] = (show["net_return"].astype(float) * 100).round(2)
            cols = [c for c in [
                "strategy_id", "strategy", "entry_time", "exit_time", "side",
                "entry_price", "exit_price", "net_return_pct", "exit_reason", "mode",
            ] if c in show.columns]
            st.dataframe(show[cols], use_container_width=True, hide_index=True)
            if "net_return" in trades.columns:
                by = trades.groupby("strategy_id")["net_return"].agg(["count", "sum", "mean"])
                by.columns = ["n_trades", "sum_net", "avg_net"]
                st.markdown("**Per-strategy paper totals**")
                st.dataframe(by.style.format({"sum_net": "{:.4f}", "avg_net": "{:.4f}"}), use_container_width=True)

    with tab_signals:
        st.markdown('<p class="section-title">Recent signals</p>', unsafe_allow_html=True)
        n = st.slider("Rows to show", 50, 500, 150, 50)
        sigs = all_signals(n)
        if sigs.empty:
            st.info("No signals yet.")
        else:
            prefer = [c for c in [
                "strategy_id", "strategy", "day", "action", "side", "price",
                "regime", "detail", "net_return", "unrealized", "equity", "ts_utc", "mode",
            ] if c in sigs.columns]
            st.dataframe(sigs[prefer], use_container_width=True, hide_index=True)
            actions = sigs["action"].value_counts() if "action" in sigs.columns else None
            if actions is not None:
                st.caption("Action mix in this window: " + ", ".join(f"{k}={v}" for k, v in actions.items()))

    with tab_run:
        st.markdown('<p class="section-title">Run shadow now</p>', unsafe_allow_html=True)
        st.markdown(
            '<div class="run-box"><p class="note" style="margin:0">'
            "Runs <code>shadow_htf_v4.py</code> (paper only). Refreshes recent klines, then advances each strategy "
            "for any new completed UTC day. Safe to click anytime — same-day re-runs usually return UP_TO_DATE."
            "</p></div>",
            unsafe_allow_html=True,
        )
        st.write("")
        skip_refresh = st.checkbox("Skip data refresh (--no-refresh)", value=False)
        col_a, col_b = st.columns([1, 2])
        with col_a:
            go = st.button("Run shadow", type="primary", use_container_width=True)
        with col_b:
            st.caption(f"Interpreter: `{PYTHON}`")
        if go:
            args = ["--no-refresh"] if skip_refresh else None
            with st.spinner("Running triple shadow…"):
                code, out = run_shadow(args)
            load_latest.clear()
            load_csv.clear()
            load_run_history.clear()
            if code == 0:
                st.success("Shadow finished. Open the Run history tab (or press R) for the new log row.")
            else:
                st.error(f"Shadow exited with code {code}")
            st.code(out[-8000:] if out else "(no output)", language="text")
            st.info("Tip: after a successful run, press R or use the menu → Rerun to refresh charts.")

    with tab_policy:
        st.markdown('<p class="section-title">Model policy</p>', unsafe_allow_html=True)
        if latest and latest.get("model_policy"):
            pol = latest["model_policy"]
            st.write(pol.get("note", ""))
            st.json(pol)
        else:
            st.write("Stateless / no trade-pattern memory. Each signal uses current market features only.")
        st.markdown(
            """
**Live stance**
- This UI does **not** place Binance orders.
- Tiny live comes only after weeks of honest shadow + explicit risk rules.
- Multi-strategy plan: keep all three in shadow; live starts with one sleeve or agreement-only.
            """
        )

    st.markdown(
        f'<p class="footer-note">SHADOW DESK · {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")} · root {ROOT}</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
