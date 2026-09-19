#!/usr/bin/env python3
"""Start the interview runner on the loopback interface and print its address."""

from __future__ import annotations

import argparse
import sys

import uvicorn

from app import config
from app.bank import load_bank
from app.main import create_app
from app.session import ensure_sessions_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the interview tool on this machine.")
    parser.add_argument("--port", type=int, default=config.DEFAULT_PORT)
    args = parser.parse_args()

    ensure_sessions_root()

    bank = load_bank()
    print(f"bank: {len(bank.questions)} questions in {len(bank.topics)} topics")
    for warning in bank.warnings:
        print(f"  bank warning: {warning.path}: {warning.problem}", file=sys.stderr)

    url = f"http://{config.HOST}:{args.port}/"
    print(f"open {url}")
    uvicorn.run(create_app(args.port), host=config.HOST, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
