# Triple HTF Shadow Logger (paper only)

Runs **three** walk-forward PASS strategies. **No Binance orders.**

| ID | Strategy | Folder |
|---|---|---|
| S1 | `both_align_no_stop` | `shadow/s1_both_align_no_stop/` |
| S2 | `both_cool7_stable7` | `shadow/s2_both_cool7_stable7/` |
| S3 | `both_btc_confirm` | `shadow/s3_both_btc_confirm/` |

S3 requires BTC daily trend to agree with the ETH side before entry.

## Run (same command as before)

```powershell
cd "D:\Trading Bot"
.\.venv\Scripts\Activate.ps1
python shadow_htf_v4.py
```

Bootstrap **only strategy 3** the first time (keeps S1/S2 history):

```powershell
python shadow_htf_v4.py --bootstrap-s3-only --bootstrap-days 90
```

Bootstrap only strategy 2 (legacy):

```powershell
python shadow_htf_v4.py --bootstrap-s2-only --bootstrap-days 90
```

Bootstrap all from scratch:

```powershell
python shadow_htf_v4.py --bootstrap-days 90 --force-bootstrap
```

## What to open (non-technical)

| File | Meaning |
|---|---|
| `shadow/latest.json` | All three strategies + **agreement** |
| `shadow/run_history.jsonl` | Append-only log of each shadow run (ok/fail + results) |
| `shadow/latest_s1.json` | S1 only |
| `shadow/latest_s2.json` | S2 only |
| `shadow/latest_s3.json` | S3 only |
| `shadow/s1_.../trades.csv` | S1 closed paper trades |
| `shadow/s2_.../trades.csv` | S2 closed paper trades |
| `shadow/s3_.../trades.csv` | S3 closed paper trades |

**agreement** in `latest.json`:
- `all_flat` — none in a trade
- `all_agree_long` / `all_agree_short` — all three same side
- `active_agree_*` — active positions agree (some flat)
- `one_active` — only one has a position
- `disagree` — mixed sides

In the UI, open the **Run history** tab for invocation logs + daily S1/S2/S3 results.
Desk chat (top of SHADOW DESK): ask in plain language (status / why / positions / health / run shadow). Rules-first; optional LLM polish via `OPENAI_API_KEY`.

## UI (SHADOW DESK)

```powershell
cd "D:\Trading Bot"
.\.venv\Scripts\Activate.ps1
pip install streamlit   # once
streamlit run ui/app.py
```

See `ui/README.md`. Paper monitor only — no live orders.

## Stop

Close the window or press Ctrl+C. Or simply don’t run it. Disable Task Scheduler if you set one up.
