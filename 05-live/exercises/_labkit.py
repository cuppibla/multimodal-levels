"""Shared lab hygiene — NOT part of the lesson.

Two chores, so the exercise output stays readable:

  setup()              loads ../.env (project, Vertex flag, model pin)
  install_quiet_loop() silences the known-cosmetic teardown noise you get when
                       a script breaks out of run_live() mid-stream — the
                       opentelemetry context-detach complaint and the
                       async-generator aclose() race. Nothing here changes
                       behavior; it only filters log spam that isn't yours.
"""
import asyncio
import logging
import warnings
from pathlib import Path

from dotenv import load_dotenv

_NOISE = (
    "aclose(): asynchronous generator is already running",
    "was created in a different Context",
    "Failed to detach context",
)


def setup() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    warnings.filterwarnings("ignore")
    logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
    logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)


def install_quiet_loop() -> None:
    """Call once inside async main() — filters known teardown noise, passes real errors through."""
    loop = asyncio.get_running_loop()

    def handler(loop, context):
        message = str(context.get("exception") or context.get("message", ""))
        if any(noise in message for noise in _NOISE):
            return
        loop.default_exception_handler(context)

    loop.set_exception_handler(handler)
