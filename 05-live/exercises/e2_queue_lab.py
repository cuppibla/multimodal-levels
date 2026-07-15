"""E2a — LiveRequestQueue lab (ADK): the queue is your hand on the channel.

A live session is NOT request→response. It's one long connection with two
independent streams — and `LiveRequestQueue` is the upstream half. Everything
your app ever "says" to a live agent goes through exactly three verbs:

    queue.send_content(...)    discrete, turn-taking   → typed text, injected events
    queue.send_realtime(...)   continuous, flowing     → mic PCM chunks, webcam frames
    queue.close()              hang up

This lab runs the real NOVA live model headless (no mic, no browser): we push
two typed turns through the queue and print every event that comes back down
the other stream, timestamped, so you can SEE the shape of a live turn —
partial transcripts streaming in, audio chunks landing, `turn_complete`.

Run:  uv run python exercises/e2_queue_lab.py
"""
import asyncio
import time
import _labkit

_labkit.setup()

from google.adk.agents import Agent
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

MODEL_ID = "gemini-live-2.5-flash-native-audio"
APP = "queue-lab"

agent = Agent(
    name="nova_headless",
    model=MODEL_ID,
    instruction=(
        "You are NOVA, the rescue ship's AI. Calm, warm, lightly wry. "
        "Reply in one short sentence — this is a voice channel."
    ),
)


async def main() -> None:
    _labkit.install_quiet_loop()
    session_service = InMemorySessionService()
    runner = Runner(app_name=APP, agent=agent, session_service=session_service)
    await session_service.create_session(app_name=APP, user_id="operator", session_id="lab")

    queue = LiveRequestQueue()

    # The model answers in AUDIO (that's what a native-audio model does) — we just
    # don't play it. Transcription gives us the words; the byte count proves the audio.
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        output_audio_transcription=types.AudioTranscriptionConfig(),
        input_audio_transcription=types.AudioTranscriptionConfig(),
    )

    turns = [
        "NOVA, status check — one sentence.",
        "And what's your name?",
    ]

    t0 = time.monotonic()
    turn_idx = 0
    audio_bytes = 0
    print(f"\n═══ live channel open · model={MODEL_ID} ═══\n")
    print(f"[t=0.00s] ⌨️  send_content → {turns[0]!r}")
    queue.send_content(types.Content(role="user", parts=[types.Part(text=turns[0])]))

    async for event in runner.run_live(
        user_id="operator", session_id="lab", live_request_queue=queue, run_config=run_config
    ):
        t = time.monotonic() - t0

        # downstream stream #1: the model's words (transcribed from its audio)
        if event.output_transcription and event.output_transcription.text:
            marker = "final" if event.output_transcription.finished else "partial"
            print(f"[t={t:5.2f}s] 🗣  transcript ({marker}): {event.output_transcription.text!r}")

        # downstream stream #2: the model's actual voice, as PCM chunks
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.inline_data and part.inline_data.data:
                    audio_bytes += len(part.inline_data.data)

        if event.interrupted:
            print(f"[t={t:5.2f}s] ✋ interrupted (barge-in)")

        if event.turn_complete:
            print(f"[t={t:5.2f}s] ✔  turn_complete · audio so far: {audio_bytes:,} bytes")
            turn_idx += 1
            if turn_idx < len(turns):
                print(f"\n[t={t:5.2f}s] ⌨️  send_content → {turns[turn_idx]!r}")
                queue.send_content(types.Content(role="user", parts=[types.Part(text=turns[turn_idx])]))
            else:
                queue.close()  # verb #3: hang up
                break

    print(f"\n═══ channel closed · total voice audio received: {audio_bytes:,} bytes "
          f"(24 kHz PCM ≈ {audio_bytes / 48000:.1f}s of speech) ═══")
    print("\nWhat you just proved:")
    print("  · one connection, two streams — you never 'waited for a response object'")
    print("  · send_content = discrete turns; the mic would use send_realtime instead")
    print("  · the words arrived as transcription events; the VOICE arrived as PCM bytes")
    print("  · compare with e2_raw_sdk.py — same conversation, no ADK, count the jobs you inherit\n")


if __name__ == "__main__":
    asyncio.run(main())
