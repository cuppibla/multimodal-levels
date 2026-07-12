"""Prove REAL cross-session memory — two separate sessions on a live Agent Engine.

    uv run python chat.py session-a     # tell the agent facts; session is saved to Memory Bank
    uv run python chat.py session-b     # a BRAND-NEW session — it already knows you
    uv run python chat.py chat "..."    # freeform one-shot (fresh session + recall)

The payoff (talk, closer): "You save the session… you open a brand-new one… and it
already knows you." No copying, no pasting the old chat.
"""
import asyncio
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from google.adk.memory import VertexAiMemoryBankService  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import VertexAiSessionService  # noqa: E402
from google.genai import types  # noqa: E402

from agent.agent import root_agent  # noqa: E402

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.environ["AGENT_ENGINE_ID"]  # from setup_engine.py
APP_NAME = AGENT_ENGINE_ID  # Vertex sessions live on the engine itself
USER_ID = os.getenv("DEMO_USER_ID", "vega-7")

# BOTH real services, keyed to ONE Agent Engine:
session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID)
memory_service = VertexAiMemoryBankService(project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID)
runner = Runner(agent=root_agent, app_name=APP_NAME,
                session_service=session_service, memory_service=memory_service)


async def turn(session_id: str, text: str) -> None:
    print(f"\n  YOU  → {text}")
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=text)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(p.text or "" for p in event.content.parts).strip()
            if reply:
                print(f"  OPS  → {reply}")


async def flush_to_memory(session_id: str) -> None:
    """The WRITE — hand the finished session to Memory Bank; Gemini curates it into facts."""
    session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
    print("\n  … generating memories from this session (Memory Bank · Gemini curation) …")
    await memory_service.add_session_to_memory(session)

    # generation is asynchronous server-side — poll until the curated facts are searchable
    t0 = time.time()
    while time.time() - t0 < 120:
        result = await memory_service.search_memory(
            app_name=APP_NAME, user_id=USER_ID, query="how should I brief this operator?")
        if result.memories:
            print(f"  ✓ {len(result.memories)} consolidated memories in the bank:")
            for m in result.memories:
                text = "".join(p.text or "" for p in (m.content.parts or [])) if m.content else ""
                print(f"      · {text}")
            return
        await asyncio.sleep(8)
        print(f"    …waiting for consolidation ({int(time.time() - t0)}s)")
    print("  (memories not yet visible — they usually land within a couple of minutes)")


async def session_a() -> None:
    s = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    print(f"  SESSION A · {s.id}  (a stranger so far)")
    await turn(s.id, "Rescue Ops, this is callsign Vega-7. My oxygen recycler keeps throwing error code 42.")
    await turn(s.id, "One more thing — long checklists overwhelm me. Walk me through things one step at a time.")
    await flush_to_memory(s.id)
    print("\n  → now run:  uv run python chat.py session-b\n")


async def session_b() -> None:
    s = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    print(f"  SESSION B · {s.id}  (brand-new session — no history copied)")
    await turn(s.id, "New day, fresh channel. What do you already know about me — and how are you going to brief me?")
    print("\n  ◉ exact facts came from user: state · the briefing style came from Memory Bank.\n")


async def one_shot(text: str) -> None:
    s = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    await turn(s.id, text)
    await flush_to_memory(s.id)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "session-a"
    if cmd == "session-a":
        asyncio.run(session_a())
    elif cmd == "session-b":
        asyncio.run(session_b())
    elif cmd == "chat" and len(sys.argv) > 2:
        asyncio.run(one_shot(" ".join(sys.argv[2:])))
    else:
        print(__doc__)
