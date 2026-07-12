# Level 5 · Live — the NOVA voice console

> Eyes and ears on the craft. A real bidirectional voice app: **speak to NOVA, she speaks back** — and she watches the camera for the neural-sync handshake.

A standalone live-voice web app (architecture follows [FashionMind](https://github.com/cuppibla/fashionmind) and [gca level_3](https://github.com/gca-americas/way-back-home/tree/main/solutions/level_3)):

```
browser ──(mic 16 kHz PCM · camera JPEG frames)──►  FastAPI /ws  ──►  ADK run_live ──► Gemini Live
        ◄──(voice 24 kHz PCM · transcripts · ⚡tool calls)──┘        (native audio)
```

| Piece | File | The idea |
|---|---|---|
| Live agent | [`backend/agent/agent.py`](backend/agent/agent.py) | NOVA: native-audio `Agent` + a server-side `report_digit` tool she calls when she *sees* your fingers |
| WS bridge | [`backend/main.py`](backend/main.py) | `run_live` + `LiveRequestQueue` + `RunConfig(BIDI, AUDIO, transcriptions, proactivity)` — credentials never reach the browser |
| Mic capture | [`frontend/public/pcm-processor.js`](frontend/public/pcm-processor.js) | AudioWorklet: resample → **16 kHz** Int16, 50 ms chunks, RMS speech gate |
| Voice playback | [`frontend/src/audio.js`](frontend/src/audio.js) | **24 kHz** PCM scheduled gaplessly at `nextPlayTime` |
| **Barge-in** | both | your speech onset (RMS ≥ 0.012) instantly cuts NOVA's playback; the server also forwards `interrupted` |
| Console UI | [`frontend/src/App.jsx`](frontend/src/App.jsx) | the orb, live transcript, biometric badge, camera preview |

## Run it locally

```bash
cp .env.example .env                     # your project; needs gcloud ADC
uv sync
cd frontend && npm install && npm run build && cd ..   # one-time (or use the dev proxy below)

uv run --directory backend python main.py     # → http://localhost:8500
```

Open **http://localhost:8500**, click **▶ OPEN LIVE CHANNEL**, allow mic + camera:

- talk — NOVA answers in **voice** (watch the orb pulse)
- **hold up 1–5 fingers** — she calls `report_digit` server-side, the badge lights up, and she confirms out loud
- **speak over her** — playback cuts instantly (client RMS barge-in; Gemini also detects it server-side)

Frontend dev loop: `cd frontend && npm run dev` → http://localhost:5510 (proxies `/ws` + `/api` to :8500).

## Deploy (Cloud Run)

```bash
gcloud run deploy nova-live --source . --region us-central1 --allow-unauthenticated \
  --no-cpu-throttling --timeout 3600 --memory 1Gi
```

`--no-cpu-throttling` keeps the CPU alive between requests for the audio stream; `--timeout 3600` allows hour-long WebSockets. One container serves SPA + WS from one origin, so `wss://` needs no CORS.

## The contract worth memorizing

- **IN:** `audio/pcm;rate=16000` (mono s16le, ~50 ms chunks, binary WS frames) · JPEG frames via `{type:"image"}` JSON
- **OUT:** 24 kHz PCM in `inlineData` parts + input/output transcriptions + `interrupted` + `turnComplete`
- The **whole ADK event** is forwarded as JSON — the browser just picks out what it needs.
