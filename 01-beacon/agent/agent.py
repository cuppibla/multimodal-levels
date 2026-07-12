"""Level 1 · the ADK consistency engine (slide Beat 5: "State keeps every image on-model").

A chat session holds the character for ONE conversation. Your app makes MANY calls — so
park the locked identity in STATE, and let CALLBACKS + the tool re-apply it to EVERY
generation:

    session.state  ──  identity (who · the Anchor)      ← locked once by a callback
                       style    (how · the Style-lock)
                       ref_image_b64 (pin · the model sheet)  ← first render, kept forever

    before_agent_callback  →  locks identity/style into state (once)
    generate_explorer_image tool  →  re-reads state EVERY call, re-attaches the ref image
                                      → turn 5 & session 2 still match turn 1

Try it:   uv run adk run agent      # ask: "draw me waving" · "now draw me on a cliff at sunset"
          uv run adk web            # same, in the dev UI
"""
import base64
import os

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import FunctionTool, ToolContext
from google import genai
from google.genai import types

IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

# The locked identity — in the real app this comes from the user's registration (Level 0).
EXPLORER = "a cheerful young explorer with freckles and short curly hair, warm coral suit trim"
STYLE_LOCK = (
    "friendly Pixar/DreamWorks-style 3D render, full white EVA astronaut spacesuit with "
    "helmet collar ring, chest control panel and shoulder mission patch, big expressive "
    "warm eyes, soft subsurface-scattered skin, high quality"
)

_client: genai.Client | None = None


def _genai_client() -> genai.Client:
    global _client
    if _client is None:
        if os.getenv("GOOGLE_API_KEY"):
            _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        else:
            _client = genai.Client(
                vertexai=True,
                project=os.environ["GOOGLE_CLOUD_PROJECT"],
                location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
            )
    return _client


# ── the callback: lock the identity ONCE, before the agent runs ──────────────────────────
def lock_identity(callback_context: CallbackContext) -> None:
    """before_agent_callback — one source of truth, seeded into state."""
    callback_context.state.setdefault("identity", EXPLORER)   # who — the Anchor
    callback_context.state.setdefault("style", STYLE_LOCK)    # how — the Style-lock


# ── the tool: EVERY generation re-reads the locked identity from state ───────────────────
def generate_explorer_image(scene: str, tool_context: ToolContext) -> dict:
    """Generates an image of the explorer in a given scene, keeping them on-model.

    Args:
        scene: What the explorer is doing / where they are (pose, action, backdrop).

    Returns:
        dict with 'status' and the saved image 'path'.
    """
    identity = tool_context.state.get("identity", EXPLORER)
    style = tool_context.state.get("style", STYLE_LOCK)

    parts: list[types.Part] = []
    ref_b64 = tool_context.state.get("ref_image_b64")
    if ref_b64:  # the pin — re-feed the model sheet so the face can't drift
        parts.append(types.Part.from_bytes(data=base64.b64decode(ref_b64), mime_type="image/png"))
        consistency = "This is the SAME character as in the attached reference image — same face, same suit, do not redesign them. "
    else:
        consistency = ""

    parts.append(types.Part.from_text(text=(
        f"{consistency}The character is: {identity}. Style: {style}. "
        f"Scene: {scene}. Centered, high quality."
    )))

    response = _genai_client().models.generate_content(
        model=IMAGE_MODEL,
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    image_part = next(
        (p for p in response.candidates[0].content.parts if p.inline_data is not None), None
    )
    if image_part is None:
        return {"status": "error", "message": "model returned no image"}

    os.makedirs("outputs", exist_ok=True)
    n = int(tool_context.state.get("image_count", 0)) + 1
    tool_context.state["image_count"] = n
    path = f"outputs/agent_{n:02d}.png"
    with open(path, "wb") as f:
        f.write(image_part.inline_data.data)

    if not ref_b64:  # first render becomes the model sheet, parked in state for every later call
        tool_context.state["ref_image_b64"] = base64.b64encode(image_part.inline_data.data).decode()

    return {"status": "success", "path": path, "render_number": n}


root_agent = Agent(
    name="beacon_artist",
    model="gemini-2.5-flash",
    description="Renders the registered explorer into any scene, always on-model.",
    instruction=(
        "You are the Beacon Artist for the rescue mission. The registered explorer is: "
        "{identity}. Visual style: {style}. "
        "When the user asks for a picture of the explorer in any scene or pose, call "
        "generate_explorer_image with a vivid one-sentence scene description. Never "
        "redescribe or alter who the character IS — identity is locked; only the scene "
        "changes. After the tool returns, tell the user the saved path in one short line."
    ),
    tools=[FunctionTool(generate_explorer_image)],
    before_agent_callback=lock_identity,
)
