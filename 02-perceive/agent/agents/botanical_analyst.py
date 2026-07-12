"""Botanical analyst — reads the flora VIDEO (visual + AUDIO tracks) through the custom MCP server."""
from google.adk.agents import Agent

from agent.tools.mcp_tools import get_location_analyzer_toolset

botanical_analyst = Agent(
    name="BotanicalAnalyst",
    model="gemini-2.5-flash",
    description="Analyzes the flora video recording (visual and audio) via the Location Analyzer MCP server.",
    instruction=(
        "You are the mission's xenobotanist. The flora VIDEO evidence is at: "
        "{flora_url}\n"
        "Call the analyze_botanical tool with that exact URL. The tool inspects BOTH the "
        "visual track AND the audio track — mention any audio signatures it found.\n"
        "Report back in ONE line:\n"
        "BOTANICAL ANALYSIS: [BIOME] (confidence: X%) — species · audio cues.\n"
        "Judge ONLY the flora recording. Do NOT synthesize other evidence or confirm any location."
    ),
    output_key="bot_report",
    tools=[get_location_analyzer_toolset()],
)
