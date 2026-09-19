"""The executive summary: one page about the candidate, nothing about the interview."""

from app.bank import load_bank
from app.report import render_scorecard, render_summary
from app.session import Session
from tests.cards import card, write


def build(tmp_path, bands, *, role="Senior Java", written=""):
    """A session over a purpose-built bank, with the given bands already assigned."""
    root = tmp_path / "bank"
    for qid, category, topic, level, _band in bands:
        write(root, f"{category}/{qid}.md", card(card_id=qid, category=category, topic=topic, level=level))
    bank = load_bank(root)

    ids = [row[0] for row in bands]
    session = Session(
        {
            "id": "2026-09-19_1100_a-petrov_senior-java",
            "candidate": "A Petrov",
            "role": role,
            "interviewer": "me",
            "mode": "adaptive",
            "seed": 1,
            "created_utc": "2026-09-19T11:00:00+00:00",
            "pool_ids": list(bank.questions),
            "position": 0,
            "answers": {},
            "finish": {"summary": written},
            "items": [
                {
                    "qid": qid,
                    "asked_title": bank.get(qid).title,
                    "asked_text": bank.get(qid).question,
                    "asked_category": bank.get(qid).category,
                    "asked_topic": bank.get(qid).topic,
                    "asked_level": bank.get(qid).level,
                }
                for qid in ids
            ],
        }
    )
    for qid, _category, _topic, _level, band in bands:
        session.set_answer(qid, {"band": band})
    return session, bank


SPREAD = [
    ("kafka-delivery-a-01", "kafka", "delivery", "mid", "senior"),
    ("kafka-delivery-b-01", "kafka", "delivery", "mid", "senior"),
    ("java-gc-a-01", "java", "gc", "senior", "junior"),
    ("java-conc-a-01", "java", "concurrency", "mid", "mid"),
]


def test_the_summary_leads_with_the_range_and_the_evidence_behind_it(tmp_path):
    session, bank = build(tmp_path, SPREAD)
    text = render_summary(session, bank)

    assert text.startswith("# A Petrov — executive summary")
    assert "/ 100 — answers read as" in text
    assert "4 banded answer(s) across 2 categories (java, kafka)" in text
    assert "Confidence **moderate**" in text


def test_the_summary_names_the_strong_and_weak_areas(tmp_path):
    session, bank = build(tmp_path, SPREAD)
    text = render_summary(session, bank)

    strong = text[text.index("## Strong") : text.index("## Weak")]
    weak = text[text.index("## Weak") :]
    assert "kafka / delivery" in strong
    assert "1 band above the level asked" in strong
    assert "java / gc" in weak
    assert "2 bands below the level asked" in weak


def test_the_summary_counts_the_questions_met_or_beaten(tmp_path):
    session, bank = build(tmp_path, SPREAD)
    assert "Met or beat the level asked on **3 of 4** questions." in render_summary(session, bank)
    assert "Deepest answer: **senior** on a mid question" in render_summary(session, bank)


def test_the_summary_leaves_out_how_the_interview_was_run(tmp_path):
    session, bank = build(tmp_path, SPREAD, written="My own words.")
    text = render_summary(session, bank)

    for noise in ("Seed", "seed", "adaptive", "Mode", "pool", "served", "0m00s", "## Evidence"):
        assert noise not in text, f"{noise!r} is process, not the candidate"
    assert "## Interviewer" in text
    assert "> My own words." in text


def test_the_summary_says_where_no_evidence_was_collected(tmp_path):
    session, bank = build(tmp_path, SPREAD)
    # A category in the pool that never got a band.
    write(tmp_path / "bank", "spring/spring-di-a-01.md", card(card_id="spring-di-a-01", category="spring", topic="di"))
    bank = load_bank(tmp_path / "bank")
    session.data["pool_ids"] = list(bank.questions)

    text = render_summary(session, bank)
    assert "## Not established" in text
    assert "No banded evidence in: spring." in text


def test_a_session_with_no_bands_says_so_and_stops(tmp_path):
    session, bank = build(tmp_path, SPREAD)
    session.data["answers"] = {}
    text = render_summary(session, bank)

    assert "No answer carries a band." in text
    assert "## Strong" not in text
    assert "/ 100" not in text


def test_the_summary_is_anonymised_with_the_scorecard(tmp_path):
    session, bank = build(tmp_path, SPREAD)
    session.data["finish"] = {"anonymise": True}
    text = render_summary(session, bank)

    assert "A Petrov" not in text
    assert "A. P." in text


def test_the_scorecard_still_carries_the_detail_the_summary_drops(tmp_path):
    session, bank = build(tmp_path, SPREAD)
    scorecard = render_scorecard(session, bank)

    assert "## Evidence" in scorecard
    assert "**Seed:**" in scorecard
    assert "## Assessment (interviewer)" in scorecard
