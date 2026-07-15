"""E1 — the amnesia ladder: from a goldfish turn to memory that survives a reboot.

One probe — "Rescue Ops, what's my callsign?" — asked after four kinds of break.
Each rung is one ADK decision, and you can watch exactly which facts survive:

  rung 1  SAME session            ✅ remembers      the session's events ARE short-term memory
  rung 2  NEW session, same svc   ❌/✅ split       plain state dies with the session;
                                                    `user:`-prefixed state crosses sessions
  rung 3  process restart         ❌ amnesia        InMemorySessionService lives in RAM
  rung 4  restart + SQLite        ✅ remembers      DatabaseSessionService — one line, and
                                                    `user:` state survives the reboot

The agent writes TWO facts when you introduce yourself, on purpose:
    state["last_topic"]      = ...   # no prefix  → this session only
    state["user:callsign"]   = ...   # user:      → this USER, every session

Run:  uv run python exercises/e1_amnesia_ladder.py
"""
import asyncio
from pathlib import Path

import _labkit

_labkit.setup()

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.tools import FunctionTool, ToolContext

MODEL = "gemini-2.5-flash"
APP = "amnesia-ladder"
USER = "operator"
DB_FILE = Path(__file__).parent / "_e1_sessions.db"

PROBE = "Rescue Ops, what's my callsign?"


def log_check_in(callsign: str, tool_context: ToolContext, topic: str = "") -> dict:
    """Log the operator's check-in the moment they give a callsign.

    Args:
        callsign: The operator's callsign, e.g. "Vega-7".
        topic: Optional — what they're currently working on, if they said.
    """
    if topic:
        tool_context.state["last_topic"] = topic        # no prefix → THIS session only
    tool_context.state["user:callsign"] = callsign      # user: → this user, EVERY session
    return {"status": "logged", "callsign": callsign, "topic": topic or "(none given)"}


def make_agent() -> Agent:
    return Agent(
        name="rescue_ops",
        model=MODEL,
        instruction=(
            "You are Rescue Ops, the mission AI. Warm, terse, practical — one short "
            "sentence per reply. When the operator introduces themselves with a callsign, "
            "call log_check_in immediately (topic is optional).\n"
            "Callsign on file: {user:callsign?} (blank = they have never checked in).\n"
            "Their current work topic: {last_topic?} (blank = you don't know it).\n"
            "Answer questions about callsign/topic strictly from those two fields — if a "
            "field is blank, say you don't have that on file."
        ),
        tools=[FunctionTool(log_check_in)],
    )


async def dump_state(service, session_id: str, label: str) -> None:
    s = await service.get_session(app_name=APP, user_id=USER, session_id=session_id)
    keep = {k: v for k, v in s.state.items() if k in ("last_topic", "user:callsign")}
    print(f"    🔎 state seen by {label}: {keep}")


async def main() -> None:
    # ─── rungs 1–3 · InMemorySessionService (the default everyone starts with) ──
    service = InMemorySessionService()
    runner = Runner(app_name=APP, agent=make_agent(), session_service=service)

    print("\n═══ rung 1 · same session — the thread remembers ═══")
    a = await service.create_session(app_name=APP, user_id=USER)
    await _labkit.turn(runner, USER, a.id, "Rescue Ops, this is callsign Vega-7, working on the oxygen recycler.")
    await _labkit.turn(runner, USER, a.id, PROBE)
    await dump_state(service, a.id, "session A")
    print("  ✅ the session's event log + state are the short-term memory — nothing special needed")

    print("\n═══ rung 2 · NEW session, same service — the prefix split ═══")
    b = await service.create_session(app_name=APP, user_id=USER)
    await dump_state(service, b.id, "session B (before a word is said)")
    await _labkit.turn(runner, USER, b.id, PROBE)
    await _labkit.turn(runner, USER, b.id, "And what was I working on last time?")
    print("  ✂️  plain `last_topic` died with session A · `user:callsign` crossed over —")
    print("      the PREFIX is the lifetime: (none)=session · user:=this user forever · app:=everyone")

    print("\n═══ rung 3 · process restart — InMemory means IN MEMORY ═══")
    service_after_reboot = InMemorySessionService()          # ← 'the ship rebooted'
    runner2 = Runner(app_name=APP, agent=make_agent(), session_service=service_after_reboot)
    c = await service_after_reboot.create_session(app_name=APP, user_id=USER)
    await _labkit.turn(runner2, USER, c.id, PROBE)
    print("  ❌ user: scope is real, but the STORE was a Python dict. The process died; so did it.")

    print("\n═══ rung 4 · one line later — memory that survives the reboot ═══")
    DB_FILE.unlink(missing_ok=True)
    db1 = DatabaseSessionService(db_url=f"sqlite+aiosqlite:///{DB_FILE}")   # ← THE line
    runner3 = Runner(app_name=APP, agent=make_agent(), session_service=db1)
    d = await db1.create_session(app_name=APP, user_id=USER)
    await _labkit.turn(runner3, USER, d.id, "Rescue Ops, callsign Vega-7 again — re-logging after the reboot.")

    db2 = DatabaseSessionService(db_url=f"sqlite+aiosqlite:///{DB_FILE}")   # ← 'restart' №2
    runner4 = Runner(app_name=APP, agent=make_agent(), session_service=db2)
    e = await db2.create_session(app_name=APP, user_id=USER)
    await _labkit.turn(runner4, USER, e.id, PROBE)
    await dump_state(db2, e.id, "a fresh service after 'restart'")
    print("  ✅ same agent, same code — only the SessionService changed. In production that")
    print("     line is DatabaseSessionService (your Postgres) or VertexAiSessionService (managed).")

    print("\nThe ladder so far:  turn → session → user-scope → survives restart.")
    print("What's still missing: none of this is SEARCHABLE knowledge — that's E2/E3,")
    print("and the managed version of everything above is ../chat.py on Agent Engine.\n")


if __name__ == "__main__":
    asyncio.run(main())
