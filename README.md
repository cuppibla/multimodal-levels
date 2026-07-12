# Multimodal Levels

Real, runnable **agent systems** for multimodal + agentic apps on Gemini — one level per folder, each verified end-to-end on live Google Cloud. Distilled from the [Way Back Home](https://github.com/cuppibla/multimodal-production-system) teaching app; architectures follow the [gca way-back-home solutions](https://github.com/gca-americas/way-back-home).

| Level | The verb | What actually runs | Verified |
|---|---|---|---|
| [`01-beacon/`](01-beacon/) | **Express** — it creates | multi-turn chat-session generation (portrait→icon, one face) · the **ADK consistency engine** (state + callback + ref-image pin) · **Veo async video** (poll the ticket) · deterministic verify gate | ✅ |
| [`02-perceive/`](02-perceive/) | **Reason** — it coordinates | a full multi-agent system: **ParallelAgent** specialist crew · a **custom FastMCP server** (soil image + flora **video with audio**) · the **Google-managed BigQuery MCP** (real star-catalog lookups) · evidence on **GCS** · code-judged beacon | ✅ |
| [`05-live/`](05-live/) | **Live** — it acts in real time | the **NOVA voice console**: FastAPI + ADK `run_live`, native-audio Gemini Live, worklet mic (16 kHz) ⇄ gapless voice (24 kHz), camera frames, RMS **barge-in**, live server-side tool calls | ✅ |
| [`06-memory/`](06-memory/) | **Recall** — it remembers | **real Vertex AI Agent Engine**: Memory Bank (custom topics · generate/retrieve) + durable `user:` state — a brand-new session that already knows you | ✅ |

Every level is its own `uv` project: `cd` in, `cp .env.example .env`, `uv sync`, run. All levels run on **your** Google Cloud project via ADC (`gcloud auth application-default login`).

## The arc

1. **Express** — output is a modality too; consistency is a *session*, not a seed; hold it app-wide with state + callbacks.
2. **Reason** — one generalist can't see everything: fan out specialists in parallel, wire tools over MCP (yours *and* Google's), let code judge.
3. **Live** — stop turn-taking: one open channel, audio and vision streaming both ways, tools firing mid-sentence.
4. **Recall** — the session is evidence, not memory: curate it into a Memory Bank, route exact facts to state, and every new session starts already knowing you.
