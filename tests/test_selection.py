from app.bank import Bank, Question
from app.levels import calibrate
from app.selection import (
    ADAPTIVE,
    MAX_BLOCK,
    LEVEL_ASC,
    MANUAL,
    RANDOM,
    SEQUENTIAL,
    PoolFilters,
    build_pool,
    choose_adaptive,
    order_pool,
    suggest,
)


def served(pool, mode, seed, bank):
    """Ids in the order a mode would serve them."""
    return [question.id for question, _reason in order_pool(pool, mode, seed, bank)]


def switches(values):
    """How many times a sequence changes value. One block per value means len(set) - 1."""
    return sum(1 for a, b in zip(values, values[1:]) if a != b)


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


def test_search_matches_the_title_the_question_text_the_topic_and_the_tags():
    bank = make_bank(
        question("a", "mid", topic="concurrency", tags=("jmm",)),
        question("b", "mid", category="kafka", topic="delivery", tags=("ordering",)),
    )
    for term, expected in [
        ("concurrency", ["a"]),
        ("jmm", ["a"]),
        ("kafka", ["b"]),
        ("ordering", ["b"]),
        ("ask", ["a", "b"]),          # the question text of both
        ("CONCURRENCY", ["a"]),       # case-insensitive
    ]:
        pool = build_pool(bank, PoolFilters(search=term))
        assert [q.id for q in pool] == expected, term


def test_every_search_term_has_to_match():
    bank = make_bank(
        question("a", "mid", category="java", topic="concurrency"),
        question("b", "mid", category="kafka", topic="concurrency"),
    )
    assert [q.id for q in build_pool(bank, PoolFilters(search="java concurrency"))] == ["a"]
    assert build_pool(bank, PoolFilters(search="java delivery")) == []


def test_search_combines_with_the_other_filters():
    bank = make_bank(
        question("a", "junior", topic="concurrency"),
        question("b", "senior", topic="concurrency"),
    )
    pool = build_pool(bank, PoolFilters(search="concurrency", levels=("senior",)))
    assert [q.id for q in pool] == ["b"]


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


MIXED = [
    ("java-conc-a", "java", "concurrency"),
    ("kafka-del-a", "kafka", "delivery"),
    ("java-conc-b", "java", "concurrency"),
    ("spring-di-a", "spring", "di"),
    ("kafka-del-b", "kafka", "delivery"),
    ("java-coll-a", "java", "collections"),
]


def mixed_bank(level="mid"):
    return make_bank(
        *(question(qid, level, category=category, topic=topic) for qid, category, topic in MIXED)
    )


def test_sequential_opens_on_the_order_field_then_stays_in_blocks():
    bank = make_bank(
        question("java-a", "mid", category="java", topic="concurrency", order=30),
        question("java-b", "mid", category="java", topic="concurrency", order=10),
        question("kafka-a", "mid", category="kafka", topic="delivery", order=20),
    )
    pool = list(bank.questions.values())
    assert served(pool, SEQUENTIAL, 1, bank) == ["java-b", "java-a", "kafka-a"], (
        "opens on the lowest order, finishes the topic, then moves on"
    )


def test_every_mode_serves_one_block_per_category():
    bank = mixed_bank()
    pool = list(bank.questions.values())
    for mode in (SEQUENTIAL, RANDOM, LEVEL_ASC):
        categories = [qid.split("-")[0] for qid in served(pool, mode, 7, bank)]
        assert switches(categories) == len(set(categories)) - 1, (
            f"{mode} left and re-entered a category"
        )


def test_a_topic_is_finished_before_the_chain_leaves_its_category():
    bank = mixed_bank()
    order = served(list(bank.questions.values()), SEQUENTIAL, 1, bank)
    topics = [qid.rsplit("-", 1)[0] for qid in order]
    assert switches(topics) == len(set(topics)) - 1


def test_random_order_is_reproducible_from_the_seed():
    bank = mixed_bank()
    pool = list(bank.questions.values())
    assert served(pool, RANDOM, 4815162342, bank) == served(pool, RANDOM, 4815162342, bank)


def test_a_different_seed_opens_the_chain_somewhere_else():
    bank = mixed_bank()
    pool = list(bank.questions.values())
    openings = {served(pool, RANDOM, seed, bank)[0] for seed in range(30)}
    assert len(openings) > 1, "the seed has to be able to move the starting point"


def test_level_ascending_still_climbs_while_staying_in_blocks():
    bank = make_bank(
        question("java-a", "senior", category="java", topic="concurrency"),
        question("java-b", "junior", category="java", topic="concurrency"),
        question("kafka-a", "junior", category="kafka", topic="delivery"),
        question("kafka-b", "senior", category="kafka", topic="delivery"),
    )
    pool = list(bank.questions.values())
    order = served(pool, LEVEL_ASC, 1, bank)
    levels = [bank.get(qid).level for qid in order]

    assert levels == ["junior", "junior", "senior", "senior"], "the run still climbs"
    assert switches([qid.split("-")[0] for qid in order]) <= 2


