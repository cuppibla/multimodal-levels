"""E2 — four kinds of knowing: working · episodic · semantic · procedural.

The cognitive-science taxonomy (CoALA) made runnable. One rescue-ops
conversation, then four probes — each answerable ONLY by the right kind of
memory, each mapped to the ADK mechanism that holds it:

  WORKING     what's in your head right now      Session.events + state, rendered
                                                 into the context window each turn
  EPISODIC    "remember that time we…"           add_session_to_memory → search:
                                                 a specific past EXPERIENCE
  SEMANTIC    a fact, independent of when        the same store, but what's recalled
              you learned it                     is the distilled fact, not the scene
  PROCEDURAL  how to do the job                  static: instruction + tools
                                                 learned: an injected LESSON — E5

Honesty note: this lab keeps episodic + semantic in one InMemoryMemoryService —
locally they differ by WHAT you ask back, not where they live. Memory Bank
(../chat.py) actually consolidates: episodes in, curated facts out.

Run:  uv run python exercises/e2_four_kinds.py
"""
import asyncio

import _labkit

_labkit.setup()

from google.adk.agents import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import load_memory

MODEL = "gemini-2.5-flash"
APP = "four-kinds"
USER = "operator"

INSTRUCTION = (
    "You are Rescue Ops, the mission AI. Warm, terse, practical — one or two short "
    "sentences. If asked about past sessions or the operator's preferences and you "
    "don't see the answer in this conversation, call load_memory first.\n"
    "LEARNED PROCEDURE on file (may be blank): {user:lesson?}\n"
    "When a learned procedure applies to the current problem, follow it and say so."
)


async def main() -> None:
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    agent = Agent(name="rescue_ops", model=MODEL, instruction=INSTRUCTION, tools=[load_memory])
    runner = Runner(app_name=APP, agent=agent,
                    session_service=session_service, memory_service=memory_service)

    print("\n═══ the experience · session A ═══")
    a = await session_service.create_session(app_name=APP, user_id=USER)
    await _labkit.turn(runner, USER, a.id,
        "Rescue Ops, callsign Vega-7. The oxygen recycler threw error code 42 this morning — "
        "we traced it to a clogged intake filter and swapping the filter fixed it.")
    await _labkit.turn(runner, USER, a.id,
        "Also, for future reference: long checklists overwhelm me. Brief me one step at a time.")

    print("\n═══ probe 1 · WORKING memory — the context window itself ═══")
    await _labkit.turn(runner, USER, a.id, "Quick check — what error code did I mention a moment ago?")
    print("  → answered from Session.events — no store, no search. Working memory IS the")
    print("    conversation (+ state), re-rendered into the context window every turn.")

    # end of call — the session becomes searchable memory
    finished = await session_service.get_session(app_name=APP, user_id=USER, session_id=a.id)
    await memory_service.add_session_to_memory(finished)
    print("\n  💾 add_session_to_memory(A) — the experience is now on the long-term shelf")

    print("\n═══ probe 2 · EPISODIC memory — a specific past experience ═══")
    b = await session_service.create_session(app_name=APP, user_id=USER)
    await _labkit.turn(runner, USER, b.id,
        "New shift, new session. What happened with the oxygen recycler last time?")
    print("  → a NEW session recalled the EVENT — what happened, and how it got fixed.")
    print("    Episodic = memory of an experience, timestamped to a past session.")

    print("\n═══ probe 3 · SEMANTIC memory — a fact about the user ═══")
    await _labkit.turn(runner, USER, b.id, "And how do I like to be briefed?")
    print("  → not a scene this time — a distilled FACT ('one step at a time'), true")
    print("    regardless of when it was learned. That's semantic memory.")

    print("\n═══ probe 4 · PROCEDURAL memory — how to do the job ═══")
    print("  static half — you're looking at it: the agent's instruction + tools ARE its")
    print("  built-in procedures (it knew to call load_memory without being taught).")
    print("  learned half — inject a lesson the agent EARNED (E5 shows where these come from):")
    c = await session_service.create_session(app_name=APP, user_id=USER, state={
        "user:lesson": "For recycler faults, check the intake filter BEFORE touching the pump assembly."
    })
    await _labkit.turn(runner, USER, c.id,
        "Rescue Ops — the recycler is acting up again. What should I check first?")
    print("  → it didn't re-derive the diagnosis; it followed the learned route.")

    print("\nThe map:  working = events+state · episodic/semantic = memory service ·")
    print("procedural = instruction+tools (static) or learned lessons (E5, the dream).")
    print("ADK ships the first three first-class. The learned half of the fourth is the")
    print("frontier — hold that thought for e5_the_dream.py.\n")


if __name__ == "__main__":
    asyncio.run(main())
