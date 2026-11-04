# Signal study - ETHUSDT daily

Research period: signals **2019-12-18 -> 2025-10-10** (every trade finished before the holdout). Holdout: signals from **2025-11-01** on, shown only in section 2. Look at it only after choosing signals.

## How to read this
- Every time a signal fires, we enter at the **next day's open** with a target of **+2 ATR** and a stop of **-1 ATR**, and wait up to **20 days**.
- **Win rate** = target reached first. Because the target is 2x the stop, roughly **33% is break-even** (timeouts aside).
- **Avg R** = average result in ATR units (+2 = full win, -1 = full loss). It's the best single measure of edge.
- **Baseline** = entering on *every* day in the same weekly trend and direction. A signal is only useful if it beats this.
- **t** = how far above the baseline, allowing for luck. Above 2 is notable. With this many rows a few will pass by chance, so confirm them on the holdout before trusting them.
- Costs: *after costs* subtracts 0.18% round-trip fees and slippage. Funding is not included (it adds about 0.1-0.3% per 20 days in calm markets, more in strong trends).
- If target and stop are both inside the same daily candle, it's counted as a loss.
- **At 5x**: *margin %* = result as a % of the margin used, after fees and slippage. ETH's median daily ATR in this period is **5.5%** of price, so a full stop-out (-1 ATR) costs about **29% of the margin** and a win (+2 ATR) makes about **54%**. Liquidation (about -19.5% price move, isolated margin) is counted as -100%. In the March 2020 and May 2021 crashes ATR was above 20%, so a 1-ATR stop sat beyond the 5x liquidation price.
- Events overlap (several signals often fire on the same day and share one outcome), so the pooled tables and t-values are somewhat optimistic.

## 1. Does the weekly trend matter?

All signals and patterns together, by whether they agreed with the weekly trend (research period):

| vs weekly trend | events | win rate | avg R |
|---|---|---|---|
| with | 325 | 24% | -0.21 |
| sideways | 276 | 41% | +0.29 |
| against | 441 | 33% | +0.10 |

Separate trend stretches in this period: **11 Up**, **10 Down**, 20 Sideways. Results per trend rest on only this many independent episodes, so treat them as indications, not laws.

Baseline: entering on every day, by weekly trend and direction:

| weekly trend | direction | days | win rate | avg R |
|---|---|---|---|---|
| Down | short | 462 | 23% | -0.21 |
| Down | long | 462 | 40% | +0.27 |
| Sideways | short | 448 | 35% | +0.13 |
| Sideways | long | 448 | 30% | -0.03 |
| Up | short | 882 | 29% | -0.03 |
| Up | long | 882 | 32% | +0.01 |

## 2. Promising (research period, n >= 30, beats baseline with t >= 2, positive after costs)

Nothing cleared the bar. That's a real result too: these signals alone don't beat random entries.

## 3. Every signal (research period)

Sorted by signal, then direction and trend alignment.

