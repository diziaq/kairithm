"""Aggregate the bands an interviewer assigned into a readable picture of one session.

Everything here is arithmetic over bands the interviewer typed in. The tool assigns no band and
draws no conclusion; it only adds up what was recorded and shows where the evidence is thin.

The 0-100 figure is an approximation with a stated formula, printed next to its inputs wherever
it is shown. It is not a percentile and it is not a verdict.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

from .levels import BAND_ORDINAL, BANDS, LEVEL_ORDINAL, LEVELS, delta

# 0 = intern, 100 = engineering tech lead. The five bands sit on that line at equal spacing.
BAND_POINTS = {"weak": 0, "junior": 25, "mid": 50, "senior": 75, "lead": 100}

# A band earned on a harder question is stronger evidence about the ceiling than the same band
# on an easy one, so the mean is weighted by the level the question was set to.
LEVEL_WEIGHT = {"junior": 1, "mid": 2, "senior": 3, "lead": 4}

FORMULA = (
    "sum(band points x level weight) / sum(level weight); "
    "band points weak 0, junior 25, mid 50, senior 75, lead 100; "
    "level weights junior 1, mid 2, senior 3, lead 4; "
    "skipped and unrated questions are left out of both sums"
)


@dataclass(frozen=True)
class Observation:
    """One answered question, reduced to what the aggregates need."""

    qid: str
    category: str
    topic: str
    level: str
    band: str

    @property
    def points(self) -> int:
        return BAND_POINTS[self.band]

    @property
    def weight(self) -> int:
        return LEVEL_WEIGHT[self.level]

    @property
    def gap(self) -> int:
        return delta(self.level, self.band)


@dataclass
class Score:
    value: int | None
    rated: int
    asked: int
    weight_total: int
    label: str
    confidence: str
    formula: str = FORMULA

    def as_dict(self) -> dict[str, object]:
        return {
            "value": self.value,
            "rated": self.rated,
            "asked": self.asked,
            "weight_total": self.weight_total,
            "label": self.label,
            "confidence": self.confidence,
            "formula": self.formula,
        }


@dataclass
class BucketRow:
    """One category or one topic, summarised."""

    name: str
    asked: int
    rated: int
    band_counts: dict[str, int] = field(default_factory=dict)
    deepest_band: str | None = None
    hardest_level_held: str | None = None
    mean_gap: float = 0.0
    score: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "asked": self.asked,
            "rated": self.rated,
            "band_counts": self.band_counts,
            "deepest_band": self.deepest_band,
            "hardest_level_held": self.hardest_level_held,
            "mean_gap": round(self.mean_gap, 2),
            "score": self.score,
        }


def nearest_band(value: float) -> str:
    """The band label closest to a 0-100 figure, so the number always carries a word."""
    return min(BANDS, key=lambda band: abs(BAND_POINTS[band] - value))


def confidence_of(rated: int, categories: int) -> str:
    """How much the figure is worth. A 100 from two questions is not a 100 from twenty."""
    if rated == 0:
        return "none"
    if rated < 4 or categories < 2:
        return "low"
    if rated < 8 or categories < 3:
        return "moderate"
    return "good"


def score(observations: Iterable[Observation]) -> Score:
    rows = list(observations)
    weight_total = sum(row.weight for row in rows)
    categories = len({row.category for row in rows})
    if not rows or weight_total == 0:
        return Score(
            value=None,
            rated=0,
            asked=0,
            weight_total=0,
            label="no evidence",
            confidence="none",
        )
    raw = sum(row.points * row.weight for row in rows) / weight_total
    return Score(
        value=round(raw),
        rated=len(rows),
        asked=len(rows),
        weight_total=weight_total,
        label=nearest_band(raw),
        confidence=confidence_of(len(rows), categories),
    )


def _bucket(observations: list[Observation], key: str) -> list[BucketRow]:
    groups: dict[str, list[Observation]] = {}
    for row in observations:
        groups.setdefault(getattr(row, key), []).append(row)

    out: list[BucketRow] = []
    for name, rows in groups.items():
        counts = Counter(row.band for row in rows)
        deepest = max(rows, key=lambda row: BAND_ORDINAL[row.band]).band
        # The hardest question the candidate answered at or above the level it was set to.
        held = [row for row in rows if row.gap >= 0]
        hardest = max(held, key=lambda row: LEVEL_ORDINAL[row.level]).level if held else None
        out.append(
            BucketRow(
                name=name,
                asked=len(rows),
                rated=len(rows),
                band_counts={band: counts[band] for band in BANDS if counts[band]},
                deepest_band=deepest,
                hardest_level_held=hardest,
                mean_gap=sum(row.gap for row in rows) / len(rows),
                score=score(rows).value,
            )
        )
    return sorted(out, key=lambda row: (-row.mean_gap, row.name))


def by_category(observations: Iterable[Observation]) -> list[BucketRow]:
    return _bucket(list(observations), "category")


def by_topic(observations: Iterable[Observation]) -> list[BucketRow]:
    return _bucket(list(observations), "topic")


def hot_spots(rows: list[BucketRow], minimum_rated: int = 1) -> dict[str, list[BucketRow]]:
    """Split buckets into the ones carrying the candidate and the ones dragging.

    The split is on mean gap: how far the assigned bands sat above or below the level the
    questions in that bucket were set to. A bucket at 0 met the bar and is neither.
    """
    usable = [row for row in rows if row.rated >= minimum_rated]
    return {
        "strong": [row for row in usable if row.mean_gap > 0],
        "at_bar": [row for row in usable if row.mean_gap == 0],
        "weak": sorted(
            [row for row in usable if row.mean_gap < 0], key=lambda row: (row.mean_gap, row.name)
        ),
    }


def band_matrix(observations: Iterable[Observation]) -> list[dict[str, object]]:
    """Counts for every (question level, assigned band) pair, for the depth chart."""
    counts = Counter((row.level, row.band) for row in observations)
    return [
        {"level": level, "band": band, "count": counts[(level, band)]}
        for level in LEVELS
        for band in BANDS
        if counts[(level, band)]
    ]
