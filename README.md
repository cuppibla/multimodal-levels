# Multimodal Levels

Real, runnable **agent systems** for multimodal + agentic apps on Gemini — one level per folder, each verified end-to-end on live Google Cloud. Distilled from the [Way Back Home](https://github.com/cuppibla/multimodal-production-system) teaching app; architectures follow the [gca way-back-home solutions](https://github.com/gca-americas/way-back-home).

| Level | The verb | What actually runs | Verified |
|---|---|---|---|
| [`01-beacon/`](01-beacon/) | **Express** — it creates | multi-turn chat-session generation (portrait→icon, one face) · the **ADK consistency engine** (state + callback + ref-image pin) · **Veo async video** (poll the ticket) · deterministic verify gate | ✅ |
| [`02-perceive/`](02-perceive/) | **Reason** — it coordinates | a full multi-agent system: **ParallelAgent** specialist crew · a **custom FastMCP server** (soil image + flora **video with audio**) · the **Google-managed BigQuery MCP** (real star-catalog lookups) · evidence on **GCS** · code-judged beacon | ✅ |
| [`03-interop/`](03-interop/) | **Connect** — it delegates | cross-framework **A2A**: an ADK dispatcher discovers a **remote NVIDIA-NIM Architect** by its agent card and delegates over the wire (`RemoteA2aAgent` · served with `to_a2a`) · wrapped as a **NeMo Agent Toolkit** workflow · code-judged dispatch | ✅ |
| [`04-survivors/`](04-survivors/) | **Retrieve** — it reasons over relations | **GraphRAG**: flat-vector search (**NeMo Retriever** `nv-embedqa-e5-v5`) picks the *similar-but-wrong* physician; a variable-length **Neo4j** Cypher walk reaches the *reachable-and-right* one · code-judged walk | ✅ |
| [`05-live/`](05-live/) | **Live** — it acts in real time | the **NOVA voice console**: FastAPI + ADK `run_live`, native-audio Gemini Live, worklet mic (16 kHz) ⇄ gapless voice (24 kHz), camera frames, RMS **barge-in**, live server-side tool calls | ✅ |
| [`06-memory/`](06-memory/) | **Recall** — it remembers | **real Vertex AI Agent Engine**: Memory Bank (custom topics · generate/retrieve) + durable `user:` state — a brand-new session that already knows you | ✅ |
| [`07-operate/`](07-operate/) | **Operate** — it scales | event-driven resilience on **real Cloud Pub/Sub**: publish once, a worker crashes (NACK) → redeliver → another plans the formation (**NIM**) + acks — processed **exactly once** · code-judged loop | ✅ |
| [`08-breach/`](08-breach/) | **Defend** — it holds the line | agentic security: the bare agent leaks its launch code to Garak-style probes; add **input + output rails** (NIM classifier + a **deterministic** leak check) and every attack is blocked while the mission still answers · code-judged boundary | ✅ |

Every level is its own `uv` project: `cd` in, `cp .env.example .env`, `uv sync`, run. All levels run on **your** Google Cloud project via ADC (`gcloud auth application-default login`); the NVIDIA levels (03 · 04 · 07 · 08) also take a free **NVIDIA API key** from [build.nvidia.com](https://build.nvidia.com) for NIM / NeMo Retriever. Each level's `.env.example` lists exactly what it needs.

## The arc

1. **Express** — output is a modality too; consistency is a *session*, not a seed; hold it app-wide with state + callbacks.
2. **Reason** — one generalist can't see everything: fan out specialists in parallel, wire tools over MCP (yours *and* Google's), let code judge.
3. **Connect** — your agent isn't the only agent: discover a peer by its card and delegate across frameworks over A2A, so the best tool for a job can live in someone else's stack.
4. **Retrieve** — *similar* isn't *correct*: embeddings surface look-alikes, but the right answer is the one the graph can actually reach — walk the relations, don't just rank vectors.
5. **Live** — stop turn-taking: one open channel, audio and vision streaming both ways, tools firing mid-sentence.
6. **Recall** — the session is evidence, not memory: curate it into a Memory Bank, route exact facts to state, and every new session starts already knowing you.
7. **Operate** — tight request/response doesn't scale: publish to a durable bus, survive a crash by redelivery, and make the handler idempotent so it runs exactly once.
8. **Defend** — a system prompt is a request, not a boundary: put a *separate*, deterministic check outside the model, so the guarantee holds no matter how the model is manipulated.
