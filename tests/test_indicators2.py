"""New indicators vs simple loop-based reference implementations + statistics helpers."""
import math

import numpy as np
import pandas as pd
import pytest

from bot.study import indicators as ind
from bot.study.indicator_search import bh_qvalues, two_prop_z


@pytest.fixture
def ohlcv():
    rng = np.random.default_rng(11)
    n = 300
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.003, n))
    h = np.maximum(o, c) * (1 + rng.uniform(0, 0.01, n))
    l = np.minimum(o, c) * (1 - rng.uniform(0, 0.01, n))
    v = rng.uniform(100, 1000, n)
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v})


def ref_rma(x, n):
    out = [math.nan] * len(x)
    first = next(i for i, v in enumerate(x) if not math.isnan(v))
    out[first + n - 1] = sum(x[first:first + n]) / n
    for i in range(first + n, len(x)):
        out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


def close_enough(a, b, tol=1e-9):
    a, b = np.asarray(a, float), np.asarray(b, float)
    assert np.array_equal(np.isnan(a), np.isnan(b))
    m = ~np.isnan(a)
    np.testing.assert_allclose(a[m], b[m], rtol=tol, atol=tol)


def test_rma(ohlcv):
    x = ohlcv["close"].tolist()
    close_enough(ind.rma(ohlcv["close"], 14), ref_rma(x, 14))


def test_atr_is_wilder(ohlcv):
    h, l, c = ohlcv["high"].tolist(), ohlcv["low"].tolist(), ohlcv["close"].tolist()
    tr = [h[0] - l[0]] + [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, len(c))]
    close_enough(ind.atr(ohlcv, 14), ref_rma(tr, 14))


def test_adx(ohlcv):
    h, l, c = ohlcv["high"].tolist(), ohlcv["low"].tolist(), ohlcv["close"].tolist()
    n = 14
    pdm, mdm, tr = [math.nan], [math.nan], [math.nan]
    for i in range(1, len(c)):
        up, dn = h[i] - h[i - 1], l[i - 1] - l[i]
        pdm.append(up if (up > dn and up > 0) else 0.0)
        mdm.append(dn if (dn > up and dn > 0) else 0.0)
        tr.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
    a, p, m = ref_rma(tr, n), ref_rma(pdm, n), ref_rma(mdm, n)
    pdi = [100 * p[i] / a[i] for i in range(len(c))]
    mdi = [100 * m[i] / a[i] for i in range(len(c))]
    dx = [100 * abs(pdi[i] - mdi[i]) / (pdi[i] + mdi[i]) for i in range(len(c))]
    adx_ref = ref_rma(dx, n)
    got, gp, gm = ind.adx(ohlcv, n)
    close_enough(gp, pdi)
    close_enough(gm, mdi)
    close_enough(got, adx_ref)
    assert got.first_valid_index() == 2 * n - 1  # 14 for DI + 14 for ADX smoothing


def test_adx_behaviour():
    up = pd.DataFrame({"close": np.arange(100.0, 200.0)})
    up["high"], up["low"], up["open"] = up["close"] + 0.5, up["close"] - 0.5, up["close"]
    a, p, m = ind.adx(up)
    assert a.iloc[-1] > 90 and p.iloc[-1] > m.iloc[-1]


def test_stoch_cci_willr(ohlcv):
    h, l, c = ohlcv["high"].to_numpy(), ohlcv["low"].to_numpy(), ohlcv["close"].to_numpy()
    k_raw, w = [], []
    for i in range(len(c)):
        if i < 13:
            k_raw.append(math.nan); w.append(math.nan); continue
        hh, ll = h[i - 13:i + 1].max(), l[i - 13:i + 1].min()
        k_raw.append(100 * (c[i] - ll) / (hh - ll))
        w.append(-100 * (hh - c[i]) / (hh - ll))
    k = [math.nan if i < 15 else sum(k_raw[i - 2:i + 1]) / 3 for i in range(len(c))]
    close_enough(ind.stochastic(ohlcv), k)
    close_enough(ind.williams_r(ohlcv), w)
    tp = (h + l + c) / 3
    cc = []
    for i in range(len(c)):
        if i < 19:
            cc.append(math.nan); continue
        win = tp[i - 19:i + 1]
        mad = np.abs(win - win.mean()).mean()
        cc.append((tp[i] - win.mean()) / (0.015 * mad))
    close_enough(ind.cci(ohlcv), cc, tol=1e-8)


