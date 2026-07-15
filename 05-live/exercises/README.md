# 🧪 Level 5 exercises — the live-agent ladder

Four hands-on exercises that climb from "I talked to a live agent" to "I know why
production live agents stall, and how to fix it." They use the SAME model and
project setup as the main app (`../.env`) — E2–E4 run **headless**: no mic, no
browser, just timestamps and transcripts, so every claim here is checkable in
your terminal.

| # | File | You prove | Time |
|---|---|---|---|
| **E1** | `e1_adk_web/` | a live agent needs **zero frontend** — `adk web` is the bridge | ~5 min |
| **E2** | `e2_queue_lab.py` + `e2_raw_sdk.py` | the **LiveRequestQueue** contract, and what raw `google-genai` leaves you holding | ~5 min |
| **E3** | `e3_stall_clinic.py` | why a slow tool **kills the conversation** — and 3 cures, measured | ~10 min |
| **E4** | `e4_memory.py` | what a live session **remembers** — socket → session → restart → long-term | ~10 min |

Setup is the same as the main README (`.env` with your project, `uv sync`). Then:

```bash
cd 05-live
uv run python exercises/e2_queue_lab.py      # any exercise, from the level root
```

---

## E1 — NOVA in the ADK dev UI (`adk web`)

Before you build a single line of frontend, ADK will hand you one. The folder
`e1_adk_web/nova_live/` is a complete live agent — the same NOVA persona and
`report_digit` tool as the main app.

```bash
cd exercises/e1_adk_web
export SSL_CERT_FILE=$(uv run python -m certifi)   # required for voice/video in the dev UI
uv run adk web --port 8600
```

Open **http://localhost:8600**, pick `nova_live`, and:

1. **Type** to her first — normal turn-taking, watch the Events tab.
2. Press the **mic** — now you're on `run_live`: talk over her mid-sentence
   (barge-in), ask her to check `ship_status`, watch the tool fire server-side.
3. Open the **Events** tab and find what a voice turn leaves behind — you'll
   meet those same events headless in E2.

> The dev UI is doing everything `../backend/main.py` does by hand: capturing
> mic PCM, pushing it into a `LiveRequestQueue`, playing the audio events back.
> That's the whole point — see the machine before building the machine.

## E2 — the queue contract (ADK) vs a bare socket (raw SDK)

**E2a** (`e2_queue_lab.py`): two typed turns through `LiveRequestQueue`,
every event timestamped. Watch the three verbs — `send_content` (discrete
turns), `send_realtime` (what the mic would use), `close()` — and watch words
arrive as *transcription events* while the voice arrives as *PCM bytes*.

**E2b** (`e2_raw_sdk.py`): the same conversation on `client.aio.live.connect()`
— the raw API that ADK wraps. Act 1: the socket remembers your name. Act 2:
reconnect, and it never met you. **A raw live socket's memory IS the
connection.** Everything else — session history, tool execution, resumption —
is yours to build. (Or ADK's. That's the sales pitch, measured.)

## E3 — the stall clinic ⭐

The failure everyone ships: the model calls your tool mid-conversation, the tool
takes 6 seconds, the voice channel goes dead. Four variants of the same
6-second scan, two clocks each:

- **loop-freeze** — longest gap in a 50 ms heartbeat = how long your *event loop*
  (mic relay! keepalive! barge-in!) was frozen
- **dead-air** — model calls the tool → next word the user hears

Measured on `gemini-live-2.5-flash-native-audio` (your numbers will wobble ±1 s):

| variant | loop-freeze | dead-air | verdict |
|---|---|---|---|
| **A** · `def` + `time.sleep` | **6.0 s** | 6.9 s | the bug: freezes the *whole process*, not just the chat |
| **B** · `async def` + `await` | 0.05 s | **6.5 s** | half a cure: loop breathes, conversation still dead |
| **C** · callback bypass | 0.05 s | **0.6 s** | `before_tool_callback` returns an instant ack → she speaks NOW; real work finishes in the background and the result is **injected via `queue.send_content`** |
| **D** · streaming tool | 0.05 s | **0.6 s** | the ADK-native cure: an async **generator** that `yield`s progress; she narrates *during* the scan (experimental, live-only) |

```bash
uv run python exercises/e3_stall_clinic.py              # all four (~2 min)
uv run python exercises/e3_stall_clinic.py --variant c  # just the bypass
```

Two lessons we learned building this, left in on purpose:

- **`async` ≠ non-blocking conversation.** B fixes the event loop (audio keeps
  relaying) but the model still waits for the tool result before speaking. If
  you only remember one row, remember B.
- **Streaming tools need instruction discipline.** ADK immediately answers the
  model with *"running asynchronously, results pending"* and then feeds it your
  `yield`s. Tell the model to call the tool **exactly once** and voice updates
  as they arrive — without that, it re-calls the tool and echoes protocol
  messages back as arguments. Experimental means experimental; variant C is
  the production pattern today.

## E4 — what does a live conversation remember?

Same question — *"NOVA, what's my name?"* — after four kinds of break:

| Act | Break | Result | Why |
|---|---|---|---|
| 1 | hang up → call back, **same session** | ✅ remembers | `run_live` replays session events into the new socket |
| 2 | *(inspection)* what's in the session? | words: yes · audio: no | transcriptions + tool calls become events; PCM isn't kept unless you set `save_live_audio=True` |
| 3 | **process restart** (`InMemorySessionService` №2) | ❌ amnesia | *InMemory* means in memory — sessions die with the process |
| 4 | new session + `add_session_to_memory` + `load_memory` tool | ✅ remembers | end of call → memory service; next call the model *searches* past conversations |

```bash
uv run python exercises/e4_memory.py
```

The ladder, bottom to top: **socket** (E2b — dies with the connection) →
**session** (survives reconnect) → **persistent session service**
(`DatabaseSessionService` / `VertexAiSessionService` — survives restart) →
**memory service** (survives everything, searchable across sessions). Act 4
uses `InMemoryMemoryService` so the lab runs free and offline-ish; in
production you swap that one line for `VertexAiMemoryBankService` — which is
exactly [Level 6](../../06-memory), where NOVA gets her real Memory Bank.

---

*`_labkit.py` is shared lab hygiene (env loading + silencing known-cosmetic
teardown noise when a script breaks out of `run_live` mid-stream). It's not
part of any lesson.*
