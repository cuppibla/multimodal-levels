"""STATE SPOTLIGHT — watch YOUR variable travel: callback → state → instruction → gate.

The deck beat (slide: "Session · state · callbacks" — park it once, read it every call),
made touchable: you type the crash coordinates, then watch them flow through the system.

  ① THE CALLBACK    before_agent_callback writes YOUR values into session state — once
  ② THE TEMPLATE    the Geologist's instruction holds a literal {soil_url}; ADK resolves
                    it FROM STATE at runtime — agents share a whiteboard, never call
                    each other
  ③ THE RUN         the real Geologist runs (real MCP tool call) and publishes its
                    report BACK to state via output_key — the whiteboard round-trip
  ④ CODE JUDGES     confirm_location checks the crew's biome against YOUR coordinates —
                    ground truth the model never saw. Set x=75 y=75 against verdant
                    evidence and watch the gate side with YOUR variable over the model.

Run (start the MCP server first — README Step 2):
    uv run python spotlight_state.py                 # interactive: asks for x, y
    uv run python spotlight_state.py --x 25 --y 25   # verdant ground truth (SW)
    uv run python spotlight_state.py --x 75 --y 75   # NE = VOLCANIC → watch a MISMATCH
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import Agent, SequentialAgent  # noqa: E402
from google.adk.agents.callback_context import CallbackContext  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from agent.agents.geological_analyst import geological_analyst as _proto  # noqa: E402
from agent.tools.confirm_tools import QUADRANT_BIOME, _quadrant  # noqa: E402

# The module-level Geologist already belongs to the crew (importing the agent package parents
# it under EvidenceAnalysisCrew) — so the spotlight runs a FRESH instance built from the SAME
# definition. Same model, same instruction (verbatim), same tools, same output_key.
geological_analyst = Agent(
    name=_proto.name,
    model=_proto.model,
    description=_proto.description,
    instruction=_proto.instruction,
    output_key=_proto.output_key,
    tools=list(_proto.tools),
)

BOLD, DIM, ORANGE, MINT, RED, END = "\033[1m", "\033[2m", "\033[38;5;215m", "\033[38;5;121m", "\033[38;5;203m", "\033[0m"
MANIFEST = Path(__file__).parent / "evidence" / "manifest.json"


def ask_num(prompt: str, default: float) -> float:
    if not sys.stdin.isatty():
        return default
    try:
        raw = input(prompt).strip()
        return float(raw) if raw else default
    except (EOFError, ValueError):
        return default


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", type=float, default=None)
    ap.add_argument("--y", type=float, default=None)
    args = ap.parse_args()

    try:
        urls = json.loads(MANIFEST.read_text())["urls"]
    except FileNotFoundError:
        raise SystemExit("evidence/manifest.json missing — run generate_evidence.py first (README Step 3).")

    print(f"\n{BOLD}━━ YOUR VARIABLE ━━{END}")
    print(f"  {DIM}the crash coordinates are the gate's ground truth — normally they come from the")
    print(f"  manifest; today they come from YOU. (quadrants: NW=CRYO NE=VOLCANIC SW=VERDANT SE=ARID){END}")
    x = args.x if args.x is not None else ask_num(f"  x (0-100) {DIM}(Enter = 25){END} > ", 25)
    y = args.y if args.y is not None else ask_num(f"  y (0-100) {DIM}(Enter = 25){END} > ", 25)

    # ① THE CALLBACK — park YOUR values in state, once
    async def hydrate_yours(callback_context: CallbackContext) -> None:
        callback_context.state["soil_url"] = urls["soil"]
        callback_context.state["flora_url"] = urls["flora"]
        callback_context.state["stars_url"] = urls["stars"]
        callback_context.state["x"], callback_context.state["y"] = x, y

    print(f"\n{BOLD}━━ ① THE CALLBACK — before_agent_callback writes state, ONCE ━━{END}")
    print(f"  state[\"soil_url\"]  = {DIM}{urls['soil']}{END}")
    print(f"  state[\"flora_url\"] = {DIM}{urls['flora'][:60]}…{END}")
    print(f"  state[\"stars_url\"] = {DIM}{urls['stars'][:60]}…{END}")
    print(f"  state[\"x\"], state[\"y\"] = {ORANGE}{x:g}, {y:g}{END}   {MINT}← YOUR VARIABLE{END}")

    # ② THE TEMPLATE — literal {key} in the instruction; ADK resolves from state at runtime
    template = geological_analyst.instruction
    print(f"\n{BOLD}━━ ② THE TEMPLATE — the Geologist's instruction, verbatim from agents/geological_analyst.py ━━{END}")
    print("  " + DIM + template.split("\n")[0] + f"{END}   {MINT}← a LITERAL {{soil_url}} — nobody pasted a URL here{END}")
    print("  " + DIM + template.split("\n")[1] + END)
    print(f"\n  at runtime ADK reads state and the same line becomes:")
    print(f"  {DIM}…The soil-sample evidence is at: {END}{ORANGE}{urls['soil']}{END}")
    print(f"  {DIM}agents never call each other — they read and write the shared whiteboard.{END}")

    # ③ THE RUN — the real Geologist, real MCP tool, report published via output_key
    print(f"\n{BOLD}━━ ③ THE RUN — real Geologist · real MCP tool call ━━{END}")
    root = SequentialAgent(name="StateSpotlight", sub_agents=[geological_analyst], before_agent_callback=hydrate_yours)
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="spotlight", user_id="you", session_id="s1")
    runner = Runner(agent=root, app_name="spotlight", session_service=session_service)
    report = ""
    async for event in runner.run_async(
        user_id="you", session_id="s1",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text="Analyze the soil evidence.")]),
    ):
        if event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts).strip()
            if text:
                report = text
                print(f"  [{event.author}] {text}")

    session = await session_service.get_session(app_name="spotlight", user_id="you", session_id="s1")
    print(f"\n  the whiteboard AFTER the run — output_key published the report back to state:")
    print(f"  state[\"geo_report\"] = {DIM}{str(session.state.get('geo_report'))[:100]}…{END}")

    # ④ CODE JUDGES — the gate's math on YOUR coordinates
    print(f"\n{BOLD}━━ ④ CODE JUDGES — confirm_location's math, on YOUR variable ━━{END}")
    quadrant = _quadrant(x, y)
    truth = QUADRANT_BIOME[quadrant]
    m = re.search(r"ANALYSIS:\s*([A-Z]+)", report or "")
    claimed = m.group(1) if m else "UNKNOWN"
    print(f"  YOUR coordinates ({x:g},{y:g}) → quadrant {quadrant} → ground truth {ORANGE}{truth}{END}")
    print(f"  the Geologist claimed {ORANGE}{claimed}{END}")
    if claimed == truth:
        print(f"  {MINT}✓ MATCH — beacon would activate. Code agreed with the model — because YOUR value said so.{END}\n")
    else:
        print(f"  {RED}✗ MISMATCH — the gate rejects the claim. The model sounded confident; YOUR variable")
        print(f"  was the ground truth it never saw. Deterministic code, not vibes, decides.{END}\n")


if __name__ == "__main__":
    asyncio.run(main())
