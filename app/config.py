"""Paths and network settings for one run of the tool."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

BANK_ROOT = REPO_ROOT / "bank"
SESSIONS_ROOT = REPO_ROOT / "sessions"
WEB_ROOT = REPO_ROOT / "web"

DEFAULT_PORT = 8765

# The tool listens on the loopback interface only. This is not configurable on purpose.
# A setting that can move the tool onto a network interface will eventually be set by accident,
# and the tool has no authentication to fall back on. See README, "Security model".
HOST = "127.0.0.1"

SESSION_ID_PATTERN = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{4}_[A-Za-z0-9-]+_[A-Za-z0-9-]+$"

DEFAULT_START_DIFFICULTY = 2
DEFAULT_QUESTION_MINUTES = 5


def allowed_hosts(port: int) -> frozenset[str]:
    """Host header values the server answers to. Anything else is a rebinding attempt."""
    return frozenset(
        {
            f"127.0.0.1:{port}",
            f"localhost:{port}",
            "127.0.0.1",
            "localhost",
        }
    )
