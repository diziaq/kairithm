"""Session state: create, read, mutate, write.

Every mutation ends in one atomic write. The process can be killed at any point and the file on
disk is either the state before the change or the state after it, never something in between.

A session stores card ids, never card bodies — the bank is the knowledge base. The one exception
is a small snapshot taken when a card is served (`asked_*`), so a scorecard written months later
still reads correctly if the card has since been edited, moved or deleted.
"""

from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bank import Bank, Question
from .config import DEFAULT_QUESTION_MINUTES, SESSIONS_ROOT
from .levels import BANDS, LEVELS, Calibration, calibrate
from .scoring import Observation
from .selection import (
    ADAPTIVE,
    MODES,
    SEQUENTIAL,
    PoolFilters,
    build_pool,
    choose_adaptive,
    order_pool,
    start_level,
)
from .storage import list_session_dirs, read_json, session_dir, write_json_atomic

SESSION_SCHEMA_VERSION = 1

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


def snapshot(question: Question) -> dict[str, Any]:
    """The minimum needed for an old session to stay readable if the card later changes."""
    return {
        "asked_title": question.title,
        "asked_text": question.question,
        "asked_category": question.category,
        "asked_topic": question.topic,
        "asked_level": question.level,
    }


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
    def summary_path(self) -> Path:
        return session_dir(self.id) / "summary.md"

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

    # --- answers -------------------------------------------------------------------------

    def answer_for(self, question_id: str) -> dict[str, Any]:
        return self.answers.get(question_id) or {}

    def set_answer(self, question_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        current = dict(self.answers.get(question_id) or {})
        if "band" in patch:
            band = patch["band"]
            if band is None:
                current["band"] = None
            elif str(band).lower() in BANDS:
                current["band"] = str(band).lower()
                # Assigning a band says the question was answered, so it cannot still be
                # skipped. Leaving both set would drop the band from the evidence silently.
                current["skipped"] = False
            else:
                raise ValueError(f"band must be one of {', '.join(BANDS)}, not {band!r}")
        # An explicit skip in the same patch still wins, so the order here matters.
        if "skipped" in patch:
            current["skipped"] = bool(patch["skipped"])
            if current["skipped"]:
                current["band"] = None
        if "note" in patch:
            current["note"] = str(patch["note"] or "")
        if "follow_ups_used" in patch:
            raw = patch["follow_ups_used"] or []
            current["follow_ups_used"] = sorted({int(index) for index in raw})
        if "elapsed_seconds" in patch:
            current["elapsed_seconds"] = max(0, int(patch["elapsed_seconds"] or 0))
        current["updated_utc"] = utc_now()
        self.answers[question_id] = current
        return current

    # --- the served list -----------------------------------------------------------------

    def served_ids(self) -> list[str]:
        return [item["qid"] for item in self.items]

    def answered_ids(self) -> list[str]:
        """Cards that carry a band or a skip.

        Distinct from `served_ids`, which in a non-adaptive mode is the whole planned queue from
        the first second. Suggestions key off this one: a card sitting further down the plan is
        a perfectly good thing to offer next, and jumping to it just moves the position.
        """
        return [
            item["qid"]
            for item in self.items
            if (self.answer_for(item["qid"]).get("band") or self.answer_for(item["qid"]).get("skipped"))
        ]

    def item_level(self, item: dict[str, Any], bank: Bank) -> str | None:
        question = bank.get(item["qid"])
        if question is not None:
            return question.level
        level = item.get("asked_level")
        return level if level in LEVELS else None

    def append_item(self, bank: Bank, question_id: str, reason: str) -> dict[str, Any] | None:
        """Serve one more card. Used by adaptive mode and by an explicit jump."""
        question = bank.get(question_id)
        if question is None or question_id in self.served_ids():
            return None
        item = {
            "qid": question.id,
            "target_level": self.target_level(bank),
            "reason": reason,
            **snapshot(question),
        }
        self.items.append(item)
        return item

    def append_adaptive_item(self, bank: Bank) -> dict[str, Any] | None:
        """Serve one more adaptive card, or return None when the pool is used up."""
        target = self.target_level(bank)
        latest, _, _ = self.replay_calibration(bank)
        picked = choose_adaptive(
            bank,
            self.pool(bank),
            self.served_ids(),
            target,
            int(self.data["seed"]),
            change_topic=bool(latest and latest.change_topic),
        )
        if picked is None:
            return None
        question, reason = picked
        item = {
            "qid": question.id,
            "target_level": target,
            "reason": reason,
            **snapshot(question),
        }
        self.items.append(item)
        return item

    # --- calibration ---------------------------------------------------------------------

    def replay_calibration(self, bank: Bank) -> tuple[Calibration | None, str, dict[str, str]]:
        """Derive the running calibration from every band recorded so far, in served order.

        Revising an earlier band therefore changes what is suggested next without discarding any
        card already asked. The per-topic map exists for the one row of the table that says to
        raise the bar "for subsequent questions in this topic".
        """
        latest: Calibration | None = None
        source = ""
        per_topic: dict[str, str] = {}
        for item in self.items:
            answer = self.answer_for(item["qid"])
            band = answer.get("band")
            level = self.item_level(item, bank)
            if not band or band not in BANDS or level is None:
                continue
            latest = calibrate(level, band)
            source = item["qid"]
            question = bank.get(item["qid"])
            topic = question.topic if question else item.get("asked_topic", "")
            if topic:
                per_topic[topic] = latest.next_level
        return latest, source, per_topic

    def target_level(self, bank: Bank) -> str:
        """The level the tool would suggest next. A manual override always wins."""
        override = self.data.get("calibration_override")
        if override in LEVELS:
            return override
        latest, _, _ = self.replay_calibration(bank)
        if latest is not None:
            return latest.next_level
        return start_level(self.data.get("setup") or {})

    # --- derived views -------------------------------------------------------------------

    def pool(self, bank: Bank) -> list[Question]:
        found = [bank.get(qid) for qid in self.data.get("pool_ids", [])]
        return [q for q in found if q is not None]

    def observations(self, bank: Bank) -> list[Observation]:
        """One entry per card that carries a band. Skips and unrated cards are not evidence."""
        out: list[Observation] = []
        for item in self.items:
            answer = self.answer_for(item["qid"])
            band = answer.get("band")
            if not band or answer.get("skipped"):
                continue
            question = bank.get(item["qid"])
            level = self.item_level(item, bank)
            if level is None:
                continue
            out.append(
                Observation(
                    qid=item["qid"],
                    category=question.category if question else item.get("asked_category", "?"),
                    topic=question.topic if question else item.get("asked_topic", "?"),
                    level=level,
                    band=band,
                )
            )
        return out

    def default_minutes_for(self, question: Question | None) -> int:
        pacing = self.data.get("pacing") or {}
        if question and question.time_estimate_min:
            return question.time_estimate_min
        return int(pacing.get("default_minutes") or DEFAULT_QUESTION_MINUTES)

    def as_state(self, bank: Bank) -> dict[str, Any]:
        """Everything the browser needs to render the session, hints excluded."""
        latest, source, per_topic = self.replay_calibration(bank)
        items = []
        for index, item in enumerate(self.items):
            question = bank.get(item["qid"])
            items.append(
                {
                    "index": index,
                    "qid": item["qid"],
                    "target_level": item.get("target_level"),
                    "reason": item.get("reason"),
                    "missing": question is None,
                    "question": question.summary()
                    if question
                    else {
                        "id": item["qid"],
                        "title": item.get("asked_title", item["qid"]),
                        "category": item.get("asked_category", "?"),
                        "topic": item.get("asked_topic", "?"),
                        "level": item.get("asked_level"),
                        "tags": [],
                        "time_estimate_min": None,
                    },
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
            "calibration": {
                "target_level": self.target_level(bank),
                "override": self.data.get("calibration_override"),
                "from_question": source,
                "latest": latest.as_dict() if latest else None,
                "by_topic": per_topic,
            },
            "finish": self.data.get("finish") or {},
            "adaptive_exhausted": bool(self.data.get("adaptive_exhausted")),
        }


def create_session(bank: Bank, setup: dict[str, Any]) -> Session:
    mode = str(setup.get("mode") or SEQUENTIAL)
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

    items = [
        {"qid": question.id, "target_level": None, "reason": reason, **snapshot(question)}
        for question, reason in order_pool(pool, mode, seed, bank)
    ]

    data: dict[str, Any] = {
        "id": session_id,
        "schema_version": SESSION_SCHEMA_VERSION,
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
        "calibration_override": None,
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
            if answer.get("band") or answer.get("skipped")
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
    """Card ids already served to this candidate name in an earlier session."""
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
