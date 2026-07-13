"""The dispatcher — a local ADK agent that discovers a remote peer and delegates across the A2A boundary."""
from __future__ import annotations
import os

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .tools.a2a_tools import discover_agent_card, delegate

root_agent = Agent(
    name="dispatcher",
    model=os.environ.get("AGENT_MODEL", "gemini-2.5-flash"),
    description="Local dispatcher that discovers a remote agent's Card and delegates tasks across the A2A boundary.",
    instruction=(
        "You are a local dispatcher. You know NOTHING about the Architect except its URL. For any "
        "repair/engineering task from the crew:\n"
        "1. Call discover_agent_card() — read the remote Agent Card (name, skills, framework, A2A endpoint). "
        "No hardcoded interface; you learn its capabilities at runtime.\n"
        "2. Call delegate(task) — send an A2A message to that endpoint and get the answer.\n"
        "Report the discovered card, confirm the call was REMOTE (remote=true), then give the Architect's "
        "answer verbatim."
    ),
    tools=[FunctionTool(discover_agent_card), FunctionTool(delegate)],
)
