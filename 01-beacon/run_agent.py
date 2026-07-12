"""Drive the ADK consistency agent programmatically — two different scenes, one face.

    uv run python run_agent.py

Proves the Beat-5 claim: state + callback + ref-image pin = the identity re-applied to
EVERY generation, so render 2 (a totally different scene) still matches render 1.
"""
import asyncio

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

from agent.agent import root_agent  # noqa: E402


async def say(runner: Runner, session_id: str, text: str) -> None:
    print(f"\n  YOU  → {text}")
    async for event in runner.run_async(
        user_id="explorer",
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=text)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(p.text or "" for p in event.content.parts).strip()
            if reply:
                print(f"  AGENT→ {reply}")


async def main() -> None:
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="beacon", user_id="explorer", session_id="s1")
    runner = Runner(agent=root_agent, app_name="beacon", session_service=session_service)

    await say(runner, "s1", "Draw the explorer waving hello at the camera.")
    await say(runner, "s1", "Now draw them planting a beacon on a cliff at sunset.")

    print("\n  → open outputs/agent_01.png and agent_02.png: different scenes, SAME face.\n")


if __name__ == "__main__":
    asyncio.run(main())
