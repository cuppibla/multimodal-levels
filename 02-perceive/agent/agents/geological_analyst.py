"""Geological analyst — reads the soil IMAGE through the custom MCP server."""
from google.adk.agents import Agent

from agent.tools.mcp_tools import get_location_analyzer_toolset

geological_analyst = Agent(
    name="GeologicalAnalyst",
    model="gemini-2.5-flash",
    description="Analyzes the soil-sample image via the Location Analyzer MCP server.",
    instruction=(
        "You are the mission's planetary geologist. The soil-sample evidence is at: "
        "{soil_url}\n"
        "Call the analyze_geological tool with that exact URL. Report back in ONE line:\n"
        "GEOLOGICAL ANALYSIS: [BIOME] (confidence: X%) — key minerals.\n"
        "Judge ONLY the soil. Do NOT synthesize other evidence or confirm any location."
    ),
    output_key="geo_report",
    tools=[get_location_analyzer_toolset()],
)
