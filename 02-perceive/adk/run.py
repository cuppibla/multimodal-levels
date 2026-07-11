"""Run the ADK perceive crew on a crash site: three images in, a voted biome out.

    uv run python run.py                                    # uses ../assets/verdant-*.png
    uv run python run.py --soil a.png --flora b.png --stars c.png

(Generate the default images once from the TS module:  cd .. && npm run samples -- verdant)
Or explore interactively:  uv run adk web   /  uv run adk run crew
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from crew.agent import root_agent

load_dotenv()
HERE = Path(__file__).parent


def part_from(path: str) -> types.Part:
    data = Path(path).read_bytes()
    mime = "image/jpeg" if path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    return types.Part.from_bytes(data=data, mime_type=mime)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--soil", default=str(HERE / "../assets/verdant-soil.png"))
    ap.add_argument("--flora", default=str(HERE / "../assets/verdant-flora.png"))
    ap.add_argument("--stars", default=str(HERE / "../assets/verdant-stars.png"))
    args = ap.parse_args()

    for p in (args.soil, args.flora, args.stars):
        if not Path(p).exists():
            sys.exit(f"  ✗ missing image: {p}\n    generate them once:  cd .. && npm run samples -- verdant")

    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() != "true":
        sys.exit("  ✗ set GOOGLE_API_KEY in .env (AI Studio) or configure Vertex — see .env.example")

    session_service = InMemorySessionService()
    await session_service.create_session(app_name="perceive", user_id="u", session_id="s")
    runner = Runner(agent=root_agent, app_name="perceive", session_service=session_service)

    content = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text="Crash-site evidence — Image 1 soil, Image 2 flora, Image 3 star field. Identify the biome."
            ),
            part_from(args.soil),
            part_from(args.flora),
            part_from(args.stars),
        ],
    )

    print("\n  ParallelAgent: fan-out → 3 specialists at once → VoteAgent tallies\n")
    async for event in runner.run_async(user_id="u", session_id="s", new_message=content):
        if event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts).strip()
            if text:
                print(f"    [{event.author:>10}]  {text}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
