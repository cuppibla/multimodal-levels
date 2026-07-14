# Level 5 · Live — the NOVA voice console

> Eyes and ears on the craft. A real bidirectional voice app: **speak to NOVA, she speaks back** — and she watches the camera for the neural-sync handshake.

![architecture](diagrams/architecture.svg)

**▶ Try it live:** https://nova-live-680476413759.us-central1.run.app — open, INITIATE NEURAL SYNC, allow mic+camera, hold up fingers.

A standalone live-voice web app:

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

## 🧭 Run it locally — step by step

Part 1 of the tutorial; Part 2 (deploying it, three ways) is the **🚀 Ship it** section below.

**Step 0 — prerequisites.** A GCP project with billing + ADC
(`gcloud auth application-default login`), Vertex AI API enabled, Node 20+, and a mic + camera.

**Step 1 — install and build the SPA (one-time).**

```bash
# copy the env template, then edit it: set GOOGLE_CLOUD_PROJECT
cp .env.example .env
uv sync
cd frontend && npm install && npm run build && cd ..
```

> **What to expect:** `frontend/dist/` appears — the built console the backend will serve.

**Step 2 — start the backend (SPA + WebSocket bridge, one origin).**

```bash
# → http://localhost:8500 (change the number to use a different port)
PORT=8500 uv run --directory backend python main.py
```

> **What to expect:** a uvicorn line on :8500. One process now serves the UI AND the `/ws`
> bridge — the browser never talks to Gemini directly (credentials stay server-side; that's
> the whole point of the bridge).

**Step 3 — prove the stream.** Open **http://localhost:8500**, click **▶ OPEN LIVE CHANNEL**,
allow mic + camera, then run the three checks:

| Do this | What to expect |
|---|---|
| talk | NOVA answers in **voice** — the orb pulses with her actual output spectrum |
| **hold up 1–5 fingers** | she calls the `report_digit` tool server-side; the biometric badge lights; she confirms out loud |
| **speak over her** | her playback cuts **instantly** (client RMS barge-in at 0.012; Gemini also detects it server-side) |

All three green = the full contract works: mic 16 kHz up · voice 24 kHz down · interruption
both ways. These are exactly what you'll re-check after deploying (Ship it, step A3).

Frontend dev loop: `cd frontend && npm run dev` → http://localhost:5510 (proxies `/ws` + `/api` to :8500).

**Troubleshooting:**

| Symptom | Fix |
|---|---|
| nothing on http://localhost:8500 | run Step 2 from `05-live/` — its startup line prints the URL to open. `Address already in use` → rerun with `PORT=8600`. A `frontend/dist` error → do Step 1's build first |
| silence after OPEN LIVE CHANNEL | mic permission denied, or `PERMISSION_DENIED: aiplatform` in the backend log (redo Step 0 auth) |
| chipmunk / slow-motion voice | a sample-rate got changed — mic path must be 16 kHz, playback 24 kHz |
| finger badge never lights | camera permission, or the camera preview is black (another app holds it) |

## 🚀 Ship it — deploying a stream is not deploying a request

> The deep tutorial behind the **⌁ Launch Bay** in the Way Back Home realm. The deployed
> service you can try at the top of this README came from exactly these commands.

The usual serverless deal — short stateless requests, CPU only while handling one, scale to
zero — is exactly what a live voice session is **not**: it's ONE connection that stays open
for an hour, with audio flowing both ways the whole time. Deploying this app = flipping those
defaults, one flag at a time.

### The architecture you're shipping (30 seconds)

```
browser ──(mic 16 kHz PCM · camera JPEG)──►  FastAPI /ws  ──►  ADK run_live ──► Gemini Live
        ◄──(voice 24 kHz PCM · transcripts · ⚡tool calls)──┘   (native audio)
```

One container = the built SPA **and** the WebSocket bridge, served from **one origin**. Why a
bridge server at all? **Credentials.** The browser never holds Google credentials — it only
speaks WS to *you*; the backend authenticates to Vertex via ADC. And why one origin? The SPA
connects to `wss://same-host/ws` — no CORS, no origin allowlists, nothing to misconfigure.

