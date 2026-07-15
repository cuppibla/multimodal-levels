# 🧪 Level 6 exercises — the memory ladder

Five hands-on exercises that climb from "it forgot my name between turns" to "the
agent learns its own job." **E1–E4 need no Agent Engine** — they run on local
services (InMemory / SQLite); only your own project's Gemini calls are used
(same `.env` as the level). Every claim below is checkable in your terminal —
headless, timestamped, verbatim.

| # | File | You prove | Time |
|---|---|---|---|
| **E1** | `e1_amnesia_ladder.py` | short→long term, rung by rung: session → `user:` scope → **survives a restart** | ~5 min |
| **E2** | `e2_four_kinds.py` | the cognitive taxonomy, runnable: **working · episodic · semantic · procedural** | ~5 min |
| **E3** | `e3_not_a_vector_store.py` | each store is WRONG for the other's job — adversarially, both directions | ~5 min |
| **E4** | `e4_working_memory.py` | managing the window itself: **compaction · rewind · cache** (take-home) | ~5 min |
| **E5** | `e5_the_dream.py` | **reflective memory**: trajectory → dream → lesson → a measurably better first move | ~5 min |

Then the finale on the REAL managed stack: [`../chat.py`](../chat.py) `session-a` /
`session-b` — Memory Bank + durable `user:` state on a live Agent Engine.

```bash
cd 06-memory
uv sync                                   # includes the [db] extra for E1
uv run python exercises/e1_amnesia_ladder.py
```

---

## E1 — the amnesia ladder

One probe — *"what's my callsign?"* — after four kinds of break. The agent's
check-in tool writes **two facts on purpose**: `last_topic` (no prefix) and
`user:callsign`. Watch which survives what:

| rung | break | verified result |
|---|---|---|
| 1 | same session | ✅ "Your callsign is Vega-7." |
| 2 | new session, same service | ✂️ the split: callsign ✅ (`user:` crossed over) · topic ❌ ("I don't have your last work topic on file.") |
| 3 | process restart (`InMemorySessionService` №2) | ❌ "I don't have a callsign on file for you." |
| 4 | restart + **`DatabaseSessionService`** (SQLite) | ✅ "Your callsign is Vega-7." — same agent, **one changed line** |

**The lesson:** the prefix is the *lifetime* (`temp:` turn · none session ·
`user:` this user forever · `app:` everyone), and the SessionService is the
*store*. In production rung 4's line is your Postgres, or
`VertexAiSessionService` managed.

## E2 — four kinds of knowing

The CoALA taxonomy with a probe per kind, one rescue-ops conversation:

- **working** — "what error code did I just mention?" → answered from
  `Session.events`, no store, no search. Working memory IS the context window.
- **episodic** — new session: "what happened with the recycler last time?" →
  `add_session_to_memory` + `load_memory` recall the *experience*.
- **semantic** — "how do I like to be briefed?" → a distilled *fact*
  ("one step at a time"), independent of when it was learned.
- **procedural** — static half: the instruction + tools you gave it. Learned
  half: a lesson injected into `{user:lesson?}` → *"Check the intake filter
  first. It is part of a learned procedure."* Where lessons come from is E5.

> Honesty note: locally, episodic + semantic share one `InMemoryMemoryService` —
> they differ by what you ask back. **Memory Bank actually consolidates**:
> episodes in, curated facts out (`../chat.py`).

## E3 — "you don't want close-ish"

Same mission facts into both kinds of store, then two adversarial questions:

**Direction 1 — facts rot in a semantic store.** Day 1: "supplies: 3 days".
Day 2: "supplies: 1 day". `search_memory("how many days of supplies?")` returns
**BOTH** — there is no *update* in a similarity store, only more entries.
Meanwhile `user:supplies_days` was overwritten in place: exactly `'1'`.
A balance, a date, an inventory count must never be a guess.

**Direction 2 — understanding never surfaces from an exact lookup.** *"Will she
stay calm under pressure?"* matches **no key** in the profile — but semantic
search finds *"pressure situations make her freeze"* from a log that never
contained the word "calm".

**The rule this earns:** exact & updatable → structured (`user:` state / SQL) ·
fuzzy & accumulated → semantic (Memory Bank) · raw perception → neither
(extract the meaning, store the file as an **Artifact**). Production agents run
**both, routed by shape**.

## E4 — working memory (take-home)

The opposite problem: a long chat poisons its own context window.

- **Compaction** — `EventsCompactionConfig(compaction_interval=3, overlap_size=1)`
  on the `App`: after 6 turns of shift chatter the verified session held 14 raw
  events **+ 2 compaction events** whose summaries now stand in for the folded
  spans. The log keeps everything; the model's working memory gets the summary.
- **Rewind** — `runner.rewind_async(rewind_before_invocation_id=…)`: set course
  for Alpha → "scrap that, through the debris field" → rewind → *"We are
  currently headed for waypoint Alpha."* Not edited — **unhappened** (state
  deltas roll back too).
- **Cache** — `ContextCacheConfig`, named honestly: *not memory*. Memory asks
  "what do I remember?"; cache asks "what can I **afford** to keep in mind?"

## E5 — the dream ⭐

The blog architecture (*"Anthropic gave agents Dreams — build your own on
Google Cloud"*), local and end-to-end. Verified run:

1. **Earn it** — ticket #1 ("airlock panel won't respond") resolved the hard
   way: `reboot_interface` (manual's first-line fix, fails) →
   `check_power_coupling` (root cause). The harness records a **trajectory** —
   actions + **outcome** + root cause — into `_dream_store.json`, `processed: false`.
2. **The dream** — an offline pass (in production: a **Cloud Run Job** on
   Cloud Scheduler) asks Gemini for ONE reusable lesson: *"For unresponsive
   electronic systems, first check power coupling before attempting software
   reboots…"* — embedded (`gemini-embedding-001`, 3072 dims), stored with scope
   + source, trajectory marked processed.
3. **Wake up** — ticket #2 ("cargo-bay door controls frozen", different words,
   same shape) recalls the lesson by cosine similarity (0.64) and A/Bs it:

   | | first move | tool calls |
   |---|---|---|
   | A · no lesson | `reboot_interface` | 2 |
   | B · with lesson | `check_power_coupling` | **1** |

   Same model, same tools. **It didn't learn the answer — it learned the route.**

Swap the JSON file for **Firestore** (structured docs + native vector search),
schedule the dream, and merge USER facts (Memory Bank) + JOB lessons in one
scoped recall tool — that's the production pattern; the full series is on
Medium: *"How to Build an AI Agent That Reflects"* (google-cloud).

---

*Generated files (`_e1_sessions.db`, `_dream_store.json`) are scratch output —
safe to delete. `_labkit.py` is env-loading + a turn helper, not a lesson.*
