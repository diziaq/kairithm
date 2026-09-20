"""Every failure mode the brief requires the validator to catch, one test each."""

from app.bank import load_bank
from app.validate import ERROR, WARNING, errors, main, validate_bank
from tests.cards import card, write


def check(tmp_path):
    return validate_bank(load_bank(tmp_path))


def problems_for(tmp_path, field: str):
    return [p for p in check(tmp_path) if p.field == field]


def test_a_clean_bank_reports_nothing(tmp_path):
    write(tmp_path, "java/java-concurrency-example-01.md", card())
    assert check(tmp_path) == []


# --- structural, surfaced by the loader ---------------------------------------------------


def test_an_unparseable_file_is_an_error_that_names_the_file(tmp_path):
    write(tmp_path, "java/java-concurrency-example-01.md", card())
    write(tmp_path, "java/broken.md", "---\ntitle: [unclosed\n---\n\n## Ask\n\nx\n")

    found = errors(check(tmp_path))
    assert len(found) == 1
    assert "broken.md" in found[0].path
    assert "cannot parse the frontmatter" in found[0].problem


def test_a_duplicate_id_is_an_error(tmp_path):
    write(tmp_path, "java/first.md", card())
    write(tmp_path, "java/second.md", card())
    assert any("duplicate id" in p.problem for p in errors(check(tmp_path)))


def test_a_missing_question_is_an_error_naming_the_field(tmp_path):
    write(tmp_path, "java/a.md", card(question=""))
    found = problems_for(tmp_path, "question")
    assert found and found[0].severity == ERROR
    assert "## Ask" in found[0].problem


def test_an_invalid_level_is_an_error(tmp_path):
    write(tmp_path, "java/a.md", card(level="principal"))
    assert problems_for(tmp_path, "level")[0].severity == ERROR


def test_a_category_that_disagrees_with_the_directory_is_an_error(tmp_path):
    write(tmp_path, "java/a.md", card(category="kafka"))
    found = problems_for(tmp_path, "category")
    assert found and "does not match the directory" in found[0].problem


def test_an_invalid_band_name_is_an_error(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(bands="## Answer bands\n\n### outstanding\n\n- Says something observable here.\n"),
    )
    found = problems_for(tmp_path, "answer_bands")
    assert found and "not a band name" in found[0].problem


# --- links ---------------------------------------------------------------------------------


