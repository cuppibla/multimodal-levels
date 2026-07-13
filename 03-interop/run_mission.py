"""ENTRYPOINT — the dispatcher discovers the remote Architect and delegates a repair task across A2A.
Start the Architect first:  uv run python -m architect.main"""
from __future__ import annotations
import asyncio

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from agent.agent import root_agent  # noqa: E402

TASK = "How do I reseat the nav-array coupling after a debris strike?"


async def main() -> None:
    sessions = InMemorySessionService()
    await sessions.create_session(app_name="interop", user_id="operator", session_id="i1")
    runner = Runner(app_name="interop", agent=root_agent, session_service=sessions)
    msg = types.Content(role="user", parts=[types.Part(text=TASK)])
    print(f"🛰  dispatching: {TASK}\n")
    async for event in runner.run_async(user_id="operator", session_id="i1", new_message=msg):
        if event.content and event.content.parts:
            for p in event.content.parts:
                if p.text:
                    print(f"[{event.author}] {p.text}")


if __name__ == "__main__":
    asyncio.run(main())
