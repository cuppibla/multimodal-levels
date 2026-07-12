"""MCP pattern #1 — connect to OUR custom Location Analyzer MCP server.

Both the geological and botanical analysts consume the SAME toolset (one server, two
tools) — each agent picks its tool by name from what the server advertises.
"""
import os

from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8788")

_mcp_toolset: MCPToolset | None = None


def get_location_analyzer_toolset() -> MCPToolset:
    global _mcp_toolset
    if _mcp_toolset is None:
        _mcp_toolset = MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=f"{MCP_SERVER_URL}/mcp", timeout=120,  # video analysis can take a while
            )
        )
    return _mcp_toolset
