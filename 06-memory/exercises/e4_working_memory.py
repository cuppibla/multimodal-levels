"""E4 — working memory: managing the context window itself (take-home rung).

Everything in E1–E3 was about REMEMBERING more. This one is about the opposite
problem: a long conversation eventually poisons its own context window — slow,
expensive, and full of stale turns. Three ADK levers, two of them runnable here:

  COMPACTION   EventsCompactionConfig — every N invocations, an LLM summarizes
               the oldest span into ONE compaction event; the raw turns stop
               being sent to the model. The session log keeps everything;
               the WORKING memory gets a summary.

  REWIND       Runner.rewind_async — surgically undo the last invocation(s):
               events after the rewind point stop being part of the context,
               state deltas are rolled back. An "unsend" for agents.

  CACHE        ContextCacheConfig — named honestly: NOT memory. It reuses the
               repeated leading tokens (system prompt, big catalog) so keeping
               them in context is AFFORDABLE. Three of the four rungs remember;
               cache is how you afford to. (App-level config; nothing to watch
               in a lab this small.)

Run:  uv run python exercises/e4_working_memory.py
"""
import asyncio

import _labkit

_labkit.setup()

from google.adk.agents import Agent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

MODEL = "gemini-2.5-flash"
USER = "operator"

CHATTER = [
    "Log: hull integrity 97 percent, no change.",
    "Log: solar array realigned, output up 4 percent.",
    "Log: the water reclaimer filter was swapped at 0600.",
    "Log: crew morale is decent; Vega-7 requested more tea rations.",
    "Log: navigation fix acquired — we drifted 2 klicks overnight.",
    "Quick check — summarize the last shift in one sentence.",
]


async def part1_compaction() -> None:
    print("\n═══ part 1 · compaction — the long chat, folded ═══")
    agent = Agent(name="ops_log", model=MODEL,
                  instruction="You are Rescue Ops keeping the shift log. Acknowledge each "
                              "log entry in a few words. Answer questions briefly.")
    app = App(name="compaction-lab", root_agent=agent,
              events_compaction_config=EventsCompactionConfig(
                  compaction_interval=3,   # fold after every 3 invocations…
                  overlap_size=1,          # …keeping 1 invocation of overlap for continuity
              ))
    service = InMemorySessionService()
    runner = Runner(app=app, session_service=service)
    s = await service.create_session(app_name="compaction-lab", user_id=USER)
    for line in CHATTER:
        await _labkit.turn(runner, USER, s.id, line, quiet=True)
    print(f"  ({len(CHATTER)} turns of shift chatter just happened, quietly)")

    session = await service.get_session(app_name="compaction-lab", user_id=USER, session_id=s.id)
    compactions = [e for e in session.events if e.actions and e.actions.compaction]
    print(f"  events in the log: {len(session.events)} · compaction events: {len(compactions)}")
    for ce in compactions:
        summary = ""
        comp = ce.actions.compaction
        if comp.compacted_content and comp.compacted_content.parts:
            summary = "".join(p.text or "" for p in comp.compacted_content.parts)
        print(f"    🗜  one summary now stands in for the folded span:")
        print(f"       {summary.strip()[:200]!r}")
    print("  → the session KEPT every raw event (audit trail); the model's working")
    print("    memory gets the summary instead. Long chats stop eating the window.")


async def part2_rewind() -> None:
    print("\n═══ part 2 · rewind — the unsend button ═══")
    agent = Agent(name="nav", model=MODEL,
                  instruction="You are the ship navigator. Confirm course settings in one "
                              "short sentence. Answer questions from the conversation.")
    service = InMemorySessionService()
    runner = Runner(app_name="rewind-lab", agent=agent, session_service=service)
    s = await service.create_session(app_name="rewind-lab", user_id=USER)

    await _labkit.turn(runner, USER, s.id, "Set course for waypoint Alpha.")
    await _labkit.turn(runner, USER, s.id, "Scrap that — set course straight through the debris field.")

    session = await service.get_session(app_name="rewind-lab", user_id=USER, session_id=s.id)
    bad_invocation = session.events[-1].invocation_id
    print(f"  ⏪ rewind_async(rewind_before_invocation_id={bad_invocation!r})  — undo the debris-field turn")
    await runner.rewind_async(user_id=USER, session_id=s.id,
                              rewind_before_invocation_id=bad_invocation)

    await _labkit.turn(runner, USER, s.id, "Confirm: where are we currently headed?")
    print("  → the bad turn is gone from the model's world — not edited, UNHAPPENED.")
    print("    (state deltas from the rewound turns are rolled back too.)")


def part3_cache_note() -> None:
    print("\n═══ part 3 · cache — the rung that is NOT memory ═══")
    print("  ContextCacheConfig (App-level) reuses the repeated LEADING tokens — system")
    print("  prompt, a big policy/catalog block — across turns (default ttl 30 min).")
    print("  It answers a different question than every other rung in this level:")
    print("     memory: 'what do I remember, and for how long?'")
    print("     cache:  'what can I AFFORD to keep in mind without re-paying every turn?'")
    print("  Nothing to observe at lab scale — but in a live voice loop (Level 5) it's")
    print("  what makes keeping the whole persona + catalog resident affordable.")


async def main() -> None:
    await part1_compaction()
    await part2_rewind()
    part3_cache_note()
    print("\nWorking memory, managed: fold the old (compaction) · unhappen the bad (rewind)")
    print("· afford the big (cache). The window is a budget, not a landfill.\n")


if __name__ == "__main__":
    asyncio.run(main())
