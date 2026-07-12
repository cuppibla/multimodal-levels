"""ENTRYPOINT — run the GraphRAG mission: ask who can treat Mara, watch flat-vector fail and the graph win."""
from __future__ import annotations
import asyncio

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from agent.agent import root_agent  # noqa: E402
from survivor_graph import MISSION_QUESTION  # noqa: E402


async def main() -> None:
    sessions = InMemorySessionService()
    await sessions.create_session(app_name="survivors", user_id="operator", session_id="m1")
    runner = Runner(app_name="survivors", agent=root_agent, session_service=sessions)
    msg = types.Content(role="user", parts=[types.Part(text=MISSION_QUESTION)])
    print(f"❓ {MISSION_QUESTION}\n")
    async for event in runner.run_async(user_id="operator", session_id="m1", new_message=msg):
        if event.content and event.content.parts:
            for p in event.content.parts:
                if p.text:
                    print(f"[{event.author}] {p.text}")


if __name__ == "__main__":
    asyncio.run(main())
