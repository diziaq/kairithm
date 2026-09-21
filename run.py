#!/usr/bin/env python3
"""Start the interview runner on the loopback interface and open it in a browser."""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

from app import config
from app.bank import load_bank
from app.main import create_app
from app.session import ensure_sessions_root
from app.validate import ERROR, validate_bank

OPEN_TIMEOUT_SECONDS = 10.0
POLL_SECONDS = 0.1


def port_is_accepting(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.25)
        return probe.connect_ex((config.HOST, port)) == 0


def open_when_ready(url: str, port: int) -> None:
    """Open the browser once the server is actually listening.

    A background thread that waits for the port rather than a startup hook on the application,
    because the tests build the application directly and nobody wants a browser window per test
    run. A fixed sleep would race on a slow machine; the port is the thing worth waiting for.
    """

    def wait_then_open() -> None:
        deadline = time.monotonic() + OPEN_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if port_is_accepting(port):
                try:
                    webbrowser.open(url)
                except Exception as error:  # noqa: BLE001 - a browser is a convenience, not the tool
                    print(f"could not open a browser ({error}); open {url} yourself", flush=True)
                return
            time.sleep(POLL_SECONDS)
        print(f"the server did not come up in time; open {url} yourself", flush=True)

    threading.Thread(target=wait_then_open, daemon=True).start()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the interview tool on this machine.")
    parser.add_argument("--port", type=int, default=config.DEFAULT_PORT)
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="start the server but do not open a browser",
    )
    args = parser.parse_args()

    ensure_sessions_root()

    bank = load_bank()
    print(
        f"bank: {len(bank.questions)} questions in {len(bank.topics)} topics "
        f"across {len(bank.categories)} categories",
        flush=True,
    )

    # The same list the home screen shows, so the terminal and the browser never disagree
    # about whether the bank is healthy.
    problems = validate_bank(bank)
    for problem in problems:
        stream = sys.stderr if problem.severity == ERROR else sys.stdout
        print(f"  {problem.line()}", file=stream, flush=True)
    if problems:
        errors = sum(1 for problem in problems if problem.severity == ERROR)
        print(
            f"  {errors} error(s), {len(problems) - errors} warning(s) — "
            f"the affected cards are listed on the home screen too",
            flush=True,
        )

    url = f"http://{config.HOST}:{args.port}/"
    if args.no_browser:
        print(f"listening on {url}", flush=True)
    else:
        print(f"opening {url}", flush=True)
        open_when_ready(url, args.port)

    uvicorn.run(create_app(args.port), host=config.HOST, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
