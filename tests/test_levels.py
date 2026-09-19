"""The navigation table from the brief, section 6, asserted row by row."""

import pytest

from app.levels import (
    ABOVE,
    BANDS,
    EQUAL,
    LEVELS,
    ONE_BELOW,
    TWO_OR_MORE_BELOW,
    calibrate,
    delta,
)


def test_the_two_scales_share_an_origin_at_junior():
    assert delta("junior", "junior") == 0
    assert delta("lead", "lead") == 0
    assert delta("senior", "weak") == -3
    assert delta("junior", "lead") == 3


@pytest.mark.parametrize(
    "level, band, outcome",
    [
        # Two or more below.
        ("senior", "weak", TWO_OR_MORE_BELOW),
        ("lead", "junior", TWO_OR_MORE_BELOW),
        ("mid", "weak", TWO_OR_MORE_BELOW),
        # One below.
        ("senior", "mid", ONE_BELOW),
        ("junior", "weak", ONE_BELOW),
        ("lead", "senior", ONE_BELOW),
        # Equal.
        ("junior", "junior", EQUAL),
        ("mid", "mid", EQUAL),
        ("senior", "senior", EQUAL),
        ("lead", "lead", EQUAL),
        # Above.
        ("junior", "mid", ABOVE),
        ("mid", "lead", ABOVE),
        ("senior", "lead", ABOVE),
    ],
)
def test_every_row_of_the_suggestion_table(level, band, outcome):
    assert calibrate(level, band).outcome == outcome


def test_a_mid_answer_to_a_senior_question_does_not_stay_at_senior():
    """The case the brief calls out by name."""
    result = calibrate("senior", "mid")

    assert result.outcome == ONE_BELOW
    assert result.next_level == "mid", "the next question must not be another senior one"
    assert result.prefer[0] == "shallower"
    assert result.change_topic is True, "moving sideways has to be on the table"


def test_two_or_more_below_prefers_shallower_and_pushes_a_topic_change():
    result = calibrate("lead", "junior")
    assert result.prefer[0] == "shallower"
    assert result.change_topic is True
    assert result.next_level == "junior"


def test_an_equal_answer_offers_sideways_or_deeper_and_holds_the_level():
    result = calibrate("mid", "mid")
    assert result.prefer == ("related", "deeper")
    assert result.change_topic is False
    assert result.next_level == "mid"


def test_an_answer_above_the_question_raises_the_bar_and_goes_deeper():
    result = calibrate("mid", "senior")
    assert result.outcome == ABOVE
    assert result.prefer[0] == "deeper"
    assert result.next_level == "senior", "the bar moves up for this topic"


def test_the_next_level_is_always_the_band_just_observed_floored_at_junior():
    for level in LEVELS:
        for band in BANDS:
            expected = "junior" if band == "weak" else band
            assert calibrate(level, band).next_level == expected


def test_an_unknown_level_or_band_is_refused():
    with pytest.raises(ValueError):
        calibrate("principal", "mid")
    with pytest.raises(ValueError):
        calibrate("mid", "outstanding")
