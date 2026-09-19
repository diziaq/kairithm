"""Render scorecard.md from a session.

Two rules shape this file.

Facts and conclusions are kept apart structurally. Everything above `## Assessment` is either
something the interviewer recorded or arithmetic over it. Everything under `## Assessment` is the
interviewer's own prose, and nothing in this module ever writes into it.

The 0-100 range is printed with its formula and its inputs right next to it. It is an
approximation over bands a person assigned, not a measurement, and a reader has to be able to see
how it was reached without opening the source.
"""

from __future__ import annotations

from datetime import datetime

from .bank import Bank
from .levels import BANDS, LEVELS
from .scoring import (
    BAND_POINTS,
    LEVEL_WEIGHT,
    band_matrix,
    by_category,
    by_topic,
    hot_spots,
    score,
)
from .session import Session, slugify


def display_name(session: Session) -> str:
    name = session.data.get("candidate") or "Candidate"
    if not (session.data.get("finish") or {}).get("anonymise"):
        return name
    parts = [part for part in name.replace(".", " ").split() if part]
    if not parts:
        return "Candidate"
    if len(parts) == 1:
        return f"{parts[0][0].upper()}."
    return f"{parts[0][0].upper()}. {parts[-1][0].upper()}."


def format_duration(seconds: int) -> str:
    minutes, remainder = divmod(max(0, int(seconds)), 60)
    return f"{minutes}m{remainder:02d}s"


def _local(stamp: str) -> datetime | None:
    try:
        return datetime.fromisoformat(stamp).astimezone()
    except (TypeError, ValueError):
        return None


