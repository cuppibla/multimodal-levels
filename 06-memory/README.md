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

## 🧭 Run it locally — step by step

Part 1 of the tutorial; Part 2 (deploying with memory, both hosts) is the **🚀 Ship it**
section below.

**Step 0 — prerequisites.** ADC login, then copy the env template and edit it:
set `GOOGLE_CLOUD_PROJECT` (+ location `us-central1`):

```bash
gcloud auth application-default login
cp .env.example .env
uv sync
```

**Step 1 — provision the memory infrastructure (one-time, ~1 min).**

```bash
uv run python setup_engine.py
```

> **What to expect:** it prints `AGENT_ENGINE_ID=<number>` — **put it in `.env`**. You just
> created the Vertex AI Agent Engine that backs BOTH stores: durable `user:` state (exact
> facts) and Memory Bank (curated patterns), with our custom topics (`survivor_context`,
> `comms_style`). Think "created a database" — every host from here on just points at this id.

**Step 2 — session A: give it something to remember.**

```bash
uv run python chat.py session-a
```

> **What to expect:** chat normally — tell it your callsign, a device error, a preference
> ("long checklists overwhelm me"). On exit the session is flushed to Memory Bank
> (`add_session_to_memory`) and the script polls until the curated memories appear. Watch which
> store each item lands in: exact values → `user:` state, meaning → the bank.

**Step 3 — session B: the proof.**

```bash
uv run python chat.py session-b
```

> **What to expect:** a BRAND-NEW session, zero history copied — ask *"what do you remember
> about me?"* Verified output from a real run:

> *"I know your callsign is **Vega-7**, and your oxygen recycler has been throwing **error code 42** — these are exact facts I have stored. I also remember from our past conversations that you find long checklists overwhelming, so you prefer to be walked through things one step at a time."*

The agent even tells you which store each memory came from — exact facts vs curated patterns. That routing is the whole lesson: **state remembers strings; Memory Bank remembers meaning.**

## 🧪 The exercise ladder — the memory primitives, hands-on

Five exercises (in [`exercises/`](exercises/)) that climb from "it forgot my name
between turns" to "the agent learns its own job." **E1–E4 need no Agent Engine** —
they run on local services (InMemory / SQLite); only your own project's Gemini calls
are used (same `.env` as the level). Every claim below is checkable in your terminal —
headless, timestamped, verbatim.

| # | File | You prove | Time |
|---|---|---|---|
| **E1** | `exercises/e1_amnesia_ladder.py` | short→long term, rung by rung: session → `user:` scope → **survives a restart** | ~5 min |
| **E2** | `exercises/e2_four_kinds.py` | the cognitive taxonomy, runnable: **working · episodic · semantic · procedural** | ~5 min |
| **E3** | `exercises/e3_not_a_vector_store.py` | each store is WRONG for the other's job — adversarially, both directions | ~5 min |
| **E4** | `exercises/e4_working_memory.py` | managing the window itself: **compaction · rewind · cache** (take-home) | ~5 min |
| **E5** | `exercises/e5_the_dream.py` | **reflective memory**: trajectory → dream → lesson → a measurably better first move | ~5 min |

Then the finale on the REAL managed stack: [`chat.py`](chat.py) `session-a` /
`session-b` (the Run-it-locally steps above) — Memory Bank + durable `user:` state
on a live Agent Engine.

`uv sync` already includes the `[db]` extra E1 needs. Every exercise runs from
the level root the same way, e.g.:

```bash
uv run python exercises/e1_amnesia_ladder.py
```

> ✂️ Command blocks in this README are comment-free on purpose — pasting
> `# comments` into a default interactive zsh throws
> `export: not valid in this context` / `unknown file attribute` errors.

### E1 — the amnesia ladder

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

### E2 — four kinds of knowing

**The question it answers: when someone says "the agent should remember", WHICH
of the four kinds do they mean?** One rescue-ops conversation, then four probes —
each answerable only by the right kind of memory (the CoALA taxonomy, runnable).

```bash
uv run python exercises/e2_four_kinds.py
```

