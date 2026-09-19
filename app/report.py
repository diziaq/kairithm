"""Render scorecard.md from a finished session."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .bank import Bank
from .session import Session, slugify

RATING_LABELS = {
    1: "No understanding",
    2: "Shaky, needed heavy prompting",
    3: "Solid, expected level",
    4: "Strong, went beyond",
    5: "Excellent, taught me something",
}

RECOMMENDATIONS = (
    "Strong hire",
    "Hire",
    "Lean hire",
    "Lean no",
    "No hire",
    "Inconclusive",
)


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


def averages(session: Session, bank: Bank, key: str) -> list[tuple[str, float, int]]:
    """Mean rating per topic or per tag. Skipped questions are left out of the mean."""
    totals: dict[str, list[int]] = defaultdict(list)
    for item in session.items:
        question = bank.get(item["qid"])
        if question is None:
            continue
        answer = session.answer_for(item["qid"])
        rating = answer.get("rating")
        if rating is None:
            continue
        buckets = [question.topic] if key == "topic" else list(question.tags)
        for bucket in buckets:
            totals[bucket].append(int(rating))
    rows = [(name, sum(values) / len(values), len(values)) for name, values in totals.items()]
    return sorted(rows, key=lambda row: (-row[1], row[0]))


def mode_line(session: Session) -> str:
    mode = session.mode
    pool_size = len(session.data.get("pool_ids") or [])
    served = len(session.items)
    if mode == "adaptive":
        start = (session.data.get("setup") or {}).get("start_difficulty", 2)
        mode = f"adaptive (start difficulty {start})"
    return f"{mode}, pool {pool_size} → asked {served}"


def quote(text: str) -> str:
    lines = (text or "").strip().splitlines() or [""]
    return "\n".join(f"> {line}".rstrip() for line in lines)


def render_scorecard(session: Session, bank: Bank) -> str:
    finish = session.data.get("finish") or {}
    topics = sorted({bank.get(i["qid"]).topic for i in session.items if bank.get(i["qid"])})

    out: list[str] = [f"# Interview Scorecard — {display_name(session)}", ""]
    out += [
        f"- **Role:** {session.data.get('role') or 'not stated'}",
        f"- **Interviewer:** {session.data.get('interviewer') or 'not stated'}",
        f"- **Date:** {date_line(session)}",
        f"- **Topics:** {', '.join(topics) if topics else 'none'}",
        f"- **Mode:** {mode_line(session)}",
        f"- **Seed:** {session.data.get('seed')}",
        f"- **Recommendation:** {finish.get('recommendation') or 'Inconclusive'}",
    ]
    if session.data.get("context"):
        out.append(f"- **Context:** {session.data['context']}")
    out.append("")

    if finish.get("summary"):
        out += ["## Summary", "", finish["summary"].strip(), ""]

    for heading, key in (
        ("Strengths", "strengths"),
        ("Concerns", "concerns"),
        ("Suggested follow-up areas", "follow_up_areas"),
    ):
        if finish.get(key):
            out += [f"## {heading}", "", finish[key].strip(), ""]

    topic_rows = averages(session, bank, "topic")
    if topic_rows:
        out += ["## Averages", "", "| Topic | Avg | Asked |", "|---|---|---|"]
        out += [f"| {name} | {avg:.1f} | {count} |" for name, avg, count in topic_rows]
        out.append("")

    tag_rows = averages(session, bank, "tag")
    if tag_rows:
        out += ["| Tag | Avg | Asked |", "|---|---|---|"]
        out += [f"| {name} | {avg:.1f} | {count} |" for name, avg, count in tag_rows]
        out.append("")

    out += ["## Questions", ""]
    for index, item in enumerate(session.items, start=1):
        question = bank.get(item["qid"])
        answer = session.answer_for(item["qid"])
        rating = answer.get("rating")
        skipped = bool(answer.get("skipped"))

        if skipped:
            verdict = "**skipped**"
        elif rating is None:
            verdict = "**not rated**"
        else:
            verdict = f"**{rating} / 5**"

        title = question.title if question else item["qid"]
        difficulty = question.difficulty if question else "?"
        elapsed = format_duration(answer.get("elapsed_seconds", 0))
        out.append(f"### {index}. {title} — {verdict} (difficulty {difficulty}, {elapsed})")
        out.append("")

        tags = ", ".join(question.tags) if question and question.tags else "none"
        meta = f"`{item['qid']}` · tags: {tags}"
        if session.mode == "adaptive" and item.get("target_difficulty") is not None:
            meta += f" · served at target {item['target_difficulty']} ({item.get('reason', '')})"
        out += [meta, ""]

        if rating is not None and not skipped:
            out += [f"{RATING_LABELS.get(int(rating), '')}", ""]
        if answer.get("note"):
            out += [quote(answer["note"]), ""]

    out += [
        "---",
        "",
        f"Machine-readable state, including per-question timings and the seed, is in "
        f"`sessions/{session.id}/session.json`.",
        "",
    ]
    return "\n".join(out)


def scorecard_filename(session: Session) -> str:
    return f"scorecard-{slugify(display_name(session), 'candidate')}.md"
