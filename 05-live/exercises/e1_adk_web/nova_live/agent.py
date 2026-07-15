"""E1 — NOVA in the ADK dev UI (`adk web`).

The same live agent as `backend/agent/agent.py`, packaged so the ADK dev UI can
serve it: run `adk web` from `exercises/e1_adk_web/`, open the browser, pick
`nova_live`, and press the mic. No custom frontend, no WebSocket bridge — the
dev UI IS the bridge. That's the point of this exercise: see everything the
bridge does for you before we build one by hand.
"""
import os

from google.adk.agents import Agent

MODEL_ID = os.getenv("MODEL_ID", "gemini-live-2.5-flash-native-audio")


def report_digit(count: int) -> dict:
    """Report how many fingers the operator is holding up to the camera.

    Args:
        count: The number of fingers detected, 1-5.

    Returns:
        dict confirming the digit was logged for the neural-sync sequence.
    """
    print(f"\n  [SERVER-SIDE TOOL] ⚡ report_digit(count={count})\n")
    return {"status": "logged", "digit": count}


def ship_status() -> dict:
    """Read the rescue ship's current status board.

    Returns:
        dict with hull, oxygen, and engine readouts.
    """
    print("\n  [SERVER-SIDE TOOL] ⚡ ship_status()\n")
    return {"hull": "97% integrity", "oxygen": "11 hours reserve", "engines": "warming up"}


root_agent = Agent(
    name="nova_live",
    model=MODEL_ID,
    description="NOVA — the ship AI, live in the ADK dev UI: hears, sees, speaks, calls tools.",
    instruction=(
        "You are NOVA, the rescue ship's AI, on a LIVE voice channel with a stranded "
        "operator. Personality: calm, warm, lightly wry. Speak in short natural "
        "sentences — this is voice, not prose.\n\n"
        "If the operator holds fingers up to the camera, FIRST call report_digit with "
        "the count, THEN confirm out loud in a few words. If asked how the ship is "
        "doing, call ship_status and summarize it in one sentence. Never narrate what "
        "you are doing, never invent a tool call you didn't make.\n\n"
        "Keep every reply under two sentences unless the operator asks for detail."
    ),
    tools=[report_digit, ship_status],
)
