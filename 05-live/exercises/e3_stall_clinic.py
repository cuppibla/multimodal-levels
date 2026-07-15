"""E3 — the stall clinic: why a slow tool kills a live conversation, and 3 cures.

The failure everyone hits: mid-conversation, the model calls your tool, the tool
takes 6 seconds, and the voice channel goes DEAD. Worse — if the tool is a plain
`def`, it doesn't just silence the model, it freezes your entire event loop:
mic audio stops relaying, keepalives stop, barge-in stops. The user hears a
crashed app.

Four variants, same 6-second "deep scan" tool, measured with two clocks:

  LOOP-FREEZE  the longest gap in a 50ms heartbeat task — how long YOUR asyncio
               loop was blocked (audio relay, keepalive, everything shares it)
  DEAD-AIR     seconds from the model's tool call to the next word the user hears

  variant A  def + time.sleep        the bug        loop freezes AND dead air
  variant B  async def + asyncio.sleep  half a cure  loop fine, dead air remains
  variant C  callback bypass         instant ack    before_tool_callback returns a
             "scan started" result immediately (model speaks NOW), real work runs
             as a background task, result injected later via queue.send_content
  variant D  streaming tool          the ADK-native cure  an async GENERATOR that
             yields progress; the model narrates while the tool still runs

Run:  uv run python exercises/e3_stall_clinic.py            (all four, ~2 min)
      uv run python exercises/e3_stall_clinic.py --variant c
"""
import argparse
import asyncio
import time
from typing import AsyncGenerator

import _labkit

_labkit.setup()

from google.adk.agents import Agent
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

MODEL_ID = "gemini-live-2.5-flash-native-audio"
SCAN_SECONDS = 6
PROMPT = "NOVA, run a deep scan of sector 7 and tell me what you find."

BASE_INSTRUCTION = (
    "You are NOVA, the rescue ship's AI on a live voice channel. Calm, warm, brief. "
    "When the operator asks for a deep scan, call scan_asteroid_field with the sector, "
    "then report the result in one short sentence."
)


# ─── the same slow scan, four ways ──────────────────────────────────────────────

def scan_sync(sector: str) -> dict:
    """Deep-scan a sector for asteroids. Takes several seconds.

    Args:
        sector: The sector designation, e.g. "7".
    """
    time.sleep(SCAN_SECONDS)  # ❌ blocks the WHOLE event loop
    return {"sector": sector, "asteroids": 3, "corridor": "clear"}


async def scan_async(sector: str) -> dict:
    """Deep-scan a sector for asteroids. Takes several seconds.

    Args:
        sector: The sector designation, e.g. "7".
    """
    await asyncio.sleep(SCAN_SECONDS)  # ✅ loop breathes… but the model still waits
    return {"sector": sector, "asteroids": 3, "corridor": "clear"}


async def scan_asteroid_field_stream(sector: str) -> AsyncGenerator[str, None]:
    """Deep-scan a sector for asteroids, streaming progress as it goes.

    Args:
        sector: The sector designation, e.g. "7".
    """
    yield f"Scan of sector {sector} initiated. First sweep running."
    await asyncio.sleep(SCAN_SECONDS / 2)
    yield "Halfway there — two contacts so far, still resolving."
    await asyncio.sleep(SCAN_SECONDS / 2)
    yield "Scan complete: 3 asteroids mapped, transit corridor is clear."


# ─── one harness, two clocks ────────────────────────────────────────────────────

async def run_variant(name: str, agent: Agent, on_tool_call=None) -> dict:
    session_service = InMemorySessionService()
    runner = Runner(app_name="clinic", agent=agent, session_service=session_service)
    await session_service.create_session(app_name="clinic", user_id="op", session_id=name)

    queue = LiveRequestQueue()
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )

    # clock 1 — heartbeat: how badly does the tool freeze OUR loop?
    # (armed on the first event, so connection setup doesn't pollute the reading)
    max_gap = 0.0
    armed = asyncio.Event()
    async def heartbeat():
        nonlocal max_gap
        await armed.wait()
        last = time.monotonic()
        while True:
            await asyncio.sleep(0.05)
            now = time.monotonic()
            max_gap = max(max_gap, now - last)
            last = now

    hb = asyncio.create_task(heartbeat())
    t0 = time.monotonic()
    t_tool_call = None
    dead_air = None
    said_after_tool = []
    print(f"\n── variant {name} " + "─" * (60 - len(name)))
    print(f"[t=0.00s] ⌨️  {PROMPT!r}")
    queue.send_content(types.Content(role="user", parts=[types.Part(text=PROMPT)]))

    try:
        async def consume():
            nonlocal t_tool_call, dead_air
            turns = 0
            async for event in runner.run_live(
                user_id="op", session_id=name, live_request_queue=queue, run_config=run_config
            ):
                armed.set()  # connection is up — heartbeat starts judging from here
                t = time.monotonic() - t0
                for fc in event.get_function_calls():
                    if t_tool_call is None:
                        t_tool_call = t
                    print(f"[t={t:5.2f}s] ⚙️  model calls {fc.name}({fc.args})")
                for fr in event.get_function_responses():
                    print(f"[t={t:5.2f}s] 📦 tool → model: {str(fr.response)[:70]}")
                if event.output_transcription and event.output_transcription.text \
                        and not event.output_transcription.finished:
                    text = event.output_transcription.text
                    print(f"[t={t:5.2f}s] 🗣  {text!r}")
                    if t_tool_call is not None and dead_air is None:
                        dead_air = t - t_tool_call
                    if t_tool_call is not None:
                        said_after_tool.append(text)
                if event.turn_complete:
                    turns += 1
                    print(f"[t={t:5.2f}s] ✔  turn_complete")
                    # done = she has SPOKEN a result and the slow work is genuinely over
                    # (in live, the voiced report lands a turn AFTER the tool response —
                    #  hanging up at the first turn_complete would cut her off mid-mission)
                    work_over = t_tool_call is not None and (t - t_tool_call) > SCAN_SECONDS
                    if (work_over and said_after_tool) or turns >= 6:
                        queue.close()
                        return

        # variant C: watch for the tool call, kick off the real work in the background
        if on_tool_call:
            asyncio.create_task(on_tool_call(queue))
        await asyncio.wait_for(consume(), timeout=90)
    finally:
        hb.cancel()

    total = time.monotonic() - t0
    return {"variant": name, "loop_freeze": max_gap, "dead_air": dead_air, "total": total}


