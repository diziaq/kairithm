"""The 0-100 range and the per-area profile.

These are aggregates over bands a person assigned. Nothing here decides anything; the tests
pin down the arithmetic so the number printed on a scorecard can be reproduced by hand.
"""

from app.scoring import (
    BAND_POINTS,
    LEVEL_WEIGHT,
    Observation,
    band_matrix,
    by_category,
    by_topic,
    hot_spots,
    nearest_band,
    score,
)


def observation(level: str, band: str, *, category: str = "java", topic: str = "concurrency"):
    return Observation(
        qid=f"{category}-{topic}-{level}-{band}",
        category=category,
        topic=topic,
        level=level,
        band=band,
    )


def test_no_evidence_produces_no_number_rather_than_a_zero():
    result = score([])
    assert result.value is None
    assert result.label == "no evidence"
    assert result.confidence == "none"


def test_the_scale_is_anchored_at_intern_and_tech_lead():
    assert score([observation("junior", "weak")]).value == 0
    assert score([observation("lead", "lead")]).value == 100
    assert score([observation("mid", "mid")]).value == 50


def test_a_harder_question_carries_more_weight_than_an_easy_one():
    """A senior band on a lead question outranks the same band on a junior one."""
    on_a_lead_question = score([observation("lead", "senior"), observation("junior", "weak")])
    on_a_junior_question = score([observation("junior", "senior"), observation("lead", "weak")])
    assert on_a_lead_question.value > on_a_junior_question.value


def test_the_figure_can_be_reproduced_by_hand():
    rows = [observation("senior", "mid"), observation("junior", "senior")]
    expected = (BAND_POINTS["mid"] * LEVEL_WEIGHT["senior"]
                + BAND_POINTS["senior"] * LEVEL_WEIGHT["junior"]) / (
        LEVEL_WEIGHT["senior"] + LEVEL_WEIGHT["junior"]
    )
    assert score(rows).value == round(expected)
    assert score(rows).weight_total == 4


def test_the_number_always_carries_a_word():
    assert nearest_band(0) == "weak"
    assert nearest_band(48) == "mid"
    assert nearest_band(97) == "lead"
    assert score([observation("senior", "senior")]).label == "senior"


def test_confidence_reflects_how_much_evidence_there_is():
    assert score([observation("mid", "mid")]).confidence == "low"
    assert score([observation("mid", "mid")] * 3).confidence == "low", "one category only"

    spread = [
        observation("mid", "mid", category="java"),
        observation("mid", "senior", category="kafka"),
        observation("senior", "mid", category="spring"),
        observation("junior", "junior", category="general"),
    ]
    assert score(spread).confidence == "moderate"
    assert score(spread * 3).confidence == "good"


def test_a_bucket_records_the_deepest_band_and_the_hardest_level_held():
    rows = by_topic(
        [
            observation("junior", "senior", topic="collections"),
            observation("senior", "mid", topic="collections"),
        ]
    )
    assert len(rows) == 1
    row = rows[0]
    assert row.asked == 2
    assert row.deepest_band == "senior"
    assert row.hardest_level_held == "junior", "the senior question was answered below its level"
    assert row.band_counts == {"mid": 1, "senior": 1}


def test_the_mean_gap_says_whether_an_area_carried_or_dragged():
    strong = by_topic([observation("mid", "senior", topic="generics")])[0]
    weak = by_topic([observation("senior", "junior", topic="gc")])[0]
    at_bar = by_topic([observation("mid", "mid", topic="io")])[0]

    assert strong.mean_gap == 1
    assert weak.mean_gap == -2
    assert at_bar.mean_gap == 0


def test_hot_spots_split_the_areas_three_ways():
    rows = by_topic(
        [
            observation("mid", "senior", topic="generics"),
            observation("senior", "junior", topic="gc"),
            observation("mid", "mid", topic="io"),
        ]
    )
    spots = hot_spots(rows)
    assert [r.name for r in spots["strong"]] == ["generics"]
    assert [r.name for r in spots["at_bar"]] == ["io"]
    assert [r.name for r in spots["weak"]] == ["gc"]


def test_buckets_come_back_strongest_first():
    rows = by_category(
        [
            observation("senior", "junior", category="kafka"),
            observation("mid", "lead", category="java"),
        ]
    )
    assert [row.name for row in rows] == ["java", "kafka"]


def test_the_band_matrix_only_lists_pairs_that_happened():
    matrix = band_matrix([observation("mid", "senior"), observation("mid", "senior")])
    assert matrix == [{"level": "mid", "band": "senior", "count": 2}]
