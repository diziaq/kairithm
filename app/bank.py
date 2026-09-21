"""Read the question bank from disk.

One file is one card. The directory name is the card's category and must match the `category`
field. The `id` in the frontmatter is the identity — not the file name — because ids are
referenced by links and by past sessions and must survive a file being renamed or moved.

The bank is read only. The user edits the files in an editor and reloads the browser to pick the
change up. The loader never writes and never raises for content it read from disk: one broken
file is reported and skipped, so it cannot stop an interview that is about to start.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .config import BANK_ROOT
from .levels import BANDS, INVERSE_LINK, LEVEL_ORDINAL, LEVELS, LINK_KINDS

# Version 2 added `## Ideal minimal answer`. Version 1 cards still load — they simply have no
# pass mark — so a card written before the change is not broken by it, which is the whole point
# of carrying a version on every card.
SCHEMA_VERSION = 2
SUPPORTED_SCHEMA_VERSIONS = (1, 2)
IDEAL_ANSWER_SINCE = 2

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)
SECTION = re.compile(r"^(#{2,3})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
BULLET = re.compile(r"^[ \t]*[-*][ \t]+(.*)$")
PROBES = re.compile(r"^probes\s*:\s*(.*)$", re.IGNORECASE)
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# `## Ask` fills the `question` field. The heading says what to do with the text; the field name
# is the one used in the schema, the API and every validator message.
KNOWN_SECTIONS = {
    "ask": "question",
    "tests": "tests",
    "ideal minimal answer": "ideal_answer",
    "listen for": "listen_for",
    "expected knowledge": "expected_knowledge",
    "strong signals": "strong_signals",
    "weak signals": "weak_signals",
    "answer bands": "answer_bands",
    "follow-ups": "follow_ups",
    "follow ups": "follow_ups",
    "notes": "notes",
    "sources": "sources",
}

LIST_SECTIONS = ("listen_for", "expected_knowledge", "strong_signals", "weak_signals", "sources")
TEXT_SECTIONS = ("question", "tests", "ideal_answer", "notes")


@dataclass(frozen=True)
class FollowUp:
    """A probe inside the current question. `probes` is interviewer-only and never read aloud."""

    text: str
    probes: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"text": self.text, "probes": self.probes}


@dataclass(frozen=True)
class Question:
    id: str
    schema_version: int
    title: str
    question: str
    category: str
    topic: str
    level: str
    tests: str
    listen_for: tuple[str, ...]
    answer_bands: dict[str, tuple[str, ...]]
    ideal_answer: str = ""
    tags: tuple[str, ...] = ()
    expected_knowledge: tuple[str, ...] = ()
    strong_signals: tuple[str, ...] = ()
    weak_signals: tuple[str, ...] = ()
    follow_ups: tuple[FollowUp, ...] = ()
    links: dict[str, tuple[str, ...]] = field(default_factory=dict)
    sources: tuple[str, ...] = ()
    notes: str = ""
    time_estimate_min: int | None = None
    order: int | None = None
    allow_term_leak: bool = False
    extra: tuple[tuple[str, str], ...] = ()
    path: str = ""

    @property
    def level_ordinal(self) -> int:
        return LEVEL_ORDINAL[self.level]

    def summary(self) -> dict[str, Any]:
        """The shape used in lists: enough to filter and choose, nothing an interviewer reads."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "topic": self.topic,
            "level": self.level,
            "tags": list(self.tags),
            "time_estimate_min": self.time_estimate_min,
        }

    def public(self, include_hints: bool) -> dict[str, Any]:
        """Shape sent to the browser.

        With hints off the interviewer fields are dropped here, server side, so the answer key is
        not sitting in the page waiting to be revealed by a stylesheet. `question` and the links
        stay: the first is read aloud, the second is navigation.
        """
        data: dict[str, Any] = self.summary()
        data["question"] = self.question
        data["links"] = {kind: list(ids) for kind, ids in self.links.items() if ids}
        if include_hints:
            data |= {
                "tests": self.tests,
                "ideal_answer": self.ideal_answer,
                "listen_for": list(self.listen_for),
                "expected_knowledge": list(self.expected_knowledge),
                "strong_signals": list(self.strong_signals),
                "weak_signals": list(self.weak_signals),
                "answer_bands": {band: list(self.answer_bands.get(band, ())) for band in BANDS
                                 if self.answer_bands.get(band)},
                "follow_ups": [f.as_dict() for f in self.follow_ups],
                "sources": list(self.sources),
                "notes": self.notes,
                "extra": [{"heading": h, "body": b} for h, b in self.extra],
            }
        return data


