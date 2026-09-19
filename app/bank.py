"""Read the question bank from disk.

One file is one question. The directory name is the topic. The file name stem is the local id.
The bank is read only for this tool. The user edits the files in an editor and starts a new
session to pick the changes up.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .config import BANK_ROOT

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)
HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

KNOWN_SECTIONS = {
    "ask": "ask",
    "look for": "look_for",
    "red flags": "red_flags",
    "follow-ups": "follow_ups",
    "follow ups": "follow_ups",
}

MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 5


@dataclass(frozen=True)
class Question:
    id: str
    topic: str
    stem: str
    title: str
    difficulty: int
    tags: tuple[str, ...]
    time_minutes: int | None
    order: int | None
    ask: str
    look_for: str
    red_flags: str
    follow_ups: str
    extra: tuple[tuple[str, str], ...]
    path: str

    def public(self, include_hints: bool) -> dict[str, Any]:
        """Shape sent to the browser. Hints are dropped server side, not hidden by CSS."""
        data: dict[str, Any] = {
            "id": self.id,
            "topic": self.topic,
            "title": self.title,
            "difficulty": self.difficulty,
            "tags": list(self.tags),
            "time_minutes": self.time_minutes,
            "ask": self.ask,
        }
        if include_hints:
            data |= {
                "look_for": self.look_for,
                "red_flags": self.red_flags,
                "follow_ups": self.follow_ups,
                "extra": [{"heading": h, "body": b} for h, b in self.extra],
            }
        return data

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "title": self.title,
            "difficulty": self.difficulty,
            "tags": list(self.tags),
            "time_minutes": self.time_minutes,
        }


@dataclass
class Warning_:
    path: str
    problem: str


@dataclass
class Bank:
    questions: dict[str, Question] = field(default_factory=dict)
    warnings: list[Warning_] = field(default_factory=list)

    @property
    def topics(self) -> list[str]:
        return sorted({q.topic for q in self.questions.values()})

    @property
    def tags(self) -> list[str]:
        return sorted({t for q in self.questions.values() for t in q.tags})

    def difficulty_histogram(self) -> dict[int, int]:
        counts = {level: 0 for level in range(MIN_DIFFICULTY, MAX_DIFFICULTY + 1)}
        for question in self.questions.values():
            counts[question.difficulty] += 1
        return counts

    def get(self, question_id: str) -> Question | None:
        return self.questions.get(question_id)


def _split_sections(body: str) -> tuple[dict[str, str], list[tuple[str, str]]]:
    known: dict[str, str] = {}
    extra: list[tuple[str, str]] = []
    matches = list(HEADING.finditer(body))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        heading = match.group(1).strip()
        text = body[start:end].strip()
        key = KNOWN_SECTIONS.get(heading.lower())
        if key:
            known[key] = text
        else:
            extra.append((heading, text))
    return known, extra


def _parse_tags(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        return tuple(part.strip() for part in raw.split(",") if part.strip())
    if isinstance(raw, list):
        return tuple(str(part).strip() for part in raw if str(part).strip())
    return ()


def _parse_optional_int(raw: Any) -> int | None:
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def load_question(path: Path, topic: str, root: Path | None = None) -> tuple[Question | None, list[str]]:
    """Parse one file. Returns the question, or None plus the reasons it was skipped."""
    problems: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return None, [f"cannot read the file: {error}"]

    match = FRONTMATTER.match(raw)
    if not match:
        return None, ["no YAML frontmatter between --- lines at the top of the file"]

    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as error:
        return None, [f"cannot parse the frontmatter: {error}"]
    if not isinstance(meta, dict):
        return None, ["frontmatter is not a mapping of keys to values"]

    known, extra = _split_sections(match.group(2))

    title = str(meta.get("title", "")).strip()
    if not title:
        problems.append("title is missing or empty")

    difficulty_raw = meta.get("difficulty")
    difficulty = _parse_optional_int(difficulty_raw)
    if difficulty_raw is None:
        problems.append("difficulty is missing")
    elif difficulty is None:
        problems.append(f"difficulty is not a whole number: {difficulty_raw!r}")
    elif not MIN_DIFFICULTY <= difficulty <= MAX_DIFFICULTY:
        problems.append(f"difficulty {difficulty} is outside the range 1 to 5")

    ask = known.get("ask", "").strip()
    if not ask:
        problems.append("the Ask section is missing or empty")

    if problems:
        return None, problems

    stem = path.stem
    base = (root or BANK_ROOT).parent
    display_path = str(path.relative_to(base)) if path.is_relative_to(base) else str(path)
    return (
        Question(
            id=f"{topic}/{stem}",
            topic=topic,
            stem=stem,
            title=title,
            difficulty=int(difficulty),
            tags=_parse_tags(meta.get("tags")),
            time_minutes=_parse_optional_int(meta.get("time_minutes")),
            order=_parse_optional_int(meta.get("order")),
            ask=ask,
            look_for=known.get("look_for", "").strip(),
            red_flags=known.get("red_flags", "").strip(),
            follow_ups=known.get("follow_ups", "").strip(),
            extra=tuple(extra),
            path=display_path,
        ),
        [],
    )


def load_bank(root: Path | None = None) -> Bank:
    """Read every question file under the bank root.

    A bad file is listed and skipped. The loader never raises for content it read from disk,
    because one broken file must not stop an interview that is about to start.
    """
    bank_root = root or BANK_ROOT
    bank = Bank()
    if not bank_root.is_dir():
        bank.warnings.append(Warning_(str(bank_root), "the bank directory does not exist"))
        return bank

    for path in sorted(bank_root.rglob("*.md")):
        if path.name.startswith("_") or any(part.startswith("_") for part in path.parts):
            continue
        relative = path.relative_to(bank_root)
        if len(relative.parts) < 2:
            bank.warnings.append(
                Warning_(str(relative), "the file is not inside a topic directory, so it has no topic")
            )
            continue
        topic = relative.parts[0]
        question, problems = load_question(path, topic, bank_root)
        if question is None:
            for problem in problems:
                bank.warnings.append(Warning_(str(relative), problem))
            continue
        if question.id in bank.questions:
            bank.warnings.append(Warning_(str(relative), f"duplicate question id {question.id}"))
            continue
        bank.questions[question.id] = question

    if not bank.questions:
        bank.warnings.append(Warning_(str(bank_root), "the bank contains no usable questions"))
    return bank