def test_mfi_obv_cmf_vwap(ohlcv):
    h, l, c, v = (ohlcv[k].to_numpy() for k in ("high", "low", "close", "volume"))
    tp = (h + l + c) / 3
    mfi = []
    for i in range(len(c)):
        if i < 14:
            mfi.append(math.nan); continue
        pos = sum(tp[j] * v[j] for j in range(i - 13, i + 1) if tp[j] > tp[j - 1])
        neg = sum(tp[j] * v[j] for j in range(i - 13, i + 1) if tp[j] < tp[j - 1])
        mfi.append(100.0 if neg == 0 else 100 - 100 / (1 + pos / neg))
    close_enough(ind.mfi(ohlcv), mfi, tol=1e-8)
    o = [0.0]
    for i in range(1, len(c)):
        o.append(o[-1] + (v[i] if c[i] > c[i - 1] else -v[i] if c[i] < c[i - 1] else 0))
    close_enough(ind.obv(ohlcv), o, tol=1e-6)
    cm, vw = [], []
    for i in range(len(c)):
        if i < 19:
            cm.append(math.nan); vw.append(math.nan); continue
        s = slice(i - 19, i + 1)
        mfm = ((c[s] - l[s]) - (h[s] - c[s])) / (h[s] - l[s])
        cm.append((mfm * v[s]).sum() / v[s].sum())
        vw.append((tp[s] * v[s]).sum() / v[s].sum())
    close_enough(ind.cmf(ohlcv), cm, tol=1e-8)
    close_enough(ind.rolling_vwap(ohlcv), vw, tol=1e-8)


def test_keltner_donchian(ohlcv):
    mid, up, lo = ind.keltner(ohlcv)
    a = ind.atr(ohlcv, 10)
    ok = mid.notna()
    assert ok.idxmax() == 19 and a.first_valid_index() == 9
    close_enough((up - mid)[ok], (2 * a)[ok])
    close_enough((mid - lo)[ok], (2 * a)[ok])
    dh, dl = ind.donchian(ohlcv)
    assert dh.iloc[50] == ohlcv["high"].iloc[31:51].max()
    assert dl.iloc[50] == ohlcv["low"].iloc[31:51].min()


def _trend_frame(prices):
    c = np.asarray(prices, float)
    return pd.DataFrame({"open": c, "close": c, "high": c * 1.005, "low": c * 0.995, "volume": 1.0})


def test_supertrend_and_psar_follow_trend_and_flip():
    prices = list(np.linspace(100, 200, 60)) + list(np.linspace(200, 120, 40))
    d = _trend_frame(prices)
    st = ind.supertrend(d)
    sar = ind.psar(d)
    assert st.iloc[55] == 1 and st.iloc[-1] == -1
    assert sar.iloc[55] < d["low"].iloc[55] and sar.iloc[-1] > d["high"].iloc[-1]
    # SAR never inside the bar it belongs to while the trend is intact
    assert (sar.iloc[5:58] <= d["low"].iloc[5:58]).all()


def test_psar_reference_small_case():
    # hand-worked: rising highs/lows, AF steps 0.02 per new high
    d = pd.DataFrame({"high": [10, 11, 12, 13], "low": [9, 10, 11, 12], "open": 0, "close": 0, "volume": 1})
    sar = ind.psar(d)
    assert math.isnan(sar[0]) and sar[1] == 9
    # bar2: s = 9 + 0.02*(10-9)?  EP starts at high[0]=10 -> 9.02, capped by min(low1, low0)=9 -> 9
    assert sar[2] == pytest.approx(9.0)
    # bar2 makes a new high 12 -> EP=12, AF=0.04; bar3: 9 + 0.04*(12-9)=9.12, cap min(low2,low1)=10 -> 9.12
    assert sar[3] == pytest.approx(9.12)


def test_indicators_have_no_lookahead(ohlcv):
    fns = [lambda d: ind.adx(d)[0], ind.stochastic, ind.cci, ind.williams_r, ind.mfi, ind.obv, ind.cmf,
           ind.rolling_vwap, ind.supertrend, ind.psar, lambda d: ind.keltner(d)[1], lambda d: ind.donchian(d)[0]]
    for f in fns:
        full = f(ohlcv)
        part = f(ohlcv.iloc[:200])
        close_enough(part, full.iloc[:200])


def test_two_prop_z():
    z, p = two_prop_z(60, 100, 40, 100)
    assert z == pytest.approx(2.828, abs=0.001) and p == pytest.approx(0.00468, abs=1e-4)


def test_bh_qvalues():
    q = bh_qvalues(np.array([0.01, 0.04, 0.03, 0.005, np.nan]))
    # sorted p: .005 .01 .03 .04 -> p*m/rank: .02 .02 .04 .04 -> monotone
    assert q[:4] == pytest.approx([0.02, 0.04, 0.04, 0.02])
    assert np.isnan(q[4])
