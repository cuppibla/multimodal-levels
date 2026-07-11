# Multimodal Levels

Hands-on building blocks for **multimodal + agentic apps on Gemini** — one concept per folder, as small, standalone, **runnable** code you can read, run, deploy, and lift straight into a talk.

Each folder is the real mechanism with the demo scaffolding stripped away, so there's nothing flashy hiding the ten lines that actually matter. (Distilled from the [Way Back Home](https://github.com/cuppibla/multimodal-production-system) teaching app — the folders below map to its realms.)

## Levels

| Folder | App realm | The one idea | Runs |
|--------|-----------|--------------|------|
| [`01-beacon/`](01-beacon/) | Realm 01 · The Beacon | a prompt has 4 layers (only 1 is the user's); identity consistency is a **session**, not a seed | ✅ |
| [`02-perceive/`](02-perceive/) | Realm 02 · The Crew | a specialist = one model + one lens + one modality; it sees two ways (read + measure); specialists fan out in parallel | ✅ |
| [`05-live/`](05-live/) | Realm 05 · Going Live | "Live" = an open session streaming events both ways — audio out, transcript, a live tool call | ✅ |
| [`06-memory/`](06-memory/) | Realm 06 · Remember Me | durable memory = a write/read loop (extract facts → recall by meaning) around a plain store | ✅ |

_(Realms 3, 4, 7, 8 are the NVIDIA-owned stack — not part of this teaching cut.)_

Each folder is its own package: `cd` in, `npm install`, run. No shared build, no monorepo tooling — copy a folder out and it still works.

## Running any level

```bash
cd 02-perceive
cp .env.example .env      # add a Gemini key OR use your own Vertex project
npm install
npm run roster           # start here — no API call, just the idea
```

Everything runs on **your** Gemini quota (an AI Studio key, or your GCP project via ADC) — same no-lock-in choice as the app.
