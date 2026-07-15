"""E2b — the same conversation with the RAW google-genai SDK. No ADK.

`client.aio.live.connect()` is what LiveRequestQueue + run_live wrap. Running
it bare shows exactly what the wrapper buys you:

  raw SDK gives you        a socket. Period.
  you now own              session history (socket dies → memory dies),
                           tool execution (model asks, YOU run the function),
                           reconnect/resumption, callbacks, multi-agent routing.

Act 1 proves the socket remembers within one connection.
Act 2 reconnects — a fresh socket — and NOVA has never met you. There is no
session service; there is nothing to come back to. Hold that thought for E4.

Run:  uv run python exercises/e2_raw_sdk.py
"""
import asyncio

import _labkit

_labkit.setup()

from google import genai
from google.genai import types

MODEL_ID = "gemini-live-2.5-flash-native-audio"

CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    output_audio_transcription=types.AudioTranscriptionConfig(),
    system_instruction=types.Content(parts=[types.Part(
        text="You are NOVA, the rescue ship's AI. Reply in one short sentence."
    )]),
)


async def say(session, text: str) -> str:
    """One turn, by hand: send, then drain server messages until turn_complete."""
    print(f"  ⌨️  → {text!r}")
    await session.send_client_content(
        turns=types.Content(role="user", parts=[types.Part(text=text)])
    )
    transcript = []
    async for message in session.receive():
        sc = message.server_content
        if sc and sc.output_transcription and sc.output_transcription.text:
            if not sc.output_transcription.finished:
                transcript.append(sc.output_transcription.text)
        if sc and sc.turn_complete:
            break
    reply = "".join(transcript).strip()
    print(f"  🗣  ← {reply!r}")
    return reply


async def main() -> None:
    _labkit.install_quiet_loop()
    client = genai.Client()  # reads GOOGLE_GENAI_USE_VERTEXAI / project from .env

    print("\n═══ Act 1 · one socket, two turns ═══")
    async with client.aio.live.connect(model=MODEL_ID, config=CONFIG) as session:
        await say(session, "NOVA, my name is Ayo. Confirm you got that.")
        await say(session, "What's my name?")   # ✅ knows — the SOCKET holds the history

    print("\n═══ Act 2 · new socket, same 'conversation' ═══")
    async with client.aio.live.connect(model=MODEL_ID, config=CONFIG) as session:
        await say(session, "What's my name?")   # ❌ gone — nothing persisted it

    print("\nWhat you just proved:")
    print("  · live 'memory' is the socket's context window — it dies with the connection")
    print("  · the raw SDK has no session service, no tool runner, no resumption")
    print("  · ADK's Runner + LiveRequestQueue is this socket, plus all of that — see e2_queue_lab.py")
    print("  · how do we make NOVA survive a reconnect? That's E4.\n")


if __name__ == "__main__":
    asyncio.run(main())
