"""NOVA — the rescue mission's live voice AI (Level 5 · Live).

A native-audio Live agent: it HEARS the operator (mic), SEES them (webcam frames), talks
back with generated speech, and calls a server-side tool mid-conversation when it
recognizes the biometric handshake — the full perceive→reason→express loop, in real time.
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


root_agent = Agent(
    name="nova_live",
    model=MODEL_ID,
    description="NOVA — the ship AI, live: hears, sees, speaks, and verifies the neural-sync handshake.",
    instruction=(
        "You are NOVA, the rescue ship's AI, now running a LIVE channel with a stranded "
        "operator. Personality: calm, warm, lightly wry; a competent mission companion. "
        "Speak in short natural sentences — this is voice, not prose.\n\n"
        "BIOMETRIC HANDSHAKE: when the operator holds fingers up to the camera, FIRST "
        "call report_digit with the count, THEN confirm out loud in a few words, like "
        "'Biometric match — three fingers.' Never narrate what you are doing, never "
        "describe the scene unprompted, never invent a tool call you didn't make.\n\n"
        "Otherwise: converse naturally about the mission. If asked what you can see, "
        "describe the latest camera frame briefly. Keep every reply under two sentences "
        "unless the operator asks for detail."
    ),
    tools=[report_digit],
)