# ─── the four patients ──────────────────────────────────────────────────────────

async def variant_a() -> dict:
    agent = Agent(name="nova_a", model=MODEL_ID, instruction=BASE_INSTRUCTION, tools=[scan_sync])
    return await run_variant("A · def + time.sleep (the bug)", agent)


async def variant_b() -> dict:
    agent = Agent(name="nova_b", model=MODEL_ID, instruction=BASE_INSTRUCTION, tools=[scan_async])
    return await run_variant("B · async def (half a cure)", agent)


async def variant_c() -> dict:
    # the bypass: acknowledge instantly, do the work in the background,
    # radio the result in through the queue when it's done.
    scan_requested = asyncio.Event()

    def ack_immediately(tool, args, tool_context):
        scan_requested.set()  # start the real work NOW, in the background
        return {  # returning a dict from before_tool_callback SKIPS the real tool
            "status": "scan launched, running in background",
            "instruction": "tell the operator the scan is underway; results will be radioed in",
        }

    async def finish_scan(queue: LiveRequestQueue):
        await scan_requested.wait()          # fires the moment the model calls the tool
        await asyncio.sleep(SCAN_SECONDS)    # the real 6s of work
        queue.send_content(types.Content(role="user", parts=[types.Part(
            text="[SHIP SYSTEMS] deep scan complete: 3 asteroids mapped, transit corridor "
                 "clear. Report this to the operator in one short sentence."
        )]))

    agent = Agent(name="nova_c", model=MODEL_ID, instruction=BASE_INSTRUCTION,
                  tools=[scan_async], before_tool_callback=ack_immediately)
    return await run_variant("C · callback bypass (instant ack)", agent, on_tool_call=finish_scan)


async def variant_d() -> dict:
    agent = Agent(
        name="nova_d", model=MODEL_ID,
        instruction=(
            "You are NOVA, the rescue ship's AI on a live voice channel. Calm, warm, brief. "
            "When the operator asks for a deep scan, call scan_asteroid_field_stream exactly "
            "ONCE with the sector. It runs in the background and its updates arrive on their "
            "own — when an update arrives, voice it to the operator in a few words. NEVER "
            "call the tool a second time, and never pass it status or result arguments."
        ),
        tools=[scan_asteroid_field_stream],
    )
    return await run_variant("D · streaming tool (yields progress)", agent)


VARIANTS = {"a": variant_a, "b": variant_b, "c": variant_c, "d": variant_d}


async def main() -> None:
    _labkit.install_quiet_loop()
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=list(VARIANTS), help="run just one")
    args = parser.parse_args()
    picks = [args.variant] if args.variant else list(VARIANTS)

    results = []
    for key in picks:
        results.append(await VARIANTS[key]())
        await asyncio.sleep(1)

    print("\n═══ clinic results ═══")
    print(f"{'variant':44}  {'loop-freeze':>11}  {'dead-air':>9}")
    for r in results:
        da = f"{r['dead_air']:.2f}s" if r["dead_air"] is not None else "—"
        print(f"{r['variant']:44}  {r['loop_freeze']:>10.2f}s  {da:>9}")
    print("\nRead it like this:")
    print("  A: loop-freeze ≈ 6s — your mic relay and keepalive were DEAD, not just quiet")
    print("  B: loop breathes (freeze ~0s) but dead-air stays ≈ 6s — async ≠ non-blocking conversation")
    print("  C: dead-air ≈ 1s — the callback acked instantly; the queue radioed the result in later")
    print("  D: the model narrates DURING the scan — the tool itself streams; live-only, experimental\n")


if __name__ == "__main__":
    asyncio.run(main())