@dataclass
class Problem:
    """One thing wrong with one file. `card_id` is empty when the file never got that far."""

    path: str
    problem: str
    card_id: str = ""
    field: str = ""
    severity: str = "error"

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "problem": self.problem,
            "card_id": self.card_id,
            "field": self.field,
            "severity": self.severity,
        }

    def line(self) -> str:
        where = f"{self.path}"
        if self.card_id:
            where += f" [{self.card_id}]"
        if self.field:
            where += f" ({self.field})"
        return f"{self.severity}: {where}: {self.problem}"


@dataclass
class Bank:
    questions: dict[str, Question] = field(default_factory=dict)
    warnings: list[Problem] = field(default_factory=list)

    @property
    def categories(self) -> list[str]:
        return sorted({q.category for q in self.questions.values()})

    @property
    def topics(self) -> list[str]:
        return sorted({q.topic for q in self.questions.values()})

    @property
    def tags(self) -> list[str]:
        return sorted({t for q in self.questions.values() for t in q.tags})

    def level_histogram(self) -> dict[str, int]:
        counts = {level: 0 for level in LEVELS}
        for question in self.questions.values():
            counts[question.level] += 1
        return counts

    def get(self, question_id: str) -> Question | None:
        return self.questions.get(question_id)

    def resolved_links(self, question_id: str) -> dict[str, list[str]]:
        """Declared links plus the inverses derived from other cards.

        Symmetry is derived here rather than demanded of the author: writing `deeper: [B]` on A
        is enough for B to offer A as `shallower`. The validator still reports a pair that was
        declared explicitly and points the wrong way, which is the case that means a mistake.
        """
        question = self.get(question_id)
        if question is None:
            return {kind: [] for kind in LINK_KINDS}

        out: dict[str, list[str]] = {
            kind: list(question.links.get(kind, ())) for kind in LINK_KINDS
        }
        for other in self.questions.values():
            if other.id == question_id:
                continue
            for kind, ids in other.links.items():
                inverse = INVERSE_LINK.get(kind)
                if inverse and question_id in ids and other.id not in out[inverse]:
                    out[inverse].append(other.id)
        return out


