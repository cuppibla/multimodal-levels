"""The Astronomer's two tools — and MCP pattern #2 (Google-MANAGED MCP).

  1. extract_star_features — a LOCAL FunctionTool: Gemini vision reads the star-field
     image and extracts features, enum-constrained to the star-catalog vocabulary.
  2. the BigQuery MCP toolset — Google's HOSTED MCP server for BigQuery. Same MCPToolset
     client wiring as our custom server, but zero server code: auth = OAuth ADC bearer.
"""
import json
import os
import re

import google.auth
import google.auth.transport.requests
from google import genai
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.genai import types as genai_types

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")

# ── tool 1 · local vision extraction (enum-constrained → exact SQL match) ────────────────
STAR_EXTRACTION_PROMPT = """You are an astronomer. Look ONLY at this star-field image.
Extract exactly these two features, choosing the CLOSEST value from the allowed lists:
  star_color:    blue_white | cyan | red_orange | deep_red | warm_yellow | golden | white | silver
  sky_condition: pale_blue_aurora | crystal_clear | ash_dimmed | orange_glow | green_airglow | humid_haze | crystal_clear_dense | no_haze
Return STRICT JSON: {"star_color": "...", "sky_condition": "...", "description": "one sentence"}"""

_genai_client: genai.Client | None = None


def _client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(
            vertexai=True, project=PROJECT_ID,
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    return _genai_client


def extract_star_features(image_url: str) -> dict:
    """Extracts star_color and sky_condition features from a star-field image.

    Args:
        image_url: Cloud Storage URL (gs://...) of the star-field image.

    Returns:
        dict with star_color, sky_condition, and a one-line description.
    """
    response = _client().models.generate_content(
        model="gemini-2.5-flash",
        contents=[STAR_EXTRACTION_PROMPT,
                  genai_types.Part.from_uri(file_uri=image_url, mime_type="image/png")],
    )
    cleaned = re.sub(r"^```(json)?|```$", "", (response.text or "").strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"star_color": "unknown", "sky_condition": "unknown", "description": cleaned[:200]}


extract_star_features_tool = FunctionTool(extract_star_features)

# ── tool 2 · Google-managed BigQuery MCP (hosted by Google — no server of ours) ──────────
_bigquery_toolset: MCPToolset | None = None


def get_bigquery_mcp_toolset() -> MCPToolset:
    global _bigquery_toolset
    if _bigquery_toolset is None:
        credentials, adc_project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        credentials.refresh(google.auth.transport.requests.Request())
        _bigquery_toolset = MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="https://bigquery.googleapis.com/mcp",
                headers={
                    "Authorization": f"Bearer {credentials.token}",
                    "x-goog-user-project": PROJECT_ID or adc_project,
                },
            ),
            tool_filter=["execute_sql_readonly"],  # a lookup needs read-only SQL, nothing more
        )
    return _bigquery_toolset