def test_level_ascending_picks_up_the_next_band_where_the_last_one_finished():
    bank = make_bank(
        question("java-a", "junior", category="java", topic="concurrency"),
        question("kafka-a", "mid", category="kafka", topic="delivery"),
        question("java-b", "mid", category="java", topic="concurrency"),
    )
    order = served(list(bank.questions.values()), LEVEL_ASC, 1, bank)
    assert order == ["java-a", "java-b", "kafka-a"], "the mid band opens next to the junior one"


def test_manual_order_is_left_exactly_as_it_was_picked():
    bank = mixed_bank()
    pool = [bank.get("kafka-del-a"), bank.get("java-conc-a"), bank.get("kafka-del-b")]
    assert served(pool, MANUAL, 1, bank) == ["kafka-del-a", "java-conc-a", "kafka-del-b"]


def test_every_served_card_carries_the_reason_it_came_next():
    bank = mixed_bank()
    walked = order_pool(list(bank.questions.values()), SEQUENTIAL, 1, bank)
    assert all(reason for _question, reason in walked)
    assert walked[0][1].startswith("opens on")


def test_adaptive_has_no_precomputed_order():
    bank = mixed_bank()
    assert order_pool(list(bank.questions.values()), ADAPTIVE, 1, bank) == []


def test_an_unknown_mode_is_refused():
    bank = mixed_bank()
    try:
        order_pool(list(bank.questions.values()), "sideways", 1, bank)
    except ValueError as error:
        assert "unknown order mode" in str(error)
    else:
        raise AssertionError("an unknown mode must not be served silently")


# --- adaptive picking ------------------------------------------------------------------------


def test_adaptive_prefers_the_target_level_then_the_nearest_one():
    bank = make_bank(
        question("a", "junior"), question("b", "senior"), question("c", "lead")
    )
    pool = list(bank.questions.values())

    picked, reason = choose_adaptive(bank, pool, [], "senior", seed=1)
    assert picked.id == "b"
    assert "target level senior" in reason

    picked, reason = choose_adaptive(bank, pool, ["b"], "senior", seed=1)
    assert picked.level == "lead", "lead is one step away, junior is two"
    assert "nearest level" in reason


def test_adaptive_stays_in_the_block_it_is_in():
    bank = make_bank(
        question("here", "mid", category="java", topic="concurrency"),
        question("near", "mid", category="java", topic="concurrency"),
        question("far", "mid", category="sap-jco", topic="rfc"),
    )
    picked, reason = choose_adaptive(bank, list(bank.questions.values()), ["here"], "mid", seed=3)

    assert picked.id == "near"
    assert "same topic, concurrency" in reason


def test_adaptive_leaves_a_topic_only_when_the_calibration_asks_and_takes_the_nearest_exit():
    """After a weak answer the point is to stop confirming a failure, not to change subject."""
    bank = make_bank(
        question("here", "mid", category="java", topic="concurrency", tags=("jmm",)),
        question("same", "mid", category="java", topic="concurrency"),
        question("sibling", "mid", category="java", topic="collections"),
        question("stranger", "mid", category="sap-jco", topic="rfc"),
    )
    pool = list(bank.questions.values())

    stay, _ = choose_adaptive(bank, pool, ["here"], "mid", seed=3)
    assert stay.id == "same"

    move, reason = choose_adaptive(bank, pool, ["here"], "mid", seed=3, escape="topic")
    assert move.id == "sibling", "a different topic, but the nearest one"
    assert "moved off concurrency" in reason


def test_adaptive_stays_put_when_a_topic_change_has_nowhere_to_go():
    bank = make_bank(
        question("here", "mid", topic="concurrency"),
        question("same", "mid", topic="concurrency"),
    )
    picked, _ = choose_adaptive(
        bank, list(bank.questions.values()), ["here"], "mid", seed=1, escape="topic"
    )
    assert picked.id == "same"


def test_adaptive_never_repeats_and_ends_when_the_pool_is_used_up():
    bank = make_bank(question("a", "mid"))
    pool = list(bank.questions.values())
    picked, _ = choose_adaptive(bank, pool, [], "mid", seed=1)
    assert picked.id == "a"
    assert choose_adaptive(bank, pool, ["a"], "mid", seed=1) is None


