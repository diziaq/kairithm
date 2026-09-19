"""Pool building and question ordering.

Every mode here is deterministic. Random and adaptive both take a seed, and the seed is stored in
the session, so a run can be repeated exactly from the scorecard.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from .bank import MAX_DIFFICULTY, MIN_DIFFICULTY, Bank, Question
from .config import DEFAULT_START_DIFFICULTY

SEQUENTIAL = "sequential"
RANDOM = "random"
DIFFICULTY_ASC = "difficulty_asc"
ADAPTIVE = "adaptive"
MANUAL = "manual"

MODES = (SEQUENTIAL, RANDOM, DIFFICULTY_ASC, ADAPTIVE, MANUAL)

STEP_UP_FROM = 4
STEP_DOWN_TO = 2


@dataclass(frozen=True)
class PoolFilters:
    topics: tuple[str, ...] = ()
    include_tags: tuple[str, ...] = ()
    exclude_tags: tuple[str, ...] = ()
    difficulty_min: int = MIN_DIFFICULTY
    difficulty_max: int = MAX_DIFFICULTY
    limit: int | None = None
    manual_ids: tuple[str, ...] = ()
    exclude_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PoolFilters":
        return cls(
            topics=tuple(raw.get("topics") or ()),
            include_tags=tuple(raw.get("include_tags") or ()),
            exclude_tags=tuple(raw.get("exclude_tags") or ()),
            difficulty_min=int(raw.get("difficulty_min", MIN_DIFFICULTY)),
            difficulty_max=int(raw.get("difficulty_max", MAX_DIFFICULTY)),
            limit=raw.get("limit") if raw.get("limit") not in (None, "", 0) else None,
            manual_ids=tuple(raw.get("manual_ids") or ()),
            exclude_ids=tuple(raw.get("exclude_ids") or ()),
        )


def build_pool(bank: Bank, filters: PoolFilters) -> list[Question]:
    """Apply the stage one filters and return the matching questions.

    Manual ids win over every filter. The interviewer picked those by hand, so the tool serves
    exactly them, in the order given.
    """
    if filters.manual_ids:
        picked = [bank.get(qid) for qid in filters.manual_ids]
        return [q for q in picked if q is not None]

    excluded = set(filters.exclude_ids)
    include = set(filters.include_tags)
    exclude = set(filters.exclude_tags)
    low, high = sorted((filters.difficulty_min, filters.difficulty_max))

    matched: list[Question] = []
    for question in bank.questions.values():
        if question.id in excluded:
            continue
        if filters.topics and question.topic not in filters.topics:
            continue
        if not low <= question.difficulty <= high:
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
    """Explicit order first, then topic and file name. Questions without order go last."""
    has_order = 0 if question.order is not None else 1
    return (has_order, question.order or 0, question.topic, question.stem)


def order_pool(pool: list[Question], mode: str, seed: int) -> list[Question]:
    """Return the served order for a non-adaptive mode.

    Adaptive returns an empty list. It has no fixed order, because each question is chosen from
    the rating just given.
    """
    if mode == ADAPTIVE:
        return []
    if mode in (SEQUENTIAL, MANUAL):
        return list(pool) if mode == MANUAL else sorted(pool, key=_sequential_key)
    if mode == RANDOM:
        shuffled = sorted(pool, key=_sequential_key)
        random.Random(seed).shuffle(shuffled)
        return shuffled
    if mode == DIFFICULTY_ASC:
        shuffled = sorted(pool, key=_sequential_key)
        random.Random(seed).shuffle(shuffled)
        return sorted(shuffled, key=lambda q: q.difficulty)
    raise ValueError(f"unknown order mode: {mode}")


def rating_to_step(rating: int | None, skipped: bool) -> int:
    """Map one rating to a change in target difficulty. A skip holds the level."""
    if skipped or rating is None:
        return 0
    if rating >= STEP_UP_FROM:
        return 1
    if rating <= STEP_DOWN_TO:
        return -1
    return 0


def next_target_difficulty(previous_target: int, rating: int | None, skipped: bool) -> int:
    step = rating_to_step(rating, skipped)
    return max(MIN_DIFFICULTY, min(MAX_DIFFICULTY, previous_target + step))


def choose_adaptive(
    pool: list[Question],
    served_ids: list[str],
    target: int,
    seed: int,
    covered_tags: set[str],
) -> tuple[Question, str] | None:
    """Pick the next question and say why it was picked.

    The rules, in order:
    1. never repeat a question inside one session;
    2. prefer the target difficulty, then the nearest level that still has questions;
    3. inside that level, prefer a question carrying a tag this session has not covered, so the
       mode does not tunnel into one subject;
    4. break the remaining tie with the session seed, so the run repeats exactly.
    """
    remaining = [q for q in pool if q.id not in served_ids]
    if not remaining:
        return None

    levels = sorted(
        {q.difficulty for q in remaining},
        key=lambda level: (abs(level - target), level),
    )
    level = levels[0]
    at_level = [q for q in remaining if q.difficulty == level]

    fresh = [q for q in at_level if set(q.tags) - covered_tags]
    candidates = fresh or at_level

    picker = random.Random(f"{seed}:{len(served_ids)}")
    chosen = picker.choice(sorted(candidates, key=lambda q: q.id))

    if level == target and fresh:
        reason = f"target difficulty {target}, new tag"
    elif level == target:
        reason = f"target difficulty {target}"
    elif fresh:
        reason = f"nearest level {level} to target {target}, new tag"
    else:
        reason = f"nearest level {level} to target {target}"
    return chosen, reason


def start_target(setup: dict[str, Any]) -> int:
    raw = setup.get("start_difficulty")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_START_DIFFICULTY
    return max(MIN_DIFFICULTY, min(MAX_DIFFICULTY, value))
