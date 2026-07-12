"""Mission Analysis AI — the full multi-agent system for Level 2 (Reason).

    MissionAnalysisAI (LlmAgent · orchestrator)
      ├─ before_agent_callback  → hydrates evidence URLs + coords into shared STATE
      ├─ EvidenceAnalysisCrew (ParallelAgent · true concurrent fan-out)
      │    ├─ GeologicalAnalyst    — soil IMAGE   → custom MCP server
      │    ├─ BotanicalAnalyst     — flora VIDEO+AUDIO → custom MCP server
      │    └─ AstronomicalAnalyst  — star image → local vision tool → BigQuery MCP lookup
      └─ confirm_location (FunctionTool) — the deterministic gate: code judges

State flows by {key} templating: the callback writes soil_url/flora_url/stars_url/x/y once,
every sub-agent instruction reads them at runtime. Agents never call each other — they
share the whiteboard.
"""
import json
import os
from pathlib import Path

from google.adk.agents import Agent, ParallelAgent
from google.adk.agents.callback_context import CallbackContext

from agent.agents import astronomical_analyst, botanical_analyst, geological_analyst
from agent.tools.confirm_tools import confirm_location_tool

MANIFEST = Path(__file__).parent.parent / "evidence" / "manifest.json"


async def setup_mission_context(callback_context: CallbackContext) -> None:
    """before_agent_callback — one hydration pass, then everything reads state."""
    callback_context.state["project_id"] = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    try:
        manifest = json.loads(MANIFEST.read_text())
    except FileNotFoundError:
        for key in ("soil_url", "flora_url", "stars_url"):
            callback_context.state[key] = "NOT AVAILABLE — run generate_evidence.py first"
        callback_context.state["x"], callback_context.state["y"] = 0, 0
        return
    callback_context.state["soil_url"] = manifest["urls"]["soil"]
    callback_context.state["flora_url"] = manifest["urls"]["flora"]
    callback_context.state["stars_url"] = manifest["urls"]["stars"]
    callback_context.state["x"] = manifest["x"]
    callback_context.state["y"] = manifest["y"]


evidence_analysis_crew = ParallelAgent(
    name="EvidenceAnalysisCrew",
    description="Runs geological, botanical, and astronomical analysis IN PARALLEL to classify the biome.",
    sub_agents=[geological_analyst, botanical_analyst, astronomical_analyst],
)

# Runs AFTER the crew (guaranteed by the SequentialAgent) — reads the three reports from
# state via {key} templating, applies the agreement rule, then hits the deterministic gate.
mission_synthesizer = Agent(
    name="MissionSynthesizer",
    model="gemini-2.5-flash",
    description="Synthesizes the crew's findings into a consensus and activates the verified beacon.",
    instruction=(
        "You are Mission Analysis AI. Your specialist crew has reported:\n"
        "· {geo_report}\n"
        "· {bot_report}\n"
        "· {astro_report}\n\n"
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

# fan-out → gather → synthesize → verify, deterministically wired
from google.adk.agents import SequentialAgent  # noqa: E402

root_agent = SequentialAgent(
    name="MissionAnalysisAI",
    description="Crash-site analysis: parallel specialist crew, then consensus + verified beacon.",
    sub_agents=[evidence_analysis_crew, mission_synthesizer],
    before_agent_callback=setup_mission_context,
)
