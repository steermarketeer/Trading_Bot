"""
Rules-first desk chat for SHADOW DESK.

Answers are grounded in shadow / strategy / ops data.
Optional LLM polish if OPENAI_API_KEY (or SHADOW_DESK_LLM=1 + key) is set —
the model only rewrites text; facts still come from tools.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
SHADOW = ROOT / "shadow"


def _norm(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"[^\w\s/+\-]", " ", t)
    return " ".join(t.split())


def extract_strategy(text: str) -> str | None:
    t = _norm(text)
    if re.search(r"\b(s1|strategy\s*1|both_align)\b", t):
        return "s1"
    if re.search(r"\b(s2|strategy\s*2|cool7|stable7)\b", t):
        return "s2"
    if re.search(r"\b(s3|strategy\s*3|btc_confirm|btc confirm)\b", t):
        return "s3"
    return None


def detect_intent(message: str, pending: str | None = None) -> tuple[str, dict]:
    """
    Return (intent, slots).
    Intents: help, status, why, positions, health, run_shadow, confirm_run,
             cancel, agreement, regime, greet, unknown
    """
    t = _norm(message)
    if not t:
        return "unknown", {}

    # Confirmation flow for paper shadow run
    if pending == "confirm_run":
        if t in ("yes", "y", "confirm", "confirm run", "ok", "do it", "run it", "go"):
            return "confirm_run", {}
        if t in ("no", "n", "cancel", "stop", "nevermind", "never mind"):
            return "cancel", {}
        # fall through — maybe user asked something else

    if t in ("hi", "hello", "hey", "yo"):
        return "greet", {}

    if any(k in t for k in ("help", "what can you", "commands", "how do i")):
        return "help", {}

    if any(k in t for k in ("run shadow", "run the shadow", "execute shadow", "refresh shadow", "update shadow")):
        return "run_shadow", {}
    if t in ("run", "shadow") and "order" not in t:
        return "run_shadow", {}

    if any(k in t for k in ("health", "scheduler", "task scheduler", "ops", "order book age", "stale", "klines")):
        return "health", {}

    if any(k in t for k in ("position", "open trade", "are we in", "in a trade", "holding", "unrealized")):
        return "positions", {}

    if any(k in t for k in ("agreement", "agree", "disagree", "all flat", "alignment")):
        return "agreement", {}

    if any(k in t for k in ("regime", "bull", "bear", "neutral")) and any(
        k in t for k in ("what", "current", "now", "status", "is", "are", "show", "how")
    ):
        return "regime", {}
    if t in ("regime", "bull or bear", "market regime"):
        return "regime", {}

    if any(k in t for k in ("why", "blocked", "block", "gate", "reason", "explain", "how come", "not entering", "no entry", "flat")):
        return "why", {"strategy": extract_strategy(t)}

    if any(k in t for k in ("status", "how are we", "summary", "overview", "what's going", "whats going", "state of")):
        return "status", {}
    if t in ("s", "stat"):
        return "status", {}

    # strategy name alone → why that strategy
    sid = extract_strategy(t)
    if sid and len(t.split()) <= 3:
        return "why", {"strategy": sid}

    return "unknown", {}


def _load_latest() -> dict | None:
    path = SHADOW / "latest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_side(side: Any) -> str:
    if side is None or side == "" or str(side).lower() in ("nan", "none"):
        return "flat"
    return str(side)


def reply_help() -> str:
    return (
        "I'm the SHADOW DESK assistant (paper-only). Ask in plain language, for example:\n"
        "- What's our status?\n"
        "- Why is S2 flat?\n"
        "- Any open positions?\n"
        "- Is the scheduler healthy?\n"
        "- What's the regime?\n"
        "- Run shadow\n\n"
        "I only use your shadow / strategy data. I never place exchange orders.\n"
        "Optional LLM polish: set OPENAI_API_KEY (facts still come from tools)."
    )


def reply_greet() -> str:
    return (
        "Hey - I'm your paper trading desk chat. "
        "Ask about status, why a strategy is flat/in a trade, positions, health, or say **run shadow**."
    )


def reply_status(latest: dict | None) -> str:
    if not latest:
        return "No `shadow/latest.json` yet. Say **run shadow** (then confirm) to create the first digest."
    agree = latest.get("agreement", {})
    lines = [
        f"**Paper status** (run `{latest.get('run_at_utc')}`)",
        f"- Agreement: **{agree.get('label')}** · ETH close: **{latest.get('latest_close')}**",
        f"- Mode: `{latest.get('mode')}` · places_orders={latest.get('places_orders')}",
        "",
        "Strategies:",
    ]
    for s in latest.get("strategies", []):
        lines.append(
            f"- **{(s.get('id') or '').upper()}** `{s.get('strategy')}`: "
            f"side={_fmt_side(s.get('side'))}, equity={float(s.get('equity') or 0):.4f}, "
            f"trades={s.get('n_trades_closed')}, last_day={s.get('last_processed_day')}, "
            f"regime={s.get('regime')}, status={s.get('status')}"
        )
    return "\n".join(lines)


def reply_why(latest: dict | None, strategy: str | None, get_decisions: Callable) -> str:
    if not latest:
        return "No shadow digest yet — run shadow first."
    try:
        decisions = get_decisions(latest)
    except Exception as e:
        return f"Couldn't compute decision gates: {e}"
    if strategy:
        decisions = [d for d in decisions if d.get("id") == strategy]
        if not decisions:
            return f"I don't have strategy `{strategy}`. Try s1, s2, or s3."
    if not decisions:
        return "No decision diagnostics available."

    parts = []
    for d in decisions:
        sid = (d.get("id") or "").upper()
        parts.append(f"**{sid} · {d.get('strategy')}** — `{d.get('verdict')}`")
        parts.append(f"{d.get('reason')}")
        parts.append(
            f"Side={_fmt_side(d.get('side'))} · regime={d.get('regime')} · "
            f"stable={d.get('stable')}/{d.get('need_stable')}"
        )
        fails = [g for g in d.get("gates", []) if not g.get("ok")]
        if fails:
            parts.append("Blocked / failing gates:")
            for g in fails:
                parts.append(f"- [x] **{g['gate']}**: {g['detail']}")
        else:
            parts.append("All monitored gates pass.")
        parts.append("")
    return "\n".join(parts).strip()


def reply_positions(latest: dict | None, get_decisions: Callable) -> str:
    if not latest:
        return "No shadow digest yet."
    try:
        decisions = get_decisions(latest)
    except Exception as e:
        return f"Couldn't load positions: {e}"
    open_ones = [d for d in decisions if d.get("side")]
    if not open_ones:
        return "No open paper positions — all strategies are flat."
    lines = ["**Open paper positions:**"]
    for d in open_ones:
        u = d.get("unrealized")
        up = "—" if u is None else f"{float(u)*100:.2f}%"
        lines.append(
            f"- **{(d.get('id') or '').upper()}** {_fmt_side(d.get('side'))} "
            f"from {d.get('entry_time')} @ {d.get('entry_price')} · "
            f"last={d.get('close')} · unrealized={up} · held={d.get('days_held')}d · "
            f"{d.get('reason') if d.get('verdict')=='EXIT_PRESSURE' else 'holding'}"
        )
    return "\n".join(lines)


def reply_health(latest: dict | None, get_health: Callable) -> str:
    h = get_health(latest)
    sched = h.get("scheduler") or {}
    shadow_ok = h.get("shadow_last_ok")
    shadow_s = "OK" if shadow_ok is True else ("FAIL" if shadow_ok is False else "unknown")
    if sched.get("available"):
        sched_s = f"{'OK' if sched.get('ok') else 'FAIL'} ({sched.get('last_result')})"
        sched_extra = f"last={sched.get('last_run')} next={sched.get('next_run')}"
    else:
        sched_s = "N/A"
        sched_extra = sched.get("error") or ""
    return (
        "**Ops health**\n"
        f"- Shadow last run: `{h.get('shadow_last_run')}` · log={shadow_s}\n"
        f"- Last processed day: `{h.get('last_processed')}`\n"
        f"- Task Scheduler: {sched_s} · {sched_extra}\n"
        f"- Order book age: **{h.get('orderbook_age')}**\n"
        f"- Klines age: **{h.get('klines_age')}**\n"
        "\nPaper only — this does not trade live."
    )


def reply_agreement(get_timeline: Callable) -> str:
    try:
        tl = get_timeline(14)
    except Exception as e:
        return f"Couldn't load agreement history: {e}"
    if tl is None or getattr(tl, "empty", True):
        return "No agreement history yet."
    recent = tl.head(10)
    lines = ["**Recent agreement (newest first):**"]
    for _, row in recent.iterrows():
        lines.append(
            f"- {row.get('day')}: **{row.get('agreement')}** · regime={row.get('regime')} · close={row.get('close')}"
        )
    return "\n".join(lines)


def reply_regime(latest: dict | None, get_strip: Callable) -> str:
    regimes = []
    if latest:
        for s in latest.get("strategies", []):
            regimes.append(f"{(s.get('id') or '').upper()}={s.get('regime')}")
    try:
        strip = get_strip(7)
        recent = ""
        if strip is not None and not getattr(strip, "empty", True):
            bits = [f"{r.day}:{r.regime}" for r in strip.head(5).itertuples()]
            recent = " Recent days: " + ", ".join(bits)
    except Exception:
        recent = ""
    if not regimes:
        return "No regime info yet." + recent
    return "**Regime (from last shadow):** " + ", ".join(regimes) + "." + recent


def reply_unknown() -> str:
    return (
        "I wasn't sure what you meant. Try asking about **status**, **why S2 is flat**, "
        "**positions**, **health**, **regime**, or **run shadow**. Type **help** for more."
    )


def optional_llm_polish(user_msg: str, draft: str) -> str:
    """Rewrite draft for tone only. Requires OPENAI_API_KEY. On any failure, return draft."""
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("SHADOW_DESK_OPENAI_KEY")
    if not key:
        return draft
    if os.environ.get("SHADOW_DESK_LLM", "1") in ("0", "false", "False"):
        return draft
    try:
        import urllib.request

        body = {
            "model": os.environ.get("SHADOW_DESK_LLM_MODEL", "gpt-4o-mini"),
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You polish assistant replies for a paper crypto trading desk. "
                        "Do NOT invent numbers, trades, or facts. Keep every fact from the draft. "
                        "Keep paper-only / no live orders warnings. Be concise."
                    ),
                },
                {
                    "role": "user",
                    "content": f"User asked:\n{user_msg}\n\nDraft facts (keep all):\n{draft}",
                },
            ],
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
        return text or draft
    except Exception:
        return draft


def handle_message(
    message: str,
    *,
    pending: str | None,
    latest: dict | None,
    get_decisions: Callable,
    get_health: Callable,
    get_timeline: Callable,
    get_strip: Callable,
    run_shadow_fn: Callable[[], tuple[int, str]] | None = None,
) -> tuple[str, str | None, dict]:
    """
    Returns (reply_text, new_pending, meta).
    meta may include run_output for UI code block.
    """
    intent, slots = detect_intent(message, pending=pending)
    meta: dict = {"intent": intent, "slots": slots}

    if intent == "confirm_run":
        if run_shadow_fn is None:
            return "Run function not wired.", None, meta
        code, out = run_shadow_fn()
        meta["run_code"] = code
        meta["run_output"] = out[-6000:] if out else ""
        if code == 0:
            return (
                "Paper shadow finished successfully. Refresh the desk (R) to see updated status. "
                "No exchange orders were placed.",
                None,
                meta,
            )
        return f"Shadow failed with code {code}. See log below.", None, meta

    if intent == "cancel":
        return "Okay — cancelled the paper shadow run.", None, meta

    if intent == "run_shadow":
        return (
            "I can run **paper** shadow (`shadow_htf_v4.py`) — it does **not** place Binance orders.\n"
            "Reply **confirm run** to execute, or **cancel**.",
            "confirm_run",
            meta,
        )

    if intent == "help":
        draft = reply_help()
    elif intent == "greet":
        draft = reply_greet()
    elif intent == "status":
        draft = reply_status(latest)
    elif intent == "why":
        draft = reply_why(latest, slots.get("strategy"), get_decisions)
    elif intent == "positions":
        draft = reply_positions(latest, get_decisions)
    elif intent == "health":
        draft = reply_health(latest, get_health)
    elif intent == "agreement":
        draft = reply_agreement(get_timeline)
    elif intent == "regime":
        draft = reply_regime(latest, get_strip)
    else:
        draft = reply_unknown()

    polished = optional_llm_polish(message, draft)
    return polished, pending if intent == "unknown" and pending else None, meta
