# 🧪 Level 6 exercises — the memory ladder

**The full tutorial for these exercises lives in the [Level 6 README](../README.md)**
(section *"🧪 The exercise ladder"*) — one centralized, comprehensive walkthrough:
what each exercise proves, the verified rung-by-rung results, and the dream's
A/B receipt.

Quick reference (run from the level root, same `.env` + `uv sync` as the level —
**E1–E4 need no Agent Engine**):

| # | Run | One line |
|---|---|---|
| **E1** | `uv run python exercises/e1_amnesia_ladder.py` | session → `user:` scope → **survives a restart** |
| **E2** | `uv run python exercises/e2_four_kinds.py` | working · **episodic** · semantic · procedural, runnable |
| **E3** | `uv run python exercises/e3_not_a_vector_store.py` | facts **rot** in a vector store — proven both directions |
| **E4** | `uv run python exercises/e4_working_memory.py` | compaction · rewind · cache (take-home) |
| **E5** | `uv run python exercises/e5_the_dream.py` | trajectory → dream → lesson → **a better first move** ⭐ |

*`_labkit.py` = env loading + a turn helper, not a lesson. `_e1_sessions.db` /
`_dream_store.json` are generated scratch — safe to delete.*
