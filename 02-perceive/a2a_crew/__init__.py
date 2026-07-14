"""The A2A variant of Level 2 — the SAME crew, deployed as separate services.

One crew, two shapes:
  · agent/  — the monolith: ParallelAgent fan-out in ONE process, state as the whiteboard
  · a2a_crew/ — this package: each analyst is its OWN service behind an Agent Card; the
              dispatcher discovers them by URL and the evidence travels IN THE MESSAGE

Install the extra once:  uv sync --extra a2a
Run it:                  see README → "Ship it — one crew, two shapes".
"""
