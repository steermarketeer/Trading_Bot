# Strategy guide: fine-tuning and adding strategies

## 1. Change numbers (no code)

Copy a file in `strategies/`, give it a new `name:`, edit it, and backtest it:

```bash
cp strategies/s3_btc_confirm.yaml strategies/my_s3.yaml
# edit my_s3.yaml
python -m bot backtest strategies/my_s3.yaml strategies/s3_btc_confirm.yaml
```

Typos are caught: an unknown key stops the run with the list of allowed keys.

### `params:` for `type: htf_trend`

| key | meaning | legacy S3 |
|---|---|---|
| `sides` | `both`, `long_only`, `short_only` | both |
| `entry_sma` | enter only when close is beyond this SMA in the regime's direction | 50 |
| `exit_sma` | exit when close crosses back through this SMA | 30 |
| `align_sma` | also require SMA(align) beyond SMA(entry) in the trade direction; `null` = off | 20 |
| `regime_stable_days` | regime must have been unchanged this many days | 5 |
| `atr_period` | ATR length (days) | 14 |
| `atr_pct_min` / `atr_pct_max` | skip entries when ATR/close is outside this band; `null` = off | 0.01 / 0.08 |
| `btc_confirm` | BTC close must be beyond its SMA in the same direction | true |
| `btc_sma` | the BTC SMA length | 50 |

### `risk:` (engine-level, works for every strategy type)

| key | meaning |
|---|---|
| `size_frac` | fraction of equity used as margin per trade (1.0 = all) |
| `leverage` | 1 = no leverage. Liquidation is simulated (isolated margin) |
| `stop_pct` | protective stop as a fraction of entry price, checked on the daily high/low; `null` = none |
| `cooldown_days` | daily closes after an exit before a new entry is allowed |
| `dd_halt` | pause new entries when drawdown reaches this; `null` = never |
| `halt_days` | how long the pause lasts; afterwards the drawdown peak resets |
| `dd_basis` | `closed` = drawdown of closed-trade equity (legacy); `mtm` = includes open profit, and also exits the open trade |

### Global settings in `config.yaml`

`costs` (fee, slippage, funding on/off), and `regime.extra_lag_periods` (1 = legacy lag; 0 = use
the latest completed week/month).

## 2. New logic (a little Python)

Create `bot/strategies/my_idea.py`:

```python
from ..data import sma
from .base import Strategy, register

@register("my_idea")
class MyIdea(Strategy):
    defaults = {"fast": 20, "slow": 100}

    def prepare(self, bars):
        d = bars.copy()
        d["fast"] = sma(d["close"], self.p["fast"])     # backward-looking only!
        d["slow"] = sma(d["close"], self.p["slow"])
        return d

    def required_columns(self):
        return ["fast", "slow"]

    def entry_signal(self, row):            # called at the daily close when flat
        if row["regime"] == "Bull" and row["fast"] > row["slow"]:
            return "long"
        return None

    def exit_signal(self, row, pos):        # called at the daily close when in a trade
        if row["fast"] < row["slow"]:
            return "fast_below_slow"        # any text = exit at next open
        return None
```

Then add `from . import my_idea` to `bot/strategies/__init__.py` and create
`strategies/my_idea.yaml` with `type: my_idea`.

Columns available in `row`: `day, open, high, low, close, volume, btc_open..btc_close, regime,
eth_weekly_score, eth_monthly_struct, btc_weekly_score` plus whatever you add in `prepare`.
`pos` has `side, entry_day, entry_price, days_held, unrealized_pct`.

Per `MODEL_POLICY.md`, don't use past trade results as inputs.

## 3. Tuning without fooling yourself

- **Write down what you're testing before running it.** Every variant you try and then keep makes
  the backtest look better than reality.
- Tune on history before **2025-11-01** (`--end 2025-10-31`). Look at the last 12 months only once,
  when you've settled on a version.
- Prefer settings whose **neighbours** also work (SMA 45/50/55 similar), not a single best spike.
- Compare against `buy_and_hold ETH`, which every backtest prints.
- A strategy with fewer than about 30 trades in the test period hasn't shown anything yet.

## 4. Putting a strategy into the shadow

Add its YAML path under `shadow.strategies` in `config.yaml`. If you change a strategy that's already
in the shadow, the shadow refuses to continue (so old and new rules never mix in one record).
Start that one fresh with `python -m bot shadow --reset --only <name>`.