| signal | dir | trend | n | win | win 95% range | avg R | after costs | baseline R | t | margin % @5x | worst | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bb_breakout | long | against | 13 | 54% | 29%-77% | +0.62 | +0.57 | +0.27 | 0.8 | +10.9% | -34% | too few |
| bb_breakout | long | sideways | 12 | 42% | 19%-68% | +0.25 | +0.21 | -0.03 | 0.6 | +5.2% | -31% | too few |
| bb_breakout | long | unknown | 19 | 21% | 9%-43% | -0.37 | -0.40 | - | - | -12.6% | -45% | too few |
| bb_breakout | long | with | 34 | 29% | 17%-46% | -0.08 | -0.12 | +0.01 | -0.4 | -0.6% | -44% | no edge |
| bb_breakout | short | against | 21 | 5% | 1%-23% | -0.69 | -0.72 | -0.03 | -4.0 | -32.8% | -100% | too few |
| bb_breakout | short | sideways | 17 | 35% | 17%-59% | +0.30 | +0.27 | +0.13 | 0.5 | +6.1% | -73% | too few |
| bb_breakout | short | unknown | 4 | 0% | 0%-49% | -1.00 | -1.02 | - | - | -57.3% | -100% | too few |
| bb_breakout | short | with | 11 | 18% | 5%-48% | -0.35 | -0.38 | -0.21 | -0.4 | -13.5% | -74% | too few |
| bb_reversal | long | against | 12 | 17% | 5%-45% | -0.25 | -0.27 | +0.27 | -1.4 | -21.6% | -70% | too few |
| bb_reversal | long | sideways | 18 | 28% | 12%-51% | -0.12 | -0.15 | -0.03 | -0.3 | -11.8% | -60% | too few |
| bb_reversal | long | unknown | 5 | 20% | 4%-62% | +0.36 | +0.34 | - | - | +16.7% | -55% | too few |
| bb_reversal | long | with | 19 | 16% | 6%-38% | -0.36 | -0.39 | +0.01 | -1.4 | -14.5% | -93% | too few |
| bb_reversal | short | against | 35 | 31% | 19%-48% | +0.01 | -0.02 | -0.03 | 0.2 | -4.5% | -47% | no edge |
| bb_reversal | short | sideways | 16 | 31% | 14%-56% | -0.06 | -0.10 | +0.13 | -0.5 | -1.5% | -31% | too few |
| bb_reversal | short | unknown | 19 | 16% | 6%-38% | -0.49 | -0.53 | - | - | -14.1% | -43% | too few |
| bb_reversal | short | with | 8 | 38% | 14%-69% | +0.12 | +0.08 | -0.21 | 0.6 | +1.3% | -41% | too few |
| bb_squeeze_breakout | long | against | 1 | 0% | 0%-79% | -1.00 | -1.03 | +0.27 | - | -31.0% | -31% | too few |
| bb_squeeze_breakout | long | unknown | 3 | 0% | 0%-56% | -1.00 | -1.04 | - | - | -25.5% | -28% | too few |
| bb_squeeze_breakout | long | with | 3 | 33% | 6%-79% | +0.42 | +0.37 | +0.01 | 0.5 | +14.4% | -17% | too few |
| bb_squeeze_breakout | short | against | 5 | 0% | -0%-43% | -1.00 | -1.04 | -0.03 | - | -26.6% | -33% | too few |
| bb_squeeze_breakout | short | sideways | 2 | 100% | 34%-100% | +2.00 | +1.94 | +0.13 | - | +45.9% | +19% | too few |
| bb_squeeze_breakout | short | with | 1 | 0% | 0%-79% | -1.00 | -1.03 | -0.21 | - | -28.4% | -28% | too few |
| double_bottom | long | against | 2 | 100% | 34%-100% | +2.00 | +1.94 | +0.27 | - | +34.1% | +24% | too few |
| double_bottom | long | with | 1 | 100% | 21%-100% | +2.00 | +1.98 | +0.01 | - | +75.8% | +76% | too few |
| double_top | short | against | 2 | 0% | 0%-66% | -0.22 | -0.24 | -0.03 | -0.2 | -8.9% | -41% | too few |
| double_top | short | sideways | 1 | 0% | 0%-79% | -1.00 | -1.04 | +0.13 | - | -25.8% | -26% | too few |
| golden_death_cross | long | sideways | 2 | 50% | 9%-91% | +0.50 | +0.47 | -0.03 | 0.4 | +13.8% | -25% | too few |
| golden_death_cross | long | with | 3 | 33% | 6%-79% | +0.73 | +0.69 | +0.01 | 0.8 | +17.9% | -27% | too few |
| golden_death_cross | short | against | 1 | 0% | 0%-79% | -1.00 | -1.03 | -0.03 | - | -31.0% | -31% | too few |
| golden_death_cross | short | sideways | 3 | 0% | 0%-56% | +0.18 | +0.15 | +0.13 | 0.1 | -1.1% | -44% | too few |
| golden_death_cross | short | with | 1 | 0% | 0%-79% | -1.00 | -1.02 | -0.21 | - | -48.0% | -48% | too few |
| head_shoulders | short | against | 1 | 100% | 21%-100% | +2.00 | +1.95 | -0.03 | - | +36.6% | +37% | too few |
| ichimoku_cloud_break | long | against | 9 | 67% | 35%-88% | +1.00 | +0.96 | +0.27 | 1.5 | +22.0% | -41% | too few |
| ichimoku_cloud_break | long | sideways | 9 | 67% | 35%-88% | +1.00 | +0.96 | -0.03 | 2.1 | +27.1% | -26% | too few |
| ichimoku_cloud_break | long | unknown | 8 | 38% | 14%-69% | +0.12 | +0.09 | - | - | -0.2% | -45% | too few |
| ichimoku_cloud_break | long | with | 15 | 47% | 25%-70% | +0.53 | +0.50 | +0.01 | 1.4 | +10.6% | -46% | too few |
| ichimoku_cloud_break | short | against | 22 | 27% | 13%-48% | -0.07 | -0.10 | -0.03 | -0.1 | -8.2% | -100% | too few |
| ichimoku_cloud_break | short | sideways | 8 | 50% | 22%-78% | +0.58 | +0.54 | +0.13 | 0.8 | +7.7% | -52% | too few |
| ichimoku_cloud_break | short | unknown | 6 | 17% | 3%-56% | -0.50 | -0.53 | - | - | -12.1% | -46% | too few |
| ichimoku_cloud_break | short | with | 12 | 25% | 9%-53% | -0.15 | -0.19 | -0.21 | 0.2 | -3.6% | -44% | too few |
| ichimoku_kumo_twist | long | against | 8 | 62% | 31%-86% | +0.88 | +0.84 | +0.27 | 1.1 | +26.6% | -41% | too few |
| ichimoku_kumo_twist | long | sideways | 6 | 67% | 30%-90% | +1.00 | +0.96 | -0.03 | 1.6 | +24.0% | -26% | too few |
| ichimoku_kumo_twist | long | unknown | 2 | 50% | 9%-91% | +0.50 | +0.47 | - | - | +21.8% | -23% | too few |
| ichimoku_kumo_twist | long | with | 6 | 50% | 19%-81% | +0.71 | +0.67 | +0.01 | 1.1 | +20.9% | -26% | too few |
| ichimoku_kumo_twist | short | against | 10 | 10% | 2%-40% | -0.61 | -0.64 | -0.03 | -1.9 | -30.3% | -100% | too few |
| ichimoku_kumo_twist | short | sideways | 5 | 40% | 12%-77% | +0.37 | +0.32 | +0.13 | 0.4 | +0.3% | -28% | too few |
| ichimoku_kumo_twist | short | unknown | 2 | 0% | 0%-66% | -0.20 | -0.21 | - | - | -36.4% | -100% | too few |
| ichimoku_kumo_twist | short | with | 6 | 0% | 0%-39% | -1.00 | -1.03 | -0.21 | - | -30.7% | -43% | too few |
| ichimoku_tk_cross | long | against | 9 | 56% | 27%-81% | +0.67 | +0.63 | +0.27 | 0.8 | +10.2% | -42% | too few |
| ichimoku_tk_cross | long | sideways | 14 | 29% | 12%-55% | -0.14 | -0.18 | -0.03 | -0.3 | -4.3% | -36% | too few |
| ichimoku_tk_cross | long | unknown | 8 | 62% | 31%-86% | +0.88 | +0.84 | - | - | +19.0% | -45% | too few |
| ichimoku_tk_cross | long | with | 14 | 14% | 4%-40% | -0.48 | -0.52 | +0.01 | -1.7 | -18.8% | -72% | too few |
| ichimoku_tk_cross | short | against | 20 | 15% | 5%-36% | -0.27 | -0.30 | -0.03 | -0.9 | -16.4% | -100% | too few |
| ichimoku_tk_cross | short | sideways | 9 | 33% | 12%-65% | +0.25 | +0.22 | +0.13 | 0.3 | +3.7% | -45% | too few |
| ichimoku_tk_cross | short | unknown | 7 | 29% | 8%-64% | +0.03 | +0.00 | - | - | +2.3% | -38% | too few |
| ichimoku_tk_cross | short | with | 9 | 22% | 6%-55% | -0.17 | -0.20 | -0.21 | 0.1 | -2.5% | -42% | too few |
| inv_head_shoulders | long | sideways | 1 | 100% | 21%-100% | +2.00 | +1.96 | -0.03 | - | +45.6% | +46% | too few |
| inv_head_shoulders | long | unknown | 1 | 100% | 21%-100% | +2.00 | +1.97 | - | - | +52.9% | +53% | too few |
| inv_head_shoulders | long | with | 2 | 0% | 0%-66% | -1.00 | -1.04 | +0.01 | - | -27.0% | -34% | too few |
| ma200_cross | long | against | 2 | 100% | 34%-100% | +2.00 | +1.95 | +0.27 | - | +36.0% | +30% | too few |
| ma200_cross | long | sideways | 10 | 60% | 31%-83% | +0.96 | +0.92 | -0.03 | 2.3 | +20.9% | -27% | too few |
| ma200_cross | long | with | 1 | 0% | 0%-79% | -1.00 | -1.04 | +0.01 | - | -24.2% | -24% | too few |
| ma200_cross | short | against | 2 | 0% | 0%-66% | -1.00 | -1.04 | -0.03 | - | -24.1% | -25% | too few |
| ma200_cross | short | sideways | 11 | 45% | 21%-72% | +0.36 | +0.33 | +0.13 | 0.5 | +2.1% | -74% | too few |
| ma30_cross | long | against | 17 | 53% | 31%-74% | +0.59 | +0.55 | +0.27 | 0.9 | +11.5% | -45% | too few |
| ma30_cross | long | sideways | 15 | 27% | 11%-52% | -0.20 | -0.24 | -0.03 | -0.5 | -3.1% | -34% | too few |
| ma30_cross | long | unknown | 14 | 64% | 39%-84% | +0.93 | +0.90 | - | - | +23.5% | -45% | too few |
| ma30_cross | long | with | 33 | 18% | 9%-34% | -0.45 | -0.49 | +0.01 | -2.3 | -13.2% | -48% | worse than random |
| ma30_cross | short | against | 42 | 29% | 17%-44% | +0.01 | -0.02 | -0.03 | 0.2 | -4.6% | -100% | no edge |
| ma30_cross | short | sideways | 13 | 46% | 23%-71% | +0.38 | +0.35 | +0.13 | 0.6 | +13.5% | -30% | too few |
| ma30_cross | short | unknown | 13 | 23% | 8%-50% | -0.31 | -0.34 | - | - | -6.3% | -45% | too few |
| ma30_cross | short | with | 11 | 9% | 2%-38% | -0.66 | -0.69 | -0.21 | -1.6 | -16.0% | -45% | too few |
| ma60_cross | long | against | 18 | 56% | 34%-75% | +0.67 | +0.63 | +0.27 | 1.1 | +14.5% | -39% | too few |
| ma60_cross | long | sideways | 8 | 50% | 22%-78% | +0.50 | +0.46 | -0.03 | 0.9 | +20.6% | -22% | too few |
| ma60_cross | long | unknown | 8 | 25% | 7%-59% | -0.25 | -0.28 | - | - | -14.5% | -55% | too few |
| ma60_cross | long | with | 21 | 33% | 17%-55% | +0.09 | +0.06 | +0.01 | 0.3 | +1.5% | -93% | too few |
| ma60_cross | short | against | 29 | 34% | 20%-53% | +0.23 | +0.19 | -0.03 | 1.0 | -6.1% | -100% | too few |
| ma60_cross | short | sideways | 7 | 71% | 36%-92% | +1.14 | +1.10 | +0.13 | 1.8 | +25.5% | -32% | too few |
| ma60_cross | short | unknown | 8 | 25% | 7%-59% | -0.08 | -0.11 | - | - | -2.3% | -57% | too few |
| ma60_cross | short | with | 12 | 17% | 5%-45% | -0.50 | -0.53 | -0.21 | -0.8 | -14.7% | -41% | too few |
| macd_signal_cross | long | against | 21 | 38% | 21%-59% | +0.25 | +0.22 | +0.27 | -0.0 | -0.1% | -64% | too few |
| macd_signal_cross | long | sideways | 16 | 50% | 28%-72% | +0.53 | +0.49 | -0.03 | 1.5 | +11.5% | -56% | too few |
| macd_signal_cross | long | unknown | 12 | 42% | 19%-68% | +0.40 | +0.37 | - | - | +9.5% | -42% | too few |
| macd_signal_cross | long | with | 34 | 24% | 12%-40% | -0.29 | -0.33 | +0.01 | -1.4 | -12.3% | -74% | no edge |
| macd_signal_cross | short | against | 43 | 33% | 20%-47% | +0.12 | +0.09 | -0.03 | 0.7 | +1.4% | -69% | no edge |
| macd_signal_cross | short | sideways | 13 | 54% | 29%-77% | +0.62 | +0.58 | +0.13 | 1.1 | +14.3% | -48% | too few |
| macd_signal_cross | short | unknown | 12 | 17% | 5%-45% | -0.50 | -0.53 | - | - | -14.5% | -45% | too few |
| macd_signal_cross | short | with | 16 | 25% | 10%-49% | -0.25 | -0.28 | -0.21 | -0.1 | -3.5% | -42% | too few |
| macd_zero_cross | long | against | 11 | 36% | 15%-65% | +0.09 | +0.05 | +0.27 | -0.4 | -0.9% | -39% | too few |
| macd_zero_cross | long | sideways | 9 | 56% | 27%-81% | +0.67 | +0.63 | -0.03 | 1.3 | +19.8% | -35% | too few |
| macd_zero_cross | long | unknown | 4 | 25% | 5%-70% | -0.25 | -0.28 | - | - | -10.7% | -43% | too few |
| macd_zero_cross | long | with | 11 | 18% | 5%-48% | -0.34 | -0.38 | +0.01 | -1.0 | -10.9% | -45% | too few |
| macd_zero_cross | short | against | 20 | 20% | 8%-42% | -0.14 | -0.17 | -0.03 | -0.4 | -10.9% | -100% | too few |
| macd_zero_cross | short | sideways | 5 | 40% | 12%-77% | +0.41 | +0.38 | +0.13 | 0.4 | +10.5% | -36% | too few |
| macd_zero_cross | short | unknown | 3 | 33% | 6%-79% | +0.00 | -0.02 | - | - | +5.9% | -55% | too few |
| macd_zero_cross | short | with | 7 | 14% | 3%-51% | -0.57 | -0.61 | -0.21 | -0.8 | -12.5% | -41% | too few |
| rsi_reversal | long | against | 7 | 29% | 8%-64% | -0.14 | -0.17 | +0.27 | -0.7 | -16.5% | -64% | too few |
| rsi_reversal | long | sideways | 7 | 14% | 3%-51% | -0.57 | -0.61 | -0.03 | -1.3 | -21.5% | -48% | too few |
| rsi_reversal | long | unknown | 4 | 25% | 5%-70% | -0.25 | -0.27 | - | - | +11.4% | -100% | too few |
| rsi_reversal | long | with | 1 | 0% | 0%-79% | -1.00 | -1.04 | +0.01 | - | -24.6% | -25% | too few |
| rsi_reversal | short | against | 26 | 38% | 22%-57% | +0.15 | +0.12 | -0.03 | 0.6 | +2.3% | -69% | too few |
| rsi_reversal | short | sideways | 11 | 18% | 5%-48% | -0.45 | -0.49 | +0.13 | -1.6 | -12.5% | -34% | too few |
| rsi_reversal | short | unknown | 12 | 33% | 14%-61% | +0.00 | -0.03 | - | - | +2.9% | -34% | too few |
| rsi_reversal | short | with | 2 | 50% | 9%-91% | +0.50 | +0.47 | -0.21 | 0.5 | +17.4% | -25% | too few |
| triangle_ascending | long | unknown | 1 | 100% | 21%-100% | +2.00 | +1.95 | - | - | +35.2% | +35% | too few |
| triangle_ascending | long | with | 1 | 100% | 21%-100% | +2.00 | +1.97 | +0.01 | - | +55.3% | +55% | too few |
| triangle_ascending | short | against | 1 | 100% | 21%-100% | +2.00 | +1.97 | -0.03 | - | +52.2% | +52% | too few |
| triangle_ascending | short | sideways | 1 | 100% | 21%-100% | +2.00 | +1.97 | +0.13 | - | +50.6% | +51% | too few |
| triangle_descending | long | sideways | 3 | 67% | 21%-94% | +1.00 | +0.95 | -0.03 | 1.0 | +35.8% | -11% | too few |
| triangle_descending | long | unknown | 1 | 100% | 21%-100% | +2.00 | +1.97 | - | - | +53.8% | +54% | too few |
| triangle_descending | short | sideways | 1 | 0% | 0%-79% | -1.00 | -1.05 | +0.13 | - | -20.5% | -21% | too few |
| triangle_symmetrical | long | against | 1 | 0% | 0%-79% | -1.00 | -1.02 | +0.27 | - | -39.5% | -39% | too few |
| triangle_symmetrical | long | with | 1 | 100% | 21%-100% | +2.00 | +1.95 | +0.01 | - | +36.7% | +37% | too few |
| volume_spike | long | against | 12 | 67% | 39%-86% | +1.00 | +0.96 | +0.27 | 1.7 | +16.3% | -62% | too few |
| volume_spike | long | sideways | 9 | 44% | 19%-73% | +0.33 | +0.29 | -0.03 | 0.7 | -1.5% | -52% | too few |
| volume_spike | long | unknown | 18 | 39% | 20%-61% | +0.17 | +0.13 | - | - | -2.8% | -100% | too few |
| volume_spike | long | with | 17 | 18% | 6%-41% | -0.40 | -0.43 | +0.01 | -1.4 | -10.2% | -41% | too few |
| volume_spike | short | against | 18 | 11% | 3%-33% | -0.67 | -0.69 | -0.03 | -2.8 | -27.8% | -100% | too few |
| volume_spike | short | sideways | 14 | 29% | 12%-55% | -0.14 | -0.17 | +0.13 | -0.7 | -12.1% | -74% | too few |
| volume_spike | short | unknown | 8 | 25% | 7%-59% | -0.25 | -0.27 | - | - | -17.8% | -100% | too few |
| volume_spike | short | with | 12 | 33% | 14%-61% | +0.00 | -0.02 | -0.21 | 0.5 | +5.0% | -79% | too few |

