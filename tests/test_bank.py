from pathlib import Path

from app.bank import load_bank


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


GOOD = """---
title: A good question
difficulty: 3
tags: [one, two]
time_minutes: 4
---

## Ask

Say this out loud.

## Look for

- A point

## Unknown heading

Kept as it is.
"""


def test_reads_a_valid_question(tmp_path):
    write(tmp_path, "java/good.md", GOOD)
    bank = load_bank(tmp_path)
    assert bank.warnings == []
    question = bank.get("java/good")
    assert question.title == "A good question"
    assert question.difficulty == 3
    assert question.tags == ("one", "two")
    assert question.ask == "Say this out loud."
    assert question.extra == (("Unknown heading", "Kept as it is."),)


def test_ignores_files_that_start_with_underscore(tmp_path):
    write(tmp_path, "java/good.md", GOOD)
    write(tmp_path, "_template.md", GOOD)
    write(tmp_path, "java/_notes.md", GOOD)
    bank = load_bank(tmp_path)
    assert list(bank.questions) == ["java/good"]


def test_reports_every_problem_and_keeps_going(tmp_path):
    write(tmp_path, "java/good.md", GOOD)
    write(tmp_path, "java/no-frontmatter.md", "just text\n")
    write(tmp_path, "java/bad-yaml.md", "---\ntitle: [unclosed\n---\n\n## Ask\n\nx\n")
    write(tmp_path, "java/no-difficulty.md", "---\ntitle: T\n---\n\n## Ask\n\nx\n")
    write(tmp_path, "java/out-of-range.md", "---\ntitle: T\ndifficulty: 9\n---\n\n## Ask\n\nx\n")
    write(tmp_path, "java/empty-ask.md", "---\ntitle: T\ndifficulty: 2\n---\n\n## Ask\n\n")

    bank = load_bank(tmp_path)

    assert list(bank.questions) == ["java/good"], "one bad file must not remove the good ones"
    problems = {w.path: w.problem for w in bank.warnings}
    assert "java/no-frontmatter.md" in problems
    assert "cannot parse the frontmatter" in problems["java/bad-yaml.md"]
    assert problems["java/no-difficulty.md"] == "difficulty is missing"
    assert "outside the range" in problems["java/out-of-range.md"]
    assert "Ask section" in problems["java/empty-ask.md"]


def test_a_file_outside_a_topic_directory_is_a_warning(tmp_path):
    write(tmp_path, "loose.md", GOOD)
    bank = load_bank(tmp_path)
    assert bank.questions == {}
    assert any("topic" in w.problem for w in bank.warnings)


def test_the_shipped_bank_loads_without_warnings():
    bank = load_bank()
    assert bank.warnings == []
    assert len(bank.questions) >= 6