def _split_sections(body: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Split the body into `##` sections, each carrying its own `###` subsections."""
    sections: list[dict[str, Any]] = []
    problems: list[str] = []
    matches = list(SECTION.finditer(body))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        depth = len(match.group(1))
        heading = match.group(2).strip()
        text = body[start:end].strip()
        if depth == 2:
            sections.append({"heading": heading, "text": text, "sub": []})
        elif sections:
            sections[-1]["sub"].append({"heading": heading, "text": text})
        else:
            problems.append(f"the `### {heading}` heading appears before any `##` section")
    return sections, problems


def _raw_items(text: str) -> list[list[str]]:
    """Bullets, each with the continuation lines indented under it.

    A section written as a paragraph instead of bullets becomes one item, so an author who
    forgets the dashes still gets something usable rather than an empty field.
    """
    items: list[list[str]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        bullet = BULLET.match(line)
        if bullet:
            items.append([bullet.group(1).strip()])
        elif items:
            items[-1].append(line.strip())
        else:
            items.append([line.strip()])
    return items


def _items(text: str) -> tuple[str, ...]:
    return tuple(" ".join(parts) for parts in _raw_items(text) if " ".join(parts).strip())


def _follow_ups(text: str) -> tuple[FollowUp, ...]:
    out: list[FollowUp] = []
    for parts in _raw_items(text):
        spoken: list[str] = [parts[0]]
        probes: list[str] = []
        for continuation in parts[1:]:
            match = PROBES.match(continuation)
            if match or probes:
                probes.append(match.group(1).strip() if match else continuation)
            else:
                spoken.append(continuation)
        text_line = " ".join(spoken).strip()
        if text_line:
            out.append(FollowUp(text=text_line, probes=" ".join(probes).strip()))
    return tuple(out)


def _parse_str_list(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        return tuple(part.strip() for part in raw.split(",") if part.strip())
    if isinstance(raw, list):
        return tuple(str(part).strip() for part in raw if str(part).strip())
    return ()


def _text_field(meta: dict[str, Any], key: str) -> str:
    """A frontmatter string. An empty YAML value parses to None, which is not the text "None"."""
    raw = meta.get(key)
    return "" if raw is None else str(raw).strip()


def _parse_optional_int(raw: Any) -> int | None:
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _parse_links(raw: Any, problems: list[tuple[str, str]]) -> dict[str, tuple[str, ...]]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        problems.append(("links", "links must be a mapping of link kind to a list of ids"))
        return {}
    out: dict[str, tuple[str, ...]] = {}
    for kind, ids in raw.items():
        name = str(kind).strip().lower()
        if name not in LINK_KINDS:
            problems.append(
                (f"links.{kind}", f"unknown link kind {kind!r}; allowed: {', '.join(LINK_KINDS)}")
            )
            continue
        out[name] = _parse_str_list(ids)
    return out


def load_question(
    path: Path, category: str, root: Path | None = None
) -> tuple[Question | None, list[Problem]]:
    """Parse one file. Returns the card, or None plus every reason it could not be used."""
    base = (root or BANK_ROOT).parent
    display_path = str(path.relative_to(base)) if path.is_relative_to(base) else str(path)
    found: list[tuple[str, str]] = []

    def fail(message: str, field_name: str = "") -> tuple[None, list[Problem]]:
        return None, [Problem(display_path, message, field=field_name)]

    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return fail(f"cannot read the file: {error}")

    match = FRONTMATTER.match(raw)
    if not match:
        return fail("no YAML frontmatter between --- lines at the top of the file")

    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as error:
        return fail(f"cannot parse the frontmatter: {error}")
    if not isinstance(meta, dict):
        return fail("frontmatter is not a mapping of keys to values")

    sections, section_problems = _split_sections(match.group(2))
    found += [("", message) for message in section_problems]

    text: dict[str, str] = {}
    bands: dict[str, tuple[str, ...]] = {}
    follow_ups: tuple[FollowUp, ...] = ()
    extra: list[tuple[str, str]] = []

    for section in sections:
        key = KNOWN_SECTIONS.get(section["heading"].lower())
        if key is None:
            extra.append((section["heading"], section["text"]))
            continue
        if key == "answer_bands":
            for sub in section["sub"]:
                name = sub["heading"].strip().lower()
                if name not in BANDS:
                    found.append(
                        (
                            "answer_bands",
                            f"`### {sub['heading']}` is not a band name; "
                            f"allowed: {', '.join(BANDS)}",
                        )
                    )
                    continue
                bands[name] = _items(sub["text"])
            continue
        if key == "follow_ups":
            follow_ups = _follow_ups(section["text"])
            continue
        text[key] = section["text"]

    card_id = _text_field(meta, "id")
    if not card_id:
        found.append(("id", "id is missing or empty"))
    elif not ID_PATTERN.match(card_id):
        found.append(
            ("id", f"id {card_id!r} must be lower-case words joined by single hyphens")
        )

    version = _parse_optional_int(meta.get("schema_version"))
    if version is None:
        found.append(("schema_version", "schema_version is missing or not a whole number"))
    elif version not in SUPPORTED_SCHEMA_VERSIONS:
        found.append(
            (
                "schema_version",
                f"schema_version {version} is not supported; this tool reads "
                f"{', '.join(str(v) for v in SUPPORTED_SCHEMA_VERSIONS)}",
            )
        )

    title = _text_field(meta, "title")
    if not title:
        found.append(("title", "title is missing or empty"))

    declared_category = _text_field(meta, "category")
    if not declared_category:
        found.append(("category", "category is missing or empty"))
    elif declared_category != category:
        found.append(
            (
                "category",
                f"category {declared_category!r} does not match the directory {category!r}; "
                f"move the file to bank/{declared_category}/ or fix the field",
            )
        )

    topic = _text_field(meta, "topic")
    if not topic:
        found.append(("topic", "topic is missing or empty"))

    level = _text_field(meta, "level").lower()
    if not level:
        found.append(("level", "level is missing or empty"))
    elif level not in LEVELS:
        found.append(("level", f"level {level!r} is not one of {', '.join(LEVELS)}"))

    question_text = text.get("question", "").strip()
    if not question_text:
        found.append(("question", "the `## Ask` section is missing or empty"))

    tests = " ".join(text.get("tests", "").split()).strip()
    if not tests:
        found.append(("tests", "the `## Tests` section is missing or empty"))

    listen_for = _items(text.get("listen_for", ""))
    if not listen_for:
        found.append(("listen_for", "the `## Listen for` section is missing or empty"))

    ideal_answer = " ".join(text.get("ideal_answer", "").split()).strip()
    if not ideal_answer and version is not None and version >= IDEAL_ANSWER_SINCE:
        found.append(
            (
                "ideal_answer",
                "the `## Ideal minimal answer` section is missing or empty; it is required from "
                f"schema_version {IDEAL_ANSWER_SINCE}",
            )
        )

    if not bands:
        found.append(("answer_bands", "the `## Answer bands` section has no `###` band headings"))

    links = _parse_links(meta.get("links"), found)

    if found:
        return None, [
            Problem(display_path, message, card_id=card_id, field=field_name)
            for field_name, message in found
        ]

    return (
        Question(
            id=card_id,
            schema_version=int(version),
            title=title,
            question=question_text,
            category=declared_category,
            topic=topic,
            level=level,
            tests=tests,
            listen_for=listen_for,
            ideal_answer=ideal_answer,
            answer_bands={band: bands[band] for band in BANDS if band in bands},
            tags=_parse_str_list(meta.get("tags")),
            expected_knowledge=_items(text.get("expected_knowledge", "")),
            strong_signals=_items(text.get("strong_signals", "")),
            weak_signals=_items(text.get("weak_signals", "")),
            follow_ups=follow_ups,
            links=links,
            sources=_items(text.get("sources", "")),
            notes=text.get("notes", "").strip(),
            time_estimate_min=_parse_optional_int(meta.get("time_estimate_min")),
            order=_parse_optional_int(meta.get("order")),
            allow_term_leak=bool(meta.get("allow_term_leak")),
            extra=tuple(extra),
            path=display_path,
        ),
        [],
    )


def load_bank(root: Path | None = None) -> Bank:
    """Read every card under the bank root. A bad file is reported and skipped, never dropped."""
    bank_root = root or BANK_ROOT
    bank = Bank()
    if not bank_root.is_dir():
        bank.warnings.append(Problem(str(bank_root), "the bank directory does not exist"))
        return bank

    seen: dict[str, str] = {}
    for path in sorted(bank_root.rglob("*.md")):
        if any(part.startswith("_") for part in path.relative_to(bank_root).parts):
            continue
        relative = path.relative_to(bank_root)
        if len(relative.parts) < 2:
            bank.warnings.append(
                Problem(
                    str(relative),
                    "the file is not inside a category directory, so it has no category",
                    field="category",
                )
            )
            continue

        question, problems = load_question(path, relative.parts[0], bank_root)
        if question is None:
            bank.warnings.extend(problems)
            continue
        if question.id in seen:
            bank.warnings.append(
                Problem(
                    question.path,
                    f"duplicate id: already used by {seen[question.id]}",
                    card_id=question.id,
                    field="id",
                )
            )
            continue
        seen[question.id] = question.path
        bank.questions[question.id] = question

    if not bank.questions:
        bank.warnings.append(Problem(str(bank_root), "the bank contains no usable cards"))
    return bank
