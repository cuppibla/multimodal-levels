"""Run the full mission: parallel crew → consensus → deterministic beacon gate.

    uv run python run_mission.py

(Or explore interactively:  uv run adk web  /  uv run adk run agent)
"""
import asyncio

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from agent.agent import root_agent  # noqa: E402


async def main() -> None:
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="mission", user_id="survivor", session_id="m1")
    runner = Runner(agent=root_agent, app_name="mission", session_service=session_service)

    print("\n  ── MISSION ANALYSIS — parallel crew · two MCP servers · BigQuery · code gate ──")
    async for event in runner.run_async(
        user_id="survivor", session_id="m1",
        new_message=types.Content(role="user", parts=[types.Part.from_text(
            text="Analyze all crash-site evidence and confirm my location. Activate the beacon.")]),
    ):
        if event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts).strip()
            if text:
                print(f"\n  [{event.author}]\n  {text}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