### Path A — single container on Cloud Run (the way it's actually deployed)

**A1 · Deploy** (from `05-live/` — the [`Dockerfile`](Dockerfile) builds the SPA, then serves
it + `/ws` from FastAPI):

```bash
gcloud run deploy nova-live --source . --region us-central1 --allow-unauthenticated \
  --no-cpu-throttling --timeout 3600 --memory 1Gi
```

**Flag by flag — remove any one of these and watch what breaks:**

| Flag | Without it |
|---|---|
| `--no-cpu-throttling` | Cloud Run parks the CPU between *requests* — but your "request" is a live stream, so the 24 kHz playback stutters, then dies. This flag = "bill me for CPU continuously while a connection is open". |
| `--timeout 3600` | the default request timeout kills the WebSocket mid-conversation. 3600s = an hour-long session may live that long |
| `--memory 1Gi` | audio buffers are per-connection; concurrent streams blow the 512Mi default |
| *(optional)* `--min-instances 1` | first visitor after idle eats a cold start — seconds of dead air on INITIATE NEURAL SYNC. Costs real money; worth it for demos, not for hobby |

**A2 · Grant Vertex access** (deployed code = service account, not you):

```bash
PROJECT=$(gcloud config get-value project)
SA=$(gcloud run services describe nova-live --region us-central1 --format 'value(spec.template.spec.serviceAccountName)')
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/aiplatform.user
```

**A3 · Smoke it** — open the URL, **▶ OPEN LIVE CHANNEL**, allow mic + camera, talk. Hold up
fingers (the `report_digit` tool fires server-side). Speak over her — playback must cut
instantly (barge-in). If all three work, the stream survived deployment.

**A4 · Sizing note.** Concurrency here = **concurrent live sessions per instance**, not
requests/sec. Each session holds memory and a Gemini Live connection. Default Vertex quota
allows ~1000 concurrent bidi streams per region — your bottleneck is usually quota, then
memory. Scale out with `--max-instances`, not up.

### Path B — split: SPA on a CDN, stream backend on Cloud Run

Right when real product traffic arrives: static assets are cheap and global on a CDN; the
backend scales on *streams only*.

```bash
cd frontend && npm run build
# SPA → CDN (or any static host)
firebase deploy --only hosting

# WS backend, same flags as A
gcloud run deploy nova-ws --source . --region us-central1 --allow-unauthenticated \
  --no-cpu-throttling --timeout 3600 --memory 1Gi
```

The cost you take on: the SPA now connects **cross-origin** — you own the `wss://` URL config
in the frontend and CORS/origin checks in FastAPI. That's the trade: global static + focused
stream scaling, in exchange for owning origin plumbing that Path A made disappear.

### Path C — GKE

Right when you need regional pinning, custom autoscaling on concurrent-stream count, or the
org already lives on Kubernetes. Long-lived WS on GKE needs the same thinking (no CPU
throttling by default — you own requests/limits instead) plus BackendConfig timeout raises on
the load balancer. Overkill for this workshop — but the flags above are the checklist you'd
port.

### Troubleshooting

| Symptom | Cause → fix |
|---|---|
| voice cuts out after ~5 min | missing `--timeout 3600` (default request timeout hit) |
| audio stutters / robotic under load | missing `--no-cpu-throttling`, or memory pressure → `--memory 1Gi`+ |
| `PERMISSION_DENIED: aiplatform` in logs | service account lacks `roles/aiplatform.user` (A2) |
| first sync after idle takes seconds | cold start → `--min-instances 1` |
| works locally, `wss://` fails deployed | mixed origin — Path A serves SPA+WS from one origin; if you split (Path B), point the frontend at the backend's `wss://` URL explicitly |

## The contract worth memorizing

- **IN:** `audio/pcm;rate=16000` (mono s16le, ~50 ms chunks, binary WS frames) · JPEG frames via `{type:"image"}` JSON
- **OUT:** 24 kHz PCM in `inlineData` parts + input/output transcriptions + `interrupted` + `turnComplete`
- The **whole ADK event** is forwarded as JSON — the browser just picks out what it needs.
