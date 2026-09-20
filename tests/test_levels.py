"""The navigation table from the brief, section 6, asserted row by row."""

import pytest

from app.levels import (
    ABOVE,
    BANDS,
    CONTRADICT_AFTER,
    MIN_ANSWERS_TO_SETTLE,
    EQUAL,
    LEVELS,
    ONE_BELOW,
    PROBE_AFTER_EQUALS,
    TWO_OR_MORE_BELOW,
    calibrate,
    delta,
    track,
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


# --- the running calibration -------------------------------------------------------------------



def test_nothing_recorded_leaves_the_calibration_where_the_setup_put_it():
    progress = track("senior", [])
    assert progress.level == "senior"
    assert progress.settled is False
    assert progress.latest is None
    assert "No band assigned" in progress.note


def test_the_bar_moves_one_step_per_answer_however_good_it_was():
    """A lead band on a junior question is evidence, not proof. Jumping three levels on one
    answer is how the old version sawtoothed for a whole interview."""
    assert track("junior", [("junior", "lead")]).level == "mid"
    assert track("junior", [("junior", "lead"), ("mid", "lead")]).level == "senior"


def test_the_ceiling_settles_when_the_level_above_the_best_held_one_fails():
    progress = track("mid", [("mid", "mid"), ("mid", "mid"), ("senior", "mid")])
    assert progress.settled is True
    assert progress.ceiling == "mid"
    assert progress.level == "mid"
    assert "ceiling looks like mid" in progress.note


def test_failing_a_question_at_a_level_they_also_hold_is_not_a_ceiling():
    """Inconsistency is not a bracket. Only the level immediately above the best held one counts."""
    progress = track("mid", [("mid", "mid"), ("mid", "mid"), ("mid", "weak")])
    assert progress.settled is False


def test_two_answers_are_never_enough_to_call_a_ceiling():
    """One unlucky topic at the start of an interview is not a bracket."""
    early = track("mid", [("mid", "mid"), ("senior", "mid")])
    assert early.settled is False
    assert len(early.held) + len(early.failed) < MIN_ANSWERS_TO_SETTLE


def test_a_settled_ceiling_stops_the_bar_moving():
    settled = track("mid", [("mid", "mid"), ("mid", "mid"), ("senior", "mid")])
    still = track("mid", [("mid", "mid"), ("mid", "mid"), ("senior", "mid"), ("mid", "mid")])
    assert still.level == settled.level == "mid"
    assert still.settled is True


def test_answering_above_a_settled_ceiling_enough_times_reopens_it():
    """The bracket can be built on one unlucky topic. Consistent contradiction falsifies it."""
    answers = [("mid", "mid"), ("mid", "mid"), ("senior", "mid")]
    assert track("mid", answers).settled is True

    for _ in range(CONTRADICT_AFTER):
        answers.append(("mid", "senior"))
    progress = track("mid", answers)

    assert progress.settled is False, "out-answered three times running"
    assert progress.level == "senior", "the estimate was too low, so it climbs again"


def test_two_answers_above_a_settled_ceiling_are_not_enough_to_reopen_it():
    answers = [("mid", "mid"), ("mid", "mid"), ("senior", "mid"),
               ("mid", "senior"), ("mid", "senior")]
    assert track("mid", answers).settled is True


def test_consecutive_answers_at_the_level_asked_trigger_a_probe_upwards():
    answers = [("mid", "mid")] * (PROBE_AFTER_EQUALS - 1)
    assert track("mid", answers).probing is False
    assert track("mid", answers).level == "mid"

    answers.append(("mid", "mid"))
    progress = track("mid", answers)
    assert progress.probing is True
    assert progress.level == "senior", "one step up, to find where it stops"
    assert "find where it stops" in progress.note


def test_a_probe_is_not_run_once_the_ceiling_is_known():
    answers = [("mid", "mid"), ("mid", "mid"), ("senior", "mid")] + [("mid", "mid")] * PROBE_AFTER_EQUALS
    progress = track("mid", answers)
    assert progress.settled is True
    assert progress.probing is False, "no point probing a wall that has already been found"


def test_two_answers_well_below_ask_for_a_different_category():
    assert track("mid", [("mid", "weak")]).escape == "topic"
    assert track("mid", [("mid", "weak"), ("junior", "weak")]).escape == "topic"
    assert track("senior", [("senior", "weak"), ("senior", "weak")]).escape == "category"


def test_an_answer_at_or_above_the_level_asks_for_nothing_to_change():
    assert track("mid", [("mid", "mid")]).escape == ""
    assert track("mid", [("mid", "senior")]).escape == ""


def test_the_floor_and_the_ceiling_of_the_scale_are_respected():
    assert track("junior", [("junior", "weak")] * 5).level == "junior"
    assert track("lead", [("lead", "lead")] * 5).level == "lead"
