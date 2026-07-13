"""ENTRYPOINT — the operator dispatches a formation over the resilient bus. Run setup_bus.py first."""
from __future__ import annotations
import asyncio

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from agent.agent import root_agent  # noqa: E402

DIRECTIVE = "Encircle the ridge to sweep every approach at once."


async def main() -> None:
    sessions = InMemorySessionService()
    await sessions.create_session(app_name="operate", user_id="operator", session_id="o1")
    runner = Runner(app_name="operate", agent=root_agent, session_service=sessions)
    msg = types.Content(role="user", parts=[types.Part(text=DIRECTIVE)])
    print(f"🛰  directive: {DIRECTIVE}\n")
    async for event in runner.run_async(user_id="operator", session_id="o1", new_message=msg):
        if event.content and event.content.parts:
            for p in event.content.parts:
                if p.text:
                    print(f"[{event.author}] {p.text}")


if __name__ == "__main__":
    asyncio.run(main())
