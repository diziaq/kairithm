from pathlib import Path

from app.bank import load_bank
from tests.cards import card, write


def test_reads_every_field_of_a_valid_card(tmp_path):
    write(tmp_path, "java/java-concurrency-example-01.md", card())
    bank = load_bank(tmp_path)

    assert bank.warnings == []
    question = bank.get("java-concurrency-example-01")
    assert question.schema_version == 2
    assert question.title == "An example card"
    assert question.category == "java"
    assert question.topic == "concurrency"
    assert question.level == "mid"
    assert question.tags == ("one", "two")
    assert question.question == "Say this part out loud."
    assert question.tests.startswith("Whether the candidate")
    assert question.listen_for == ("The step where the other thread lands",)


def test_answer_bands_are_read_from_the_sub_headings(tmp_path):
    write(tmp_path, "java/java-concurrency-example-01.md", card())
    question = load_bank(tmp_path).get("java-concurrency-example-01")

    assert list(question.answer_bands) == ["weak", "junior", "mid"], "order follows the scale"
    assert question.answer_bands["junior"] == (
        "States the basic rule and gives one worked example.",
    )
    assert "senior" not in question.answer_bands, "only the meaningful bands are present"


def test_a_follow_up_keeps_its_probes_line_apart_from_the_spoken_text(tmp_path):
    write(tmp_path, "java/java-concurrency-example-01.md", card())
    question = load_bank(tmp_path).get("java-concurrency-example-01")

    first, second = question.follow_ups
    assert first.text == "You run it once and it works. Are you finished?"
    assert first.probes == "whether they see this as timing-dependent"
    assert second.probes == "", "probes is optional"


def test_a_wrapped_bullet_becomes_one_item(tmp_path):
    write(
        tmp_path,
        "java/java-concurrency-example-01.md",
        card(listen_for="- The first half of the point\n  and the second half"),
    )
    question = load_bank(tmp_path).get("java-concurrency-example-01")
    assert question.listen_for == ("The first half of the point and the second half",)


def test_an_unrecognised_heading_is_kept_under_its_own_title(tmp_path):
    write(
        tmp_path,
        "java/java-concurrency-example-01.md",
        card(extra_sections="## House rules\n\nKept as it is."),
    )
    question = load_bank(tmp_path).get("java-concurrency-example-01")
    assert question.extra == (("House rules", "Kept as it is."),)


def test_files_and_directories_that_start_with_underscore_are_ignored(tmp_path):
    write(tmp_path, "java/java-concurrency-example-01.md", card())
    write(tmp_path, "_template.md", card(card_id="template-01"))
    write(tmp_path, "java/_notes.md", card(card_id="notes-01"))
    write(tmp_path, "_drafts/java/x.md", card(card_id="draft-01"))

    assert list(load_bank(tmp_path).questions) == ["java-concurrency-example-01"]


def test_every_problem_is_reported_and_the_good_cards_survive(tmp_path):
    write(tmp_path, "java/java-concurrency-example-01.md", card())
    write(tmp_path, "java/no-frontmatter.md", "just text\n")
    write(tmp_path, "java/bad-yaml.md", "---\ntitle: [unclosed\n---\n\n## Ask\n\nx\n")
    write(tmp_path, "java/no-id.md", card(card_id=""))
    write(tmp_path, "java/bad-id.md", card(card_id="Java Concurrency 01"))
    write(tmp_path, "java/bad-level.md", card(card_id="bad-level-01", level="principal"))
    write(tmp_path, "java/wrong-category.md", card(card_id="wrong-cat-01", category="kafka"))
    write(tmp_path, "java/no-ask.md", card(card_id="no-ask-01", question=""))
    write(tmp_path, "java/no-tests.md", card(card_id="no-tests-01", tests=""))
    write(tmp_path, "java/no-listen.md", card(card_id="no-listen-01", listen_for=""))
    write(tmp_path, "java/no-bands.md", card(card_id="no-bands-01", bands=""))
    write(tmp_path, "java/bad-version.md", card(card_id="bad-version-01", schema_version=99))

    bank = load_bank(tmp_path)

    assert list(bank.questions) == ["java-concurrency-example-01"], "one bad file keeps the rest"
    problems = {(Path(w.path).name, w.field): w.problem for w in bank.warnings}
    assert "no YAML frontmatter" in problems[("no-frontmatter.md", "")]
    assert "cannot parse the frontmatter" in problems[("bad-yaml.md", "")]
    assert problems[("no-id.md", "id")] == "id is missing or empty"
    assert "single hyphens" in problems[("bad-id.md", "id")]
    assert "not one of" in problems[("bad-level.md", "level")]
    assert "does not match the directory" in problems[("wrong-category.md", "category")]
    assert "## Ask" in problems[("no-ask.md", "question")]
    assert "## Tests" in problems[("no-tests.md", "tests")]
    assert "## Listen for" in problems[("no-listen.md", "listen_for")]
    assert "band headings" in problems[("no-bands.md", "answer_bands")]
    assert "not supported" in problems[("bad-version.md", "schema_version")]

    # Every problem names the file it came from.
    assert all(w.path for w in bank.warnings)


