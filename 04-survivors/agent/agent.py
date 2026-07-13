"""The GraphRAG router — an ADK agent that shows both retrievals, then commits to the graph's answer."""
from __future__ import annotations
import os

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .tools.graph_tools import flat_vector_search, graph_answer

MODEL = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")

root_agent = Agent(
    name="survivor_router",
    model=MODEL,
    description="Routes a rescue 'who can treat this survivor?' question to the right physician via GraphRAG.",
    instruction=(
        "You triage rescue questions of the form 'who can treat this survivor?'. ALWAYS do BOTH, in "
        "order, and show your work:\n"
        "1. Call flat_vector_search(question) — the naive similarity baseline. Report its top pick.\n"
        "2. Call graph_answer(question) — the GraphRAG walk. Report the anchor survivor it located, the "
        "typed path (each hop as `from -edge-> to`), and the physician it reaches.\n"
        "Then state the lesson plainly: flat similarity ranks by WORDS, so it can surface the wrong "
        "physician — the one whose bio merely echoes the condition. The graph follows typed edges "
        "(needs -> provided_by), so it finds the physician who can actually help, even though that "
        "physician's bio never mentions the condition. Give the graph_answer physician as THE answer."
    ),
    tools=[FunctionTool(flat_vector_search), FunctionTool(graph_answer)],
)
