from app.bank import Bank, Question
from app.selection import (
    ADAPTIVE,
    DIFFICULTY_ASC,
    RANDOM,
    PoolFilters,
    build_pool,
    choose_adaptive,
    next_target_difficulty,
    order_pool,
)


def question(qid: str, difficulty: int, tags: tuple[str, ...] = (), order: int | None = None):
    topic, stem = qid.split("/")
    return Question(
        id=qid,
        topic=topic,
        stem=stem,
        title=qid,
        difficulty=difficulty,
        tags=tags,
        time_minutes=None,
        order=order,
        ask="ask",
        look_for="",
        red_flags="",
        follow_ups="",
        extra=(),
        path=qid,
    )


def make_bank(*questions: Question) -> Bank:
    return Bank(questions={q.id: q for q in questions})


def test_filters_by_topic_tag_and_difficulty():
    bank = make_bank(
        question("java/a", 1, ("core",)),
        question("java/b", 4, ("core", "slow")),
        question("kafka/c", 3, ("core",)),
    )
    pool = build_pool(bank, PoolFilters(topics=("java",), difficulty_min=2, difficulty_max=5))
    assert [q.id for q in pool] == ["java/b"]

    pool = build_pool(bank, PoolFilters(exclude_tags=("slow",)))
    assert [q.id for q in pool] == ["java/a", "kafka/c"]

    pool = build_pool(bank, PoolFilters(include_tags=("slow",)))
    assert [q.id for q in pool] == ["java/b"]


def test_manual_ids_win_and_keep_their_order():
    bank = make_bank(question("java/a", 1), question("java/b", 2), question("java/c", 3))
    pool = build_pool(bank, PoolFilters(manual_ids=("java/c", "java/a")))
    assert [q.id for q in pool] == ["java/c", "java/a"]


def test_limit_applies_after_filtering():
    bank = make_bank(*(question(f"java/{n}", 2) for n in "abcde"))
    pool = build_pool(bank, PoolFilters(limit=2))
    assert len(pool) == 2


def test_random_order_is_reproducible_from_the_seed():
    pool = [question(f"java/{n}", 3) for n in "abcdefgh"]
    first = [q.id for q in order_pool(pool, RANDOM, 4815162342)]
    second = [q.id for q in order_pool(pool, RANDOM, 4815162342)]
    other = [q.id for q in order_pool(pool, RANDOM, 99)]
    assert first == second
    assert first != other, "a different seed should give a different order for eight questions"


def test_difficulty_ascending_sorts_by_difficulty():
    pool = [question("java/a", 4), question("java/b", 1), question("java/c", 3)]
    assert [q.difficulty for q in order_pool(pool, DIFFICULTY_ASC, 1)] == [1, 3, 4]


def test_adaptive_has_no_precomputed_order():
    pool = [question("java/a", 2)]
    assert order_pool(pool, ADAPTIVE, 1) == []


def test_rating_moves_the_target_and_clamps():
    assert next_target_difficulty(2, 5, False) == 3
    assert next_target_difficulty(2, 4, False) == 3
    assert next_target_difficulty(3, 3, False) == 3
    assert next_target_difficulty(3, 2, False) == 2
    assert next_target_difficulty(3, 1, False) == 2
    assert next_target_difficulty(3, None, True) == 3, "a skip holds the level"
    assert next_target_difficulty(5, 5, False) == 5, "clamped at the top"
    assert next_target_difficulty(1, 1, False) == 1, "clamped at the bottom"


def test_adaptive_prefers_the_target_then_the_nearest_level():
    pool = [question("java/a", 1), question("java/b", 3), question("java/c", 5)]
    picked, reason = choose_adaptive(pool, [], target=3, seed=1, covered_tags=set())
    assert picked.id == "java/b"
    assert "target difficulty 3" in reason

    picked, reason = choose_adaptive(pool, ["java/b"], target=3, seed=1, covered_tags=set())
    assert picked.difficulty in (1, 5)
    assert "nearest level" in reason


def test_adaptive_prefers_an_uncovered_tag():
    pool = [question("java/a", 3, ("seen",)), question("java/b", 3, ("fresh",))]
    picked, reason = choose_adaptive(pool, [], target=3, seed=7, covered_tags={"seen"})
    assert picked.id == "java/b"
    assert "new tag" in reason


def test_adaptive_never_repeats_and_ends_when_the_pool_is_used_up():
    pool = [question("java/a", 3)]
    picked, _ = choose_adaptive(pool, [], target=3, seed=1, covered_tags=set())
    assert picked.id == "java/a"
    assert choose_adaptive(pool, ["java/a"], target=3, seed=1, covered_tags=set()) is None


def test_adaptive_is_reproducible_from_the_seed():
    pool = [question(f"java/{n}", 3) for n in "abcdef"]
    runs = []
    for _ in range(2):
        served: list[str] = []
        for _ in range(4):
            picked, _ = choose_adaptive(pool, served, target=3, seed=555, covered_tags=set())
            served.append(picked.id)
        runs.append(served)
    assert runs[0] == runs[1]
