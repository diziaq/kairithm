"""Relatedness, and the walk that turns a pool into blocks."""

from app.affinity import affinity, chain, explain, link_map, nearest_of
from tests.test_selection import make_bank, question


def test_a_card_is_not_related_to_itself():
    a = question("a", "mid")
    assert affinity(a, a) == 0.0


def test_the_signals_stack_in_the_documented_order():
    base = question("a", "mid", category="java", topic="concurrency", tags=("jmm",))
    same_topic = question("b", "mid", category="java", topic="concurrency")
    same_category = question("c", "mid", category="java", topic="collections")
    shared_tag = question("d", "mid", category="kafka", topic="delivery", tags=("jmm",))
    unrelated = question("e", "mid", category="spring", topic="di")

    assert affinity(base, same_topic) > affinity(base, same_category)
    assert affinity(base, same_category) > affinity(base, shared_tag)
    assert affinity(base, shared_tag) > affinity(base, unrelated)
    assert affinity(base, unrelated) == 0.0


def test_staying_in_a_topic_beats_following_a_link_out_of_the_category():
    """A topic is finished before the chain leaves it."""
    base = question("a", "mid", category="java", topic="concurrency", links={"related": ("far",)})
    near = question("b", "mid", category="java", topic="concurrency")
    far = question("far", "mid", category="kafka", topic="delivery")
    linked = link_map(make_bank(base, near, far))

    assert affinity(base, near, linked) > affinity(base, far, linked)


def test_a_link_inside_a_topic_wins_outright():
    base = question("a", "junior", topic="concurrency", links={"deeper": ("b",)})
    authored = question("b", "senior", topic="concurrency")
    sibling = question("c", "mid", topic="concurrency")
    linked = link_map(make_bank(base, authored, sibling))

    assert affinity(base, authored, linked) > affinity(base, sibling, linked)


def test_shared_tags_are_scored_by_overlap_not_by_count():
    base = question("a", "mid", category="java", tags=("one", "two"))
    exact = question("b", "mid", category="kafka", topic="x", tags=("one", "two"))
    partial = question("c", "mid", category="kafka", topic="x", tags=("one", "nine", "ten"))

    assert affinity(base, exact) > affinity(base, partial) > 0


def test_the_chain_finishes_one_category_before_starting_another():
    bank = make_bank(
        question("java-a", "mid", category="java", topic="concurrency"),
        question("kafka-a", "mid", category="kafka", topic="delivery"),
        question("java-b", "mid", category="java", topic="concurrency"),
        question("kafka-b", "mid", category="kafka", topic="delivery"),
        question("java-c", "mid", category="java", topic="collections"),
    )
    walked = [q.id for q, _ in chain(bank, list(bank.questions.values()), lambda q: q.id)]
    categories = [qid.split("-")[0] for qid in walked]

    assert categories == ["java", "java", "java", "kafka", "kafka"]
    assert walked[:2] == ["java-a", "java-b"], "the tighter topic is exhausted first"


def test_the_chain_explains_every_move_it_makes():
    bank = make_bank(
        question("java-a", "mid", category="java", topic="concurrency"),
        question("java-b", "mid", category="java", topic="collections"),
        question("kafka-a", "mid", category="kafka", topic="delivery"),
    )
    reasons = [reason for _, reason in chain(bank, list(bank.questions.values()), lambda q: q.id)]

    assert reasons[0].startswith("opens on java / concurrency")
    assert "concurrency → collections, still java" in reasons[1]
    assert "new block" in reasons[2]


def test_an_anchor_starts_the_chain_next_to_a_card_outside_the_pool():
    anchor = question("anchor", "junior", category="kafka", topic="delivery")
    bank = make_bank(
        anchor,
        question("java-a", "mid", category="java", topic="concurrency"),
        question("kafka-a", "mid", category="kafka", topic="delivery"),
    )
    pool = [bank.get("java-a"), bank.get("kafka-a")]
    walked = chain(bank, pool, lambda q: q.id, anchor=anchor)

    assert walked[0][0].id == "kafka-a", "picks up where the previous block left off"
    assert "same topic" in walked[0][1]


def test_the_rank_decides_where_the_chain_opens_and_how_ties_break():
    cards = [question(name, "mid") for name in ("a", "b", "c")]
    bank = make_bank(*cards)

    forwards = [q.id for q, _ in chain(bank, cards, lambda q: q.id)]
    backwards = [q.id for q, _ in chain(bank, cards, lambda q: (1 / (ord(q.id[0]) or 1), q.id))]

    assert forwards == ["a", "b", "c"]
    assert backwards[0] == "c", "a different rank opens somewhere else"


def test_the_chain_is_a_permutation_of_the_pool():
    cards = [
        question(f"{category}-{n}", "mid", category=category, topic=f"t{n % 2}")
        for category in ("java", "kafka", "spring")
        for n in range(4)
    ]
    bank = make_bank(*cards)
    walked = [q.id for q, _ in chain(bank, cards, lambda q: q.id)]

    assert sorted(walked) == sorted(q.id for q in cards)
    assert len(walked) == len(set(walked))


def test_an_empty_pool_walks_to_nothing():
    assert chain(make_bank(), [], lambda q: q.id) == []


def test_nearest_of_is_stable_when_nothing_relates():
    current = question("a", "mid", category="java", topic="concurrency")
    others = [
        question("x", "mid", category="spring", topic="di"),
        question("y", "mid", category="sap-jco", topic="rfc"),
    ]
    assert [q.id for q in nearest_of(current, others)] == ["x", "y"]
    assert [q.id for q in nearest_of(None, others)] == ["x", "y"]


def test_explain_names_the_tag_that_joined_two_categories():
    a = question("a", "mid", category="java", topic="concurrency", tags=("correctness",))
    b = question("b", "mid", category="kafka", topic="delivery", tags=("correctness",))
    assert explain(a, b) == "java → kafka via correctness"
