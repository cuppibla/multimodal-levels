"""Level 5 · Live — the WebSocket bridge:  browser ⇄ THIS server ⇄ Gemini Live (ADK run_live).

The browser never talks to Gemini — credentials stay here. One FastAPI service carries
the REST health check, the live WebSocket, AND the built frontend (same origin → wss://
just works on Cloud Run).

Audio contract:  mic IN = 16 kHz mono s16le PCM (binary WS frames) · voice OUT = 24 kHz PCM.

Run:   uv run python main.py     → http://localhost:8500
"""
import asyncio
import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from google.adk.agents.live_request_queue import LiveRequestQueue  # noqa: E402
from google.adk.agents.run_config import RunConfig, StreamingMode  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from agent.agent import root_agent  # noqa: E402

APP_NAME = "nova-live"
PORT = int(os.getenv("PORT", 8500))

app = FastAPI()
session_service = InMemorySessionService()  # live audio: keep sessions in-process (latency)
runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "model": root_agent.model}


@app.websocket("/ws/{user_id}/{session_id}")
async def live_ws(websocket: WebSocket, user_id: str, session_id: str) -> None:
    await websocket.accept()

    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],                            # native audio out
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        session_resumption=types.SessionResumptionConfig(),
        proactivity=types.ProactivityConfig(proactive_audio=True),
    )

    if not await session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id):
        await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)

    queue = LiveRequestQueue()
    # wake NOVA so she speaks first
    queue.send_content(types.Content(role="user", parts=[types.Part(
        text="The operator just connected to the live channel. Greet them in one short sentence "
             "and invite them to begin the neural sync when ready.")]))

    async def keepalive() -> None:  # beat proxy idle-timeouts on Cloud Run
        while True:
            await asyncio.sleep(15)
            await websocket.send_text(json.dumps({"type": "ping"}))

    async def upstream() -> None:  # browser → Gemini
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect()
            if "bytes" in message and message["bytes"] is not None:  # raw mic PCM (16 kHz s16le)
                queue.send_realtime(types.Blob(mime_type="audio/pcm;rate=16000", data=message["bytes"]))
            elif "text" in message and message["text"]:
                m = json.loads(message["text"])
                if m.get("type") == "image":   # webcam frame (JPEG base64)
                    queue.send_realtime(types.Blob(mime_type=m.get("mimeType", "image/jpeg"),
                                                   data=base64.b64decode(m["data"])))
                elif m.get("type") == "text":
                    queue.send_content(types.Content(role="user", parts=[types.Part(text=str(m.get("text", "")))]))

    async def downstream() -> None:  # Gemini → browser: forward every ADK event as JSON
        async for event in runner.run_live(user_id=user_id, session_id=session_id,
                                           live_request_queue=queue, run_config=run_config):
            await websocket.send_text(event.model_dump_json(exclude_none=True, by_alias=True))

    try:
        done, pending = await asyncio.wait(
            [asyncio.create_task(upstream()), asyncio.create_task(downstream()),
             asyncio.create_task(keepalive())],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except WebSocketDisconnect:
        pass
    finally:
        queue.close()


# serve the built SPA (frontend/dist) from the same origin — mounted LAST so /api and /ws win
DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).parent.parent / "frontend" / "dist"))
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="spa")

if __name__ == "__main__":
    import uvicorn

    print(f"\n  NOVA live console → http://localhost:{PORT}  (model: {root_agent.model})\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
