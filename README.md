# Way Back Home — Levels

The concepts behind the [Way Back Home](https://github.com/cuppibla/multimodal-production-system) app, pulled out one per folder as **small, standalone, runnable** code you can read, run, deploy, and lift straight into a talk.

The app is the *experience*. These folders are the *substance* — each one is the real mechanism with the demo scaffolding stripped away, so there's nothing flashy hiding the ten lines that actually matter.

## Levels

| Folder | App realm | The one idea | Runs |
|--------|-----------|--------------|------|
| [`02-perceive/`](02-perceive/) | Realm 02 · Perceive | a specialist = one model + one lens + one modality; it sees two ways (read + measure); many specialists fan out in parallel | ✅ |
| `03-…` | _(next)_ | — | — |

Each folder is its own package: `cd` in, `npm install`, run. No shared build, no monorepo tooling — copy a folder out and it still works.

## Running any level

```bash
cd 02-perceive
cp .env.example .env      # add a Gemini key OR use your own Vertex project
npm install
npm run roster           # start here — no API call, just the idea
```

Everything runs on **your** Gemini quota (an AI Studio key, or your GCP project via ADC) — same no-lock-in choice as the app.
