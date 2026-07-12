# Level 1 · Express — Identity & Generation

> Output is a modality too. The app doesn't just describe the world — it **creates**, and puts *you* on the map.

Real, runnable code for every beat of the session (deck: *Way Back Home · D1·S1 — Express*):

| Slide beat | Code | The one idea |
|---|---|---|
| ① Output is a modality too | [`generator.py`](generator.py) | one model emits text **and** image in a single call (`response_modalities=["TEXT","IMAGE"]`) |
| ② Generation is a conversation | [`generator.py`](generator.py) | two stateless calls = two strangers; **one chat session** = the same explorer (in-context conditioning, not a seed) |
| ③ Structure makes it repeatable | [`generator.py`](generator.py) | the 4-layer prompt — Anchor / Style-lock / Constraints / Consistency; user input only ever touches the Anchor |
| ⑤ Session · State · Callback | [`agent/agent.py`](agent/agent.py) | the **ADK consistency engine**: identity locked in `state` by a `before_agent_callback`, the ref image pinned in state, every tool call re-applies it |
| ⑥ Image now, video later | [`video.py`](video.py) | Veo returns a **long-running operation** — a ticket, not a file; you poll `operation.done` |
| ⑦ Models create, code judges | [`verify.py`](verify.py) | probabilistic creation, **deterministic verification** — the gate is code, never the model's opinion |

## Run it locally

```bash
cp .env.example .env          # set GOOGLE_CLOUD_PROJECT (Vertex/ADC) or GOOGLE_API_KEY
uv sync

# ② the keystone — portrait → icon in ONE chat session (same person)
uv run python generator.py
uv run python generator.py --naive        # the problem: two stateless calls → two strangers
uv run python generator.py --anchor "a cheerful botanist with round glasses"

# ⑤ the ADK consistency engine — different scenes, one face
uv run python run_agent.py                # or interactively:  uv run adk run agent  /  uv run adk web

# ⑥ async video — a ticket, not a file (Veo, ~1 min, billed)
uv run python video.py

# ⑦ the deterministic gate
uv run python verify.py
```

Outputs land in `outputs/`. Open `naive-1.png` vs `naive-2.png` (drift), then `portrait.png` vs `icon.png` (matched), then `agent_01.png` vs `agent_02.png` (different scenes, same face — that's state + callback at work).

## The consistency ladder (slide ④ — pick the lightest that holds)

1. **Prompt** — the 4-layer structure *(lightest)*
2. **Chat session** — in-context conditioning ← `generator.py`, most demos
3. **Reference images** — 4–5 refs pinned per call ← `agent/agent.py` pins the first render in state and re-feeds it
4. **Fine-tune / LoRA** — bake it into the weights *(heaviest)*

## Model IDs move

`gemini-2.5-flash-image` (Nano Banana) sunsets Oct 2026 → set `GEMINI_IMAGE_MODEL=gemini-3.1-flash-image` (speed · 4 refs) or `gemini-3-pro-image` (pro · 5 refs). **Same API, same session, same `response_modalities` — same pattern, new ID.**
