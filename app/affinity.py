"""How closely two cards sit to each other, and how to walk a pool so it reads as a chain.

An interview that jumps from Java concurrency to SAP RFC to Spring transactions and back costs
the candidate a context switch on every question, and costs the interviewer the thread of the
conversation. Questions belong in blocks: work through an area, then move to the nearest
adjacent one.

Nothing new has to be authored for this. The bank already carries four signals of relatedness,
and they are combined into one number:

| Signal                     | Weight | Why that weight |
|----------------------------|--------|-----------------|
| Same topic                 |  0.8   | The tightest natural block. |
| Same category              |  0.5   | Stacks with topic, so same-topic scores 1.3. |
| An explicit link, any kind |  0.9   | Hand-authored: somebody said these belong together. |
| Shared tags                |  0-0.35| Jaccard overlap. Connects areas nothing else joins. |

The numbers matter only in relation to each other. Two consequences are deliberate:

- A same-topic card (1.3) outranks a cross-category link (0.9 + tags), so a topic is finished
  before the chain leaves it.
- A `deeper` link inside a topic scores 2.2 and wins outright, so an authored progression is
  followed exactly.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Iterable

from .bank import Bank, Question

SAME_TOPIC = 0.8
SAME_CATEGORY = 0.5
EXPLICIT_LINK = 0.9
SHARED_TAGS = 0.35


def link_map(bank: Bank) -> dict[str, set[str]]:
    """Every explicitly linked pair, both ways, computed once per walk.

    Direction does not matter here. `deeper` and `shallower` are the same statement about
    closeness; which end of it a card sits on is the navigation question, not this one.
    """
    out: dict[str, set[str]] = defaultdict(set)
    for question in bank.questions.values():
        for ids in question.links.values():
            for other in ids:
                out[question.id].add(other)
                out[other].add(question.id)
    return out


def affinity(a: Question, b: Question, linked: dict[str, set[str]] | None = None) -> float:
    """How closely two cards sit. Higher is nearer; 0 means nothing connects them."""
    if a.id == b.id:
        return 0.0
    score = 0.0
    if a.category == b.category:
        score += SAME_CATEGORY
        if a.topic == b.topic:
            score += SAME_TOPIC
    if linked and b.id in linked.get(a.id, ()):
        score += EXPLICIT_LINK
    if a.tags and b.tags:
        shared = set(a.tags) & set(b.tags)
        if shared:
            score += SHARED_TAGS * len(shared) / len(set(a.tags) | set(b.tags))
    return score


def explain(a: Question, b: Question, linked: dict[str, set[str]] | None = None) -> str:
    """Why the chain moved from one card to the next. Ends up in the scorecard."""
    if linked and b.id in linked.get(a.id, ()):
        return f"linked from {a.topic}"
    if a.category == b.category and a.topic == b.topic:
        return f"same topic, {b.topic}"
    if a.category == b.category:
        return f"{a.topic} → {b.topic}, still {b.category}"
    shared = sorted(set(a.tags) & set(b.tags))
    if shared:
        return f"{a.category} → {b.category} via {', '.join(shared)}"
    return f"new block, {b.category} / {b.topic}"


def chain(
    bank: Bank,
    pool: Iterable[Question],
    rank: Callable[[Question], object],
    anchor: Question | None = None,
) -> list[tuple[Question, str]]:
    """Walk the pool nearest-first, returning each card with the reason it came next.

    `rank` decides two things: which card opens the chain, and which of two equally related
    cards is taken first. That is the only place a mode's own character enters — sequential
    ranks by the `order` field, random by a seeded shuffle — so every mode produces blocks
    while still behaving like itself.

    `anchor` starts the walk next to a card that is not in the pool, which is how the level
    bands in level-ascending mode are joined into one continuous chain.
    """
    remaining = sorted(pool, key=rank)
    if not remaining:
        return []

    linked = link_map(bank)
    out: list[tuple[Question, str]] = []

    if anchor is None:
        first = remaining.pop(0)
        out.append((first, f"opens on {first.category} / {first.topic}"))
    else:
        index = _nearest(anchor, remaining, linked)
        picked = remaining.pop(index)
        out.append((picked, explain(anchor, picked, linked)))

    while remaining:
        current = out[-1][0]
        index = _nearest(current, remaining, linked)
        picked = remaining.pop(index)
        out.append((picked, explain(current, picked, linked)))
    return out


def _nearest(current: Question, remaining: list[Question], linked: dict[str, set[str]]) -> int:
    """Index of the closest card. `remaining` is in rank order, so ties fall to the earlier one."""
    return max(
        range(len(remaining)),
        key=lambda index: (affinity(current, remaining[index], linked), -index),
    )


def nearest_of(
    current: Question | None,
    candidates: list[Question],
    linked: dict[str, set[str]] | None = None,
) -> list[Question]:
    """`candidates` sorted by closeness to `current`, most related first. Stable otherwise."""
    if current is None:
        return list(candidates)
    ordered = list(enumerate(candidates))
    ordered.sort(key=lambda pair: (-affinity(current, pair[1], linked), pair[0]))
    return [question for _, question in ordered]
