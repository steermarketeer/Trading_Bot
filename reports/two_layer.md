# Two-layer model: main rules decide the trade, indicators can only veto

16,598 candidate trades from the main rules on 2h / 4h / 1D (all setups allowed), each a 2:1 trade with the concept's own stop. win % = profit after costs. Every number below is out-of-sample.

- **Layer 1** (62 main-rule inputs: structure on 1h-1W, patterns on 4h/1D/1W, events on other timeframes, zones, liquidity, weekly trend, volatility regime, which concept) picks the trades.
- **Layer 2** (290 indicator inputs) reviews only those and can veto.

## Win % at 2:1

| period | all candidates | win % all | layer 1 picks | win % layer 1 | avg R layer 1 | after layer 2 | win % layer 1+2 | avg R layer 1+2 |
|---|---|---|---|---|---|---|---|---|
| 2022 | 2488 | 36% | 1520 | 37% | -0.01 | 1198 | 36% | -0.02 |
| 2023 | 3090 | 35% | 399 | 41% | +0.08 | 362 | 41% | +0.07 |
| 2024 | 2439 | 38% | 80 | 42% | +0.18 | 32 | 53% | +0.45 |
| 2025 | 2466 | 36% | 160 | 36% | -0.01 | 159 | 36% | -0.00 |
| holdout | 2554 | 33% | 604 | 30% | -0.23 | 562 | 30% | -0.23 |
| 2022-25 total | 10483 | 36% | 2159 | 38% | +0.01 | 1751 | 38% | +0.01 |

## Which main-rule trades layer 1 takes (all out-of-sample periods)

| main-rule setup | candidates | win % if taken always | share layer 1 takes | win % when layer 1 takes it | win % after layer 2 | holdout win % after layer 2 |
|---|---|---|---|---|---|---|
| 1D level-test bounce | 439 | 40% | 32% | 47% | 48% | 45% |
| break of structure | 427 | 41% | 21% | 44% | 45% | 45% |
| liquidity run | 368 | 40% | 23% | 40% | 38% | 36% |
| S/R zone bounce | 3222 | 37% | 18% | 37% | 37% | 29% |
| trendline break | 2285 | 34% | 22% | 36% | 37% | 29% |
| S/R zone breakout | 2912 | 37% | 23% | 36% | 36% | 32% |
| liquidity sweep reversal | 335 | 34% | 20% | 35% | 33% | 31% |
| range break | 635 | 37% | 23% | 33% | 31% | 24% |
| trendline bounce | 1969 | 31% | 20% | 31% | 30% | 25% |
| change of character | 445 | 34% | 22% | 31% | 29% | 27% |

## What layer 1 looks at most (final model)

| main-rule input | share of importance |
|---|---|
| vol_regime | 13% |
| zone_behind_atr | 8% |
| zone_ahead_atr | 6% |
| zone_touches | 5% |
| brk_1D | 4% |
| ev_1D_brk | 4% |
| st_1h | 3% |
| wtrend | 3% |
| ev_1D_rev | 3% |
| liq_in_path | 3% |
| brk_12h | 3% |
| ev_4h_brk | 3% |
| c_count | 3% |
| st_4h | 3% |
| brk_1W | 2% |
| liq_in_risk | 2% |
| st_1W | 2% |
| ev_4h_rev | 2% |
| st_1D | 2% |
| is_long | 2% |

## Layer 1 in plain rules (a 4-level decision tree that imitates its picks)

```
|--- vol_regime <= 0.59
|   |--- zone_touches <= 6.50
|   |   |--- pat_1W <= 0.50
|   |   |   |--- is_1D <= 0.50
|   |   |   |   |--- class: 0
|   |   |   |--- is_1D >  0.50
|   |   |   |   |--- class: 1
|   |   |--- pat_1W >  0.50
|   |   |   |--- vol_regime <= 0.25
|   |   |   |   |--- class: 0
|   |   |   |--- vol_regime >  0.25
|   |   |   |   |--- class: 0
|   |--- zone_touches >  6.50
|   |   |--- vol_regime <= 0.03
|   |   |   |--- ev_1D_rev <= 0.50
|   |   |   |   |--- class: 0
|   |   |   |--- ev_1D_rev >  0.50
|   |   |   |   |--- class: 1
|   |   |--- vol_regime >  0.03
|   |   |   |--- pat_1W <= 0.50
|   |   |   |   |--- class: 0
|   |   |   |--- pat_1W >  0.50
|   |   |   |   |--- class: 0
|--- vol_regime >  0.59
|   |--- st_1W <= 0.50
|   |   |--- st_1W <= -0.50
|   |   |   |--- brk_12h <= -0.50
|   |   |   |   |--- class: 0
|   |   |   |--- brk_12h >  -0.50
|   |   |   |   |--- class: 0
|   |   |--- st_1W >  -0.50
|   |   |   |--- vol_regime <= 0.64
|   |   |   |   |--- class: 0
|   |   |   |--- vol_regime >  0.64
|   |   |   |   |--- class: 0
|   |--- st_1W >  0.50
|   |   |--- zone_touches <= 3.50
|   |   |   |--- vol_regime <= 0.83
|   |   |   |   |--- class: 0
|   |   |   |--- vol_regime >  0.83
|   |   |   |   |--- class: 1
|   |   |--- zone_touches >  3.50
|   |   |   |--- brk_choch_12h <= 0.50
|   |   |   |   |--- class: 0
|   |   |   |--- brk_choch_12h >  0.50
|   |   |   |   |--- class: 0

```

