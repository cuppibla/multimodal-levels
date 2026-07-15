"""E4 — memory in a live conversation: four acts, from socket to Memory Bank.

E2b showed the brutal baseline: a raw live socket forgets you the moment it
closes. This lab climbs the whole ladder with ADK, headless, and PROVES each
rung by asking NOVA the same question — "what's my name?" — after each kind of
break:

  Act 1  SAME session, NEW connection      ✅ remembers — the session service
         (hang up, call back)                 replays history into the new socket
  Act 2  what did the session actually keep?  dump session.events — the WORDS
                                              (transcripts) + tool calls persist;
                                              the AUDIO bytes do not (by default)
  Act 3  process restart                   ❌ amnesia — InMemorySessionService
         (new InMemorySessionService)         lives and dies with the process
  Act 4  long-term memory                  ✅ remembers across sessions — end of
         (add_session_to_memory +             call: session → memory service;
          load_memory tool)                   new session: agent SEARCHES memory

Act 4 uses InMemoryMemoryService so the lab runs anywhere free. In production
you swap ONE line for VertexAiMemoryBankService — that's Level 6 (../06-memory),
where NOVA gets her real Memory Bank.

Run:  uv run python exercises/e4_memory.py
"""
import asyncio
import _labkit

_labkit.setup()

from google.adk.agents import Agent
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import load_memory
from google.genai import types

MODEL_ID = "gemini-live-2.5-flash-native-audio"
APP = "memory-lab"
USER = "operator"

INSTRUCTION = (
    "You are NOVA, the rescue ship's AI on a live voice channel. Calm, warm, brief — "
    "one short sentence per reply."
)
# only agents that HAVE the tool get told about it — mention a tool an agent doesn't
# have and the model will happily hallucinate a call to it (ask us how we know)
MEMORY_SUFFIX = (
    " If the operator asks about something you don't see in this conversation "
    "(like their name), call load_memory before answering."
)


def make_agent(with_memory_tool: bool = False) -> Agent:
    return Agent(
        name="nova_memory",
        model=MODEL_ID,
        instruction=INSTRUCTION + (MEMORY_SUFFIX if with_memory_tool else ""),
        tools=[load_memory] if with_memory_tool else [],
    )


async def live_turn(runner: Runner, session_id: str, text: str) -> str:
    """One complete live turn: open a connection, say one thing, hang up."""
    queue = LiveRequestQueue()
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )
    print(f"  ⌨️  → {text!r}")
    queue.send_content(types.Content(role="user", parts=[types.Part(text=text)]))
    transcript = []
    async def consume():
        turns = 0
        async for event in runner.run_live(
            user_id=USER, session_id=session_id, live_request_queue=queue, run_config=run_config
        ):
            if event.output_transcription and event.output_transcription.text \
                    and not event.output_transcription.finished:
                transcript.append(event.output_transcription.text)
            for fc in event.get_function_calls():
                print(f"  ⚙️  model calls {fc.name}({fc.args})")
            if event.turn_complete:
                turns += 1
                # a tool-call turn completes BEFORE the spoken answer (E3's lesson) —
                # stay on the line until she has actually said something
                if transcript or turns >= 4:
                    queue.close()
                    return
    await asyncio.wait_for(consume(), timeout=60)
    reply = "".join(transcript).strip()
    print(f"  🗣  ← {reply!r}")
    return reply


async def main() -> None:
    _labkit.install_quiet_loop()
    # ─── Acts 1–3 share one "process": one session service ─────────────────────
    session_service = InMemorySessionService()
    runner = Runner(app_name=APP, agent=make_agent(), session_service=session_service)
    await session_service.create_session(app_name=APP, user_id=USER, session_id="call-1")

    print("\n═══ Act 1 · same session, new connection (hang up, call back) ═══")
    await live_turn(runner, "call-1", "NOVA, my name is Ayo. Remember it.")
    # the connection above is now CLOSED. Call back on the same session id:
    await live_turn(runner, "call-1", "What's my name?")
    print("  ✅ she knows — run_live replayed the session's events into the new socket")

    print("\n═══ Act 2 · what did the session actually keep? ═══")
    session = await session_service.get_session(app_name=APP, user_id=USER, session_id="call-1")
    audio_events = text_events = transcript_events = 0
    for ev in session.events:
        parts = ev.content.parts if ev.content and ev.content.parts else []
        audio_events += any(p.inline_data for p in parts if p)
        text_events += any(p.text for p in parts if p)
        transcript_events += bool(ev.output_transcription or ev.input_transcription)
    print(f"  {len(session.events)} events persisted · text: {text_events} · "
          f"transcription: {transcript_events} · raw audio: {audio_events}")
    for ev in session.events:
        text = next((p.text for p in (ev.content.parts if ev.content and ev.content.parts else []) if p and p.text), None)
        if not text and ev.output_transcription:
            text = f"(voice transcript) {ev.output_transcription.text}"
        if text:
            print(f"    [{ev.author:>11}] {str(text)[:70]!r}")
    print("  → the WORDS survive (transcriptions become events); the PCM audio doesn't (by default)")
    print("    (RunConfig(save_live_audio=True) can keep the audio too — it's a choice, not a given)")

    print("\n═══ Act 3 · process restart ═══")
    session_service_after_reboot = InMemorySessionService()   # ← 'the ship rebooted'
    runner2 = Runner(app_name=APP, agent=make_agent(), session_service=session_service_after_reboot)
    await session_service_after_reboot.create_session(app_name=APP, user_id=USER, session_id="call-2")
    await live_turn(runner2, "call-2", "What's my name?")
    print("  ❌ amnesia — InMemory* means IN MEMORY. The process died, the sessions died with it.")
    print("    (cure #1: a persistent SessionService — Database/VertexAi — keeps sessions across restarts)")

    print("\n═══ Act 4 · long-term memory: end of call → memory; new call → recall ═══")
    memory_service = InMemoryMemoryService()   # prod: VertexAiMemoryBankService (see ../06-memory)
    session_service3 = InMemorySessionService()
    runner3 = Runner(app_name=APP, agent=make_agent(with_memory_tool=True),
                     session_service=session_service3, memory_service=memory_service)
    await session_service3.create_session(app_name=APP, user_id=USER, session_id="call-3")
    await live_turn(runner3, "call-3", "NOVA, my name is Ayo and my favorite color is teal.")
    finished = await session_service3.get_session(app_name=APP, user_id=USER, session_id="call-3")
    await memory_service.add_session_to_memory(finished)      # ← end-of-call save. THE line.
    print("  💾 add_session_to_memory(call-3) — the call is now searchable memory")

    await session_service3.create_session(app_name=APP, user_id=USER, session_id="call-4")
    await live_turn(runner3, "call-4", "What's my name? Check your memory if you need to.")
    print("  ✅ new session, and she found it — load_memory searched past conversations mid-call")

    print("\nThe ladder you just climbed:")
    print("  socket (E2b: dies with connection) → session (survives reconnect) →")
    print("  persistent session service (survives restart) → memory service (survives EVERYTHING,")
    print("  searchable across sessions). Level 6 swaps in Memory Bank and NOVA finally remembers you.\n")


if __name__ == "__main__":
    asyncio.run(main())