def test_a_duplicate_id_is_reported_and_the_second_file_is_skipped(tmp_path):
    write(tmp_path, "java/first.md", card())
    write(tmp_path, "java/second.md", card())
    bank = load_bank(tmp_path)

    assert len(bank.questions) == 1
    assert any(w.field == "id" and "duplicate" in w.problem for w in bank.warnings)


def test_a_file_outside_a_category_directory_is_a_problem(tmp_path):
    write(tmp_path, "loose.md", card())
    bank = load_bank(tmp_path)
    assert bank.questions == {}
    assert any("category" in w.problem for w in bank.warnings)


def test_the_id_is_the_identity_not_the_file_name(tmp_path):
    write(tmp_path, "java/some-other-name.md", card(card_id="java-concurrency-example-01"))
    bank = load_bank(tmp_path)
    assert bank.get("java-concurrency-example-01") is not None


def test_the_inverse_of_a_declared_link_is_derived_at_load_time(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(card_id="java-a-01", links="links:\n  deeper: [java-b-01]"),
    )
    write(tmp_path, "java/b.md", card(card_id="java-b-01", level="senior"))
    bank = load_bank(tmp_path)

    assert bank.resolved_links("java-a-01")["deeper"] == ["java-b-01"]
    assert bank.resolved_links("java-b-01")["shallower"] == ["java-a-01"], "derived, not declared"
    assert bank.get("java-b-01").links == {}, "the file itself stays untouched"


def test_related_links_are_derived_both_ways(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01", links="links:\n  related: [kafka-b-01]"))
    write(tmp_path, "kafka/b.md", card(card_id="kafka-b-01", category="kafka", topic="delivery"))
    bank = load_bank(tmp_path)
    assert bank.resolved_links("kafka-b-01")["related"] == ["java-a-01"]


def test_an_unknown_link_kind_is_reported(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01", links="links:\n  sideways: [x]"))
    bank = load_bank(tmp_path)
    assert any("unknown link kind" in w.problem for w in bank.warnings)


def test_hints_are_dropped_server_side(tmp_path):
    write(tmp_path, "java/java-concurrency-example-01.md", card())
    question = load_bank(tmp_path).get("java-concurrency-example-01")

    public = question.public(include_hints=False)
    assert public["question"] == "Say this part out loud."
    assert "links" in public, "navigation is not an answer"
    for hidden in ("listen_for", "answer_bands", "follow_ups", "tests", "weak_signals", "notes"):
        assert hidden not in public

    full = question.public(include_hints=True)
    assert full["answer_bands"]["weak"]
    assert full["follow_ups"][0]["probes"]


def test_a_file_that_cannot_be_decoded_is_reported_not_raised(tmp_path):
    path = tmp_path / "java" / "binary.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"---\ntitle: \xff\xfe broken\n---\n")
    bank = load_bank(tmp_path)
    assert any("cannot read the file" in w.problem for w in bank.warnings)


def test_the_shipped_bank_loads_without_problems():
    bank = load_bank()
    assert bank.warnings == [], [w.line() for w in bank.warnings]
    assert len(bank.questions) >= 3


# --- schema version 2: the ideal minimal answer ------------------------------------------------


def test_a_version_two_card_carries_an_ideal_minimal_answer(tmp_path):
    write(
        tmp_path,
        "java/a.md",
        card(card_id="java-a-01", ideal_answer="The interleaving loses updates."),
    )
    question = load_bank(tmp_path).get("java-a-01")
    assert question.schema_version == 2
    assert question.ideal_answer == "The interleaving loses updates."


def test_a_version_two_card_without_one_is_an_error(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01", ideal_answer=""))
    bank = load_bank(tmp_path)

    assert bank.questions == {}
    problem = next(w for w in bank.warnings if w.field == "ideal_answer")
    assert "Ideal minimal answer" in problem.problem
    assert "required from schema_version 2" in problem.problem


def test_a_version_one_card_still_loads_without_one(tmp_path):
    """A card written before the field existed is not broken by it."""
    write(tmp_path, "java/a.md", card(card_id="java-a-01", schema_version=1))
    question = load_bank(tmp_path).get("java-a-01")
    assert question is not None
    assert question.ideal_answer == ""


def test_an_unsupported_schema_version_is_still_refused(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01", schema_version=99))
    bank = load_bank(tmp_path)
    assert any("not supported" in w.problem for w in bank.warnings)


def test_the_ideal_answer_is_interviewer_only(tmp_path):
    write(tmp_path, "java/a.md", card(card_id="java-a-01"))
    question = load_bank(tmp_path).get("java-a-01")
    assert "ideal_answer" not in question.public(include_hints=False)
    assert question.public(include_hints=True)["ideal_answer"]
