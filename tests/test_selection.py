from app.bank import Bank, Question
from app.levels import calibrate
from app.selection import (
    ADAPTIVE,
    LEVEL_ASC,
    RANDOM,
    SEQUENTIAL,
    PoolFilters,
    build_pool,
    choose_adaptive,
    order_pool,
    suggest,
)


def question(
    qid: str,
    level: str,
    *,
    category: str = "java",
    topic: str = "concurrency",
    tags: tuple[str, ...] = (),
    order: int | None = None,
    links: dict[str, tuple[str, ...]] | None = None,
) -> Question:
    return Question(
        id=qid,
        schema_version=1,
        title=qid,
        question="ask",
        category=category,
        topic=topic,
        level=level,
        tests="what it probes",
        listen_for=("a point",),
        answer_bands={"mid": ("Says something observable.",)},
        tags=tags,
        order=order,
        links=links or {},
        path=f"bank/{category}/{qid}.md",
    )


def make_bank(*questions: Question) -> Bank:
    return Bank(questions={q.id: q for q in questions})


# --- pool ----------------------------------------------------------------------------------


def test_filters_by_category_topic_tag_and_level():
    bank = make_bank(
        question("a", "junior", tags=("core",)),
        question("b", "lead", tags=("core", "slow")),
        question("c", "mid", category="kafka", topic="delivery", tags=("core",)),
    )

    assert [q.id for q in build_pool(bank, PoolFilters(categories=("java",)))] == ["a", "b"]
    assert [q.id for q in build_pool(bank, PoolFilters(topics=("delivery",)))] == ["c"]
    assert [q.id for q in build_pool(bank, PoolFilters(levels=("lead",)))] == ["b"]
    assert [q.id for q in build_pool(bank, PoolFilters(exclude_tags=("slow",)))] == ["a", "c"]
    assert [q.id for q in build_pool(bank, PoolFilters(include_tags=("slow",)))] == ["b"]


def test_an_unknown_level_in_the_filter_is_dropped_rather_than_matching_nothing():
    filters = PoolFilters.from_dict({"levels": ["mid", "principal"]})
    assert filters.levels == ("mid",)


def test_manual_ids_win_and_keep_their_order():
    bank = make_bank(question("a", "junior"), question("b", "mid"), question("c", "senior"))
    pool = build_pool(bank, PoolFilters(manual_ids=("c", "a")))
    assert [q.id for q in pool] == ["c", "a"]


def test_limit_applies_after_filtering():
    bank = make_bank(*(question(name, "mid") for name in "abcde"))
    assert len(build_pool(bank, PoolFilters(limit=2))) == 2


def test_excluded_ids_are_removed():
    bank = make_bank(question("a", "mid"), question("b", "mid"))
    assert [q.id for q in build_pool(bank, PoolFilters(exclude_ids=("a",)))] == ["b"]


# --- ordering ------------------------------------------------------------------------------


def test_sequential_uses_the_order_field_then_the_id():
    pool = [
        question("z", "mid"),
        question("a", "mid", order=20),
        question("b", "mid", order=10),
    ]
    assert [q.id for q in order_pool(pool, SEQUENTIAL, 1)] == ["b", "a", "z"]


def test_random_order_is_reproducible_from_the_seed():
    pool = [question(name, "mid") for name in "abcdefgh"]
    first = [q.id for q in order_pool(pool, RANDOM, 4815162342)]
    second = [q.id for q in order_pool(pool, RANDOM, 4815162342)]
    other = [q.id for q in order_pool(pool, RANDOM, 99)]
    assert first == second
    assert first != other, "a different seed should give a different order for eight cards"


def test_level_ascending_walks_the_scale_upwards():
    pool = [
        question("a", "senior"),
        question("b", "junior"),
        question("c", "lead"),
        question("d", "mid"),
    ]
    assert [q.level for q in order_pool(pool, LEVEL_ASC, 1)] == ["junior", "mid", "senior", "lead"]


def test_adaptive_has_no_precomputed_order():
    assert order_pool([question("a", "mid")], ADAPTIVE, 1) == []


# --- adaptive picking ------------------------------------------------------------------------


def test_adaptive_prefers_the_target_level_then_the_nearest_one():
    pool = [question("a", "junior"), question("b", "senior"), question("c", "lead")]

    picked, reason = choose_adaptive(pool, [], "senior", seed=1, covered_topics=set())
    assert picked.id == "b"
    assert "target level senior" in reason

    picked, reason = choose_adaptive(pool, ["b"], "senior", seed=1, covered_topics=set())
    assert picked.level == "lead", "lead is one step away, junior is two"
    assert "nearest level" in reason


def test_adaptive_prefers_a_topic_the_session_has_not_covered():
    pool = [
        question("a", "mid", topic="collections"),
        question("b", "mid", topic="generics"),
    ]
    picked, reason = choose_adaptive(pool, [], "mid", seed=7, covered_topics={"collections"})
    assert picked.id == "b"
    assert "topic not covered yet" in reason


def test_adaptive_never_repeats_and_ends_when_the_pool_is_used_up():
    pool = [question("a", "mid")]
    picked, _ = choose_adaptive(pool, [], "mid", seed=1, covered_topics=set())
    assert picked.id == "a"
    assert choose_adaptive(pool, ["a"], "mid", seed=1, covered_topics=set()) is None


def test_adaptive_is_reproducible_from_the_seed():
    pool = [question(name, "mid") for name in "abcdef"]
    runs = []
    for _ in range(2):
        served: list[str] = []
        for _ in range(4):
            picked, _ = choose_adaptive(pool, served, "mid", seed=555, covered_topics=set())
            served.append(picked.id)
        runs.append(served)
    assert runs[0] == runs[1]


# --- suggestions -----------------------------------------------------------------------------


def test_suggestions_follow_the_link_order_the_calibration_asks_for():
    easier = question("easy", "junior")
    current = question("now", "senior", links={"deeper": ("hard",), "shallower": ("easy",)})
    harder = question("hard", "lead")
    bank = make_bank(easier, current, harder)

    # A mid answer to a senior question: shallower comes first.
    below = suggest(bank, current, calibrate("senior", "mid"), "mid", ["now"])
    assert below[0].question_id == "easy"
    assert below[0].kind == "shallower"

    # A lead answer to a senior question: deeper comes first.
    above = suggest(bank, current, calibrate("senior", "lead"), "lead", ["now"])
    assert above[0].question_id == "hard"
    assert above[0].kind == "deeper"


def test_suggestions_fall_back_to_the_target_level_when_there_are_no_links():
    current = question("now", "senior")
    other = question("other", "mid", topic="collections")
    bank = make_bank(current, other)

    found = suggest(bank, current, calibrate("senior", "mid"), "mid", ["now"])
    assert [s.question_id for s in found] == ["other"]
    assert found[0].kind == "level"
    assert "topic not covered yet" in found[0].reason


def test_a_card_already_served_is_never_suggested_again():
    current = question("now", "senior", links={"shallower": ("easy",)})
    easier = question("easy", "junior")
    bank = make_bank(current, easier)

    assert suggest(bank, current, calibrate("senior", "weak"), "junior", ["now", "easy"]) == []


def test_a_topic_change_pushes_uncovered_topics_to_the_front():
    current = question("now", "senior", topic="concurrency")
    same = question("same", "mid", topic="concurrency")
    fresh = question("fresh", "mid", topic="collections")
    bank = make_bank(current, same, fresh)

    found = suggest(bank, current, calibrate("senior", "mid"), "mid", ["now"])
    assert [s.question_id for s in found] == ["fresh", "same"]