def test_adaptive_is_reproducible_from_the_seed():
    bank = mixed_bank()
    pool = list(bank.questions.values())
    runs = []
    for _ in range(2):
        order: list[str] = []
        for _ in range(4):
            picked, _ = choose_adaptive(bank, pool, order, "mid", seed=555)
            order.append(picked.id)
        runs.append(order)
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
    assert "concurrency → collections" in found[0].reason


def test_suggestions_at_the_target_level_come_nearest_first():
    """An answer at the level asked holds the topic, so the nearest card leads."""
    current = question("now", "mid", category="java", topic="concurrency")
    near = question("near", "mid", category="java", topic="concurrency")
    sibling = question("sibling", "mid", category="java", topic="collections")
    stranger = question("stranger", "mid", category="sap-jco", topic="rfc")
    bank = make_bank(current, near, sibling, stranger)

    found = suggest(bank, current, calibrate("mid", "mid"), "mid", ["now"])
    assert [s.question_id for s in found] == ["near", "sibling", "stranger"]


def test_a_card_already_served_is_never_suggested_again():
    current = question("now", "senior", links={"shallower": ("easy",)})
    easier = question("easy", "junior")
    bank = make_bank(current, easier)

    assert suggest(bank, current, calibrate("senior", "weak"), "junior", ["now", "easy"]) == []


def test_a_topic_change_pushes_the_current_topic_to_the_back_without_dropping_it():
    current = question("now", "senior", topic="concurrency")
    same = question("same", "mid", topic="concurrency")
    sibling = question("sibling", "mid", topic="collections")
    bank = make_bank(current, same, sibling)

    found = suggest(bank, current, calibrate("senior", "mid"), "mid", ["now"])
    assert [s.question_id for s in found] == ["sibling", "same"], (
        "a different topic leads, but the current one is still one click away"
    )


# --- the block budget and the settled state ---------------------------------------------------


def block_bank():
    cards = [
        question(f"java-{n}", "mid", category="java", topic=f"t{n}") for n in range(6)
    ] + [question(f"kafka-{n}", "mid", category="kafka", topic=f"k{n}") for n in range(3)]
    return make_bank(*cards)


def test_a_run_leaves_a_category_once_the_block_budget_is_spent():
    bank = block_bank()
    pool = list(bank.questions.values())
    served = [f"java-{n}" for n in range(MAX_BLOCK)]

    picked, reason = choose_adaptive(bank, pool, served, "mid", seed=1)
    assert picked.category == "kafka", f"{MAX_BLOCK} in a row is enough of one area"
    assert f"{MAX_BLOCK} questions in java" in reason


def test_a_shorter_run_stays_in_the_block():
    bank = block_bank()
    pool = list(bank.questions.values())
    served = [f"java-{n}" for n in range(MAX_BLOCK - 1)]
    picked, _ = choose_adaptive(bank, pool, served, "mid", seed=1)
    assert picked.category == "java"


def test_two_answers_well_below_leave_the_category_immediately():
    bank = block_bank()
    pool = list(bank.questions.values())
    picked, reason = choose_adaptive(bank, pool, ["java-0"], "mid", seed=1, escape="category")

    assert picked.category == "kafka", "grinding the area they are worst at collects nothing"
    assert "two answers well below in java" in reason


def test_the_budget_is_ignored_when_there_is_nowhere_else_to_go():
    bank = make_bank(*(question(f"java-{n}", "mid", topic=f"t{n}") for n in range(6)))
    pool = list(bank.questions.values())
    served = [f"java-{n}" for n in range(MAX_BLOCK)]
    picked, _ = choose_adaptive(bank, pool, served, "mid", seed=1)
    assert picked.category == "java", "a one-category pool is not a reason to serve nothing"


def test_a_settled_ceiling_turns_the_run_towards_new_ground():
    bank = block_bank()
    pool = list(bank.questions.values())
    # One question in, still inside the block budget: without `settled` it would stay in java.
    staying, _ = choose_adaptive(bank, pool, ["java-0"], "mid", seed=1)
    assert staying.category == "java"

    widening, reason = choose_adaptive(bank, pool, ["java-0"], "mid", seed=1, settled=True)
    assert widening.category == "kafka"
    assert "ceiling settled, new category" in reason


def test_suggestions_prefer_new_ground_once_the_ceiling_is_settled():
    current = question("now", "mid", category="java", topic="concurrency")
    same = question("same", "mid", category="java", topic="collections")
    fresh = question("fresh", "mid", category="kafka", topic="delivery")
    bank = make_bank(current, same, fresh)

    hunting = suggest(bank, current, calibrate("mid", "mid"), "mid", ["now"])
    assert hunting[0].question_id == "same", "relatedness leads while the ceiling is unknown"

    settled = suggest(bank, current, calibrate("mid", "mid"), "mid", ["now"], settled=True)
    assert settled[0].question_id == "fresh", "breadth leads once it is known"
