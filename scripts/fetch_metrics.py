"""Download Binance USD-M daily 'metrics' (5m open interest, long/short ratios, taker ratio) into one CSV."""
import io, sys, zipfile, datetime as dt, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd

sym = sys.argv[1] if len(sys.argv) > 1 else "ETHUSDT"
start, end = dt.date(2021, 12, 1), dt.date.today() - dt.timedelta(days=1)
base = f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-"

def get(d):
    for _ in range(4):
        try:
            with urllib.request.urlopen(f"{base}{d:%Y-%m-%d}.zip", timeout=30) as r:
                z = zipfile.ZipFile(io.BytesIO(r.read()))
                return pd.read_csv(z.open(z.namelist()[0]))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
    return None

days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
with ThreadPoolExecutor(16) as ex:
    parts = list(ex.map(get, days))
missing = [str(d) for d, p in zip(days, parts) if p is None]
df = pd.concat([p for p in parts if p is not None]).drop_duplicates("create_time").sort_values("create_time")
out = Path("data/metrics"); out.mkdir(parents=True, exist_ok=True)
df.to_csv(out / f"{sym}_metrics_5m.csv", index=False)
print(f"{sym}: {len(df)} rows {df.create_time.min()} -> {df.create_time.max()}; missing days {len(missing)}: {missing[:10]}")
