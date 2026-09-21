"""Build card files for tests.

Written as text rather than as objects on purpose: the loader is what is under test, so the
tests have to go through the same parsing a hand-edited file does.
"""

from __future__ import annotations

from pathlib import Path

BANDS_BLOCK = """## Answer bands

### weak

- Repeats the phrase back with no example.

### junior

- States the basic rule and gives one worked example.

### mid

- Explains the trade-off and names a failure seen in production.
"""


def card(
    card_id: str = "java-concurrency-example-01",
    *,
    category: str = "java",
    topic: str = "concurrency",
    level: str = "mid",
    title: str = "An example card",
    schema_version: int = 2,
    tags: str = "[one, two]",
    links: str = "",
    question: str = "Say this part out loud.",
    tests: str = "Whether the candidate can take the line apart into machine steps.",
    # None means "whatever this schema version requires"; pass "" to leave the section out.
    ideal_answer: str | None = None,
    listen_for: str = "- The step where the other thread lands",
    bands: str = BANDS_BLOCK,
    follow_ups: str = (
        "## Follow-ups\n\n"
        "- You run it once and it works. Are you finished?\n"
        "  probes: whether they see this as timing-dependent\n"
        "- Your fix made the loop slower. Where did the time go?\n"
    ),
    extra_frontmatter: str = "",
    extra_sections: str = "",
) -> str:
    front = [
        f"id: {card_id}",
        f"schema_version: {schema_version}",
        f"title: {title}",
        f"category: {category}",
        f"topic: {topic}",
        f"level: {level}",
        f"tags: {tags}",
    ]
    if links:
        front.append(links)
    if extra_frontmatter:
        front.append(extra_frontmatter)

    if ideal_answer is None:
        ideal_answer = (
            "The two threads interleave inside the increment and one overwrites the other."
            if schema_version >= 2
            else ""
        )

    body = ["## Ask", "", question, "", "## Tests", "", tests, ""]
    if ideal_answer:
        body += ["## Ideal minimal answer", "", ideal_answer, ""]
    if listen_for:
        body += ["## Listen for", "", listen_for, ""]
    if bands:
        body += [bands, ""]
    if follow_ups:
        body += [follow_ups, ""]
    if extra_sections:
        body += [extra_sections, ""]

    return "---\n" + "\n".join(front) + "\n---\n\n" + "\n".join(body)


def write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