1. **Session A plants the experience** (error 42, fixed by a filter swap,
   "brief me one step at a time") — then **probe 1 · working**: *"what error
   code did I mention a moment ago?"* Answered with no store and no search.
   **→ what you learn:** working memory IS the context window — `Session.events`
   + state, re-rendered into the prompt every turn. Nothing was "remembered";
   it's simply still in view.
2. **Watch `💾 add_session_to_memory(A)`, then probe 2 · episodic** — a NEW
   session asks *"what happened with the recycler last time?"* and the agent
   calls `load_memory` and retells the event.
   **→ what you learn:** episodic memory is a **specific past experience**,
   reachable from a session with zero copied history — end-of-call filing plus
   mid-call search, the same two moves as Level 5's E4.
3. **Probe 3 · semantic** — *"how do I like to be briefed?"* Same store, but
   what comes back is the distilled fact ("one step at a time"), not the scene.
   **→ what you learn:** the store is one; the *kind* of knowing is in what you
   ask back. A fact outlives the episode it was learned in.
4. **Probe 4 · procedural** — session C is created with
   `state={"user:lesson": "check the intake filter BEFORE the pump"}`, the
   instruction template `{user:lesson?}` injects it, and she follows the route
   without re-deriving it.
   **→ what you learn:** procedural memory = instruction + tools (the static
   half) plus **learned lessons injected as state** (the earned half). Where
   lessons come from is E5's whole plot.

> Honesty note: locally, episodic + semantic share one `InMemoryMemoryService` —
> they differ by what you ask back. **Memory Bank actually consolidates**:
> episodes in, curated facts out (`chat.py`).

### E3 — "you don't want close-ish"

**The question it answers: SQL or vectors?** Adversarially, in both directions,
with the same mission facts in both kinds of store.

```bash
uv run python exercises/e3_not_a_vector_store.py
```

1. **Setup — the same life, recorded twice.** Two day-logs go onto the semantic
   shelf (append-only); the exact profile gets `user:supplies_days` overwritten
   in place, 3 → 1.
   **→ what you learn:** the two stores make **opposite promises** the moment
   data changes — one accumulates versions, one keeps exactly the current value.
2. **Direction 1 — ask both: "how many days of supplies?"** The semantic store
   returns **BOTH** logs; the profile returns exactly `'1'`. Then the
   quartermaster agent — given only the semantic store — is forced to answer
   "one number": read its answer against the two logs it saw.
   **→ what you learn:** there is no *update* in a similarity store, only more
   entries — whatever the model answers is an **arbitration, not a lookup**. A
   balance, a date, an inventory count must never work this way.
3. **Direction 2 — ask both: "will she stay calm under pressure?"** The profile
   lookup prints `NO KEY MATCHES`; semantic search finds *"pressure situations
   make her freeze"* from a log that never contained the word "calm".
   **→ what you learn:** a key/value profile answers only the questions you
   predicted when you designed the schema. Understanding surfaces by
   **similarity** — you can't schema your way to it.
4. **Read the verdict block** — the rule this lab earns: exact & updatable →
   structured (`user:` state / SQL) · fuzzy & accumulated → semantic (Memory
   Bank) · raw perception → neither (extract the meaning, store the file as an
   **Artifact**).
   **→ what you learn:** it's never SQL *or* vectors — production agents run
   **both, routed by the shape of the data**.

### E4 — working memory (take-home)

**The question it answers: what do you do when the problem isn't forgetting —
it's that a long chat poisons its own context window?** Three parts, one run.

```bash
uv run python exercises/e4_working_memory.py
```

1. **Part 1 · compaction.** Six turns of shift chatter, then read the count line:
   the verified session held 14 raw events **+ 2 compaction events**, and the
   printed `🗜` summary now stands in for the folded span
   (`EventsCompactionConfig(compaction_interval=3, overlap_size=1)` on the `App`).
   **→ what you learn:** the session log is an **audit trail** — it keeps every
   raw event; only the model's *working* view gets the summary. Compaction
   spends one summary to buy back a window.
