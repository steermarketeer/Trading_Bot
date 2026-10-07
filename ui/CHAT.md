# Desk chat

Natural-language assistant at the top of SHADOW DESK.

## Behavior
- **Rules-first**: understands status / why / positions / health / regime / agreement / run shadow
- **Grounded**: answers from `latest.json`, decision gates, run history, scheduler, signals
- **Paper only**: never places exchange orders
- **Run shadow**: asks you to reply `confirm run` before executing

## Optional LLM polish
If `OPENAI_API_KEY` is set, replies may be rewritten for tone. Facts still come from tools.

```powershell
$env:OPENAI_API_KEY = "sk-..."
# optional:
$env:SHADOW_DESK_LLM_MODEL = "gpt-4o-mini"
$env:SHADOW_DESK_LLM = "0"   # disable polish even if key is set
```

## Files
- `ui/desk_chat.py` — intent + grounded replies
- `ui/app.py` — `st.chat_message` / `st.chat_input` UI
