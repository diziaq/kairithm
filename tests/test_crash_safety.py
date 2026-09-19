"""The claim that a kill loses nothing is tested by killing the process, not by reading the code."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from app.storage import write_json_atomic

REPO_ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            httpx.get(url, timeout=1.0)
            return
        except httpx.HTTPError:
            time.sleep(0.15)
    raise AssertionError(f"server did not start: {url}")


def test_the_encoder_runs_before_the_file_is_touched(tmp_path):
    target = tmp_path / "session.json"
    write_json_atomic(target, {"a": 1})

    with pytest.raises(TypeError):
        write_json_atomic(target, {"bad": object()})

    assert json.loads(target.read_text()) == {"a": 1}


def test_a_failure_during_the_write_leaves_the_old_content(tmp_path, monkeypatch):
    """This is the test that fails if the write stops being atomic.

    A plain open in write mode truncates the target first. The old content is gone from the moment
    the file is opened, so any failure after that point loses the session.
    """
    target = tmp_path / "session.json"
    write_json_atomic(target, {"a": 1})

    def explode(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(os, "fsync", explode)
    with pytest.raises(OSError):
        write_json_atomic(target, {"a": 2})

    assert json.loads(target.read_text()) == {"a": 1}, "a failed write must not destroy the record"
    assert list(tmp_path.glob("*.tmp")) == [], "the temporary file must be cleaned up"


def test_a_failure_during_the_rename_leaves_the_old_content(tmp_path, monkeypatch):
    target = tmp_path / "session.json"
    write_json_atomic(target, {"a": 1})

    def explode(*args, **kwargs):
        raise OSError("rename refused")

    monkeypatch.setattr(os, "replace", explode)
    with pytest.raises(OSError):
        write_json_atomic(target, {"a": 2})

    assert json.loads(target.read_text()) == {"a": 1}
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.parametrize("stop_signal", [signal.SIGKILL])
def test_killing_the_server_mid_session_loses_nothing(tmp_path, stop_signal):
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    process = subprocess.Popen(
        [sys.executable, "run.py", "--port", str(port)],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    session_id = None
    try:
        wait_for(f"{base}/api/bank")
        created = httpx.post(
            f"{base}/api/sessions",
            json={
                "candidate": "Crash Test",
                "role": "Backend",
                "interviewer": "me",
                "mode": "sequential",
                "seed": 777,
                "filters": {"categories": ["java"]},
            },
            timeout=5.0,
        ).json()
        session_id = created["id"]
        qid = created["items"][0]["qid"]
        httpx.patch(
            f"{base}/api/sessions/{session_id}/answers/{qid}",
            json={"band": "senior", "note": "written before the kill", "elapsed_seconds": 42},
            timeout=5.0,
        )
        httpx.post(f"{base}/api/sessions/{session_id}/next", json={}, timeout=5.0)

        process.send_signal(stop_signal)
        process.wait(timeout=10)

        process = subprocess.Popen(
            [sys.executable, "run.py", "--port", str(port)],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_for(f"{base}/api/bank")

        state = httpx.get(f"{base}/api/sessions/{session_id}", timeout=5.0).json()
        assert state["position"] == 1, "the position must survive the kill"
        answer = state["items"][0]["answer"]
        assert answer["band"] == "senior"
        assert answer["note"] == "written before the kill"
        assert answer["elapsed_seconds"] == 42
        assert state["calibration"]["target_level"] == "senior", "the calibration is rederived"

        listed = httpx.get(f"{base}/api/sessions", timeout=5.0).json()["sessions"]
        assert any(row["id"] == session_id and row["resumable"] for row in listed)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        if session_id:
            directory = REPO_ROOT / "sessions" / session_id
            for child in directory.glob("*"):
                child.unlink()
            directory.rmdir()
