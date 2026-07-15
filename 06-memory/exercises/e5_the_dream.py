"""E5 — the dream: the agent learns the JOB, not just the user.

Everything before this remembers the USER. The frontier is reflective memory —
the agent improving its own procedure from finished work. This is the
architecture from the blog ("Anthropic gave agents Dreams — build your own on
Google Cloud"), run locally end-to-end:

  act 1  EARN IT      a real ticket gets resolved the hard way; the harness
                      records a structured TRAJECTORY — actions + OUTCOME +
                      root cause. (The outcome is the whole game: without it,
                      reflection can only produce vague advice.)
  act 2  THE DREAM    an offline pass reads the unprocessed trajectory, asks
                      Gemini to derive ONE scoped, reusable lesson, embeds it
                      (gemini-embedding-001), stores it, marks the source
                      processed. In production: a Cloud Run Job on a schedule.
  act 3  WAKE UP      a NEW ticket, different words, same shape. Recall by
                      embedding similarity, inject the lesson — and A/B the
                      agent's behavior with vs without it.

Local stand-in: `_dream_store.json` plays Firestore (one store for structured
trajectories AND lesson vectors). Swap file-writes for Firestore writes + its
native vector search and this IS the production architecture — see the blog
series (medium.com/google-cloud → "How to Build an AI Agent That Reflects").

Run:  uv run python exercises/e5_the_dream.py
"""
import asyncio
import json
import math
from pathlib import Path

import _labkit

_labkit.setup()

from google import genai
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

MODEL = "gemini-2.5-flash"
EMBED_MODEL = "gemini-embedding-001"
APP = "dream-lab"
USER = "operator"
STORE = Path(__file__).parent / "_dream_store.json"

TICKET_1 = "Maintenance ticket: the airlock control panel won't respond to any input."
TICKET_2 = "Maintenance ticket: the cargo-bay door controls are frozen and won't take commands."


# ─── the maintenance tools (scripted world: the root cause is always the coupling) ──

def reboot_interface(target: str) -> dict:
    """Soft-reboot a control interface — the ship manual's STANDARD first-line fix.

    Args:
        target: The panel or control surface to reboot, e.g. "airlock panel".
    """
    return {"action": "interface rebooted", "panel_status": "still unresponsive"}


def check_power_coupling(target: str) -> dict:
    """Inspect and reseat the power coupling feeding a control surface.

    Args:
        target: The panel or control surface to inspect, e.g. "airlock panel".
    """
    return {"action": "coupling fault found and reseated",
            "panel_status": "RESPONSIVE — issue resolved", "root_cause": "power coupling fault"}


def make_agent(lesson: str = "") -> Agent:
    return Agent(
        name="maintenance", model=MODEL,
        instruction=(
            "You are the ship's maintenance agent. Resolve the ticket by calling tools, "
            "one at a time, until a tool reports the issue resolved; then state the fix in "
            "one sentence. Follow the ship manual's standard procedure — first-line fix "
            "first — unless a LEARNED LESSON below says otherwise.\n"
            f"LEARNED LESSON on file: {lesson or '(none)'}"
        ),
        tools=[reboot_interface, check_power_coupling],
    )


async def run_ticket(ticket: str, lesson: str = "") -> dict:
    """Run one ticket; return the trajectory the harness observed."""
    service = InMemorySessionService()
    runner = Runner(app_name=APP, agent=make_agent(lesson), session_service=service)
    s = await service.create_session(app_name=APP, user_id=USER)
    await _labkit.turn(runner, USER, s.id, ticket)
    session = await service.get_session(app_name=APP, user_id=USER, session_id=s.id)
    actions, root_cause = [], None
    for ev in session.events:
        for fc in ev.get_function_calls():
            actions.append(fc.name)
        for fr in ev.get_function_responses():
            if isinstance(fr.response, dict) and fr.response.get("root_cause"):
                root_cause = fr.response["root_cause"]
    return {"task": ticket, "actions": actions, "outcome": "resolved",
            "root_cause": root_cause, "processed": False}


def embed(client: genai.Client, text: str) -> list[float]:
    res = client.models.embed_content(model=EMBED_MODEL, contents=text)
    return list(res.embeddings[0].values)


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


async def main() -> None:
    client = genai.Client()

    print("\n═══ act 1 · earn it — ticket #1, resolved the hard way ═══")
    print(f"  🎫 {TICKET_1}")
    trajectory = await run_ticket(TICKET_1)
    print(f"\n  the harness recorded a TRAJECTORY (not a transcript):")
    print(f"    actions:    {trajectory['actions']}")
    print(f"    outcome:    {trajectory['outcome']} · root_cause: {trajectory['root_cause']}")
    STORE.write_text(json.dumps({"trajectories": [trajectory], "lessons": []}, indent=2))
    print(f"  💾 → {STORE.name} (processed: false — the dream job's work queue)")

    print("\n═══ act 2 · the dream — offline reflection (Cloud Run Job, played by us) ═══")
    store = json.loads(STORE.read_text())
    todo = [t for t in store["trajectories"] if not t["processed"]]
    print(f"  ⏰ scheduled wake-up: {len(todo)} unprocessed trajectory")
    prompt = (
        "You are the reflection pass of a maintenance-agent system. From this completed "
        "trajectory, derive ONE reusable lesson (max 25 words) a future agent should apply "
        "to similar tickets. State the procedure, not the story.\n\n"
        f"{json.dumps(todo[0], indent=2)}"
    )
    lesson = client.models.generate_content(model=MODEL, contents=prompt).text.strip()
    print(f"  🌙 Gemini reflects → lesson:\n     {lesson!r}")
    vec = embed(client, lesson)
    store["lessons"].append({"lesson": lesson, "scope": "agent:maintenance",
                             "source": "trajectory-0", "embedding": vec})
    todo[0]["processed"] = True
    STORE.write_text(json.dumps(store, indent=2))
    print(f"  💾 embedded ({len(vec)} dims, {EMBED_MODEL}) + stored with scope + source · trajectory marked processed")

    print("\n═══ act 3 · wake up — a new ticket, different words, same shape ═══")
    print(f"  🎫 {TICKET_2}")
    qvec = embed(client, TICKET_2)
    best = max(store["lessons"], key=lambda L: cosine(qvec, L["embedding"]))
    score = cosine(qvec, best["embedding"])
    print(f"  🔎 recall by similarity → top lesson (cosine {score:.2f}): {best['lesson']!r}")

    print("\n  A · WITHOUT the lesson:")
    a = await run_ticket(TICKET_2)
    print("\n  B · WITH the lesson injected:")
    b = await run_ticket(TICKET_2, lesson=best["lesson"])

    print("\n═══ the receipt ═══")
    print(f"  {'':14}{'first move':32}{'tool calls'}")
    print(f"  {'A no lesson':14}{a['actions'][0] if a['actions'] else '—':32}{len(a['actions'])}")
    print(f"  {'B with lesson':14}{b['actions'][0] if b['actions'] else '—':32}{len(b['actions'])}")
    print("\n  Same model. Same tools. It didn't learn the ANSWER — it learned the ROUTE.")
    print("  The production version of this file: trajectories + lessons in Firestore")
    print("  (native vector search), the dream as a Cloud Run Job on Cloud Scheduler,")
    print("  and a recall tool that merges USER facts (Memory Bank) + JOB lessons under scope.\n")


if __name__ == "__main__":
    asyncio.run(main())