## 4. Signal definitions

- **ichimoku_tk_cross**: Tenkan (9) crosses Kijun (26)
- **ichimoku_cloud_break**: Close breaks out of the Ichimoku cloud (above top / below bottom)
- **ichimoku_kumo_twist**: Future cloud changes colour (Span A crosses Span B)
- **macd_signal_cross**: MACD (12,26) crosses its 9-day signal line
- **macd_zero_cross**: MACD line crosses zero
- **ma30_cross**: Close crosses the 30-day average
- **ma60_cross**: Close crosses the 60-day average
- **ma200_cross**: Close crosses the 200-day average
- **golden_death_cross**: 50-day average crosses the 200-day average
- **bb_breakout**: Close moves outside a Bollinger band (20, 2) - continuation
- **bb_reversal**: Close comes back inside a Bollinger band after closing outside - reversal
- **bb_squeeze_breakout**: Bollinger breakout within 5 days of a 120-day low in band width
- **volume_spike**: Volume > 2x its 20-day average; direction = day's candle colour
- **rsi_reversal**: RSI (14) crosses back above 30 (bullish) / below 70 (bearish)
- **double_top**: Two similar highs with a dip between; close breaks below the dip (bearish)
- **double_bottom**: Two similar lows with a bounce between; close breaks above the bounce (bullish)
- **head_shoulders**: Three highs, middle highest; close breaks below the neckline (bearish)
- **inv_head_shoulders**: Three lows, middle lowest; close breaks above the neckline (bullish)
- **triangle_ascending**: Flat highs + rising lows; direction = breakout side
- **triangle_descending**: Falling highs + flat lows; direction = breakout side
- **triangle_symmetrical**: Falling highs + rising lows; direction = breakout side

## Settings

- outcome: `{'target_atr': 2.0, 'stop_atr': 1.0, 'max_days': 20}`
- patterns: `{'swing_k': 5, 'max_breakout_wait': 40, 'double_tol': 0.03, 'double_min_depth': 0.05, 'double_min_gap': 10, 'double_max_gap': 120, 'hs_head_margin': 0.03, 'hs_shoulder_tol': 0.08, 'hs_max_span': 150, 'tri_flat': 0.02, 'tri_slope': 0.03, 'tri_max_span': 90}`
- weekly trend: Up = weekly close above SMA20w and SMA50w, SMA20w rising over 3 weeks; Down = mirror; else Sideways (first 50 completed weeks: Unknown, excluded from trend tables)
- data: 5m bad-print wicks (>15% beyond body and neighbours) are clipped before building daily bars; ATR is Wilder's 14-day ATR

Raw data: `signal_events.csv` (every event with its outcome), `signal_summary_*.csv`.
