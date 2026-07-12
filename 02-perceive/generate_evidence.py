"""Generate the crash-site evidence the crew analyzes — REAL multimodal artifacts on GCS.

  · soil + star-field IMAGES — one chat session (Level 1's consistency lesson, reused:
    a self-consistent site, so honest specialists tend to agree)
  · flora VIDEO — Veo, with NATIVE AUDIO (wind, ice crackle, insect calls — the audio
    signatures the botanical analyst listens for)
  · uploads all three to Cloud Storage → gs:// URLs → evidence/manifest.json

Run:   uv run python generate_evidence.py --biome verdant
"""
import argparse
import io
import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.cloud import storage
from google.genai import types
from PIL import Image

load_dotenv()

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
VEO_CANDIDATES = ([os.environ["VEO_MODEL"]] if os.getenv("VEO_MODEL")
                  else ["veo-3.1-generate-preview", "veo-3.0-generate-001"])
BUCKET = os.getenv("GCS_BUCKET", f"{PROJECT_ID}-multimodal-levels")

# One self-consistent crash site per biome — visuals + the AUDIO the video must carry.
BIOMES = {
    "cryo": {"x": 25, "y": 75, "soil": "pale blue-grey frozen regolith crusted with white frost and ice crystals",
             "stars": "sharp cold blue-white stars over a glacial horizon, faint pale-blue aurora",
             "flora": "a frost-dusted blue-green succulent trembling in icy wind on a frozen tundra",
             "audio": "howling arctic wind, brittle ice crackling underfoot"},
    "volcanic": {"x": 75, "y": 75, "soil": "black basaltic rock and grey ash with glowing orange lava cracks",
                 "stars": "stars dimmed by drifting ash, deep red-orange glow on the horizon",
                 "flora": "a charred dark-red leathery plant near a lava flow, embers drifting past",
                 "audio": "low volcanic rumble, hissing steam vents, crackling embers"},
    "verdant": {"x": 25, "y": 25, "soil": "rich dark loam threaded with green moss and fine white root hairs",
                "stars": "warm yellow stars glimpsed through a jungle canopy, faint green airglow",
                "flora": "a lush alien fern with dew drops swaying gently in a humid jungle breeze",
                "audio": "gentle humid breeze, chirping alien insects, distant birdsong, dripping water"},
    "arid": {"x": 75, "y": 25, "soil": "fine red-orange desert sand and cracked dry clay flakes, bone dry",
             "stars": "a brilliant dense white starfield over desert dunes, crystal-clear dry air",
             "flora": "a lone pale spiny succulent on cracked red earth shimmering in heat haze",
             "audio": "dry desert wind, faint sand hiss, deep silence between gusts"},
}


_image_client: genai.Client | None = None


def client() -> genai.Client:
    global _image_client  # keep one live client — per-call clients can be GC-closed mid-chat
    if _image_client is None:
        _image_client = genai.Client(vertexai=True, project=PROJECT_ID,
                                     location=os.getenv("GEMINI_IMAGE_LOCATION", "global"))
    return _image_client


def veo_client() -> genai.Client:
    return genai.Client(vertexai=True, project=PROJECT_ID,
                        location=os.getenv("VEO_LOCATION", "us-central1"))


def save_image(response, path: str) -> None:
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            Image.open(io.BytesIO(part.inline_data.data)).save(path)
            return
    raise RuntimeError(f"no image in response for {path}")


def generate_images(biome: dict) -> None:
    """ONE chat session → a self-consistent site (soil + stars agree about the world)."""
    chat = client().chats.create(
        model=IMAGE_MODEL,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    print("  soil image (turn 1) …")
    save_image(chat.send_message(
        f"Extreme macro top-down photo of an alien SOIL sample on a neutral tray: {biome['soil']}. "
        f"Scientific flat-lay, photorealistic."), "evidence/soil_sample.png")
    print("  star field (turn 2, same session — same world) …")
    save_image(chat.send_message(
        f"Now the night sky above that SAME crash site: {biome['stars']}. Photorealistic, no ground clutter."),
        "evidence/star_field.png")


def generate_video(biome: dict) -> None:
    """Veo — native audio + video together. The botanical analyst LISTENS to this."""
    c = veo_client()
    prompt = (f"Handheld 4-second field recording at an alien crash site: {biome['flora']}. "
              f"Ambient sound: {biome['audio']}. Photorealistic, slight camera shake, natural light.")
    operation = None
    for model in VEO_CANDIDATES:
        print(f"  flora video · {model} …")
        try:
            operation = c.models.generate_videos(
                model=model, prompt=prompt,
                config=types.GenerateVideosConfig(aspect_ratio="16:9", resolution="720p", duration_seconds=4))
            break
        except Exception as e:  # noqa: BLE001
            if "404" in str(e):
                print("    (not on this project — next)")
                continue
            raise
    if operation is None:
        raise SystemExit("  ✗ no Veo model available on this project")
    waited = 0
    while not operation.done:
        time.sleep(10)
        waited += 10
        operation = c.operations.get(operation)
        print(f"    …{waited}s")
    operation.response.generated_videos[0].video.save("evidence/flora_recording.mp4")
    print("    ✓ evidence/flora_recording.mp4 (native audio)")


def upload(biome_id: str) -> dict:
    sc = storage.Client(project=PROJECT_ID)
    try:
        bucket = sc.get_bucket(BUCKET)
    except Exception:  # noqa: BLE001
        print(f"  creating bucket gs://{BUCKET} …")
        bucket = sc.create_bucket(BUCKET, location="US")
    urls = {}
    for key, fname in (("soil", "soil_sample.png"), ("flora", "flora_recording.mp4"), ("stars", "star_field.png")):
        blob = bucket.blob(f"evidence/{biome_id}/{fname}")
        blob.upload_from_filename(f"evidence/{fname}")
        urls[key] = f"gs://{BUCKET}/evidence/{biome_id}/{fname}"
        print(f"  ↑ {urls[key]}")
    return urls


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--biome", default="verdant", choices=list(BIOMES))
    args = ap.parse_args()
    biome = BIOMES[args.biome]

    os.makedirs("evidence", exist_ok=True)
    print(f"\n  crash site: {args.biome.upper()}  (truth the agents never see: x={biome['x']}, y={biome['y']})\n")
    generate_images(biome)
    generate_video(biome)
    urls = upload(args.biome)

    manifest = {"biome_generated": args.biome.upper(), "x": biome["x"], "y": biome["y"], "urls": urls}
    with open("evidence/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print("\n  ✓ evidence/manifest.json — now run the mission:  uv run python run_mission.py\n")
