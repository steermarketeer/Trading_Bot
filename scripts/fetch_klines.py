"""Download Binance USD-M 5m klines + funding history (data.binance.vision) in the repo's CSV format.
usage: python scripts/fetch_klines.py SOLUSDT [BNBUSDT ...]"""
import io, sys, zipfile, datetime as dt, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd

B = "https://data.binance.vision/data/futures/um"
KCOLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trades",
         "taker_buy_base", "taker_buy_quote", "ignore"]

def fetch(url):
    for _ in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                z = zipfile.ZipFile(io.BytesIO(r.read()))
                return z.read(z.namelist()[0]).decode()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
    return None

def parse(txt, cols):
    if txt is None:
        return None
    first = txt.split("\n", 1)[0]
    has_header = not first.split(",")[0].strip().lstrip("-").isdigit()
    df = pd.read_csv(io.StringIO(txt), header=0 if has_header else None)
    if not has_header:
        df.columns = cols[:df.shape[1]]
    return df

def months(start):
    m, end = start, dt.date.today().replace(day=1)
    while m < end:
        yield m
        m = (m.replace(day=28) + dt.timedelta(days=4)).replace(day=1)

for sym in sys.argv[1:]:
    ms = list(months(dt.date(2019, 9, 1)))
    with ThreadPoolExecutor(12) as ex:
        kparts = list(ex.map(lambda m: parse(fetch(f"{B}/monthly/klines/{sym}/5m/{sym}-5m-{m:%Y-%m}.zip"), KCOLS), ms))
        first_day = dt.date.today().replace(day=1)
        days = [first_day + dt.timedelta(days=i) for i in range((dt.date.today() - first_day).days)]
        kparts += list(ex.map(lambda d: parse(fetch(f"{B}/daily/klines/{sym}/5m/{sym}-5m-{d:%Y-%m-%d}.zip"), KCOLS), days))
        fparts = list(ex.map(lambda m: parse(fetch(f"{B}/monthly/fundingRate/{sym}/{sym}-fundingRate-{m:%Y-%m}.zip"),
                                             ["calc_time", "funding_interval_hours", "last_funding_rate"]), ms))
    k = pd.concat([p for p in kparts if p is not None])
    k = k[[c for c in KCOLS if c != "ignore"]].astype({"open_time": "int64"}).drop_duplicates("open_time").sort_values("open_time")
    Path("data/klines").mkdir(parents=True, exist_ok=True)
    k.to_csv(f"data/klines/{sym}_5m.csv", index=False)
    f = pd.concat([p for p in fparts if p is not None])
    f = pd.DataFrame({"fundingTime": f["calc_time"].astype("int64"), "fundingRate": f["last_funding_rate"].astype(float)})
    f.drop_duplicates("fundingTime").sort_values("fundingTime").to_csv(f"data/funding/{sym}.csv", index=False)
    print(sym, len(k), pd.to_datetime(k.open_time.min(), unit="ms"), "->", pd.to_datetime(k.open_time.max(), unit="ms"),
          "| funding", len(f))
