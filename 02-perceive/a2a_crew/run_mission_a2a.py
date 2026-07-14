"""Run the A2A mission: remote crew → consensus → the SAME deterministic gate.

Start the three analyst services first (each in its own terminal, or `&` them):

    ANALYST=geological   uv run python -m a2a_crew.serve_analyst    # :8791
    ANALYST=botanical    uv run python -m a2a_crew.serve_analyst    # :8792
    ANALYST=astronomical uv run python -m a2a_crew.serve_analyst    # :8793

Then:  uv run python -m a2a_crew.run_mission_a2a

The one visible difference from run_mission.py: the evidence manifest is read HERE and
sent IN THE MESSAGE — remote services can't read the caller's session state.
"""
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from a2a_crew.agent import root_agent  # noqa: E402

MANIFEST = Path(__file__).parent.parent / "evidence" / "manifest.json"


def build_mission_message() -> str:
    """State → message: the whiteboard the monolith shared becomes an explicit payload."""
    manifest = json.loads(MANIFEST.read_text())
    urls = manifest["urls"]
    return (
        "CRASH-SITE EVIDENCE MANIFEST\n"
        f"soil: {urls['soil']}\n"
        f"flora: {urls['flora']}\n"
        f"stars: {urls['stars']}\n\n"
        "Analyze all crash-site evidence and confirm my location. Activate the beacon."
    )


async def main() -> None:
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="mission-a2a", user_id="survivor", session_id="m1")
    runner = Runner(agent=root_agent, app_name="mission-a2a", session_service=session_service)

    print("\n  ── MISSION ANALYSIS · A2A SHAPE — remote crew · agent cards · same code gate ──")
    async for event in runner.run_async(
        user_id="survivor", session_id="m1",
        new_message=types.Content(role="user", parts=[types.Part.from_text(
            text=build_mission_message())]),
    ):
        if event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts).strip()
            if text:
                print(f"\n  [{event.author}]\n  {text}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
