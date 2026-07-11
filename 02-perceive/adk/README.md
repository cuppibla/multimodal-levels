# Level 2 · Perceive — the ADK version

The [`../src`](../src) folder shows the **primitive**: `Promise.all(map(perceive))` + a hand-written `consensus()`. This folder shows the **framework** — the exact same fan-out + vote as a real [ADK](https://adk.dev) multi-agent system.

```
3 specialists (LlmAgent, one lens each)  →  ParallelAgent (fan-out)  →  VoteAgent (deterministic tally)
```

| File | What it is |
|------|-----------|
| [`crew/agent.py`](crew/agent.py) | the 3 lens `LlmAgent`s, the `ParallelAgent`, and a custom `BaseAgent` vote |
| [`run.py`](run.py) | feed three crash-site images through the crew |

## How it maps to ADK

- **Each specialist** is an `LlmAgent` — same `model`, a different `instruction` (its lens), and its own `output_key` so its biome pick lands in `session.state`.
- **The fan-out** is `ParallelAgent(sub_agents=[geologist, botanist, astronomer])` — they run concurrently (distinct `output_key`s, no race).
- **The vote** is a custom `BaseAgent` (`VoteAgent`) whose `_run_async_impl` reads the three picks from state and tallies a majority in plain Python — *the model proposes, code disposes.*
- **Wiring** is a `SequentialAgent([ParallelAgent, VoteAgent])`: fan-out first, vote second.

That's the honest mapping the app's slides gesture at with `ParallelAgent(...)` — here it actually runs.

## Run it

```bash
cp .env.example .env         # add GOOGLE_API_KEY (AI Studio), or configure Vertex
cd .. && npm run samples -- verdant && cd adk   # draw the crash-site images once (from the TS module)

uv sync                      # installs google-adk into a local .venv
uv run python run.py         # fan-out → 3 picks → voted consensus
```

Prefer the ADK dev UI? `uv run adk web` (then open the `crew` app) or `uv run adk run crew`.
