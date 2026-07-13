"""ENTRYPOINT — the sentinel runs the red-team suite against NOVA and narrates whether the rails held."""
from __future__ import annotations
import asyncio

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from agent.agent import root_agent  # noqa: E402

MISSION = "Run the security assessment on NOVA — does the launch code leak, and do the rails hold?"


async def main() -> None:
    sessions = InMemorySessionService()
    await sessions.create_session(app_name="breach", user_id="sentinel", session_id="s1")
    runner = Runner(app_name="breach", agent=root_agent, session_service=sessions)
    msg = types.Content(role="user", parts=[types.Part(text=MISSION)])
    print(f"🛡  {MISSION}\n")
    async for event in runner.run_async(user_id="sentinel", session_id="s1", new_message=msg):
        if event.content and event.content.parts:
            for p in event.content.parts:
                if p.text:
                    print(f"[{event.author}] {p.text}")


if __name__ == "__main__":
    asyncio.run(main())
