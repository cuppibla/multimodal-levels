"""Astronomical analyst — a TWO-STEP pipeline inside one agent:
vision extraction (local FunctionTool) → star-catalog lookup (Google-managed BigQuery MCP).
"""
from google.adk.agents import Agent

from agent.tools.star_tools import extract_star_features_tool, get_bigquery_mcp_toolset

astronomical_analyst = Agent(
    name="AstronomicalAnalyst",
    model="gemini-2.5-flash",
    description="Extracts star-field features, then triangulates the biome from the BigQuery star catalog.",
    instruction=(
        "You are the mission's astronomer. The star-field evidence is at: {stars_url}\n"
        "STEP 1 — call extract_star_features with that exact URL. It returns star_color "
        "and sky_condition, already constrained to the catalog vocabulary.\n"
        "STEP 2 — call execute_sql_readonly on BigQuery with EXACTLY this SQL (substitute "
        "the two values from step 1):\n"
        "SELECT quadrant, biome FROM `{project_id}.multimodal_levels.star_catalog` "
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
    output_key="astro_report",
    tools=[extract_star_features_tool, get_bigquery_mcp_toolset()],
)