def date_line(session: Session) -> str:
    start = _local(session.data.get("created_utc", ""))
    end = _local(session.data.get("finished_utc") or "")
    if not start:
        return "unknown"
    if not end:
        return start.strftime("%Y-%m-%d %H:%M")
    minutes = max(0, int((end - start).total_seconds() // 60))
    return f"{start:%Y-%m-%d %H:%M}–{end:%H:%M} ({minutes} min)"


def mode_line(session: Session) -> str:
    mode = session.mode
    pool_size = len(session.data.get("pool_ids") or [])
    served = len(session.items)
    if mode == "adaptive":
        start = (session.data.get("setup") or {}).get("start_level", "mid")
        mode = f"adaptive (started at {start})"
    return f"{mode}, pool {pool_size} → asked {served}"


def quote(text: str) -> str:
    lines = (text or "").strip().splitlines() or [""]
    return "\n".join(f"> {line}".rstrip() for line in lines)


def _gap_label(mean_gap: float) -> str:
    if mean_gap > 0:
        return f"+{mean_gap:.1f} above"
    if mean_gap < 0:
        return f"{mean_gap:.1f} below"
    return "at the bar"


def coverage_gaps(session: Session, bank: Bank) -> list[str]:
    """Areas that were on the table but produced no evidence."""
    gaps: list[str] = []

    observed = {row.category for row in session.observations(bank)}
    selected = set()
    for qid in session.data.get("pool_ids") or []:
        question = bank.get(qid)
        if question:
            selected.add(question.category)
    for category in sorted(selected - observed):
        gaps.append(f"`{category}` was in the pool but no answer in it carries a band")

    for index, item in enumerate(session.items, start=1):
        answer = session.answer_for(item["qid"])
        title = item.get("asked_title", item["qid"])
        if answer.get("skipped"):
            gaps.append(f"question {index}, {title}, was skipped")
        elif not answer.get("band"):
            gaps.append(f"question {index}, {title}, was asked but never banded")
    return gaps


def render_scorecard(session: Session, bank: Bank) -> str:
    finish = session.data.get("finish") or {}
    observations = session.observations(bank)
    overall = score(observations)
    categories = by_category(observations)
    topics = by_topic(observations)
    spots = hot_spots(topics)

    covered = sorted({item.get("asked_category", "?") for item in session.items})

    out: list[str] = [f"# Interview Scorecard — {display_name(session)}", ""]
    out += [
        f"- **Role:** {session.data.get('role') or 'not stated'}",
        f"- **Interviewer:** {session.data.get('interviewer') or 'not stated'}",
        f"- **Date:** {date_line(session)}",
        f"- **Categories covered:** {', '.join(covered) if covered else 'none'}",
        f"- **Mode:** {mode_line(session)}",
        f"- **Seed:** {session.data.get('seed')}",
    ]
    if session.data.get("context"):
        out.append(f"- **Context:** {session.data['context']}")
    out.append("")

    # --- the headline figure -------------------------------------------------------------
    out += ["## Range", ""]
    if overall.value is None:
        out += [
            "No question carries a band, so there is nothing to summarise.",
            "",
        ]
    else:
        out += [
            f"### {overall.value} / 100 — reads as **{overall.label}**",
            "",
            f"- 0 is an intern, 100 an engineering tech lead.",
            f"- Based on {overall.rated} banded answer(s) across "
            f"{len({row.category for row in observations})} category/categories.",
            f"- Confidence in the figure: **{overall.confidence}**"
            + (
                " — too few answers to lean on."
                if overall.confidence in ("none", "low")
                else "."
            ),
            "",
            "<details><summary>How this number is produced</summary>",
            "",
            f"`{overall.formula}`",
            "",
            "| Question level | Weight | Band assigned | Band points |",
            "|---|---|---|---|",
        ]
        for observation in observations:
            out.append(
                f"| {observation.level} | {LEVEL_WEIGHT[observation.level]} "
                f"| {observation.band} | {BAND_POINTS[observation.band]} |"
            )
        out += ["", "</details>", ""]

        counts = {band: 0 for band in BANDS}
        for observation in observations:
            counts[observation.band] += 1
        out += [
            "| Band assigned | " + " | ".join(BANDS) + " |",
            "|---|" + "---|" * len(BANDS),
            "| Questions | " + " | ".join(str(counts[band]) for band in BANDS) + " |",
            "",
        ]

    # --- hot spots -----------------------------------------------------------------------
    if spots["strong"] or spots["weak"]:
        out += ["## Hot spots", ""]
        out += [
            "`vs level` is how far the assigned bands sat above or below the level the questions "
            "in that topic were set to.",
            "",
            "| Topic | Asked | Deepest band | Held at | vs level |",
            "|---|---|---|---|---|",
        ]
        for row in spots["strong"] + spots["at_bar"] + spots["weak"]:
            out.append(
                f"| {row.name} | {row.asked} | {row.deepest_band} "
                f"| {row.hardest_level_held or '—'} | {_gap_label(row.mean_gap)} |"
            )
        out.append("")

    if categories:
        out += ["## Profile by category", "", "| Category | Asked | Range | Deepest band | vs level |", "|---|---|---|---|---|"]
        for row in categories:
            out.append(
                f"| {row.name} | {row.asked} | {row.score} | {row.deepest_band} "
                f"| {_gap_label(row.mean_gap)} |"
            )
        out.append("")

    matrix = band_matrix(observations)
    if matrix:
        out += ["<details><summary>Question level against band assigned</summary>", ""]
        out += ["| | " + " | ".join(BANDS) + " |", "|---|" + "---|" * len(BANDS)]
        for level in LEVELS:
            row = [
                str(next((c["count"] for c in matrix if c["level"] == level and c["band"] == band), 0))
                for band in BANDS
            ]
            if any(value != "0" for value in row):
                out.append(f"| **{level}** | " + " | ".join(row) + " |")
        out += ["", "</details>", ""]

    # --- evidence ------------------------------------------------------------------------
    out += [
        "## Evidence",
        "",
        "Everything in this section was observed or recorded during the interview.",
        "",
    ]
    for index, item in enumerate(session.items, start=1):
        question = bank.get(item["qid"])
        answer = session.answer_for(item["qid"])
        band = answer.get("band")
        skipped = bool(answer.get("skipped"))
        level = session.item_level(item, bank) or "?"

        if skipped:
            verdict = "**skipped**"
        elif not band:
            verdict = "**not banded**"
        else:
            verdict = f"**{band}** band on a **{level}** question"

        title = question.title if question else item.get("asked_title", item["qid"])
        elapsed = format_duration(answer.get("elapsed_seconds", 0))
        out += [f"### {index}. {title} — {verdict}", ""]

        category = question.category if question else item.get("asked_category", "?")
        topic = question.topic if question else item.get("asked_topic", "?")
        meta = f"`{item['qid']}` · {category} / {topic} · level {level} · {elapsed}"
        if item.get("reason"):
            meta += f" · served: {item['reason']}"
        if question is None:
            meta += " · **this card is no longer in the bank; text below is the snapshot taken when it was asked**"
        out += [meta, ""]

        asked_text = item.get("asked_text") or (question.question if question else "")
        if asked_text:
            out += [quote(asked_text), ""]

        used = answer.get("follow_ups_used") or []
        if used and question is not None:
            out.append("Follow-ups used:")
            for position in used:
                if 0 <= position < len(question.follow_ups):
                    out.append(f"- {question.follow_ups[position].text}")
            out.append("")
        elif used:
            out += [f"Follow-ups used: {', '.join(str(p + 1) for p in used)}", ""]

        if answer.get("note"):
            out += ["Interviewer notes:", "", quote(answer["note"]), ""]

    gaps = coverage_gaps(session, bank)
    if gaps:
        out += ["## Gaps — no evidence collected", ""]
        out += [f"- {gap}" for gap in gaps]
        out.append("")

    # --- the interviewer's own words -----------------------------------------------------
    out += [
        "## Assessment (interviewer)",
        "",
        "Written by the interviewer. Nothing in this section is generated.",
        "",
    ]
    wrote_anything = False
    for heading, key in (
        ("Summary", "summary"),
        ("Strengths", "strengths"),
        ("Concerns", "concerns"),
        ("Follow up in the next round", "follow_up_areas"),
    ):
        if finish.get(key):
            out += [f"### {heading}", "", finish[key].strip(), ""]
            wrote_anything = True
    if not wrote_anything:
        out += ["_Not filled in._", ""]

    out += [
        "---",
        "",
        f"Machine-readable state, including per-question timings, follow-ups used and the seed, "
        f"is in `sessions/{session.id}/session.json`.",
        "",
    ]
    return "\n".join(out)


def scorecard_filename(session: Session) -> str:
    return f"scorecard-{slugify(display_name(session), 'candidate')}.md"
