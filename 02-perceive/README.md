# Level 2 · Reason — the specialist crew

> One generalist can't see everything. Build a crew of specialists, run them **in parallel**, let **code** verify the answer.

A real multi-agent system (architecture follows [gca way-back-home level_1](https://github.com/gca-americas/way-back-home/tree/main/solutions/level_1)) — verified end-to-end:

```
MissionAnalysisAI (SequentialAgent)
 ├─ before_agent_callback ······· hydrates evidence URLs + coords into shared STATE
 ├─ EvidenceAnalysisCrew (ParallelAgent — true concurrent fan-out)
 │   ├─ GeologicalAnalyst ······· soil IMAGE        → custom MCP · analyze_geological
 │   ├─ BotanicalAnalyst ········ flora VIDEO+AUDIO → custom MCP · analyze_botanical
 │   └─ AstronomicalAnalyst ····· star image → local vision tool → BigQuery MCP lookup
 └─ MissionSynthesizer ·········· 2-of-3 consensus → confirm_location (deterministic gate)
```

## What makes it real

- **True multimodal evidence** — the botanist analyzes a Veo-generated **video with a native audio track** (it reported *"water dripping, insect calls"* from the soundtrack in our verification run). Evidence lives on **Cloud Storage** as `gs://` URIs; Gemini ingests it by URI inside the tools.
- **Two MCP patterns, one client wiring** (the pedagogical core):
  - [`mcp-server/`](mcp-server/) — a **custom** FastMCP server *you* author (Streamable HTTP, 2 tools), consumed via ADK `MCPToolset`.
  - the **Google-managed BigQuery MCP** (`https://bigquery.googleapis.com/mcp`) — zero server code, OAuth ADC auth; the astronomer runs `execute_sql_readonly` against a real **BigQuery** table.
- **State as the whiteboard** — the callback writes `soil_url / flora_url / stars_url / x / y` once; every sub-agent instruction reads them by `{key}` templating; analysts publish reports via `output_key` for the synthesizer.
- **Code judges** — `confirm_location` checks the crew's biome against coordinates the model never saw, and writes `outputs/beacon.json`. The gate is deterministic.

| Piece | File |
|---|---|
| Orchestration (parallel → synthesize) | [`agent/agent.py`](agent/agent.py) |
| The three specialists | [`agent/agents/`](agent/agents/) |
| Custom-MCP / BigQuery-MCP / gate tools | [`agent/tools/`](agent/tools/) |
| The custom MCP server | [`mcp-server/main.py`](mcp-server/main.py) |
| BigQuery star catalog seed | [`setup/setup_star_catalog.py`](setup/setup_star_catalog.py) |
| Evidence generator (images + Veo video → GCS) | [`generate_evidence.py`](generate_evidence.py) |

## Run it locally

```bash
cp .env.example .env                        # your project; needs gcloud ADC
uv sync

uv run python setup/setup_star_catalog.py   # ① seed the BigQuery star catalog (one-time)
cd mcp-server && uv run python main.py &    # ② start the custom MCP server → :8788/mcp
cd ..
uv run python generate_evidence.py --biome verdant   # ③ images (one chat session) + Veo video → GCS
uv run python run_mission.py                # ④ the mission: parallel crew → consensus → beacon
```

Verified run: all three specialists independently returned VERDANT (the astronomer's answer came out of BigQuery, quadrant SW), the synthesizer applied 2-of-3, and the code gate wrote `outputs/beacon.json` → **BEACON ACTIVATED**. Try `--biome volcanic` to regenerate the whole site elsewhere.

## The simpler on-ramps

- [`adk-basics/`](adk-basics/) *(if present)* / [`src/`](src/) — the original TypeScript "two ways of seeing" primitive (`read` + `measure` + `Promise.all` fan-out), still runnable with `npm install && npm run roster`. Read it first if the full system feels like a lot — it's the same shape, minus the infrastructure.
