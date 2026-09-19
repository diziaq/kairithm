"""The two vocabularies the tool reasons about, and the table that connects them.

`level` is the seniority a QUESTION is aimed at.
`band`  is an observable description of how a candidate ANSWERED one.

They are deliberately not the same scale. A `mid` answer to a `senior` question is the
interesting case: the candidate is productive, but not at the bar the question was set to,
and the next question should not be another `senior` one on that topic.

The interviewer assigns the band. Nothing in this module ever does.
"""

from __future__ import annotations

from dataclasses import dataclass

LEVELS = ("junior", "mid", "senior", "lead")
BANDS = ("weak", "junior", "mid", "senior", "lead")

# `weak` has no matching level, so the two scales share an origin at `junior`.
# delta = BAND_ORDINAL[band] - LEVEL_ORDINAL[level] is then the number of bands the answer
# sits above or below the question, which is exactly what the navigation table keys on.
LEVEL_ORDINAL = {name: index + 1 for index, name in enumerate(LEVELS)}
BAND_ORDINAL = {name: index for index, name in enumerate(BANDS)}

LINK_KINDS = ("deeper", "shallower", "related", "prerequisite")
INVERSE_LINK = {"deeper": "shallower", "shallower": "deeper", "related": "related"}

TWO_OR_MORE_BELOW = "two_or_more_below"
ONE_BELOW = "one_below"
EQUAL = "equal"
ABOVE = "above"


@dataclass(frozen=True)
class Calibration:
    """What the tool suggests after one band was assigned. Always advisory, never applied."""

    outcome: str
    next_level: str
    prefer: tuple[str, ...]
    change_topic: bool
    advice: str

    def as_dict(self) -> dict[str, object]:
        return {
            "outcome": self.outcome,
            "next_level": self.next_level,
            "prefer": list(self.prefer),
            "change_topic": self.change_topic,
            "advice": self.advice,
        }


def clamp_level(ordinal: int) -> str:
    """Map any ordinal onto a level name. `weak` (0) floors to `junior`."""
    return LEVELS[max(1, min(len(LEVELS), ordinal)) - 1]


def delta(level: str, band: str) -> int:
    """How many bands the answer sat above (+) or below (-) the question's level."""
    return BAND_ORDINAL[band] - LEVEL_ORDINAL[level]


def calibrate(level: str, band: str) -> Calibration:
    """The suggestion table from the brief, section 6, as one function.

    The next level is always the band that was just observed, floored at `junior`. That single
    rule reproduces every row: a `mid` answer to a `senior` question suggests `mid` next, a
    `senior` answer to a `mid` question suggests `senior` next, and a `weak` answer to anything
    suggests `junior`.
    """
    if level not in LEVEL_ORDINAL:
        raise ValueError(f"unknown level: {level!r}")
    if band not in BAND_ORDINAL:
        raise ValueError(f"unknown band: {band!r}")

    gap = delta(level, band)
    next_level = clamp_level(BAND_ORDINAL[band])

    if gap <= -2:
        return Calibration(
            outcome=TWO_OR_MORE_BELOW,
            next_level=next_level,
            prefer=("shallower", "prerequisite", "related"),
            change_topic=True,
            advice=(
                f"Two bands or more below the question. Drop to {next_level} "
                f"and consider moving to another topic — repeating this one confirms a failure "
                f"rather than finding a ceiling."
            ),
        )
    if gap == -1:
        return Calibration(
            outcome=ONE_BELOW,
            next_level=next_level,
            prefer=("shallower", "related"),
            change_topic=True,
            advice=(
                f"One band below the question. Go shallower in this topic, "
                f"or stay at {level} in an adjacent topic."
            ),
        )
    if gap == 0:
        return Calibration(
            outcome=EQUAL,
            next_level=next_level,
            prefer=("related", "deeper"),
            change_topic=False,
            advice=(
                f"At the level the question was set to. Move sideways at {next_level}, "
                f"or go deeper to find where it stops."
            ),
        )
    return Calibration(
        outcome=ABOVE,
        next_level=next_level,
        prefer=("deeper", "related"),
        change_topic=False,
        advice=(
            f"Above the level the question was set to. Go deeper; "
            f"the bar for this topic moves to {next_level}."
        ),
    )
