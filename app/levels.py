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


# Consecutive answers at the level asked before the tool tries one step up. Three is enough to
# say "this is comfortably their level" and still leaves most of an interview for coverage.
PROBE_AFTER_EQUALS = 3

# A settled ceiling is a hypothesis, not a verdict. This many answers in a row above it means the
# bracket was built on a bad data point — one unlucky topic — and the estimate has to be retried.
CONTRADICT_AFTER = 3

# Two answers cannot bracket a ceiling. One unlucky topic at the start of an interview would
# otherwise settle the bar on the spot, and the run would spend questions climbing back out.
MIN_ANSWERS_TO_SETTLE = 3


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


# --- the running calibration --------------------------------------------------------------------
#
# `calibrate` above answers "given this one answer, what now" and is the brief's table verbatim.
# It is still what the interview screen shows as the advice for the answer just given.
#
# This section answers a different question: given everything recorded so far, what level should
# the next question be pitched at. Deriving that from the last answer alone makes it sawtooth —
# a candidate sitting between two levels answers above, then below, then above, for the whole
# interview, and the tool spends the session re-confirming a ceiling it found in three questions.
#
# So the running calibration moves one step at a time, and stops moving once the ceiling has been
# bracketed: some level was held, and the one above it was not. After that the point is coverage,
# not another attempt at the same wall.


@dataclass(frozen=True)
class Progress:
    """What every band recorded so far says, and what to pitch next."""

    level: str
    settled: bool
    ceiling: str | None
    probing: bool
    escape: str  # "" | "topic" | "category"
    equal_streak: int
    fail_streak: int
    above_streak: int
    held: tuple[str, ...]
    failed: tuple[str, ...]
    latest: Calibration | None
    note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "settled": self.settled,
            "ceiling": self.ceiling,
            "probing": self.probing,
            "escape": self.escape,
            "equal_streak": self.equal_streak,
            "fail_streak": self.fail_streak,
            "above_streak": self.above_streak,
            "held": list(self.held),
            "failed": list(self.failed),
            "latest": self.latest.as_dict() if self.latest else None,
            "note": self.note,
        }


def track(start_level: str, answers: list[tuple[str, str]]) -> Progress:
    """Replay every (question level, assigned band) pair in the order they were asked.

    Replaying rather than accumulating means revising an old band re-derives everything, so the
    interviewer can correct a mistake an hour later and the suggestions follow.
    """
    level = start_level if start_level in LEVEL_ORDINAL else "mid"
    held: list[str] = []
    failed: list[str] = []
    latest: Calibration | None = None
    equal_streak = 0
    fail_streak = 0
    above_streak = 0
    settled = False
    ceiling: str | None = None

    for question_level, band in answers:
        latest = calibrate(question_level, band)
        if latest.outcome in (EQUAL, ABOVE):
            held.append(question_level)
        else:
            failed.append(question_level)
        equal_streak = equal_streak + 1 if latest.outcome == EQUAL else 0
        above_streak = above_streak + 1 if latest.outcome == ABOVE else 0
        fail_streak = fail_streak + 1 if latest.outcome == TWO_OR_MORE_BELOW else 0

        if settled and ceiling is not None and above_streak >= CONTRADICT_AFTER:
            # Out-answered the estimate three times running. Forget the single failure the
            # bracket was built on — it was one bad topic, not a ceiling — and climb again.
            stale = LEVEL_ORDINAL[ceiling] + 1
            failed = [name for name in failed if LEVEL_ORDINAL[name] != stale]
            level = clamp_level(stale)
            settled = False
            ceiling = None

        top_held = max((LEVEL_ORDINAL[name] for name in held), default=None)
        failed_levels = {LEVEL_ORDINAL[name] for name in failed}

        # Bracketed: the best level they held was tried one higher, and that one did not hold.
        # Failing a question at a level they also hold is inconsistency, not a ceiling, so the
        # test is the level immediately above rather than "anything at or below".
        answered = len(held) + len(failed)
        if (
            not settled
            and answered >= MIN_ANSWERS_TO_SETTLE
            and top_held is not None
            and top_held + 1 in failed_levels
        ):
            settled = True
            ceiling = clamp_level(top_held)
            level = ceiling
        elif not settled:
            # One step towards what the last answer asked for, never a jump.
            here = LEVEL_ORDINAL[level]
            wanted = LEVEL_ORDINAL[latest.next_level]
            level = clamp_level(here + (1 if wanted > here else -1 if wanted < here else 0))

    probing = not settled and equal_streak >= PROBE_AFTER_EQUALS
    serve = clamp_level(LEVEL_ORDINAL[level] + 1) if probing else level

    if fail_streak >= 2:
        escape = "category"
    elif latest is not None and latest.change_topic:
        escape = "topic"
    else:
        escape = ""

    if settled:
        note = (
            f"The ceiling looks like {ceiling}. Widening coverage at that level rather than "
            f"pushing at the same wall again."
        )
    elif probing:
        note = (
            f"{equal_streak} answers at the level asked. Trying one {serve} question to find "
            f"where it stops."
        )
    elif latest is not None:
        note = latest.advice
    else:
        note = "No band assigned yet."

    return Progress(
        level=serve,
        settled=settled,
        ceiling=ceiling,
        probing=probing,
        escape=escape,
        equal_streak=equal_streak,
        fail_streak=fail_streak,
        above_streak=above_streak,
        held=tuple(held),
        failed=tuple(failed),
        latest=latest,
        note=note,
    )