2. **Part 2 · rewind.** Set course for Alpha → "scrap that, through the debris
   field" → `runner.rewind_async(rewind_before_invocation_id=…)` → ask again:
   *"We are currently headed for waypoint Alpha."*
   **→ what you learn:** the bad turn isn't edited, it's **unhappened** — state
   deltas from the rewound turns roll back too. That's the difference between
   an unsend button and a cover-up.
3. **Part 3 · cache.** Nothing to observe at lab scale — on purpose.
   **→ what you learn:** `ContextCacheConfig` is the rung that is **not
   memory**: memory asks "what do I remember?"; cache asks "what can I
   **afford** to keep in mind without re-paying every turn?" In a live voice
   loop (Level 5) it's what makes a resident persona + catalog affordable.

The closing line is the level's thesis in one sentence: **the window is a
budget, not a landfill** — fold the old, unhappen the bad, afford the big.

### E5 — the dream ⭐

**The question it answers: can an agent get *better at its job* — not just
remember its users?** The blog architecture (*"Anthropic gave agents Dreams —
build your own on Google Cloud"*), local and end-to-end.

```bash
uv run python exercises/e5_the_dream.py
```

1. **Act 1 · earn it.** Ticket #1 ("airlock panel won't respond") is resolved
   the hard way: `reboot_interface` (the manual's first-line fix — fails) →
   `check_power_coupling` (root cause). Watch what the harness records: a
   **trajectory** — actions + outcome + root cause — into `_dream_store.json`
   with `processed: false`.
   **→ what you learn:** agents don't learn from transcripts; they learn from
   **outcome-stamped action sequences**. The store isn't a diary — it's the
   dream job's work queue.
2. **Act 2 · the dream.** An offline pass finds the unprocessed trajectory and
   asks Gemini for ONE reusable lesson (*"for unresponsive electronic systems,
   check the power coupling before attempting software reboots"*), embeds it
   (`gemini-embedding-001`, 3072 dims), stores it with scope + source, and marks
   the trajectory processed.
   **→ what you learn:** reflection is a **batch job, not a chat feature** — no
   user is waiting while the agent thinks about its life. In production this
   pass is a Cloud Run Job on Cloud Scheduler.
3. **Act 3 · wake up.** Ticket #2 ("cargo-bay door controls frozen") — different
   words, same *shape* — recalls the lesson by cosine similarity (≈0.64) and
   A/Bs it, and the receipt table prints:

   | | first move | tool calls |
   |---|---|---|
   | A · no lesson | `reboot_interface` | 2 |
   | B · with lesson | `check_power_coupling` | **1** |

   **→ what you learn:** same model, same tools, measurably better first move.
   **It didn't learn the answer — it learned the route.** And the recall was by
   meaning: ticket #2 never mentions airlocks or panels.

Swap the JSON file for **Firestore** (structured docs + native vector search),
schedule the dream, and merge USER facts (Memory Bank) + JOB lessons in one
scoped recall tool — that's the production pattern; the full series is on
Medium: *"How to Build an AI Agent That Reflects"* (google-cloud).

*`exercises/_labkit.py` is env-loading + a turn helper, not a lesson. Generated
files (`_e1_sessions.db`, `_dream_store.json`) are scratch output — safe to delete.*

## 🚀 Ship it — the agent is disposable; the memory is infrastructure

> The deep tutorial behind the **⌁ Launch Bay** in the Way Back Home realm. The deployed
> `memory-agent` service below runs exactly this recipe.

The deployment insight of this level: **Memory Bank lives in Agent Engine, but the agent that
USES it can be hosted anywhere.** Deploying "with memory" is three moves — provision the
engine once, point any host at it, prove a fresh process still remembers.

### Step 1 · PROVISION — create the engine (once, like creating a database)

Copy then edit `.env` (`GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION=us-central1`),
then provision — it prints `AGENT_ENGINE_ID=…` → put that in `.env` too:

```bash
cp .env.example .env
uv sync
uv run python setup_engine.py
```

This is *infrastructure provisioning*, not deployment — the engine holds both stores
(`VertexAiSessionService` for exact `user:` facts, `VertexAiMemoryBankService` for curated
patterns), configured with our custom topics (`survivor_context`, `comms_style`). Every host
in step 2 points at THIS id. You never run this again unless you want a fresh brain.

### Step 2 · POINT — pick a host and hand it two things

Any host needs exactly two things: the **`AGENT_ENGINE_ID` env var** and **IAM permission to
reach it**. No key files — ADC everywhere.

**Host A — Cloud Run (how the live `memory-agent` service runs).** Your own HTTP surface
([`server.py`](server.py): `/chat` + the explicit `/end` flush), the [`Dockerfile`](Dockerfile)
ships agent + server:

The service authenticates as its service account, so the last two lines grant it
Vertex access:

```bash
PROJECT=$(gcloud config get-value project)

gcloud run deploy memory-agent \
  --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_LOCATION=us-central1,AGENT_ENGINE_ID=YOUR_ENGINE_ID

SA=$(gcloud run services describe memory-agent --region us-central1 --format 'value(spec.template.spec.serviceAccountName)')
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/aiplatform.user
```

Redeploy this service as often as you like — **every instance is disposable**; nothing it
remembers lives inside it. (The public demo service also honors an optional `WORKSHOP_TOKEN`
env — when set, requests need an `X-WBH-Token` header. Leave it unset for your own deploys.)

**Host B — Agent Engine hosts the agent too (least code).** Sessions, memory, AND the runtime
in one managed place:

```bash
uv run adk deploy agent_engine \
  --project $(gcloud config get-value project) \
  --region us-central1 \
  --display_name memory-agent \
  agent
```

Takes 5–10 minutes. Choose B when you don't need a custom HTTP surface; choose A when you want
your own endpoints (like `/end`) or the same host pattern as every other level in this repo.

**Host C — your laptop, pointed at the SAME engine (the stage moment).** `chat.py` session A
on your laptop, then curl the Cloud Run service as the same `user_id` — it recalls what you
told your laptop. Memory ≠ process, demonstrated in one breath.

### Step 3 · PROVE — the deterministic receipt

The reply recalls the exact facts (`user:` state) AND the curated patterns
(Memory Bank):

```bash
curl -X POST https://memory-agent-680476413759.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"vega-7","text":"What do you remember about me?"}'
```

`POST /end {user_id, session_id}` flushes a finished session to the bank (WRITE = curation:
Gemini extracts durable facts per topic, merges duplicates, updates stale ones).

The kill-test worth doing once: redeploy the service (`gcloud run deploy …` again), then re-run
the curl — **same memories**. The agent process died; the memory didn't. That's the whole
lesson.

### Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `KeyError: AGENT_ENGINE_ID` at startup | step 1 not run, or the env var didn't reach the deploy → check `--set-env-vars` |
| `PERMISSION_DENIED` reaching the engine | the *service account* lacks `roles/aiplatform.user` (step 2A) — your own ADC working locally proves nothing about the service |
| brand-new session remembers nothing | session was never flushed — call `/end` (or rely on the `after_agent_callback` pattern below) |
| exact facts recalled, patterns missing (or vice-versa) | the two stores are separate by design — `user:` state holds values, Memory Bank holds meaning; check which one you wrote to |
| `403` with `X-WBH-Token` errors | the deployed demo has `WORKSHOP_TOKEN` set — send the header, or deploy your own without it |

## Production notes

- A long-running app fires the WRITE in an `after_agent_callback` as a background task instead of an explicit flush ([gca level_2 pattern](https://github.com/gca-americas/way-back-home/tree/main/solutions/level_2)).
- You do **not** have to host the agent inside Agent Engine to use Memory Bank — Cloud Run + `VertexAiMemoryBankService` pointed at the engine works (that's how [FashionMind](https://github.com/cuppibla/fashionmind) runs).
- Live-audio caveat: voice transcripts live in `input/output_transcription`, not `content.parts` — replay them as synthetic events before flushing, or Memory Bank sees an empty session.
