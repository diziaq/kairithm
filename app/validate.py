"""Check the whole bank and report every problem with the file, the card id and the field.

One implementation, two surfaces: the CLI below, and `/api/bank`, which merges the same list into
the warnings the home screen already renders. A card that fails is reported in both places and is
never silently missing from the bank.

Run it with:

    .venv/bin/python -m app.validate
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from .bank import Bank, Problem, Question, load_bank
from .levels import BANDS, LINK_KINDS

ERROR = "error"
WARNING = "warning"

MIN_FOLLOW_UPS = 2
MAX_FOLLOW_UPS = 4
MIN_BAND_WORDS = 3

WORD = re.compile(r"[a-z0-9]+")
BACKTICKED = re.compile(r"`([^`]+)`")
TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*")

# Length at which a plain word is distinctive enough to be worth flagging on its own.
# Below this the check produces noise ("twenty", "cover", "claim") and gets ignored, which is
# worse than not running it. Shorter technical terms still get caught by the backtick,
# hyphenation and internal-capital rules.
LONG_TERM = 10
CONCEPT_TERM = 7

# A band bullet made only of these is a verdict, not an observation. "excellent understanding"
# tells the next reader nothing about what the candidate actually said.
VERDICT_WORDS = frozenset(
    """
    good great excellent perfect strong solid fine ok okay adequate average acceptable
    poor bad terrible awful weak shaky limited lacking nothing everything
    understanding knowledge grasp command mastery awareness
    understands knows grasps masters
    expert competent capable confident unclear confused wrong right correct incorrect
    well badly clearly vaguely fully partially completely
    junior mid senior lead level answer answers response
    """.split()
)

# Words that carry no signal for the leak check. Guidance verbs are in here on purpose: a
# follow-up that shares "explains" with a band is not leaking anything.
STOPWORDS = frozenset(
    """
    about above after again against along already also although always among another answer
    answers anything around aside asked asking because become becomes been before behind being
    below better between both bring builds cannot change changes come comes common connects
    consider could describe describes design different discuss discusses does doing done during
    each either else enough even every everything example examples explain explains fails first
    from gets gives given goes going happen happens have having here however identify includes
    instead into itself just keeps knows known lists looks made make makes many mentions might
    more most moves much must names needs never notes often only other others over point points
    prefer probably problem problems provide provides real really refers relies rather same says
    separate several should shows since some something sometimes specific start starts state
    states still such takes talks tell tells than that their them then there these they thing
    things think this those through time times treat treats under until uses using very want
    what when where which while will with within without work works would your
    """.split()
)

# Common in this domain and in almost every card, so sharing one of these with the guidance is
# not evidence that a follow-up gave anything away.
DOMAIN_FILLER = frozenset(
    """
    application applications approach architecture behaviour behavior business component
    components condition configuration connection connections consumer consumers container
    customer database databases development difference environment example exception expected
    experience implementation instance interface message messages operation operations parameter
    performance pipeline platform position problem processing producer producers production
    property question reference request requests resource response responses scenario service
    services situation solution something standard structure system systems technical
    """.split()
)

SUFFIXES = ("ies", "ing", "ers", "ed", "es", "s")


def _stem(word: str) -> str:
    """Crude suffix stripping, so `retries` and `retry` are treated as the same term."""
    word = word.strip("`-")
    if word.endswith("ies") and len(word) > 5:
        return word[:-3] + "y"
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _common(word: str) -> bool:
    return word in STOPWORDS or word in VERDICT_WORDS or word in DOMAIN_FILLER


def _terms(text: str, minimum: int = LONG_TERM) -> set[str]:
    """The terms in a piece of text distinctive enough that repeating one gives something away.

    Four things qualify: a token in backticks, a hyphenated compound, a token with an internal
    capital, and a long word that is not ordinary English or ordinary shop talk. Everything else
    is vocabulary any sentence about the topic would use anyway.
    """
    out: set[str] = set()

    def add(raw: str) -> None:
        word = raw.lower().strip("-")
        if word and not _common(word):
            out.add(_stem(word))

    for match in BACKTICKED.finditer(text):
        for token in TOKEN.finditer(match.group(1)):
            add(token.group(0))

    for match in TOKEN.finditer(text):
        token = match.group(0)
        if "-" in token and len(token) >= 7:
            add(token)
            continue
        if any(character.isupper() for character in token[1:]):
            add(token)
            continue
        if len(token) >= minimum:
            add(token)
    return out


def _is_verdict_only(bullet: str) -> bool:
    words = [w.group(0) for w in WORD.finditer(bullet.lower())]
    meaningful = [w for w in words if w not in STOPWORDS]
    if not meaningful:
        return True
    if len(words) < MIN_BAND_WORDS:
        return True
    return all(_stem(word) in VERDICT_WORDS or word in VERDICT_WORDS for word in meaningful)


def _check_bands(question: Question) -> list[Problem]:
    found: list[Problem] = []
    for band in BANDS:
        bullets = question.answer_bands.get(band)
        if bullets is None:
            continue
        if not bullets:
            found.append(
                Problem(
                    question.path,
                    f"the `{band}` band has no bullets; remove the heading or describe what "
                    f"an answer in that band looks like",
                    card_id=question.id,
                    field=f"answer_bands.{band}",
                )
            )
            continue
        for bullet in bullets:
            if _is_verdict_only(bullet):
                found.append(
                    Problem(
                        question.path,
                        f"the `{band}` band bullet {bullet!r} is a verdict, not an observation; "
                        f"say what the candidate does or says",
                        card_id=question.id,
                        field=f"answer_bands.{band}",
                    )
                )
    return found


def _check_links(bank: Bank, question: Question) -> list[Problem]:
    found: list[Problem] = []
    for kind in LINK_KINDS:
        for target_id in question.links.get(kind, ()):
            if target_id == question.id:
                found.append(
                    Problem(
                        question.path,
                        f"`{kind}` links the card to itself",
                        card_id=question.id,
                        field=f"links.{kind}",
                    )
                )
                continue
            target = bank.get(target_id)
            if target is None:
                found.append(
                    Problem(
                        question.path,
                        f"`{kind}` points at {target_id!r}, which is not a card in the bank",
                        card_id=question.id,
                        field=f"links.{kind}",
                    )
                )
                continue
            # Inverses are derived at load time, so a missing one is fine. A declared one that
            # points the wrong way is a mistake, because both files now disagree.
            if kind == "deeper" and question.id in target.links.get("deeper", ()):
                found.append(
                    Problem(
                        question.path,
                        f"{target_id!r} also lists this card as `deeper`; one of the two should "
                        f"be `shallower`",
                        card_id=question.id,
                        field="links.deeper",
                    )
                )
            if kind == "shallower" and question.id in target.links.get("shallower", ()):
                found.append(
                    Problem(
                        question.path,
                        f"{target_id!r} also lists this card as `shallower`; one of the two "
                        f"should be `deeper`",
                        card_id=question.id,
                        field="links.shallower",
                    )
                )
            if kind == "deeper" and target.level_ordinal < question.level_ordinal:
                found.append(
                    Problem(
                        question.path,
                        f"`deeper` points at {target_id!r}, which is {target.level} — below this "
                        f"card's {question.level}",
                        card_id=question.id,
                        field="links.deeper",
                        severity=WARNING,
                    )
                )
    return found


def _check_follow_ups(question: Question) -> list[Problem]:
    found: list[Problem] = []
    count = len(question.follow_ups)
    if count < MIN_FOLLOW_UPS or count > MAX_FOLLOW_UPS:
        found.append(
            Problem(
                question.path,
                f"{count} follow-up(s); the bank aims for {MIN_FOLLOW_UPS} to {MAX_FOLLOW_UPS}",
                card_id=question.id,
                field="follow_ups",
                severity=WARNING,
            )
        )
    if question.allow_term_leak:
        return found

    guidance = " ".join(
        [
            *question.listen_for,
            *(bullet for bullets in question.answer_bands.values() for bullet in bullets),
        ]
    )
    # `Expected knowledge` is the explicit list of concepts being waited for, so the bar for a
    # term coming from there is lower than for prose in the bands.
    wanted = _terms(guidance) | _terms(" ".join(question.expected_knowledge), CONCEPT_TERM)

    # Anything the card already says out loud — the question, the title, the topic, the tags —
    # is shared vocabulary, not a giveaway. A follow-up has to be able to refer to the subject.
    framing = _terms(
        " ".join([question.question, question.title, question.topic, *question.tags]),
        CONCEPT_TERM,
    )
    leakable = wanted - framing

    for follow_up in question.follow_ups:
        shared = sorted(_terms(follow_up.text, CONCEPT_TERM) & leakable)
        if shared:
            found.append(
                Problem(
                    question.path,
                    f"follow-up {follow_up.text!r} names {', '.join(shared)}, which the guidance "
                    f"is waiting to hear; describe the situation instead, or set "
                    f"`allow_term_leak: true` if the card exists to test the word",
                    card_id=question.id,
                    field="follow_ups",
                    severity=WARNING,
                )
            )
    return found


def _check_filename(question: Question) -> list[Problem]:
    if Path(question.path).stem == question.id:
        return []
    return [
        Problem(
            question.path,
            f"the file name does not match the id {question.id!r}; the convention is "
            f"bank/{question.category}/{question.id}.md",
            card_id=question.id,
            field="id",
            severity=WARNING,
        )
    ]


def _check_order_collisions(bank: Bank) -> list[Problem]:
    """Two cards in one category claiming the same position in sequential mode.

    Not fatal — the sort falls back to the id, so a run is still deterministic — but the author
    asked for a position and did not get it, and nothing else would ever tell them.
    """
    claimed: dict[tuple[str, int], list[Question]] = defaultdict(list)
    for question in bank.questions.values():
        if question.order is not None:
            claimed[(question.category, question.order)].append(question)

    found: list[Problem] = []
    for (category, order), questions in claimed.items():
        if len(questions) < 2:
            continue
        for question in sorted(questions, key=lambda q: q.id):
            others = [q.id for q in questions if q.id != question.id]
            found.append(
                Problem(
                    question.path,
                    f"order {order} is also claimed in {category} by {', '.join(sorted(others))}; "
                    f"sequential mode will fall back to the id",
                    card_id=question.id,
                    field="order",
                    severity=WARNING,
                )
            )
    return found


def validate_bank(bank: Bank) -> list[Problem]:
    """Every problem in the bank: the loader's, plus everything only visible across cards."""
    found: list[Problem] = list(bank.warnings)
    for question in bank.questions.values():
        found += _check_bands(question)
        found += _check_links(bank, question)
        found += _check_follow_ups(question)
        found += _check_filename(question)
    found += _check_order_collisions(bank)
    return sorted(found, key=lambda p: (p.severity != ERROR, p.path, p.field, p.problem))


def errors(problems: list[Problem]) -> list[Problem]:
    return [p for p in problems if p.severity == ERROR]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the question bank.")
    parser.add_argument("bank", nargs="?", type=Path, default=None, help="bank directory")
    parser.add_argument("-q", "--quiet", action="store_true", help="print errors only")
    args = parser.parse_args(argv)

    bank = load_bank(args.bank)
    problems = validate_bank(bank)
    failures = errors(problems)

    for problem in problems:
        if args.quiet and problem.severity != ERROR:
            continue
        print(problem.line(), file=sys.stderr if problem.severity == ERROR else sys.stdout)

    print(
        f"\n{len(bank.questions)} card(s) loaded, "
        f"{len(failures)} error(s), {len(problems) - len(failures)} warning(s)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
