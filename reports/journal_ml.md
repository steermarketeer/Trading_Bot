# Machine learning on the journal's precise inputs

10,735 main-rule signals (2h / 4h / 1D, one per candle and direction). 2 : 1 from the signal's stop, labelled on 5m candles with costs and funding. Every number is out-of-sample (walk-forward by year; holdout last). **win % = profit after costs.**

## Results (2% risk per trade, max 5x, compounding, overlapping positions)

| entry | period | trades | n | per week | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|---|---|
| enter at the signal | 2022 - 2025 | all signals | 6743 | 32.4 | 35% | -0.09 | 0.88 | 0.00x | -100% |
| enter at the signal | 2022 - 2025 | model takes | 2384 | 11.5 | 36% | -0.06 | 0.92 | 0.01x | -99% |
| enter at the signal | holdout | all signals | 1658 | 34.3 | 32% | -0.19 | 0.75 | 0.00x | -100% |
| enter at the signal | holdout | model takes | 400 | 8.3 | 32% | -0.19 | 0.76 | 0.19x | -87% |
| wait for the 4h close (your lesson) | 2022 - 2025 | all signals | 1599 | 7.7 | 43% | +0.02 | 1.03 | 0.88x | -81% |
| wait for the 4h close (your lesson) | 2022 - 2025 | model takes | 734 | 3.5 | 43% | +0.00 | 1.00 | 0.74x | -72% |
| wait for the 4h close (your lesson) | holdout | all signals | 427 | 8.8 | 35% | -0.19 | 0.73 | 0.16x | -84% |
| wait for the 4h close (your lesson) | holdout | model takes | 122 | 2.5 | 37% | -0.14 | 0.80 | 0.69x | -39% |

## By year (every scored period is shown)

| entry | period | all signals | win % | avg R | model takes | win % | avg R |
|---|---|---|---|---|---|---|---|
| confirm4h | 2022 | 377 | 43% | +0.05 | 234 | 44% | +0.07 |
| confirm4h | 2023 | 495 | 41% | -0.07 | 313 | 39% | -0.13 |
| confirm4h | 2024 | 365 | 47% | +0.11 | 71 | 42% | +0.01 |
| confirm4h | 2025 | 362 | 42% | +0.02 | 116 | 49% | +0.21 |
| confirm4h | holdout | 427 | 35% | -0.19 | 122 | 37% | -0.14 |
| now | 2022 | 1629 | 35% | -0.07 | 1239 | 36% | -0.03 |
| now | 2023 | 1962 | 34% | -0.16 | 525 | 35% | -0.13 |
| now | 2024 | 1621 | 37% | -0.02 | 262 | 37% | -0.00 |
| now | 2025 | 1531 | 34% | -0.08 | 358 | 34% | -0.08 |
| now | holdout | 1658 | 32% | -0.19 | 400 | 32% | -0.19 |

## The 20 inputs the model leans on most (confirm-4h model, research data)

| input | share of the model's decisions |
|---|---|
| vol_regime | 5% |
| n_cvd_trend | 4% |
| n_vwap_day | 3% |
| lq_pool2_r | 3% |
| lq_pool3_r | 3% |
| zone_behind_atr | 3% |
| n_vwap_week | 3% |
| n_vp_poc_side | 3% |
| j_ceiling_dist_r | 2% |
| x_stop_pct | 2% |
| lq_pool1_r | 2% |
| lq_zone_r | 2% |
| j_rejections | 2% |
| zone_ahead_atr | 2% |
| liq_in_risk | 2% |
| lq_htf_pool_r | 2% |
| m_8h_cmf | 1% |
| lq_eq_pool_r | 1% |
| zone_touches | 1% |
| m_1W_macd | 1% |

