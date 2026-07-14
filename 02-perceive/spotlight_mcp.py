"""MCP spotlight — the tool layer in 60 seconds, both flavors, one protocol.

Act ①  YOUR server   — the custom FastMCP Location Analyzer:
        initialize → tools/list → tools/call analyze_geological(soil image)
Act ②  GOOGLE's      — the managed BigQuery MCP (zero server code of yours):
        initialize → tools/list → tools/call execute_sql_readonly(star_catalog lookup)

Same client, same three verbs — the only difference is who runs the server.

Run:
    cd mcp-server && uv run python main.py &      # act ① target (or set MCP_SERVER_URL)
    uv run python spotlight_mcp.py

Env:  MCP_SERVER_URL   custom-server URL (default http://localhost:8788/mcp; a deployed
                       location-analyzer works too — set WORKSHOP_TOKEN if it's gated)
      GOOGLE_CLOUD_PROJECT + ADC (gcloud auth application-default login) for act ②
      — the star catalog must be seeded once:  uv run python setup/setup_star_catalog.py
"""
import asyncio
import json
import os

import google.auth
from dotenv import load_dotenv
from google.auth.transport.requests import Request as AuthRequest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
CUSTOM_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8788").rstrip("/")
CUSTOM_URL = CUSTOM_URL if CUSTOM_URL.endswith("/mcp") else CUSTOM_URL + "/mcp"
BIGQUERY_URL = "https://bigquery.googleapis.com/mcp"

# ash-dimmed red-orange stars — the VOLCANIC row (see setup/setup_star_catalog.py)
LOOKUP_SQL = (
    f"SELECT star_color, sky_condition, quadrant, biome "
    f"FROM `{PROJECT_ID}.multimodal_levels.star_catalog` "
    f"WHERE LOWER(star_color) = 'red_orange' AND LOWER(sky_condition) = 'ash_dimmed' LIMIT 1"
)


def soil_url() -> str:
    """The soil evidence from the last generate_evidence.py run (falls back to the verdant set)."""
    try:
        with open("evidence/manifest.json") as f:
            return json.load(f)["urls"]["soil"]
    except (FileNotFoundError, KeyError):
        return f"gs://{PROJECT_ID}-multimodal-levels/evidence/verdant/soil_sample.png"


def banner(title: str) -> None:
    print(f"\n{'─' * 74}\n{title}\n{'─' * 74}")


def show_result(result) -> None:
    """Print whatever shape the server returned (structured or text content)."""
    payloads = []
    if getattr(result, "structuredContent", None):
        payloads.append(result.structuredContent)      # structured wins; text parts mirror it
    else:
        for part in result.content or []:
            text = getattr(part, "text", None)
            if text:
                try:
                    payloads.append(json.loads(text))
                except json.JSONDecodeError:
                    print(text)
    for p in payloads:
        if isinstance(p, dict) and p.get("rows") and p.get("schema"):   # BigQuery result → a table
            cols = [f["name"] for f in p["schema"]["fields"]]
            print("            " + " · ".join(cols))
            for row in p["rows"]:
                print("            " + " · ".join(c.get("v", "") for c in row["f"]))
        else:
            print(json.dumps(p, indent=2, ensure_ascii=False))


async def spotlight(name: str, url: str, headers: dict, tool: str, args: dict) -> None:
    banner(f"{name}\n{url}")
    async with streamablehttp_client(url, headers=headers) as (read, write, _sid):
        async with ClientSession(read, write) as session:
            info = await session.initialize()                       # ① the handshake
            server = getattr(info, "serverInfo", None)
            print(f"initialize  → {getattr(server, 'name', '?')} v{getattr(server, 'version', '?')}")

            tools = await session.list_tools()                      # ② discovery
            print(f"tools/list  → {[t.name for t in tools.tools]}")

            print(f"tools/call  → {tool}({json.dumps(args)[:90]}…)")  # ③ invocation
            result = await session.call_tool(tool, arguments=args)
            show_result(result)


async def main() -> None:
    # ── act ① · the server YOU wrote ─────────────────────────────────────────
    custom_headers = {}
    if os.environ.get("WORKSHOP_TOKEN"):
        custom_headers["X-WBH-Token"] = os.environ["WORKSHOP_TOKEN"]
    await spotlight(
        "ACT ① · custom FastMCP — you authored this server (mcp-server/main.py)",
        CUSTOM_URL, custom_headers,
        "analyze_geological", {"image_url": soil_url()},
    )

    # ── act ② · the server GOOGLE runs ───────────────────────────────────────
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/bigquery"])
    creds.refresh(AuthRequest())
    await spotlight(
        "ACT ② · Google-managed BigQuery MCP — zero server code, just OAuth",
        BIGQUERY_URL, {"Authorization": f"Bearer {creds.token}"},
        "execute_sql_readonly", {"projectId": PROJECT_ID, "query": LOOKUP_SQL},
    )

    banner("same protocol, same three verbs — the only difference is who runs the server")


if __name__ == "__main__":
    asyncio.run(main())
