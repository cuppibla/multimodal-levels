"""Level 6 · Recall — the rescue-ops agent with REAL long-term memory.

Two kinds of knowing (talk: "two kinds of memory, and they don't live in the same place"):

  EXACT facts   — a value you look up (callsign, an error code, a date).
                  → durable `user:` STATE on VertexAiSessionService. Written the moment
                    the user says it, via the save_exact_fact tool. Looked up exactly.

  PATTERNS      — meaning built over time ("freezes up at long checklists").
                  → Vertex AI MEMORY BANK. Written by generate (Gemini curates the session
                    into consolidated facts), read back by similarity.

READ path  = PreloadMemoryTool() — ADK retrieves this user's memories before the model
             runs and injects them into the prompt.
WRITE path = memory_service.add_session_to_memory(session) — fired when a session ends
             (chat.py flushes explicitly; a long-running app can do it in an
             after_agent_callback as a background task instead).
"""
from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool


# ── EXACT facts: structured, written the moment they're said, looked up exactly ──────────
def save_exact_fact(key: str, value: str, tool_context: ToolContext) -> dict:
    """Saves one exact, look-up-able fact about the operator (a value, not a vibe).

    Args:
        key: Short snake_case label, e.g. "callsign", "recycler_error_code", "pickup_date".
        value: The exact value to store.

    Returns:
        dict with status and the stored key.
    """
    tool_context.state[f"user:{key}"] = value  # user: prefix → persists across sessions
    return {"status": "saved", "key": key, "value": value}


def get_exact_facts(tool_context: ToolContext) -> dict:
    """Returns every exact fact stored about this operator (their profile of look-up values).

    Returns:
        dict mapping each stored key to its exact value.
    """
    facts = {k.removeprefix("user:"): v for k, v in tool_context.state.to_dict().items()
             if k.startswith("user:")}
    return {"status": "success", "facts": facts or {}}


root_agent = Agent(
    name="rescue_ops",
    model="gemini-2.5-flash",
    description="Rescue-mission operations AI that remembers each survivor across sessions.",
    instruction=(
        "You are Rescue Ops, the mission AI supporting a stranded survivor over many "
        "sessions. Be warm, terse, and practical.\n"
        "MEMORY DISCIPLINE — route each fact to the store that fits its shape:\n"
        "· When the user states an EXACT value (their callsign, an error code, a date, a "
        "  quantity, a name), immediately call save_exact_fact — you want the value back "
        "  verbatim later, not something 'similar' to it.\n"
        "· Soft traits and preferences (how they like to be briefed, what stresses them, "
        "  their situation) need NO tool — the memory service curates those from the "
        "  conversation automatically when the session is saved.\n"
        "· When asked what you know about the operator, call get_exact_facts for the "
        "  looked-up values AND use any recalled memories in your context for the rest — "
        "  and say which is which.\n"
        "If past-conversation memories appear in your context, greet the user personally "
        "and apply what you know without being asked."
    ),
    tools=[
        PreloadMemoryTool(),               # READ — retrieves + injects this user's memories
        FunctionTool(save_exact_fact),
        FunctionTool(get_exact_facts),
    ],
)
