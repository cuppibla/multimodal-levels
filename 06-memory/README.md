# Level 6 · Recall — real cross-session memory

> You save the session… you open a brand-new one… **and it already knows you.**

![architecture](diagrams/architecture.svg)

Real ADK + **Vertex AI Agent Engine** integration — no mocks. One Agent Engine instance backs both kinds of long-term memory (the "two kinds of knowing"):

| Kind | Example | Where it lives | How it's found |
|---|---|---|---|
| **Exact fact** — a value you look up | callsign `Vega-7`, error code `42` | durable `user:` state · `VertexAiSessionService` | exact match — you want *your* value, not something *similar* |
| **Pattern** — meaning built over time | "long checklists overwhelm me" | **Memory Bank** · `VertexAiMemoryBankService` | similarity — recalled by what it *means* |

| File | What it is |
|---|---|
| [`setup_engine.py`](setup_engine.py) | creates/reuses the Agent Engine — with **custom memory topics** (`survivor_context`, `comms_style`) + managed topics |
| [`agent/agent.py`](agent/agent.py) | the agent: `PreloadMemoryTool` (READ) + `save_exact_fact`/`get_exact_facts` (`user:` state) |
| [`chat.py`](chat.py) | the proof: session A → flush → **brand-new** session B recalls everything |

## The loop (talk: "the memory loop")

1. **The session is evidence, not memory.** A transcript is a recording; memory is what you *learn* from it.
2. **WRITE — generate.** `memory_service.add_session_to_memory(session)` hands the conversation to Gemini, which **curates** it: extracts durable facts per topic, merges duplicates, updates stale ones.
3. **READ — retrieve.** `PreloadMemoryTool()` similarity-searches the bank for this `user_id` before the model runs and injects the matches into the prompt.
4. Exact values skip the bank entirely — they're written to `user:` state the moment they're said.

## Run it

```bash
cp .env.example .env                    # your project; needs gcloud ADC
uv sync
uv run python setup_engine.py           # one-time — prints AGENT_ENGINE_ID → put it in .env

uv run python chat.py session-a         # tell it facts; watch Memory Bank consolidate them
uv run python chat.py session-b         # BRAND-NEW session — it already knows you
```

Verified output from a real run (session B, zero history copied):

> *"I know your callsign is **Vega-7**, and your oxygen recycler has been throwing **error code 42** — these are exact facts I have stored. I also remember from our past conversations that you find long checklists overwhelming, so you prefer to be walked through things one step at a time."*

The agent even tells you which store each memory came from — exact facts vs curated patterns. That routing is the whole lesson: **state remembers strings; Memory Bank remembers meaning.**

## The deployed service

The same agent runs as a public Cloud Run service (proof that Memory Bank needs no Agent Engine hosting):

```bash
curl -X POST https://memory-agent-680476413759.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"vega-7","text":"What do you remember about me?"}'
# → recalls the exact facts (user: state) AND the curated patterns (Memory Bank)
```

`POST /end {user_id, session_id}` flushes a finished session to the bank. Deploy your own: `gcloud run deploy memory-agent --source . …` (see [`Dockerfile`](Dockerfile)).

## Production notes

- A long-running app fires the WRITE in an `after_agent_callback` as a background task instead of an explicit flush ([gca level_2 pattern](https://github.com/gca-americas/way-back-home/tree/main/solutions/level_2)).
- You do **not** have to host the agent inside Agent Engine to use Memory Bank — Cloud Run + `VertexAiMemoryBankService` pointed at the engine works (that's how [FashionMind](https://github.com/cuppibla/fashionmind) runs).
- Live-audio caveat: voice transcripts live in `input/output_transcription`, not `content.parts` — replay them as synthetic events before flushing, or Memory Bank sees an empty session.
