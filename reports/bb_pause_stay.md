# Touches the middle band, keeps on the upper side, then a pump?

Six coins (BTC, ETH, BNB, SOL, XRP, DOGE), mirrored for dumps. Decision at the N-th close after the touch, all of them above the middle band. **pump** = a new high above everything so far before a close 0.5 ATR below the middle band (30 candles). **fair** = 1.5 ATR up before 1.5 ATR down (50% = coin flip). The pump rate depends on how far the old high and the failure level are (median distances shown, in ATR), so compare the two rows of each pair, not the pump rate with 50%. 90% intervals: bootstrap of calendar months.

| timeframe | closes above the middle after the touch |  | cases 2020-25 | pump | 90% low | 90% high | distance to the old high | distance to the failure level | fair test | 90% low | 90% high | holdout cases | holdout pump | holdout fair |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | 1 | after a pump and sideways (the trader's sequence) | 200 | 36% | 30% | 42% | 1.8 | 1.1 | 52% | 45% | 58% | 32 | 38% | 62% |
| 1D | 1 | without the sequence | 3360 | 40% | 36% | 43% | 2.2 | 1.1 | 54% | 51% | 57% | 584 | 30% | 48% |
| 1D | 2 | after a pump and sideways (the trader's sequence) | 171 | 40% | 33% | 47% | 1.7 | 1.1 | 49% | 42% | 56% | 28 | 43% | 61% |
| 1D | 2 | without the sequence | 2863 | 42% | 38% | 46% | 2.1 | 1.2 | 54% | 51% | 57% | 478 | 34% | 49% |
| 1D | 3 | after a pump and sideways (the trader's sequence) | 138 | 46% | 39% | 53% | 1.6 | 1.3 | 51% | 43% | 59% | 24 | 46% | 50% |
| 1D | 3 | without the sequence | 2517 | 43% | 39% | 48% | 2.0 | 1.3 | 54% | 50% | 58% | 408 | 38% | 50% |
| 1D | 5 | after a pump and sideways (the trader's sequence) | 100 | 48% | 40% | 56% | 1.5 | 1.3 | 56% | 47% | 66% | 16 | 56% | 50% |
| 1D | 5 | without the sequence | 2015 | 44% | 40% | 49% | 1.9 | 1.5 | 52% | 47% | 56% | 307 | 40% | 47% |
| 4h | 1 | after a pump and sideways (the trader's sequence) | 1176 | 37% | 34% | 40% | 1.9 | 1.0 | 50% | 48% | 53% | 215 | 36% | 50% |
| 4h | 1 | without the sequence | 21953 | 36% | 34% | 38% | 2.2 | 1.0 | 51% | 50% | 53% | 3690 | 39% | 52% |
| 4h | 2 | after a pump and sideways (the trader's sequence) | 972 | 40% | 37% | 43% | 1.7 | 1.1 | 49% | 46% | 52% | 168 | 42% | 52% |
| 4h | 2 | without the sequence | 18246 | 39% | 37% | 41% | 2.1 | 1.2 | 51% | 50% | 53% | 3022 | 43% | 53% |
| 4h | 3 | after a pump and sideways (the trader's sequence) | 809 | 44% | 41% | 47% | 1.6 | 1.2 | 49% | 45% | 52% | 137 | 47% | 56% |
| 4h | 3 | without the sequence | 15809 | 41% | 39% | 43% | 2.0 | 1.3 | 51% | 50% | 53% | 2610 | 45% | 52% |
| 4h | 5 | after a pump and sideways (the trader's sequence) | 588 | 49% | 45% | 53% | 1.4 | 1.3 | 48% | 44% | 52% | 94 | 59% | 63% |
| 4h | 5 | without the sequence | 12598 | 43% | 41% | 45% | 1.8 | 1.5 | 50% | 48% | 52% | 2099 | 46% | 50% |


## Does the trader's sequence add anything at the same distances?

Pump rate of the sequence minus ordinary middle-band holds, within groups of the same timeframe, distance to the old high and distance to the failure level (quintiles); p by a bootstrap of calendar months.

| timeframe | closes above the middle | sequence minus without, same distances | noise | holdout, same distances |
|---|---|---|---|---|
| 1D | 1 | -8.0 pts | 0.005 | -0.3 pts |
| 1D | 2 | -2.8 pts | 0.190 | -2.9 pts |
| 1D | 3 | -0.7 pts | 0.970 | -2.1 pts |
| 1D | 5 | -4.3 pts | 0.300 | +8.2 pts |
| 4h | 1 | -4.3 pts | 0.005 | -2.4 pts |
| 4h | 2 | -3.9 pts | 0.030 | +0.2 pts |
| 4h | 3 | -2.0 pts | 0.340 | +0.9 pts |
| 4h | 5 | -0.2 pts | 0.930 | +5.1 pts |

Audit: pending.
