"""Shared lab hygiene + one tiny helper — NOT part of the lesson.

  setup()   loads ../.env (project, Vertex flag) and silences warning spam
  turn()    one request→response exchange through a Runner, returning the final
            text and printing any tool calls the model made along the way
"""
import logging
import warnings
from pathlib import Path

from dotenv import load_dotenv


def setup() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    warnings.filterwarnings("ignore")
    logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
    logging.getLogger("google_genai").setLevel(logging.ERROR)


async def turn(runner, user_id: str, session_id: str, text: str, quiet: bool = False) -> str:
    """One exchange. Prints YOU/OPS lines (unless quiet) and any tool calls."""
    from google.genai import types

    if not quiet:
        print(f"  YOU → {text}")
    reply = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=text)]),
    ):
        for fc in event.get_function_calls():
            print(f"    ⚙️  {fc.name}({fc.args})")
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(p.text or "" for p in event.content.parts).strip()
    if not quiet:
        print(f"  OPS → {reply}")
    return reply
