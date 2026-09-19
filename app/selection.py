"""Pool building and question ordering.

Every mode here is deterministic. Random and adaptive both take a seed, and the seed is stored in
the session, so a run can be repeated exactly from the scorecard.

Nothing in this module assigns a band or advances the interview. It answers one question — given
what has been asked and what the interviewer recorded, which cards are worth offering next — and
the interviewer is free to ignore all of it.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from .bank import Bank, Question
from .levels import LEVEL_ORDINAL, LEVELS, LINK_KINDS, Calibration

SEQUENTIAL = "sequential"
RANDOM = "random"
LEVEL_ASC = "level_asc"
ADAPTIVE = "adaptive"
MANUAL = "manual"

MODES = (SEQUENTIAL, RANDOM, LEVEL_ASC, ADAPTIVE, MANUAL)

DEFAULT_START_LEVEL = "mid"


@dataclass(frozen=True)
class PoolFilters:
    categories: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    include_tags: tuple[str, ...] = ()
    exclude_tags: tuple[str, ...] = ()
    levels: tuple[str, ...] = ()
    limit: int | None = None
    manual_ids: tuple[str, ...] = ()
    exclude_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PoolFilters":
        levels = tuple(str(v).lower() for v in (raw.get("levels") or ()) if str(v).lower() in LEVELS)
        return cls(
            categories=tuple(raw.get("categories") or ()),
            topics=tuple(raw.get("topics") or ()),
            include_tags=tuple(raw.get("include_tags") or ()),
            exclude_tags=tuple(raw.get("exclude_tags") or ()),
            levels=levels,
            limit=raw.get("limit") if raw.get("limit") not in (None, "", 0) else None,
            manual_ids=tuple(raw.get("manual_ids") or ()),
            exclude_ids=tuple(raw.get("exclude_ids") or ()),
        )


def build_pool(bank: Bank, filters: PoolFilters) -> list[Question]:
    """Apply the stage one filters and return the matching cards.

    Manual ids win over every filter. The interviewer picked those by hand, so the tool serves
    exactly them, in the order given.
    """
    if filters.manual_ids:
        picked = [bank.get(qid) for qid in filters.manual_ids]
        return [q for q in picked if q is not None]

    excluded = set(filters.exclude_ids)
    include = set(filters.include_tags)
    exclude = set(filters.exclude_tags)
    levels = set(filters.levels)

    matched: list[Question] = []
    for question in bank.questions.values():
        if question.id in excluded:
            continue
        if filters.categories and question.category not in filters.categories:
            continue
        if filters.topics and question.topic not in filters.topics:
            continue
        if levels and question.level not in levels:
            continue
        tags = set(question.tags)
        if include and not (tags & include):
            continue
        if exclude and (tags & exclude):
            continue
        matched.append(question)

    matched.sort(key=_sequential_key)
    if filters.limit:
        matched = matched[: int(filters.limit)]
    return matched


def _sequential_key(question: Question) -> tuple[int, int, str, str]:
    """Explicit order first, then category and id. Cards without `order` go last."""
    has_order = 0 if question.order is not None else 1
    return (has_order, question.order or 0, question.category, question.id)


def order_pool(pool: list[Question], mode: str, seed: int) -> list[Question]:
    """Return the served order for a non-adaptive mode.

    Adaptive returns an empty list. It has no fixed order, because each card is chosen from the
    band the interviewer assigned to the one before it.
    """
    if mode == ADAPTIVE:
        return []
    if mode == MANUAL:
        return list(pool)
    if mode == SEQUENTIAL:
        return sorted(pool, key=_sequential_key)
    if mode == RANDOM:
        shuffled = sorted(pool, key=_sequential_key)
        random.Random(seed).shuffle(shuffled)
        return shuffled
    if mode == LEVEL_ASC:
        shuffled = sorted(pool, key=_sequential_key)
        random.Random(seed).shuffle(shuffled)
        return sorted(shuffled, key=lambda q: LEVEL_ORDINAL[q.level])
    raise ValueError(f"unknown order mode: {mode}")


def start_level(setup: dict[str, Any]) -> str:
    raw = str(setup.get("start_level") or "").strip().lower()
    return raw if raw in LEVELS else DEFAULT_START_LEVEL


@dataclass(frozen=True)
class Suggestion:
    """One card the tool is offering. `kind` says where it came from, so the UI can group them."""

    question_id: str
    kind: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"question_id": self.question_id, "kind": self.kind, "reason": self.reason}


def suggest(
    bank: Bank,
    current: Question | None,
    calibration: Calibration | None,
    target_level: str,
    served_ids: list[str],
    pool: list[Question] | None = None,
    limit: int = 8,
) -> list[Suggestion]:
    """Cards worth offering next, best first. Always advisory.

    Order of preference:
    1. links out of the current card, in the order the calibration asks for;
    2. cards at the target level in a topic this session has not touched;
    3. cards at the target level anywhere in the pool.

    Nothing is filtered out for being a poor fit — the interviewer can pick any card in the bank
    at any time from the browser. This list only decides what is one click away.
    """
    served = set(served_ids)
    out: list[Suggestion] = []
    taken: set[str] = set()

    def offer(question_id: str, kind: str, reason: str) -> None:
        if question_id in served or question_id in taken or bank.get(question_id) is None:
            return
        taken.add(question_id)
        out.append(Suggestion(question_id, kind, reason))

    if current is not None:
        links = bank.resolved_links(current.id)
        order = list(calibration.prefer) if calibration else list(LINK_KINDS)
        order += [kind for kind in LINK_KINDS if kind not in order]
        for kind in order:
            for target_id in links.get(kind, []):
                offer(target_id, kind, f"{kind} than {current.title!r}")

    candidates = pool if pool is not None else list(bank.questions.values())
    covered_topics = {bank.get(qid).topic for qid in served if bank.get(qid)}

    at_target = [q for q in candidates if q.level == target_level and q.id not in served]
    fresh_topic = [q for q in at_target if q.topic not in covered_topics]
    if calibration and calibration.change_topic:
        ordered = fresh_topic + [q for q in at_target if q.topic in covered_topics]
    else:
        ordered = at_target
    for question in ordered:
        note = "topic not covered yet" if question.topic not in covered_topics else "same topic"
        offer(question.id, "level", f"{target_level} in {question.topic} — {note}")

    return out[:limit]


def choose_adaptive(
    pool: list[Question],
    served_ids: list[str],
    target_level: str,
    seed: int,
    covered_topics: set[str],
) -> tuple[Question, str] | None:
    """Pick the card adaptive mode serves next, and say why it was picked.

    The rules, in order:
    1. never repeat a card inside one session;
    2. prefer the target level, then the nearest level that still has cards;
    3. inside that level, prefer a topic this session has not covered, so the mode does not
       tunnel into one subject;
    4. break the remaining tie with the session seed, so the run repeats exactly.
    """
    remaining = [q for q in pool if q.id not in served_ids]
    if not remaining:
        return None

    target_ordinal = LEVEL_ORDINAL[target_level]
    levels = sorted(
        {q.level for q in remaining},
        key=lambda name: (abs(LEVEL_ORDINAL[name] - target_ordinal), LEVEL_ORDINAL[name]),
    )
    level = levels[0]
    at_level = [q for q in remaining if q.level == level]

    fresh = [q for q in at_level if q.topic not in covered_topics]
    candidates = fresh or at_level

    picker = random.Random(f"{seed}:{len(served_ids)}")
    chosen = picker.choice(sorted(candidates, key=lambda q: q.id))

    where = "target level" if level == target_level else f"nearest level to target {target_level}"
    topic = ", topic not covered yet" if fresh else ""
    return chosen, f"{where} {level}{topic}"
