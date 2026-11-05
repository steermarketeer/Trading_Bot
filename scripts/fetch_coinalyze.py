"""Download Coinalyze liquidation + open-interest history for ETH perps (all the free tier keeps per interval).
The API key is injected by the session's network proxy; it is never stored in the repo."""
import json, time, urllib.request
from pathlib import Path
import pandas as pd

API = "https://api.coinalyze.net/v1"
SYMS = {"ETHUSDT_PERP.A": "binance_usdt", "ETHUSD_PERP.A": "binance_coin", "ETHUSDT.6": "bybit_usdt",
        "ETHUSDT_PERP.3": "okx_usdt"}
INTERVALS = ["5min", "1hour", "4hour", "12hour", "daily"]
out = Path("data/coinalyze"); out.mkdir(parents=True, exist_ok=True)

def get(path):
    for k in range(8):
        try:
            with urllib.request.urlopen(f"{API}/{path}", timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After", 10)) + 1)
                continue
            raise
    raise RuntimeError(path)

now = int(time.time())
for iv in INTERVALS:
    for kind, ep in (("liq", "liquidation-history"), ("oi", "open-interest-history")):
        d = get(f"{ep}?symbols={','.join(SYMS)}&interval={iv}&from=1577836800&to={now}&convert_to_usd=true")
        rows = [{"t": h["t"], "market": SYMS[x["symbol"]], **{k: v for k, v in h.items() if k != "t"}}
                for x in d for h in x["history"]]
        df = pd.DataFrame(rows)
        df["time"] = pd.to_datetime(df["t"], unit="s")
        df.drop(columns="t").to_csv(out / f"eth_{kind}_{iv}.csv", index=False)
        print(kind, iv, len(df), df["time"].min(), "->", df["time"].max())
        time.sleep(2)
