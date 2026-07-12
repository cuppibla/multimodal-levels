"""Rescue Ops as an HTTP service — Memory Bank from Cloud Run (no Agent Engine hosting).

The point this deployment proves (talk, slide 15): "you do NOT have to run your agent
inside Agent Engine to use Memory Bank." The agent lives on Cloud Run; both memory
services just point at the engine.

    POST /chat {"user_id": "...", "text": "...", "session_id": null|"..."}
      → {"reply", "session_id"}          # pass session_id back to continue a session
    POST /end  {"user_id": "...", "session_id": "..."}
      → flushes the session to Memory Bank (generate)

Run locally:   uv run python server.py       → http://localhost:8600
"""
import os

from dotenv import load_dotenv

load_dotenv()

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from google.adk.memory import VertexAiMemoryBankService  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import VertexAiSessionService  # noqa: E402
from google.genai import types  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from agent.agent import root_agent  # noqa: E402

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.environ["AGENT_ENGINE_ID"]
APP_NAME = AGENT_ENGINE_ID

session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID)
memory_service = VertexAiMemoryBankService(project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID)
runner = Runner(agent=root_agent, app_name=APP_NAME,
                session_service=session_service, memory_service=memory_service)

app = FastAPI(title="Rescue Ops — memory agent")


class ChatIn(BaseModel):
    user_id: str = "vega-7"
    text: str
    session_id: str | None = None


class EndIn(BaseModel):
    user_id: str = "vega-7"
    session_id: str


@app.get("/health")  # NOTE: /healthz is reserved by Google Front End on run.app
async def health() -> dict:
    return {"ok": True, "engine": AGENT_ENGINE_ID}


@app.post("/chat")
async def chat(body: ChatIn) -> dict:
    session_id = body.session_id
    if not session_id:
        session = await session_service.create_session(app_name=APP_NAME, user_id=body.user_id)
        session_id = session.id
    reply = ""
    async for event in runner.run_async(
        user_id=body.user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=body.text)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(p.text or "" for p in event.content.parts).strip()
    return {"reply": reply, "session_id": session_id}


@app.post("/end")
async def end(body: EndIn) -> dict:
    """Session over → WRITE: Memory Bank curates the transcript into durable facts."""
    session = await session_service.get_session(app_name=APP_NAME, user_id=body.user_id, session_id=body.session_id)
    if session is None:
        return {"ok": False, "error": "session not found"}
    await memory_service.add_session_to_memory(session)
    return {"ok": True, "message": "session handed to Memory Bank for consolidation"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8600)))
