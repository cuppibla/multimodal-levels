"""Location Analyzer — a CUSTOM MCP server (FastMCP · Streamable HTTP).

This is MCP pattern #1 of the level: tools YOU author, served over the Model Context
Protocol, consumed by ADK agents through `MCPToolset`. (Pattern #2 is the Google-MANAGED
BigQuery MCP the astronomer uses — same client wiring, zero server code.)

Two tools, both truly multimodal — Gemini ingests the media by URI inside the tool:
  · analyze_geological(image_url)  — reads a soil-sample IMAGE
  · analyze_botanical(video_url)   — reads a flora VIDEO, visual track AND audio track

Run locally:   uv run python main.py          → http://localhost:8788/mcp
Deploy:        gcloud run deploy location-analyzer --source . --allow-unauthenticated
"""
import json
import os
import re
from typing import Annotated

from fastmcp import FastMCP
from google import genai
from google.genai import types as genai_types
from pydantic import Field

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

mcp = FastMCP("Location Analyzer MCP Server 🛸")
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

BIOMES = "CRYO (frozen, NW) · VOLCANIC (magma, NE) · VERDANT (jungle, SW) · ARID (desert, SE)"

GEOLOGICAL_PROMPT = f"""You are a planetary geologist. Analyze ONLY this soil sample image.
Classify the biome from soil/rock texture, colour and mineral cues. Biomes: {BIOMES}.
Return STRICT JSON: {{"biome": "CRYO|VOLCANIC|VERDANT|ARID", "confidence": 0-100,
"minerals_detected": ["..."], "description": "one sentence"}}"""

BOTANICAL_PROMPT = f"""You are a xenobotanist. Analyze this flora VIDEO — BOTH the visual
track (plant life, leaf form, colour, motion) AND the audio track (wind, ice crackle,
volcanic hiss, insect/bird calls, humming). Biomes: {BIOMES}.
Return STRICT JSON: {{"biome": "CRYO|VOLCANIC|VERDANT|ARID", "confidence": 0-100,
"species_detected": ["..."], "audio_signatures": ["..."], "visual_features": ["..."],
"description": "one sentence"}}"""


def parse_json_response(text: str) -> dict:
    cleaned = re.sub(r"^```(json)?|```$", "", (text or "").strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"biome": "UNKNOWN", "confidence": 0, "description": cleaned[:200]}


@mcp.tool()
def analyze_geological(
    image_url: Annotated[str, Field(description="Cloud Storage URL (gs://...) of the soil sample image")],
) -> dict:
    """Analyzes a soil-sample image and classifies the planetary biome from geological cues."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[GEOLOGICAL_PROMPT,
                  genai_types.Part.from_uri(file_uri=image_url, mime_type="image/png")],
    )
    return parse_json_response(response.text)


@mcp.tool()
def analyze_botanical(
    video_url: Annotated[str, Field(description="Cloud Storage URL (gs://...) of the flora video recording")],
) -> dict:
    """Analyzes a flora video — visual AND audio tracks — and classifies the planetary biome."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[BOTANICAL_PROMPT,
                  genai_types.Part.from_uri(file_uri=video_url, mime_type="video/mp4")],
    )
    return parse_json_response(response.text)


# Workshop gate: when WORKSHOP_TOKEN is set on the service, every HTTP call must carry X-WBH-Token —
# both tools call Gemini on the host's bill. Unset (local dev / your own deploy) → open as before.
WORKSHOP_TOKEN = os.environ.get("WORKSHOP_TOKEN", "")
_inner = mcp.http_app()


async def app(scope, receive, send):  # thin ASGI wrapper — lifespan passes straight through
    if scope["type"] == "http" and WORKSHOP_TOKEN:
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers") or []}
        if headers.get("x-wbh-token") != WORKSHOP_TOKEN:
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"content-type", b"application/json")]})
            await send({"type": "http.response.body", "body": b'{"error": "workshop token required"}'})
            return
    await _inner(scope, receive, send)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8788))
    print(f"  Location Analyzer MCP · http://localhost:{port}/mcp")
    uvicorn.run(app, host="0.0.0.0", port=port)
