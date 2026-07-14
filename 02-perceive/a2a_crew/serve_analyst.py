"""Serve ONE analyst as its own A2A service — same agent, its own host.

    ANALYST=geological   uv run python -m a2a_crew.serve_analyst    # :8791
    ANALYST=botanical    uv run python -m a2a_crew.serve_analyst    # :8792
    ANALYST=astronomical uv run python -m a2a_crew.serve_analyst    # :8793

`to_a2a` wraps the agent in a Starlette app that publishes the Agent Card at
/.well-known/agent-card.json and speaks the A2A protocol — the ADK-native version of
what 03-interop's architect/main.py hand-rolls with FastAPI.

On Cloud Run the platform sets PORT (=8080); locally each analyst gets its own default
so all three can run side by side.
"""
import os

from dotenv import load_dotenv

load_dotenv()

import uvicorn  # noqa: E402
from google.adk.a2a.utils.agent_to_a2a import to_a2a  # noqa: E402

from a2a_crew.analysts import ANALYSTS  # noqa: E402

DEFAULT_PORTS = {"geological": 8791, "botanical": 8792, "astronomical": 8793}


def main() -> None:
    which = os.environ.get("ANALYST", "").strip().lower()
    if which not in ANALYSTS:
        raise SystemExit(f"Set ANALYST to one of {sorted(ANALYSTS)} (got {which!r}).")

    port = int(os.environ.get("PORT", DEFAULT_PORTS[which]))
    host = os.environ.get("HOST", "0.0.0.0")

    app = to_a2a(ANALYSTS[which], host=host, port=port)
    print(f"  ⬆ {which} analyst → http://localhost:{port}/.well-known/agent-card.json")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
