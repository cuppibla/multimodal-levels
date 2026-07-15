"""E3 — "you don't want close-ish": each store is WRONG for the other's job.

The question every team asks: *SQL or vectors?* This lab answers it adversarially,
in both directions, with the same rescue-ops facts:

  direction 1  FACTS ROT IN A SEMANTIC STORE
               "supplies: 3 days" … later … "supplies: 1 day".
               A similarity store can't overwrite — search returns BOTH versions,
               and the model has to GUESS which is current.
               `user:` state updates in place — exactly one value, always current.

  direction 2  UNDERSTANDING NEVER SURFACES FROM AN EXACT LOOKUP
               "will she stay calm under pressure?" matches NO key in a key/value
               profile — but semantic search finds "she freezes under pressure"
               from a conversation that never used the word "calm".

Honesty note: InMemoryMemoryService matches keywords; a real vector store matches
meaning. The failure SHAPE is identical — no overwrite, recall-by-similarity —
keyword matching is just the lab's free stand-in.

The rule this earns:   exact value you'll query or UPDATE  → structured (state/SQL)
                       fuzzy thing you recall by MEANING   → semantic (Memory Bank)

Run:  uv run python exercises/e3_not_a_vector_store.py
"""
import asyncio

import _labkit

_labkit.setup()

from google.adk.agents import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import load_memory
from google.genai import types

MODEL = "gemini-2.5-flash"
APP = "store-shapes"
USER = "operator"


async def remember_session(session_service, memory_service, session_id: str, *lines: str) -> None:
    """Scripted mini-session → straight onto the memory shelf (no model needed)."""
    s = await session_service.create_session(app_name=APP, user_id=USER, session_id=session_id)
    from google.adk.events import Event
    for line in lines:
        await session_service.append_event(s, Event(
            author="user", invocation_id=f"log-{session_id}",
            content=types.Content(role="user", parts=[types.Part(text=line)]),
        ))
    await memory_service.add_session_to_memory(
        await session_service.get_session(app_name=APP, user_id=USER, session_id=session_id))


async def main() -> None:
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    # the same life, recorded twice — once as episodes, once as a profile
    print("\n═══ setup · two days of mission logs, into BOTH kinds of store ═══")
    await remember_session(session_service, memory_service, "day-1",
        "Mission log day 1: supplies remaining 3 days. Vega-7 says pressure situations "
        "make her freeze — she panics under pressure and wants one step at a time.")
    await remember_session(session_service, memory_service, "day-2",
        "Mission log day 2: supplies remaining 1 day after the storage leak.")
    profile = {"user:supplies_days": "1", "user:callsign": "Vega-7"}   # updated IN PLACE
    print("  semantic shelf ← day-1 log, day-2 log (append-only, recalled by similarity)")
    print(f"  exact profile ← {profile}  (day-2 OVERWROTE supplies_days: 3 → 1)")

    print("\n═══ direction 1 · ask both stores: how many days of supplies? ═══")
    hits = await memory_service.search_memory(app_name=APP, user_id=USER,
                                              query="how many days of supplies remain?")
    print("  semantic store returns:")
    for m in hits.memories:
        text = "".join(p.text or "" for p in (m.content.parts or [])) if m.content else ""
        print(f"    · {text[:90]}")
    print("  → BOTH versions came back. There is no 'update' in a similarity store —")
    print("    only more entries. Whatever the model picks now is a guess, not a lookup.")
    print(f"\n  exact profile returns:  supplies_days = {profile['user:supplies_days']!r}")
    print("  → one value, current, atomically overwritten. Facts want exactly this.")

    agent = Agent(name="quartermaster", model=MODEL, tools=[load_memory],
                  instruction="You are the ship quartermaster. If asked about mission facts, "
                              "call load_memory and answer in one short sentence.")
    runner = Runner(app_name=APP, agent=agent,
                    session_service=session_service, memory_service=memory_service)
    q = await session_service.create_session(app_name=APP, user_id=USER)
    print("\n  the model, given only the semantic store:")
    await _labkit.turn(runner, USER, q.id, "Exactly how many days of supplies remain? One number.")
    print("  → read its answer against the two logs above: it had to arbitrate between")
    print("    'facts'. A balance, a date, an inventory count must never work this way.")

    print("\n═══ direction 2 · ask both stores: will she stay calm under pressure? ═══")
    question_keys = [k for k in profile if "calm" in k or "pressure" in k]
    print(f"  exact profile lookup for a matching key … {question_keys or 'NO KEY MATCHES'}")
    print("  → a key/value profile answers only questions you predicted. This wasn't one.")
    hits2 = await memory_service.search_memory(app_name=APP, user_id=USER,
                                               query="will she stay calm under pressure?")
    print("  semantic store returns:")
    for m in hits2.memories:
        text = "".join(p.text or "" for p in (m.content.parts or [])) if m.content else ""
        if "pressure" in text or "panic" in text:
            print(f"    · {text[:90]}")
    print("  → recalled by MEANING from a log that never contained the word 'calm'.")
    print("    Understanding wants similarity; you can't schema your way to it.")

    print("\nThe verdict — route by shape, run BOTH:")
    print("  exact & updatable   → user:/app: state · your SQL      (supplies, balances, dates)")
    print("  fuzzy & accumulated → memory service / Memory Bank     (traits, preferences, style)")
    print("  and raw perception  → neither: extract meaning, store the file as an Artifact.\n")


if __name__ == "__main__":
    asyncio.run(main())
