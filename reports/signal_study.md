# Signal study - ETHUSDT daily

Research period **2019-12-18 -> 2025-10-27**. Holdout **2025-11-01 ->** is shown separately and should only be looked at after choosing signals.

## How to read this
- Every time a signal fires, we enter at the **next day's open** with a target of **+2 ATR** and a stop of **-1 ATR**, and wait up to **20 days**.
- **Win rate** = target reached first. Because the target is 2x the stop, roughly **33% is break-even** (timeouts aside).
- **Avg R** = average result in ATR units (+2 = full win, -1 = full loss). It's the best single measure of edge.
- **Baseline** = entering on *every* day in the same weekly trend and direction. A signal is only useful if it beats this.
- **t** = how far above the baseline, allowing for luck. Above 2 is notable. With this many rows a few will pass by chance, so confirm them on the holdout before trusting them.
- Costs: *after costs* subtracts 0.18% round-trip fees and slippage. Funding is not included (it adds about 0.1-0.3% per 20 days in calm markets, more in strong trends).
- If target and stop are both inside the same daily candle, it's counted as a loss.
- **At 5x**: *margin %* = result as a % of the margin used, after fees and slippage. With ETH's daily ATR of about 4-5%, a full stop-out (-1 ATR) costs roughly **22% of the margin**, and a win (+2 ATR) makes roughly **45%**. Liquidation (about -20% price move) is counted as -100%.

## 1. Does the weekly trend matter?

All signals and patterns together, by whether they agreed with the weekly trend (research period):

| vs weekly trend | events | win rate | avg R |
|---|---|---|---|
| with | 257 | 30% | -0.07 |
| sideways | 448 | 39% | +0.20 |
| against | 356 | 34% | +0.15 |

Baseline: entering on every day, by weekly trend and direction:

| weekly trend | direction | days | win rate | avg R |
|---|---|---|---|---|
| Down | short | 280 | 27% | -0.06 |
| Down | long | 280 | 36% | +0.19 |
| Sideways | short | 756 | 31% | -0.01 |
| Sideways | long | 756 | 34% | +0.08 |
| Up | short | 776 | 29% | -0.00 |
| Up | long | 776 | 33% | +0.05 |

## 2. Promising (research period, n >= 30, beats baseline with t >= 2, positive after costs)

Nothing cleared the bar. That's a real result too: these signals alone don't beat random entries.

## 3. Every signal (research period)

Sorted by signal, then direction and trend alignment.

