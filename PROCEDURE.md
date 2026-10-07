# Procedure — from zero to a running simulation

## Files (all three go in one folder)
- `download_data.py` — pulls ETHUSDT + BTCUSDT, 5m + 1m, full history, funding. Already configured; no edits needed.
- `claude_code_brief_v2.md` — the full build specification. Pasted into Claude Code as the first message.
- `PROCEDURE.md` — this file.

## Phase 1 — Setup (about 15 minutes, once)
1. Install the Claude desktop app from claude.com/download (Mac or Windows). It includes Claude Code. A paid plan is required.
2. Windows only: install Git from git-scm.com. Macs already have it.
3. Install Python 3.11+ from python.org if not present (Windows: tick "Add to PATH" in the installer).
4. Create a folder called `trading-bot` on a drive with at least **50 GB free** — the trade-level data is large.
5. Put the three files in that folder.
6. Open the Claude app → sign in → **Code** tab → environment **Local** → **Select folder** → choose `trading-bot` → pick the strongest model in the dropdown.

## Phase 2 — Build and simulate (hours; leave it running)
7. Open `claude_code_brief_v2.md`, copy everything, paste it as the first message. Send.
8. Let it work. Data download alone is roughly 20–30 minutes; the full build and backtest take much longer. The machine must stay awake and online — disable sleep.
9. Check in from the Claude mobile app whenever you like. Useful things to send:
   - `Read PROGRESS.md and continue from where you left off.` (after any interruption or new session)
   - `What section are you on and what is left?`
   - `Show me the funnel counts so far.`
10. Do not intervene mid-build unless it asks a question. If it asks, answer it and let it continue.
11. It is finished when `results.md`, `alphas.md` and `README.md` exist in the folder.

## Phase 3 — Dissect (with me, here)
12. Open `results.md` and paste it into this chat (or the parts it asks for). Bring `alphas.md` too.
13. We go through: the three top findings, the funnel report, with-trend vs counter-trend, the weekend heatmap, the error ledger (how many "wrong at first" trades came back), which exit variant and sizing cell won, feature importance, and any overfitting flags.
14. We decide changes. I write them as a short follow-up message; you paste it into the same Claude Code session. Repeat until we are satisfied. Expect several rounds — that is the correction loop working.

## Phase 4 — Prove it live without money
15. Tell Claude Code: `Start shadow mode.` The bot runs on real prices with simulated fills and compares itself to the backtest every day.
16. Run it for at least three to four weeks. Bring the shadow report back here. If it matches the backtest, the simulation was honest. If it does not, we find out why before a dollar is at stake.

## Phase 5 — Live
17. Move the bot to a VPS in Tokyo or Singapore (Claude Code can set this up over SSH from the Code tab). Your laptop is not where it should live.
18. Create Binance API keys with **trading enabled, withdrawals disabled**, restricted to the VPS IP. Never paste keys into any chat.
19. Start small. Let the daily digest run. Drift detection and champion/challenger retraining run on their own.
20. Phase two: the 30-coin universe, using the method in section 14 of the brief — only after ETH has proven itself live.

## If something breaks
- Session lost or app closed: new session in the same folder → `Read PROGRESS.md and continue.`
- A download URL fails: tell Claude Code to check the parent directory on data.binance.vision and adapt.
- Out of disk: reduce the aggTrades window in section 1 of the brief from 24 months to 12.
- Anything unclear: bring the error text here.