def test_a_link_to_an_id_that_does_not_exist_is_an_error(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01", links="links:\n  deeper: [nope-99]"))
    found = problems_for(tmp_path, "links.deeper")
    assert found and found[0].severity == ERROR
    assert "not a card in the bank" in found[0].problem
    assert found[0].card_id == "java-a-01"


def test_a_card_that_links_to_itself_is_an_error(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(card_id="java-a-01", links="links:\n  related: [java-a-01]"),
    )
    assert any("links the card to itself" in p.problem for p in errors(check(tmp_path)))


def test_a_pair_that_both_declare_deeper_is_reported_as_asymmetric(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01", links="links:\n  deeper: [java-b-01]"))
    write(
        tmp_path,
        "java/b.md",
        card(card_id="java-b-01", level="senior", links="links:\n  deeper: [java-a-01]"),
    )
    found = [p for p in errors(check(tmp_path)) if "should be `shallower`" in p.problem]
    assert len(found) == 2, "both files disagree, so both are named"


def test_a_one_sided_deeper_link_is_fine_because_the_inverse_is_derived(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01", links="links:\n  deeper: [java-b-01]"))
    write(tmp_path, "java/b.md", card(card_id="java-b-01", level="senior"))
    assert errors(check(tmp_path)) == []


def test_deeper_pointing_at_an_easier_card_is_a_warning(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(card_id="java-a-01", level="senior", links="links:\n  deeper: [java-b-01]"),
    )
    write(tmp_path, "java/b.md", card(card_id="java-b-01", level="junior"))
    found = problems_for(tmp_path, "links.deeper")
    assert found and found[0].severity == WARNING


# --- answer bands --------------------------------------------------------------------------


def test_a_verdict_only_band_is_an_error(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(bands="## Answer bands\n\n### senior\n\n- Excellent understanding.\n"),
    )
    found = problems_for(tmp_path, "answer_bands.senior")
    assert found and found[0].severity == ERROR
    assert "is a verdict, not an observation" in found[0].problem


def test_a_band_of_one_word_is_an_error(tmp_path):
    write(tmp_path, "java/a.md", card(bands="## Answer bands\n\n### mid\n\n- Good\n"))
    assert problems_for(tmp_path, "answer_bands.mid")[0].severity == ERROR


def test_a_band_heading_with_no_bullets_is_an_error(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(bands="## Answer bands\n\n### weak\n\n### mid\n\n- Names a real failure case.\n"),
    )
    found = problems_for(tmp_path, "answer_bands.weak")
    assert found and "no bullets" in found[0].problem


def test_an_observable_band_passes(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(
            bands=(
                "## Answer bands\n\n### senior\n\n"
                "- Explains the mechanism rather than the API surface.\n"
                "- Describes what happens to the queue when the node restarts.\n"
            )
        ),
    )
    assert problems_for(tmp_path, "answer_bands.senior") == []


# --- follow-ups ----------------------------------------------------------------------------


def test_a_follow_up_that_names_a_waited_for_term_is_a_warning(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(
            listen_for="- Uses a stable business key so the write can be repeated, for idempotency",
            follow_ups="## Follow-ups\n\n- Did you consider idempotency?\n- And what else?\n",
        ),
    )
    found = problems_for(tmp_path, "follow_ups")
    leaks = [p for p in found if "idempotency" in p.problem]
    assert leaks and leaks[0].severity == WARNING, "a leak is a warning, never an error"


def test_a_follow_up_describing_the_situation_does_not_warn(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(
            listen_for="- Uses a stable business key so the write can be repeated, for idempotency",
            follow_ups=(
                "## Follow-ups\n\n"
                "- What changes if that call is made a second time?\n"
                "- The network drops the reply. What does your caller see?\n"
            ),
        ),
    )
    assert [p for p in problems_for(tmp_path, "follow_ups") if "names" in p.problem] == []


def test_allow_term_leak_silences_the_check_for_a_card_that_tests_the_word(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(
            listen_for="- Uses a stable business key, for idempotency",
            follow_ups="## Follow-ups\n\n- Did you consider idempotency?\n- And what else?\n",
            extra_frontmatter="allow_term_leak: true",
        ),
    )
    assert [p for p in problems_for(tmp_path, "follow_ups") if "names" in p.problem] == []


def test_the_wrong_number_of_follow_ups_is_a_warning(tmp_path):
    write(tmp_path, "java/a.md", card(follow_ups="## Follow-ups\n\n- Only one probe here?\n"))
    found = [p for p in problems_for(tmp_path, "follow_ups") if "follow-up(s)" in p.problem]
    assert found and found[0].severity == WARNING


# --- conventions ---------------------------------------------------------------------------


def test_a_file_name_that_does_not_match_the_id_is_a_warning(tmp_path):
    write(tmp_path, "java/something-else.md", card(card_id="java-concurrency-example-01"))
    found = problems_for(tmp_path, "id")
    assert found and found[0].severity == WARNING
    assert "bank/java/java-concurrency-example-01.md" in found[0].problem


# --- the CLI and the shipped bank ------------------------------------------------------------


def test_the_cli_exits_non_zero_on_an_error_and_zero_on_a_clean_bank(tmp_path, capsys):
    write(tmp_path, "java/a.md", card())
    assert main([str(tmp_path)]) == 0

    write(tmp_path, "java/b.md", card(level="principal"))
    assert main([str(tmp_path)]) == 1
    assert "level" in capsys.readouterr().err


def test_the_shipped_bank_validates_clean():
    problems = validate_bank(load_bank())
    assert problems == [], [p.line() for p in problems]


def test_two_cards_claiming_the_same_position_is_a_warning(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01", extra_frontmatter="order: 20"))
    write(tmp_path, "java/b.md", card(card_id="java-b-01", extra_frontmatter="order: 20"))
    found = problems_for(tmp_path, "order")

    assert len(found) == 2, "both cards are named, because either one could move"
    assert all(p.severity == WARNING for p in found)
    assert "also claimed in java by java-b-01" in found[0].problem


def test_the_same_position_in_two_different_categories_is_fine(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01", extra_frontmatter="order: 20"))
    write(
        tmp_path,
        "kafka/b.md",
        card(card_id="kafka-b-01", category="kafka", topic="delivery", extra_frontmatter="order: 20"),
    )
    assert problems_for(tmp_path, "order") == []
