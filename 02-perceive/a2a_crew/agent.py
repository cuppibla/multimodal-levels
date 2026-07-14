"""The A2A dispatcher — the SAME orchestration tree, remote crew.

    Monolith:  ParallelAgent(sub_agents=[geo, bot, astro])            — one process
    A2A:       ParallelAgent(sub_agents=[RemoteA2aAgent × 3])         — three services

The tree didn't change; the hosting did. Two honest differences:

  1. STATE DOES NOT TRAVEL. The monolith's callback hydrates soil_url/flora_url/stars_url
     into shared state and every analyst reads it by {key} templating. A remote analyst
     never sees the caller's state — so the evidence manifest rides IN THE MESSAGE
     (run_mission_a2a.py builds it), and each specialist extracts its own line.
  2. NO output_key ACROSS THE WIRE. RemoteA2aAgent has no output_key, so the synthesizer
     reads the three reports from the conversation instead of state templating.

The deterministic gate is unchanged — confirm_location still checks the crew's biome
against coordinates hydrated into DISPATCHER-local state. Code judges, wherever the
crew happens to be hosted.
"""
import json
import os
from pathlib import Path

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)

from agent.tools.confirm_tools import confirm_location_tool

MANIFEST = Path(__file__).parent.parent / "evidence" / "manifest.json"


def _card(env_key: str, default_port: int) -> str:
    base = os.environ.get(env_key, f"http://localhost:{default_port}").rstrip("/")
    return f"{base}{AGENT_CARD_WELL_KNOWN_PATH}"


async def setup_gate_context(callback_context: CallbackContext) -> None:
    """before_agent_callback — the gate's ground truth stays DISPATCHER-local.

    Only x/y are hydrated: the remote analysts must not (and cannot) see them.
    """
    try:
        manifest = json.loads(MANIFEST.read_text())
        callback_context.state["x"] = manifest["x"]
        callback_context.state["y"] = manifest["y"]
    except FileNotFoundError:
        callback_context.state["x"], callback_context.state["y"] = 0, 0


remote_crew = ParallelAgent(
    name="RemoteEvidenceCrew",
    description="Fans out to three REMOTE analyst services in parallel via A2A.",
    sub_agents=[
        RemoteA2aAgent(
            name="GeologicalAnalyst",
            description="Remote geologist — soil image via custom MCP.",
            agent_card=_card("GEO_ANALYST_URL", 8791),
            timeout=300,
        ),
        RemoteA2aAgent(
            name="BotanicalAnalyst",
            description="Remote xenobotanist — flora video+audio via custom MCP.",
            agent_card=_card("BOT_ANALYST_URL", 8792),
            timeout=300,
        ),
        RemoteA2aAgent(
            name="AstronomicalAnalyst",
            description="Remote astronomer — star field via vision tool + BigQuery MCP.",
            agent_card=_card("ASTRO_ANALYST_URL", 8793),
            timeout=300,
        ),
    ],
)

mission_synthesizer = Agent(
    name="MissionSynthesizer",
    model="gemini-2.5-flash",
    description="Synthesizes the remote crew's findings into a consensus and activates the verified beacon.",
    instruction=(
        "You are Mission Analysis AI. Your specialist crew just reported in this "
        "conversation — find the three report lines beginning with GEOLOGICAL ANALYSIS, "
        "BOTANICAL ANALYSIS, and ASTRONOMICAL ANALYSIS.\n\n"
        "PROTOCOL:\n"
        "1. Apply the 2-of-3 agreement rule: if at least two specialists name the same "
        "biome, that is the crew's finding. If all three disagree, weigh confidences and "
        "say the finding is contested.\n"
        "2. Call confirm_location with the crew's biome. This is a DETERMINISTIC check "
        "against the crash coordinates — if it reports a mismatch, tell the survivor "
        "which specialist was likely fooled and by what.\n"
        "3. Give the survivor a tight mission summary: one line per specialist, then the "
        "verdict (beacon status).\n"
        "Reference: CRYO=frozen/NW · VOLCANIC=magma/NE · VERDANT=jungle/SW · ARID=desert/SE."
    ),
    tools=[confirm_location_tool],
)

root_agent = SequentialAgent(
    name="MissionAnalysisAI",
    description="Crash-site analysis, A2A shape: remote specialist crew, then consensus + verified beacon.",
    sub_agents=[remote_crew, mission_synthesizer],
    before_agent_callback=setup_gate_context,
)
