"""Disk access. The filesystem is the record, so every write here is crash safe."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from .config import SESSION_ID_PATTERN, SESSIONS_ROOT

_SESSION_ID = re.compile(SESSION_ID_PATTERN)


class UnsafePath(ValueError):
    """A caller supplied an identifier that does not resolve inside its own root."""


def write_text_atomic(path: Path, text: str) -> None:
    """Replace the file in one step, so a kill never leaves a half-written file.

    The temporary file is created in the target directory. A rename is only atomic within one
    filesystem, and the system temporary directory is often a different one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def write_json_atomic(path: Path, data: Any) -> None:
    write_text_atomic(path, json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def session_dir(session_id: str) -> Path:
    """Resolve a session directory, refusing anything that escapes the sessions root.

    The identifier arrives in a URL, so it is attacker controlled. The pattern check rejects
    separators and dots outright. The resolved-prefix check is the second layer, and it also
    catches a symlink planted inside the sessions root.
    """
    if not _SESSION_ID.match(session_id):
        raise UnsafePath(f"session id has an unexpected shape: {session_id!r}")
    root = SESSIONS_ROOT.resolve()
    candidate = (SESSIONS_ROOT / session_id).resolve()
    if candidate != root and root not in candidate.parents:
        raise UnsafePath(f"session id resolves outside the sessions directory: {session_id!r}")
    return candidate


def list_session_dirs() -> list[Path]:
    if not SESSIONS_ROOT.is_dir():
        return []
    found = [d for d in SESSIONS_ROOT.iterdir() if d.is_dir() and (d / "session.json").is_file()]
    return sorted(found, key=lambda d: d.name, reverse=True)
