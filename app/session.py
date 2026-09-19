"""Session state: create, read, mutate, write.

Every mutation ends in one atomic write. The process can be killed at any point and the file on
disk is either the state before the change or the state after it, never something in between.
"""

from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bank import Bank, Question
from .config import DEFAULT_QUESTION_MINUTES, SESSIONS_ROOT
from .selection import (
    ADAPTIVE,
    MODES,
    PoolFilters,
    build_pool,
    choose_adaptive,
    next_target_difficulty,
    order_pool,
    start_target,
)
from .storage import list_session_dirs, read_json, session_dir, write_json_atomic

SLUG_STRIP = re.compile(r"[^a-z0-9]+")
MAX_SLUG = 24


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(value: str, fallback: str) -> str:
    slug = SLUG_STRIP.sub("-", (value or "").lower()).strip("-")[:MAX_SLUG].strip("-")
    return slug or fallback


def new_session_id(candidate: str, role: str, when: datetime | None = None) -> str:
    stamp = (when or datetime.now()).strftime("%Y-%m-%d_%H%M")
    return f"{stamp}_{slugify(candidate, 'candidate')}_{slugify(role, 'role')}"


class Session:
    """One interview. The dictionary is the file, so the shape here is the shape on disk."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @property
    def id(self) -> str:
        return self.data["id"]

    @property
    def path(self) -> Path:
        return session_dir(self.id) / "session.json"

    @property
    def scorecard_path(self) -> Path:
        return session_dir(self.id) / "scorecard.md"

    @property
    def mode(self) -> str:
        return self.data["mode"]

    @property
    def items(self) -> list[dict[str, Any]]:
        return self.data["items"]

    @property
    def answers(self) -> dict[str, Any]:
        return self.data["answers"]

    @property
    def finished(self) -> bool:
        return bool(self.data.get("finished_utc"))

    def save(self) -> None:
        self.data["revision"] = int(self.data.get("revision", 0)) + 1
        self.data["updated_utc"] = utc_now()
        write_json_atomic(self.path, self.data)

    def answer_for(self, question_id: str) -> dict[str, Any]:
        return self.answers.get(question_id) or {}

    def set_answer(self, question_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        current = dict(self.answers.get(question_id) or {})
        if "rating" in patch:
            rating = patch["rating"]
            current["rating"] = None if rating is None else max(1, min(5, int(rating)))
        if "skipped" in patch:
            current["skipped"] = bool(patch["skipped"])
            if current["skipped"]:
                current["rating"] = None
        if "note" in patch:
            current["note"] = str(patch["note"] or "")
        if "elapsed_seconds" in patch:
            current["elapsed_seconds"] = max(0, int(patch["elapsed_seconds"] or 0))
        current["updated_utc"] = utc_now()
        self.answers[question_id] = current
        return current

    def replay_target(self, bank: Bank) -> int:
        """Derive the adaptive target from every answer recorded so far, in served order.

        Revising an earlier rating therefore changes the next question without discarding any
        question already asked.
        """
        target = start_target(self.data.get("setup") or {})
        for item in self.items:
            answer = self.answer_for(item["qid"])
            if not answer:
                continue
            target = next_target_difficulty(
                target, answer.get("rating"), bool(answer.get("skipped"))
            )
        return target

    def covered_tags(self, bank: Bank) -> set[str]:
        tags: set[str] = set()
        for item in self.items:
            question = bank.get(item["qid"])
            if question:
                tags |= set(question.tags)
        return tags

    def pool(self, bank: Bank) -> list[Question]:
        found = [bank.get(qid) for qid in self.data.get("pool_ids", [])]
        return [q for q in found if q is not None]

    def append_adaptive_item(self, bank: Bank) -> dict[str, Any] | None:
        """Serve one more adaptive question, or return None when the pool is used up."""
        target = self.replay_target(bank)
        served = [item["qid"] for item in self.items]
        picked = choose_adaptive(
            self.pool(bank), served, target, int(self.data["seed"]), self.covered_tags(bank)
        )
        if picked is None:
            return None
        question, reason = picked
        item = {"qid": question.id, "target_difficulty": target, "reason": reason}
        self.items.append(item)
        return item

    def default_minutes_for(self, question: Question | None) -> int:
        pacing = self.data.get("pacing") or {}
        if question and question.time_minutes:
            return question.time_minutes
        return int(pacing.get("default_minutes") or DEFAULT_QUESTION_MINUTES)

    def as_state(self, bank: Bank) -> dict[str, Any]:
        """Everything the browser needs to render, hints excluded."""
        items = []
        for index, item in enumerate(self.items):
            question = bank.get(item["qid"])
            items.append(
                {
                    "index": index,
                    "qid": item["qid"],
                    "target_difficulty": item.get("target_difficulty"),
                    "reason": item.get("reason"),
                    "missing": question is None,
                    "question": question.summary() if question else {"id": item["qid"]},
                    "answer": self.answer_for(item["qid"]),
                    "budget_minutes": self.default_minutes_for(question),
                }
            )
        return {
            "id": self.id,
            "revision": self.data.get("revision", 0),
            "candidate": self.data["candidate"],
            "role": self.data["role"],
            "interviewer": self.data["interviewer"],
            "context": self.data.get("context", ""),
            "created_utc": self.data["created_utc"],
            "finished_utc": self.data.get("finished_utc"),
            "mode": self.mode,
            "seed": self.data["seed"],
            "pacing": self.data.get("pacing") or {"kind": "untimed"},
            "position": self.data.get("position", 0),
            "pool_size": len(self.data.get("pool_ids", [])),
            "items": items,
            "finish": self.data.get("finish") or {},
            "adaptive_exhausted": bool(self.data.get("adaptive_exhausted")),
        }


def create_session(bank: Bank, setup: dict[str, Any]) -> Session:
    mode = str(setup.get("mode") or "sequential")
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")

    filters = PoolFilters.from_dict(setup.get("filters") or {})
    pool = build_pool(bank, filters)
    if not pool:
        raise ValueError("the filters matched no questions")

    seed = setup.get("seed")
    seed = int(seed) if seed not in (None, "") else secrets.randbelow(10_000_000_000)

    candidate = str(setup.get("candidate") or "").strip()
    role = str(setup.get("role") or "").strip()
    session_id = new_session_id(candidate, role)
    directory = session_dir(session_id)
    if (directory / "session.json").exists():
        session_id = f"{session_id}-{secrets.token_hex(2)}"

    ordered = order_pool(pool, mode, seed)
    items = [
        {"qid": q.id, "target_difficulty": None, "reason": f"{mode} order"} for q in ordered
    ]

    data: dict[str, Any] = {
        "id": session_id,
        "revision": 0,
        "created_utc": utc_now(),
        "updated_utc": utc_now(),
        "finished_utc": None,
        "candidate": candidate,
        "role": role,
        "interviewer": str(setup.get("interviewer") or "").strip(),
        "context": str(setup.get("context") or "").strip(),
        "mode": mode,
        "seed": seed,
        "pacing": setup.get("pacing") or {"kind": "untimed"},
        "setup": setup,
        "pool_ids": [q.id for q in pool],
        "items": items,
        "answers": {},
        "position": 0,
        "finish": {},
        "adaptive_exhausted": False,
    }
    session = Session(data)
    if mode == ADAPTIVE:
        session.append_adaptive_item(bank)
    session.save()
    return session


def load_session(session_id: str) -> Session:
    return Session(read_json(session_dir(session_id) / "session.json"))


def list_sessions() -> list[dict[str, Any]]:
    """Every session on disk, newest first, with the flag the home screen needs."""
    rows = []
    for directory in list_session_dirs():
        try:
            data = read_json(directory / "session.json")
        except (OSError, ValueError):
            continue
        answered = sum(
            1
            for answer in (data.get("answers") or {}).values()
            if answer.get("rating") is not None or answer.get("skipped")
        )
        rows.append(
            {
                "id": data.get("id", directory.name),
                "candidate": data.get("candidate", ""),
                "role": data.get("role", ""),
                "interviewer": data.get("interviewer", ""),
                "created_utc": data.get("created_utc", ""),
                "mode": data.get("mode", ""),
                "served": len(data.get("items") or []),
                "answered": answered,
                "resumable": not (directory / "scorecard.md").exists(),
            }
        )
    return rows


def previously_asked_ids(candidate: str) -> list[str]:
    """Question ids already served to this candidate name in an earlier session."""
    wanted = slugify(candidate, "")
    if not wanted:
        return []
    seen: set[str] = set()
    for directory in list_session_dirs():
        try:
            data = read_json(directory / "session.json")
        except (OSError, ValueError):
            continue
        if slugify(data.get("candidate", ""), "") != wanted:
            continue
        for item in data.get("items") or []:
            seen.add(item["qid"])
    return sorted(seen)


def ensure_sessions_root() -> None:
    SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)