| signal | dir | trend | n | win | win 95% range | avg R | after costs | baseline R | t | margin % @5x | worst | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bb_breakout | long | against | 10 | 70% | 40%-89% | +1.10 | +1.05 | +0.19 | 2.0 | +17.8% | -32% | too few |
| bb_breakout | long | sideways | 20 | 40% | 22%-61% | +0.20 | +0.16 | +0.08 | 0.4 | +4.2% | -31% | too few |
| bb_breakout | long | unknown | 19 | 21% | 9%-43% | -0.37 | -0.41 | - | - | -11.7% | -36% | too few |
| bb_breakout | long | with | 29 | 31% | 17%-49% | -0.07 | -0.10 | +0.05 | -0.4 | +1.0% | -43% | too few |
| bb_breakout | short | against | 18 | 11% | 3%-33% | -0.48 | -0.51 | -0.00 | -2.0 | -27.8% | -100% | too few |
| bb_breakout | short | sideways | 22 | 23% | 10%-43% | -0.13 | -0.17 | -0.01 | -0.4 | -6.8% | -58% | too few |
| bb_breakout | short | unknown | 4 | 0% | 0%-49% | -1.00 | -1.02 | - | - | -55.3% | -100% | too few |
| bb_breakout | short | with | 9 | 22% | 6%-55% | -0.20 | -0.23 | -0.06 | -0.3 | -9.8% | -69% | too few |
| bb_reversal | long | against | 9 | 0% | 0%-30% | -0.64 | -0.67 | +0.19 | -3.0 | -33.0% | -66% | too few |
| bb_reversal | long | sideways | 24 | 29% | 15%-49% | -0.12 | -0.16 | +0.08 | -0.7 | -13.2% | -55% | too few |
| bb_reversal | long | unknown | 5 | 20% | 4%-62% | +0.55 | +0.52 | - | - | +27.9% | -27% | too few |
| bb_reversal | long | with | 16 | 19% | 7%-43% | -0.24 | -0.27 | +0.05 | -0.9 | -11.1% | -100% | too few |
| bb_reversal | short | against | 31 | 35% | 21%-53% | +0.06 | +0.03 | -0.00 | 0.3 | -5.5% | -50% | no edge |
| bb_reversal | short | sideways | 23 | 35% | 19%-55% | +0.04 | +0.00 | -0.01 | 0.2 | -0.5% | -33% | too few |
| bb_reversal | short | unknown | 19 | 11% | 3%-31% | -0.65 | -0.68 | - | - | -19.8% | -41% | too few |
| bb_reversal | short | with | 5 | 20% | 4%-62% | -0.40 | -0.45 | -0.06 | -0.6 | -7.4% | -40% | too few |
| bb_squeeze_breakout | long | against | 1 | 0% | 0%-79% | -1.00 | -1.03 | +0.19 | - | -29.2% | -29% | too few |
| bb_squeeze_breakout | long | unknown | 3 | 0% | 0%-56% | -1.00 | -1.04 | - | - | -23.9% | -27% | too few |
| bb_squeeze_breakout | long | with | 3 | 67% | 21%-94% | +1.00 | +0.95 | +0.05 | 1.0 | +25.8% | -14% | too few |
| bb_squeeze_breakout | short | against | 4 | 0% | 0%-49% | -1.00 | -1.04 | -0.00 | - | -21.8% | -26% | too few |
| bb_squeeze_breakout | short | sideways | 3 | 67% | 21%-94% | +1.00 | +0.94 | -0.01 | 1.0 | +14.6% | -34% | too few |
| bb_squeeze_breakout | short | with | 1 | 0% | 0%-79% | -1.00 | -1.03 | -0.06 | - | -28.3% | -28% | too few |
| double_bottom | long | against | 1 | 100% | 21%-100% | +2.00 | +1.96 | +0.19 | - | +46.0% | +46% | too few |
| double_bottom | long | sideways | 2 | 100% | 34%-100% | +2.00 | +1.95 | +0.08 | - | +39.7% | +23% | too few |
| double_bottom | long | with | 2 | 100% | 34%-100% | +2.00 | +1.97 | +0.05 | - | +66.3% | +41% | too few |
| double_top | short | against | 2 | 0% | 0%-66% | -0.23 | -0.25 | -0.00 | -0.3 | -8.6% | -40% | too few |
| double_top | short | sideways | 2 | 50% | 9%-91% | +0.50 | +0.47 | -0.01 | 0.3 | +18.5% | -26% | too few |
| golden_death_cross | long | sideways | 3 | 33% | 6%-79% | +0.00 | -0.03 | +0.08 | -0.1 | -0.3% | -28% | too few |
| golden_death_cross | long | with | 2 | 50% | 9%-91% | +1.56 | +1.53 | +0.05 | 3.4 | +44.0% | +38% | too few |
| golden_death_cross | short | against | 1 | 0% | 0%-79% | -1.00 | -1.03 | -0.00 | - | -30.4% | -30% | too few |
| golden_death_cross | short | sideways | 4 | 0% | 0%-49% | -0.11 | -0.14 | -0.01 | -0.2 | -12.2% | -49% | too few |
| head_shoulders | short | against | 1 | 100% | 21%-100% | +2.00 | +1.95 | -0.00 | - | +31.9% | +32% | too few |
| ichimoku_cloud_break | long | against | 7 | 71% | 36%-92% | +1.14 | +1.10 | +0.19 | 1.7 | +21.4% | -46% | too few |
| ichimoku_cloud_break | long | sideways | 12 | 58% | 32%-81% | +0.75 | +0.71 | +0.08 | 1.5 | +20.1% | -29% | too few |
| ichimoku_cloud_break | long | unknown | 12 | 42% | 19%-68% | +0.25 | +0.21 | - | - | +2.0% | -56% | too few |
| ichimoku_cloud_break | long | with | 14 | 57% | 33%-79% | +0.77 | +0.73 | +0.05 | 1.8 | +14.6% | -45% | too few |
| ichimoku_cloud_break | short | against | 19 | 26% | 12%-49% | +0.06 | +0.03 | -0.00 | 0.2 | -6.6% | -100% | too few |
| ichimoku_cloud_break | short | sideways | 19 | 37% | 19%-59% | +0.14 | +0.11 | -0.01 | 0.4 | -0.6% | -55% | too few |
| ichimoku_cloud_break | short | unknown | 6 | 17% | 3%-56% | -0.50 | -0.53 | - | - | -8.8% | -40% | too few |
| ichimoku_cloud_break | short | with | 5 | 40% | 12%-77% | +0.20 | +0.16 | -0.06 | 0.3 | +3.6% | -27% | too few |
| ichimoku_kumo_twist | long | against | 3 | 100% | 44%-100% | +2.00 | +1.96 | +0.19 | - | +54.4% | +27% | too few |
| ichimoku_kumo_twist | long | sideways | 12 | 50% | 25%-75% | +0.50 | +0.46 | +0.08 | 0.9 | +11.8% | -44% | too few |
| ichimoku_kumo_twist | long | unknown | 2 | 0% | 0%-66% | -1.00 | -1.04 | - | - | -26.4% | -31% | too few |
| ichimoku_kumo_twist | long | with | 5 | 80% | 38%-96% | +1.40 | +1.36 | +0.05 | 2.3 | +34.5% | -20% | too few |
| ichimoku_kumo_twist | short | against | 9 | 22% | 6%-55% | -0.23 | -0.26 | -0.00 | -0.5 | -24.1% | -100% | too few |
| ichimoku_kumo_twist | short | sideways | 10 | 20% | 6%-51% | -0.31 | -0.35 | -0.01 | -0.8 | -16.1% | -46% | too few |
| ichimoku_kumo_twist | short | unknown | 3 | 0% | 0%-56% | -0.51 | -0.52 | - | - | -57.6% | -100% | too few |
| ichimoku_kumo_twist | short | with | 2 | 0% | 0%-66% | -1.00 | -1.03 | -0.06 | - | -30.8% | -33% | too few |
| ichimoku_tk_cross | long | against | 4 | 75% | 30%-95% | +1.25 | +1.20 | +0.19 | 1.4 | +19.3% | -35% | too few |
| ichimoku_tk_cross | long | sideways | 21 | 33% | 17%-55% | +0.00 | -0.04 | +0.08 | -0.3 | -2.2% | -44% | too few |
| ichimoku_tk_cross | long | unknown | 8 | 62% | 31%-86% | +0.88 | +0.84 | - | - | +18.7% | -32% | too few |
| ichimoku_tk_cross | long | with | 12 | 25% | 9%-53% | -0.25 | -0.29 | +0.05 | -0.8 | -12.1% | -58% | too few |
| ichimoku_tk_cross | short | against | 18 | 22% | 9%-45% | -0.10 | -0.13 | -0.00 | -0.3 | -10.5% | -100% | too few |
| ichimoku_tk_cross | short | sideways | 17 | 35% | 17%-59% | +0.28 | +0.25 | -0.01 | 0.8 | +5.3% | -45% | too few |
| ichimoku_tk_cross | short | unknown | 8 | 25% | 7%-59% | -0.10 | -0.13 | - | - | -10.2% | -100% | too few |
| ichimoku_tk_cross | short | with | 4 | 0% | 0%-49% | -0.64 | -0.67 | -0.06 | -1.6 | -16.4% | -38% | too few |
| inv_head_shoulders | long | sideways | 2 | 50% | 9%-91% | +0.50 | +0.45 | +0.08 | 0.3 | +10.5% | -18% | too few |
| inv_head_shoulders | long | unknown | 1 | 100% | 21%-100% | +2.00 | +1.96 | - | - | +48.5% | +48% | too few |
| inv_head_shoulders | long | with | 2 | 0% | 0%-66% | -1.00 | -1.04 | +0.05 | - | -25.6% | -32% | too few |
| ma200_cross | long | against | 2 | 100% | 34%-100% | +2.00 | +1.95 | +0.19 | - | +34.5% | +26% | too few |
| ma200_cross | long | sideways | 10 | 70% | 40%-89% | +1.10 | +1.06 | +0.08 | 2.2 | +28.2% | -55% | too few |
| ma200_cross | long | with | 1 | 0% | 0%-79% | -1.00 | -1.04 | +0.05 | - | -23.9% | -24% | too few |
| ma200_cross | short | against | 2 | 50% | 9%-91% | +0.50 | +0.46 | -0.00 | 0.3 | +7.0% | -25% | too few |
| ma200_cross | short | sideways | 11 | 55% | 28%-79% | +0.64 | +0.60 | -0.01 | 1.4 | +7.4% | -60% | too few |
| ma30_cross | long | against | 9 | 56% | 27%-81% | +0.67 | +0.63 | +0.19 | 0.9 | +14.6% | -36% | too few |
| ma30_cross | long | sideways | 26 | 31% | 17%-50% | -0.08 | -0.12 | +0.08 | -0.6 | -3.6% | -42% | too few |
| ma30_cross | long | unknown | 14 | 64% | 39%-84% | +0.93 | +0.89 | - | - | +22.7% | -45% | too few |
| ma30_cross | long | with | 31 | 23% | 11%-40% | -0.29 | -0.33 | +0.05 | -1.5 | -9.2% | -45% | no edge |
| ma30_cross | short | against | 39 | 28% | 17%-44% | +0.03 | -0.00 | -0.00 | 0.2 | -3.9% | -100% | no edge |
| ma30_cross | short | sideways | 23 | 48% | 29%-67% | +0.44 | +0.40 | -0.01 | 1.4 | +14.5% | -37% | too few |
| ma30_cross | short | unknown | 13 | 23% | 8%-50% | -0.31 | -0.34 | - | - | -5.9% | -55% | too few |
| ma30_cross | short | with | 5 | 0% | -0%-43% | -0.84 | -0.88 | -0.06 | -5.0 | -23.0% | -38% | too few |
| ma60_cross | long | against | 12 | 58% | 32%-81% | +0.75 | +0.71 | +0.19 | 1.2 | +14.8% | -39% | too few |
| ma60_cross | long | sideways | 16 | 38% | 18%-61% | +0.12 | +0.08 | +0.08 | 0.1 | +5.0% | -40% | too few |
| ma60_cross | long | unknown | 8 | 25% | 7%-59% | -0.12 | -0.15 | - | - | -9.3% | -58% | too few |
| ma60_cross | long | with | 19 | 42% | 23%-64% | +0.35 | +0.31 | +0.05 | 0.9 | +7.7% | -100% | too few |
| ma60_cross | short | against | 26 | 35% | 19%-54% | +0.28 | +0.24 | -0.00 | 1.1 | -8.4% | -100% | too few |
| ma60_cross | short | sideways | 14 | 50% | 27%-73% | +0.50 | +0.46 | -0.01 | 1.2 | +11.2% | -34% | too few |
| ma60_cross | short | unknown | 8 | 25% | 7%-59% | -0.09 | -0.12 | - | - | -2.7% | -62% | too few |
| ma60_cross | short | with | 8 | 12% | 2%-47% | -0.62 | -0.66 | -0.06 | -1.5 | -22.2% | -41% | too few |
| macd_signal_cross | long | against | 11 | 27% | 10%-57% | +0.09 | +0.06 | +0.19 | -0.2 | -4.8% | -51% | too few |
| macd_signal_cross | long | sideways | 33 | 48% | 33%-65% | +0.45 | +0.42 | +0.08 | 1.4 | +7.7% | -49% | no edge |
| macd_signal_cross | long | unknown | 12 | 42% | 19%-68% | +0.37 | +0.34 | - | - | +7.2% | -45% | too few |
| macd_signal_cross | long | with | 28 | 25% | 13%-43% | -0.25 | -0.28 | +0.05 | -1.2 | -8.9% | -71% | too few |
| macd_signal_cross | short | against | 35 | 40% | 26%-56% | +0.26 | +0.23 | -0.00 | 1.1 | +2.6% | -83% | no edge |
| macd_signal_cross | short | sideways | 29 | 41% | 26%-59% | +0.24 | +0.21 | -0.01 | 0.9 | +5.1% | -45% | too few |
| macd_signal_cross | short | unknown | 12 | 25% | 9%-53% | -0.25 | -0.28 | - | - | -3.9% | -43% | too few |
| macd_signal_cross | short | with | 8 | 25% | 7%-59% | -0.25 | -0.28 | -0.06 | -0.4 | -4.2% | -39% | too few |
| macd_zero_cross | long | against | 7 | 43% | 16%-75% | +0.29 | +0.24 | +0.19 | 0.2 | +0.3% | -37% | too few |
| macd_zero_cross | long | sideways | 14 | 43% | 21%-67% | +0.29 | +0.24 | +0.08 | 0.5 | +9.5% | -31% | too few |
| macd_zero_cross | long | unknown | 4 | 25% | 5%-70% | -0.25 | -0.29 | - | - | -7.1% | -33% | too few |
| macd_zero_cross | long | with | 10 | 30% | 11%-60% | -0.10 | -0.14 | +0.05 | -0.3 | -8.0% | -49% | too few |
| macd_zero_cross | short | against | 18 | 17% | 6%-39% | -0.17 | -0.20 | -0.00 | -0.6 | -13.7% | -100% | too few |
| macd_zero_cross | short | sideways | 10 | 40% | 17%-69% | +0.30 | +0.27 | -0.01 | 0.7 | +7.4% | -40% | too few |
| macd_zero_cross | short | unknown | 3 | 33% | 6%-79% | +0.00 | -0.03 | - | - | +6.5% | -59% | too few |
| macd_zero_cross | short | with | 4 | 0% | 0%-49% | -1.00 | -1.03 | -0.06 | - | -28.8% | -41% | too few |
| rsi_reversal | long | against | 5 | 0% | -0%-43% | -0.84 | -0.86 | +0.19 | -6.3 | -37.0% | -53% | too few |
| rsi_reversal | long | sideways | 9 | 33% | 12%-65% | +0.00 | -0.03 | +0.08 | -0.2 | -4.0% | -52% | too few |
| rsi_reversal | long | unknown | 4 | 0% | 0%-49% | -0.10 | -0.12 | - | - | +21.1% | -100% | too few |
| rsi_reversal | long | with | 1 | 0% | 0%-79% | -1.00 | -1.04 | +0.05 | - | -23.9% | -24% | too few |
| rsi_reversal | short | against | 22 | 41% | 23%-61% | +0.23 | +0.20 | -0.00 | 0.7 | +4.5% | -83% | too few |
| rsi_reversal | short | sideways | 15 | 13% | 4%-38% | -0.60 | -0.64 | -0.01 | -2.2 | -18.6% | -40% | too few |
| rsi_reversal | short | unknown | 12 | 25% | 9%-53% | -0.25 | -0.28 | - | - | -5.8% | -43% | too few |
| rsi_reversal | short | with | 2 | 50% | 9%-91% | +0.50 | +0.46 | -0.06 | 0.4 | +16.6% | -23% | too few |
| triangle_ascending | long | unknown | 1 | 100% | 21%-100% | +2.00 | +1.94 | - | - | +31.0% | +31% | too few |
| triangle_ascending | long | with | 2 | 50% | 9%-91% | +0.50 | +0.46 | +0.05 | 0.3 | +15.7% | -19% | too few |
| triangle_ascending | short | against | 1 | 0% | 0%-79% | -1.00 | -1.02 | -0.00 | - | -42.5% | -42% | too few |
| triangle_ascending | short | sideways | 2 | 100% | 34%-100% | +2.00 | +1.96 | -0.01 | - | +45.8% | +42% | too few |
| triangle_ascending | short | unknown | 2 | 0% | 0%-66% | -1.00 | -1.04 | - | - | -26.0% | -29% | too few |
| triangle_descending | long | sideways | 3 | 67% | 21%-94% | +1.00 | +0.94 | +0.08 | 0.9 | +30.6% | -10% | too few |
| triangle_descending | long | unknown | 1 | 100% | 21%-100% | +2.00 | +1.96 | - | - | +39.4% | +39% | too few |
| triangle_descending | short | sideways | 2 | 50% | 9%-91% | +0.50 | +0.46 | -0.01 | 0.3 | +15.8% | -21% | too few |
| triangle_symmetrical | long | sideways | 3 | 67% | 21%-94% | +1.00 | +0.97 | +0.08 | 0.9 | +16.4% | -40% | too few |
| triangle_symmetrical | long | unknown | 1 | 100% | 21%-100% | +2.00 | +1.96 | - | - | +48.5% | +48% | too few |
| triangle_symmetrical | long | with | 3 | 33% | 6%-79% | +0.00 | -0.04 | +0.05 | -0.0 | -7.9% | -32% | too few |
| triangle_symmetrical | short | against | 2 | 100% | 34%-100% | +2.00 | +1.96 | -0.00 | - | +42.1% | +32% | too few |
| volume_spike | long | against | 11 | 64% | 35%-85% | +0.91 | +0.87 | +0.19 | 1.6 | +8.8% | -56% | too few |
| volume_spike | long | sideways | 13 | 38% | 18%-64% | +0.15 | +0.12 | +0.08 | 0.2 | -2.2% | -52% | too few |
| volume_spike | long | unknown | 18 | 39% | 20%-61% | +0.23 | +0.20 | - | - | -3.9% | -100% | too few |
| volume_spike | long | with | 15 | 27% | 11%-52% | -0.20 | -0.23 | +0.05 | -0.7 | -5.3% | -43% | too few |
| volume_spike | short | against | 16 | 12% | 3%-36% | -0.57 | -0.60 | -0.00 | -2.2 | -28.1% | -100% | too few |
| volume_spike | short | sideways | 19 | 21% | 9%-43% | -0.37 | -0.40 | -0.01 | -1.3 | -18.9% | -58% | too few |
| volume_spike | short | unknown | 8 | 25% | 7%-59% | -0.25 | -0.27 | - | - | -19.7% | -100% | too few |
| volume_spike | short | with | 9 | 44% | 19%-73% | +0.33 | +0.31 | -0.06 | 0.7 | +15.6% | -78% | too few |

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
- weekly trend: Up = weekly close > SMA20w > SMA50w and SMA20w rising over 3 weeks; Down = mirror; else Sideways (first 53 weeks: Unknown, excluded from trend tables)

Raw data: `signal_events.csv` (every event with its outcome), `signal_summary_*.csv`.
