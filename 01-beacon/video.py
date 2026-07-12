"""Level 1 · Beat 6 — "Image now. Video later." Image is synchronous; video is a TICKET.

Image generation returns the pixels inline, immediately. Video (Veo) hands back a
LONG-RUNNING OPERATION — you poll it until it's done (tens of seconds). The room panics
~3 seconds in; pre-empt it: you got a ticket at the counter, not a file. It didn't fail —
it's working.

Run:
    uv run python video.py
    uv run python video.py --prompt "the explorer plants a rescue beacon on a ridge at dawn"
"""
import argparse
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Veo access differs by project — try candidates, keep the first that starts (set VEO_MODEL to pin).
VEO_CANDIDATES = (
    [os.environ["VEO_MODEL"]] if os.getenv("VEO_MODEL")
    else ["veo-3.1-generate-preview", "veo-3.0-generate-001", "veo-2.0-generate-001"]
)


def client() -> genai.Client:
    if os.getenv("GOOGLE_API_KEY"):
        return genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return genai.Client(
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        # Veo is region-served (not "global") — needs its own location setting.
        location=os.getenv("VEO_LOCATION", "us-central1"),
    )


def generate_video(prompt: str, out_path: str = "outputs/beacon_video.mp4") -> str:
    c = client()

    # THE TICKET — this returns an operation, not a video.
    operation = None
    for model in VEO_CANDIDATES:
        print(f"\n  requesting video · {model}")
        try:
            operation = c.models.generate_videos(
                model=model,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                    resolution="720p",
                    duration_seconds=4,
                ),
            )
            break
        except Exception as e:  # noqa: BLE001 — model not enabled on this project → try next
            if "404" in str(e):
                print("    (not available on this project — trying next)")
                continue
            raise
    if operation is None:
        raise SystemExit("  ✗ no Veo model available — request access or set VEO_MODEL")
    print("  → got an OPERATION (a ticket), not a file. Polling…")

    # THE POLL — ask "is it done?" until it is. This is the async pattern, verbatim.
    waited = 0
    while not operation.done:
        time.sleep(10)
        waited += 10
        operation = c.operations.get(operation)
        print(f"    …{waited}s")

    video = operation.response.generated_videos[0]
    os.makedirs("outputs", exist_ok=True)
    video.video.save(out_path)
    print(f"  ✓ {out_path}  (~4s, 720p, native audio)\n")
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--prompt",
        default=(
            "Cinematic 4-second shot: a friendly Pixar-style astronaut explorer in a white "
            "EVA suit with coral trim plants a glowing rescue beacon on an alien ridge at "
            "dawn, wind ripples the dust, warm rim light, gentle triumphant hum."
        ),
    )
    args = ap.parse_args()
    generate_video(args.prompt)
