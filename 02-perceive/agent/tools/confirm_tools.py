"""The deterministic gate — the model proposes, CODE disposes.

The crew's biome claim is verified against ground truth the model never saw (the
coordinates in the evidence manifest, hydrated into state by the callback). Never gate
progress on an LLM grading itself.
"""
import json
import os

from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

QUADRANT_BIOME = {"NW": "CRYO", "NE": "VOLCANIC", "SW": "VERDANT", "SE": "ARID"}


def _quadrant(x: float, y: float) -> str:
    return ("N" if y >= 50 else "S") + ("W" if x < 50 else "E")


def confirm_location(biome: str, tool_context: ToolContext) -> dict:
    """Confirms the analyzed biome against the crash coordinates and activates the beacon.

    Args:
        biome: The crew's final biome classification (CRYO, VOLCANIC, VERDANT, or ARID).

    Returns:
        dict with success flag, the verified quadrant/biome, and a status message.
    """
    x = float(tool_context.state.get("x", 0))
    y = float(tool_context.state.get("y", 0))
    actual_quadrant = _quadrant(x, y)
    actual_biome = QUADRANT_BIOME[actual_quadrant]

    claimed = biome.upper().strip()
    if claimed != actual_biome:
        return {
            "success": False,
            "message": (f"LOCATION MISMATCH — crew claimed {claimed}, but coordinates "
                        f"({x:.0f},{y:.0f}) sit in {actual_quadrant} = {actual_biome}. "
                        f"Re-examine the evidence."),
        }

    os.makedirs("outputs", exist_ok=True)  # the side effect a backend PATCH would do
    with open("outputs/beacon.json", "w") as f:
        json.dump({"beacon": "ACTIVE", "biome": actual_biome,
                   "quadrant": actual_quadrant, "x": x, "y": y}, f, indent=2)

    return {"success": True, "quadrant": actual_quadrant, "biome": actual_biome,
            "message": f"BEACON ACTIVATED — {actual_biome} · quadrant {actual_quadrant} · rescue inbound."}


confirm_location_tool = FunctionTool(confirm_location)
