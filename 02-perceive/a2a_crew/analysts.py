"""The three specialists, re-instructed for remote life — same tools, new contract.

The monolith analysts read their evidence URL from shared session STATE ({soil_url} …)
hydrated by the dispatcher's callback. A remote service has no access to the caller's
state — in A2A, everything the specialist needs must arrive IN THE MESSAGE. That is the
one real change between the two shapes; the tools are imported untouched.

Config that used to ride in state (project_id) now comes from the SERVICE's own env —
each deployment carries its own configuration, which is exactly how you want it split.
"""
import os

from google.adk.agents import Agent

from agent.tools.mcp_tools import get_location_analyzer_toolset
from agent.tools.star_tools import extract_star_features_tool, get_bigquery_mcp_toolset

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")

_MANIFEST_CONTRACT = (
    "The user message contains a crash-site evidence manifest with one line per "
    "evidence type, e.g. 'soil: gs://…', 'flora: gs://…', 'stars: gs://…'.\n"
)

geological_analyst = Agent(
    name="GeologicalAnalyst",
    model="gemini-2.5-flash",
    description="Remote geologist service — analyzes the soil-sample image via the Location Analyzer MCP server.",
    instruction=(
        "You are the mission's planetary geologist, running as your own remote service.\n"
        + _MANIFEST_CONTRACT +
        "YOUR evidence is the 'soil:' line — call the analyze_geological tool with that "
        "exact URL. Report back in ONE line:\n"
        "GEOLOGICAL ANALYSIS: [BIOME] (confidence: X%) — key minerals.\n"
        "Judge ONLY the soil. Do NOT synthesize other evidence or confirm any location."
    ),
    tools=[get_location_analyzer_toolset()],
)

botanical_analyst = Agent(
    name="BotanicalAnalyst",
    model="gemini-2.5-flash",
    description="Remote xenobotanist service — analyzes the flora video (visual + audio) via the Location Analyzer MCP server.",
    instruction=(
        "You are the mission's xenobotanist, running as your own remote service.\n"
        + _MANIFEST_CONTRACT +
        "YOUR evidence is the 'flora:' line — call the analyze_botanical tool with that "
        "exact URL. The tool inspects BOTH the visual track AND the audio track — mention "
        "any audio signatures it found.\n"
        "Report back in ONE line:\n"
        "BOTANICAL ANALYSIS: [BIOME] (confidence: X%) — species · audio cues.\n"
        "Judge ONLY the flora recording. Do NOT synthesize other evidence or confirm any location."
    ),
    tools=[get_location_analyzer_toolset()],
)

astronomical_analyst = Agent(
    name="AstronomicalAnalyst",
    model="gemini-2.5-flash",
    description="Remote astronomer service — extracts star-field features, then triangulates the biome from the BigQuery star catalog.",
    instruction=(
        "You are the mission's astronomer, running as your own remote service.\n"
        + _MANIFEST_CONTRACT +
        "YOUR evidence is the 'stars:' line.\n"
        "STEP 1 — call extract_star_features with that exact URL. It returns star_color "
        "and sky_condition, already constrained to the catalog vocabulary.\n"
        "STEP 2 — call execute_sql_readonly on BigQuery with EXACTLY this SQL (substitute "
        "the two values from step 1):\n"
        f"SELECT quadrant, biome FROM `{PROJECT_ID}.multimodal_levels.star_catalog` "
        "WHERE LOWER(star_color) = LOWER('STAR_COLOR') "
        "AND LOWER(sky_condition) = LOWER('SKY_CONDITION') LIMIT 1\n"
        "If no row matches, relax to matching star_color only (LIMIT 1).\n"
        "Report back in ONE line:\n"
        "ASTRONOMICAL ANALYSIS: [BIOME] (quadrant Q) — star_color · sky_condition.\n"
        "The biome and quadrant MUST come from the BigQuery result — if the query fails "
        "or returns no rows, report exactly 'ASTRONOMICAL ANALYSIS: INCONCLUSIVE' and "
        "say why. NEVER invent a biome or quadrant.\n"
        "Judge ONLY the sky. Do NOT synthesize other evidence or confirm any location."
    ),
    tools=[extract_star_features_tool, get_bigquery_mcp_toolset()],
)

ANALYSTS = {
    "geological": geological_analyst,
    "botanical": botanical_analyst,
    "astronomical": astronomical_analyst,
}
