"""Level 1 · Express — multi-turn image generation with a consistent identity.

THE CORE LESSON (slide: "Generation is a conversation"):
  Two independent calls with the same prompt give you TWO DIFFERENT PEOPLE — each call is
  stateless, a stranger every time. The fix is a CHAT SESSION: generate the portrait in
  turn 1, then ask for the map icon in turn 2 of the SAME chat. The model literally sees
  the portrait it just drew (in-context multimodal conditioning) — same explorer, no seed.

Run:
    uv run python generator.py                       # portrait + icon, one session
    uv run python generator.py --naive               # two stateless calls → two strangers
    uv run python generator.py --anchor "a cheerful botanist with round glasses"
"""
import argparse
import io
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

# "Output is a modality too": the SAME model emits text AND image in a single call.
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")  # Nano Banana
# NOTE (slide: "The model IDs move"): gemini-2.5-flash-image sunsets Oct 2026.
# Same API, same session, same response_modalities — set GEMINI_IMAGE_MODEL to
# gemini-3.1-flash-image (speed, 4 refs) or gemini-3-pro-image (pro, 5 refs) when available.


def client() -> genai.Client:
    if os.getenv("GOOGLE_API_KEY"):  # AI Studio path
        return genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return genai.Client(  # Vertex path (ADC) — what the workshop uses
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
    )


# ── THE 4-LAYER CONSISTENCY PROMPT (slide: "Structure makes it repeatable") ──────────────
# 1 ANCHOR       — who the character is            ← the ONLY layer user input touches
# 2 STYLE-LOCK   — the visual style that must persist
# 3 CONSTRAINTS  — format · framing · output spec (white bg: it composites onto a map)
# 4 CONSISTENCY  — "the SAME character as before"  ← lives in turn 2 (icon_prompt)
def portrait_prompt(anchor: str, suit_color: str = "warm coral") -> str:
    return (
        # 1 · ANCHOR — user words slot in as DATA ("the character is: {x}", never "generate {x}")
        f"A character portrait. The character is: {anchor}. "
        f"They wear a full detailed white EVA astronaut spacesuit with a metallic helmet "
        f"collar ring, a chest control panel with small illuminated dials, a circular "
        f"mission patch on the shoulder, and {suit_color} accent trim. "
        # 2 · STYLE-LOCK
        f"Friendly Pixar/DreamWorks-style 3D render, big expressive warm eyes, soft "
        f"subsurface-scattered skin, high quality. "
        # 3 · CONSTRAINTS — designed for where the image lands (composited onto the map)
        f"Head-and-shoulders 3/4 view, framed so the chest panel is visible, centered, "
        f"PURE WHITE background."
    )


def icon_prompt(suit_color: str = "warm coral") -> str:
    # 4 · CONSISTENCY DEMAND — shouted on purpose; the model still drifts, so we repeat.
    return (
        f"Now create a circular map icon of this SAME character. SAME face, SAME "
        f"expression, SAME {suit_color}-accented white EVA spacesuit, SAME person — do "
        f"not redesign them. Tighter head-and-shoulders crop centered in a clean circular "
        f"frame, pure white background, crisp and readable when shrunk to a 64px map "
        f"marker, 1:1 aspect, same 3D render style as the portrait."
    )


def save_image(response, path: str) -> str:
    """The extraction pattern: find the inline_data part, decode, save."""
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            Image.open(io.BytesIO(part.inline_data.data)).save(path)
            return path
    raise RuntimeError(f"no image part in response for {path}")


def generate_explorer(anchor: str, suit_color: str) -> dict:
    """THE FIX — one chat session, two turns, one face."""
    c = client()
    chat = c.chats.create(
        model=IMAGE_MODEL,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    print(f"  session open · {IMAGE_MODEL}")

    print("  turn 1 → portrait …")
    portrait = chat.send_message(portrait_prompt(anchor, suit_color))
    p_path = save_image(portrait, "outputs/portrait.png")
    print(f"    ✓ {p_path}")

    print("  turn 2 → map icon (same session — it SEES the portrait it just drew) …")
    icon = chat.send_message(icon_prompt(suit_color))
    i_path = save_image(icon, "outputs/icon.png")
    print(f"    ✓ {i_path}")

    return {"portrait_path": p_path, "icon_path": i_path}


def generate_naive(anchor: str, suit_color: str) -> dict:
    """THE PROBLEM — two independent stateless calls: two strangers."""
    c = client()
    cfg = types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
    print("  two INDEPENDENT calls, same prompt …")
    r1 = c.models.generate_content(model=IMAGE_MODEL, contents=portrait_prompt(anchor, suit_color), config=cfg)
    p1 = save_image(r1, "outputs/naive-1.png")
    print(f"    ✓ {p1}")
    r2 = c.models.generate_content(model=IMAGE_MODEL, contents=portrait_prompt(anchor, suit_color), config=cfg)
    p2 = save_image(r2, "outputs/naive-2.png")
    print(f"    ✓ {p2}")
    print("  → open them side by side: same prompt, two different people.")
    return {"naive_1": p1, "naive_2": p2}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", default="a cheerful young explorer with freckles and short curly hair")
    ap.add_argument("--suit-color", default="warm coral")
    ap.add_argument("--naive", action="store_true", help="demonstrate the drift problem instead")
    args = ap.parse_args()

    os.makedirs("outputs", exist_ok=True)
    print()
    if args.naive:
        generate_naive(args.anchor, args.suit_color)
    else:
        result = generate_explorer(args.anchor, args.suit_color)
        print(f"\n  one session, two turns, one face → {result}")
    print()
