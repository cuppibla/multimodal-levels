# 🧪 Level 5 exercises — the live-agent ladder

**The full tutorial for these exercises lives in the [Level 5 README](../README.md)**
(section *"🧪 The exercise ladder"*) — one centralized, comprehensive walkthrough:
what each exercise proves, the measured stall-clinic numbers, and the lessons
learned building them.

Quick reference (run from the level root, same `.env` + `uv sync` as the app):

| # | Run | One line |
|---|---|---|
| **E1** | `cd exercises/e1_adk_web && export SSL_CERT_FILE=$(uv run python -m certifi) && uv run adk web` | a live agent with **zero frontend** |
| **E2** | `uv run python exercises/e2_queue_lab.py` · `e2_raw_sdk.py` | the `LiveRequestQueue` contract vs a raw socket |
| **E3** | `uv run python exercises/e3_stall_clinic.py` | slow tool, two clocks, **3 measured cures** ⭐ |
| **E4** | `uv run python exercises/e4_memory.py` | what a live session remembers, four breaks |

*`_labkit.py` = env loading + teardown-noise hygiene, not a lesson.*
