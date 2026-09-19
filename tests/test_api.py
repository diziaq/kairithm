import pytest
from fastapi.testclient import TestClient

from app.config import DEFAULT_PORT
from app.main import create_app
from tests.cards import card, write

HOST = f"127.0.0.1:{DEFAULT_PORT}"
JSON = {"Content-Type": "application/json", "Host": HOST}


@pytest.fixture()
def bank_root(tmp_path):
    """A small bank with enough shape to exercise levels, topics and links."""
    root = tmp_path / "bank"
    write(
        root,
        "java/java-conc-junior-01.md",
        card(
            card_id="java-conc-junior-01",
            level="junior",
            topic="concurrency",
            links="links:\n  deeper: [java-conc-senior-01]",
        ),
    )
    write(root, "java/java-conc-mid-01.md", card(card_id="java-conc-mid-01", topic="concurrency"))
    write(
        root,
        "java/java-conc-senior-01.md",
        card(card_id="java-conc-senior-01", level="senior", topic="concurrency"),
    )
    write(
        root,
        "java/java-coll-mid-01.md",
        card(card_id="java-coll-mid-01", topic="collections"),
    )
    write(
        root,
        "kafka/kafka-delivery-senior-01.md",
        card(
            card_id="kafka-delivery-senior-01",
            category="kafka",
            topic="delivery",
            level="senior",
        ),
    )
    write(
        root,
        "kafka/kafka-delivery-lead-01.md",
        card(card_id="kafka-delivery-lead-01", category="kafka", topic="delivery", level="lead"),
    )
    return root


@pytest.fixture()
def client(tmp_path, bank_root, monkeypatch):
    from app import bank as bank_module
    from app import config, storage

    monkeypatch.setattr(bank_module, "BANK_ROOT", bank_root)
    monkeypatch.setattr(config, "SESSIONS_ROOT", tmp_path / "sessions")
    monkeypatch.setattr(storage, "SESSIONS_ROOT", tmp_path / "sessions")
    (tmp_path / "sessions").mkdir()
    return TestClient(create_app(DEFAULT_PORT), headers={"Host": HOST})


def make_session(client, **overrides):
    setup = {
        "candidate": "A Petrov",
        "role": "Senior Java",
        "interviewer": "me",
        "mode": "sequential",
        "seed": 12345,
        "filters": {"categories": ["java"]},
        "pacing": {"kind": "untimed"},
    }
    setup.update(overrides)
    response = client.post("/api/sessions", json=setup, headers=JSON)
    assert response.status_code == 200, response.text
    return response.json()


def band(client, session_id, qid, value):
    response = client.patch(
        f"/api/sessions/{session_id}/answers/{qid}", json={"band": value}, headers=JSON
    )
    assert response.status_code == 200, response.text
    return response.json()


# --- the four security measures ------------------------------------------------------------


def test_a_foreign_host_header_is_refused(client):
    assert client.get("/api/bank", headers={"Host": "evil.test"}).status_code == 421


def test_a_form_encoded_mutation_is_refused(client):
    response = client.post(
        "/api/sessions",
        content="candidate=x",
        headers={"Content-Type": "application/x-www-form-urlencoded", "Host": HOST},
    )
    assert response.status_code == 415


def test_a_text_plain_mutation_is_refused(client):
    response = client.post(
        "/api/sessions", content="{}", headers={"Content-Type": "text/plain", "Host": HOST}
    )
    assert response.status_code == 415


@pytest.mark.parametrize(
    "session_id", ["..%2Fsecret", "%2e%2e%2fetc", "a/b", "....//etc", "a b", "2026-01-01_0900_x_y"]
)
def test_a_session_id_that_escapes_its_directory_is_refused_over_http(client, session_id):
    assert client.get(f"/api/sessions/{session_id}").status_code in (400, 404)


@pytest.mark.parametrize(
    "session_id", [".", "..", "../secret", "/etc/passwd", "a/b", "%2e", "", "2026-01-01_0900_x_y/.."]
)
def test_session_dir_refuses_anything_outside_the_sessions_root(session_id):
    """Some of these never reach the route, because a client normalises the URL first.

    The containment check must still refuse them, because normalisation is the client's choice,
    not a guarantee.
    """
    from app.storage import UnsafePath, session_dir

    with pytest.raises(UnsafePath):
        session_dir(session_id)


# --- the bank ---------------------------------------------------------------------------------


def test_the_bank_endpoint_lists_categories_levels_and_problems(client):
    payload = client.get("/api/bank").json()
    assert payload["count"] == 6
    assert payload["categories"] == ["java", "kafka"]
    assert payload["level_histogram"] == {"junior": 1, "mid": 2, "senior": 2, "lead": 1}
    assert payload["problems"] == []
    assert payload["error_count"] == 0


def test_a_broken_card_shows_up_in_the_bank_endpoint_rather_than_vanishing(client, bank_root):
    write(bank_root, "java/broken.md", "---\ntitle: [unclosed\n---\n\n## Ask\n\nx\n")
    payload = client.get("/api/bank").json()

    assert payload["error_count"] == 1
    assert "broken.md" in payload["problems"][0]["path"]
    assert payload["count"] == 6, "the good cards are still there"


def test_previewing_a_card_resolves_its_links_both_ways(client):
    payload = client.get("/api/bank/questions/java-conc-senior-01").json()
    assert payload["resolved_links"]["shallower"][0]["id"] == "java-conc-junior-01"
    assert payload["resolved_links"]["shallower"][0]["level"] == "junior"


def test_previewing_a_card_can_drop_the_hints(client):
    with_hints = client.get("/api/bank/questions/java-conc-mid-01?hints=1").json()
    without = client.get("/api/bank/questions/java-conc-mid-01?hints=0").json()
    assert with_hints["answer_bands"]
    assert "answer_bands" not in without
    assert without["question"]


def test_an_unknown_card_id_is_a_clear_404(client):
    assert client.get("/api/bank/questions/nope-99").status_code == 404


def test_preview_counts_the_pool(client):
    payload = client.post(
        "/api/bank/preview", json={"filters": {"categories": ["java"]}}, headers=JSON
    ).json()
    assert payload["count"] == 4
    assert payload["estimated_minutes"] > 0


def test_preview_filters_by_level(client):
    payload = client.post(
        "/api/bank/preview", json={"filters": {"levels": ["senior", "lead"]}}, headers=JSON
    ).json()
    assert {q["level"] for q in payload["questions"]} == {"senior", "lead"}


# --- sessions ---------------------------------------------------------------------------------


def test_a_session_round_trips_through_disk(client):
    created = make_session(client)
    fetched = client.get(f"/api/sessions/{created['id']}").json()
    assert fetched["id"] == created["id"]
    assert fetched["seed"] == 12345
    assert len(fetched["items"]) == 4


def test_the_question_text_is_snapshotted_when_a_card_is_served(client, bank_root, tmp_path):
    import json

    session = make_session(client)
    stored = json.loads((tmp_path / "sessions" / session["id"] / "session.json").read_text())
    item = next(i for i in stored["items"] if i["qid"] == "java-conc-junior-01")
    assert item["asked_text"] == "Say this part out loud."
    assert item["asked_level"] == "junior"
    assert item["asked_topic"] == "concurrency"


def test_a_session_survives_a_card_leaving_the_bank(client, bank_root):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    (bank_root / "java" / f"{qid}.md").unlink()

    state = client.get(f"/api/sessions/{session['id']}").json()
    assert state["items"][0]["missing"] is True
    assert state["items"][0]["question"]["title"] == "An example card", "from the snapshot"
    assert client.get(f"/api/sessions/{session['id']}/question/0").status_code == 410


def test_bands_are_saved_and_read_back(client):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    client.patch(
        f"/api/sessions/{session['id']}/answers/{qid}",
        json={"band": "senior", "note": "clear and specific", "elapsed_seconds": 91},
        headers=JSON,
    )
    answer = client.get(f"/api/sessions/{session['id']}").json()["items"][0]["answer"]
    assert answer["band"] == "senior"
    assert answer["note"] == "clear and specific"
    assert answer["elapsed_seconds"] == 91


def test_an_unknown_band_is_refused(client):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    response = client.patch(
        f"/api/sessions/{session['id']}/answers/{qid}", json={"band": "amazing"}, headers=JSON
    )
    assert response.status_code == 400
    assert "band must be one of" in response.json()["detail"]


def test_marking_skipped_clears_the_band(client):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    band(client, session["id"], qid, "lead")
    client.patch(
        f"/api/sessions/{session['id']}/answers/{qid}", json={"skipped": True}, headers=JSON
    )
    answer = client.get(f"/api/sessions/{session['id']}").json()["items"][0]["answer"]
    assert answer["skipped"] is True
    assert answer["band"] is None


def test_follow_ups_used_are_recorded(client):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    client.patch(
        f"/api/sessions/{session['id']}/answers/{qid}",
        json={"follow_ups_used": [1, 0, 1]},
        headers=JSON,
    )
    answer = client.get(f"/api/sessions/{session['id']}").json()["items"][0]["answer"]
    assert answer["follow_ups_used"] == [0, 1]


def test_an_answer_for_a_card_outside_the_session_is_refused(client):
    session = make_session(client)
    response = client.patch(
        f"/api/sessions/{session['id']}/answers/kafka-delivery-senior-01",
        json={"band": "mid"},
        headers=JSON,
    )
    assert response.status_code == 404


def test_hints_are_left_out_of_the_response_when_they_are_off(client):
    session = make_session(client)
    with_hints = client.get(f"/api/sessions/{session['id']}/question/0?hints=1").json()
    assert "listen_for" in with_hints["question"]
    assert "answer_bands" in with_hints["question"]

    without = client.get(f"/api/sessions/{session['id']}/question/0?hints=0").json()
    for hidden in ("listen_for", "answer_bands", "follow_ups", "weak_signals", "tests"):
        assert hidden not in without["question"]
    assert without["question"]["question"]


# --- navigation -------------------------------------------------------------------------------


def test_next_and_goto_move_the_position(client):
    session = make_session(client)
    state = client.post(f"/api/sessions/{session['id']}/next", json={}, headers=JSON).json()
    assert state["position"] == 1
    state = client.post(f"/api/sessions/{session['id']}/goto", json={"index": 0}, headers=JSON).json()
    assert state["position"] == 0
    assert client.post(
        f"/api/sessions/{session['id']}/goto", json={"index": 99}, headers=JSON
    ).status_code == 400


def test_jumping_to_a_card_outside_the_pool_serves_it_and_keeps_everything_else(client):
    session = make_session(client)
    first = session["items"][0]["qid"]
    client.patch(
        f"/api/sessions/{session['id']}/answers/{first}",
        json={"band": "mid", "note": "kept"},
        headers=JSON,
    )

    state = client.post(
        f"/api/sessions/{session['id']}/jump",
        json={"question_id": "kafka-delivery-lead-01"},
        headers=JSON,
    ).json()

    assert state["items"][-1]["qid"] == "kafka-delivery-lead-01"
    assert state["position"] == len(state["items"]) - 1
    assert state["items"][0]["answer"]["note"] == "kept", "leaving the plan loses nothing"


def test_jumping_back_to_a_card_already_served_moves_rather_than_duplicates(client):
    session = make_session(client)
    before = len(session["items"])
    target = session["items"][2]["qid"]

    state = client.post(
        f"/api/sessions/{session['id']}/jump", json={"question_id": target}, headers=JSON
    ).json()
    assert state["position"] == 2
    assert len(state["items"]) == before


def test_jumping_to_an_unknown_card_is_a_clear_404(client):
    session = make_session(client)
    response = client.post(
        f"/api/sessions/{session['id']}/jump", json={"question_id": "nope-99"}, headers=JSON
    )
    assert response.status_code == 404


# --- calibration and suggestions ----------------------------------------------------------------


def test_the_calibration_starts_where_the_setup_asked(client):
    session = make_session(client, mode="adaptive", start_level="senior")
    assert session["calibration"]["target_level"] == "senior"


def test_a_mid_band_on_a_senior_question_drops_the_calibration_to_mid(client):
    """The case the brief names. The next suggestion must not be another senior question."""
    session = make_session(
        client, filters={"manual_ids": ["java-conc-senior-01"]}, mode="manual"
    )
    result = band(client, session["id"], "java-conc-senior-01", "mid")

    assert result["calibration"]["target_level"] == "mid"
    assert result["calibration"]["latest"]["outcome"] == "one_below"
    assert result["calibration"]["latest"]["prefer"][0] == "shallower"

    suggestions = client.get(f"/api/sessions/{session['id']}/suggestions").json()["suggestions"]
    assert suggestions, "something has to be offered"
    assert all(s["level"] != "senior" for s in suggestions), "do not confirm the same failure"


def test_a_band_above_the_question_raises_the_bar_and_offers_deeper_first(client):
    session = make_session(client, filters={"manual_ids": ["java-conc-junior-01"]}, mode="manual")
    result = band(client, session["id"], "java-conc-junior-01", "senior")

    assert result["calibration"]["target_level"] == "senior"
    assert result["calibration"]["latest"]["outcome"] == "above"

    suggestions = client.get(f"/api/sessions/{session['id']}/suggestions").json()["suggestions"]
    assert suggestions[0]["kind"] == "deeper"
    assert suggestions[0]["id"] == "java-conc-senior-01"


def test_revising_an_earlier_band_changes_the_calibration_without_losing_the_past(client):
    session = make_session(client)
    first, second = session["items"][0]["qid"], session["items"][1]["qid"]
    band(client, session["id"], first, "lead")
    band(client, session["id"], second, "weak")
    assert client.get(f"/api/sessions/{session['id']}").json()["calibration"]["target_level"] == "junior"

    band(client, session["id"], second, "senior")
    state = client.get(f"/api/sessions/{session['id']}").json()
    assert state["calibration"]["target_level"] == "senior"
    assert state["items"][0]["answer"]["band"] == "lead", "nothing already asked is lost"


def test_the_calibration_can_be_overridden_and_cleared(client):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    band(client, session["id"], qid, "weak")
    assert client.get(f"/api/sessions/{session['id']}").json()["calibration"]["target_level"] == "junior"

    state = client.post(
        f"/api/sessions/{session['id']}/calibration", json={"level": "lead"}, headers=JSON
    ).json()
    assert state["calibration"]["target_level"] == "lead"
    assert state["calibration"]["override"] == "lead"

    state = client.post(
        f"/api/sessions/{session['id']}/calibration", json={"level": None}, headers=JSON
    ).json()
    assert state["calibration"]["target_level"] == "junior", "back to what the bands say"


def test_an_unknown_override_level_is_refused(client):
    session = make_session(client)
    response = client.post(
        f"/api/sessions/{session['id']}/calibration", json={"level": "principal"}, headers=JSON
    )
    assert response.status_code == 400


def test_the_calibration_is_tracked_per_topic_as_well(client):
    session = make_session(client)
    ids = [item["qid"] for item in session["items"]]
    band(client, session["id"], "java-coll-mid-01", "lead")
    band(client, session["id"], "java-conc-mid-01", "weak")

    by_topic = client.get(f"/api/sessions/{session['id']}").json()["calibration"]["by_topic"]
    assert by_topic["collections"] == "lead"
    assert by_topic["concurrency"] == "junior"
    assert ids


def test_adaptive_follows_the_bands_up_and_then_back_down(client):
    session = make_session(
        client, mode="adaptive", start_level="junior", filters={"categories": ["java", "kafka"]}
    )
    session_id = session["id"]
    targets = []
    for value in ("lead", "lead", "weak"):
        state = client.get(f"/api/sessions/{session_id}").json()
        current = state["items"][state["position"]]
        targets.append(current["target_level"])
        band(client, session_id, current["qid"], value)
        client.post(f"/api/sessions/{session_id}/next", json={}, headers=JSON)

    final = client.get(f"/api/sessions/{session_id}").json()
    targets.append(final["items"][final["position"]]["target_level"])

    assert targets[0] == "junior"
    assert targets[1] == "lead", "a lead band raises the bar straight away"
    assert targets[3] == "junior", "a weak band drops it to the floor"


def test_adaptive_stops_cleanly_when_the_pool_is_used_up(client):
    session = make_session(
        client, mode="adaptive", filters={"manual_ids": ["java-conc-mid-01"]}
    )
    state = client.post(f"/api/sessions/{session['id']}/next", json={}, headers=JSON).json()
    assert state["adaptive_exhausted"] is True
    assert len(state["items"]) == 1


# --- finishing ---------------------------------------------------------------------------------


def test_the_summary_endpoint_returns_the_range_and_the_hot_spots(client):
    session = make_session(client)
    band(client, session["id"], "java-coll-mid-01", "lead")
    band(client, session["id"], "java-conc-senior-01", "junior")

    payload = client.get(f"/api/sessions/{session['id']}/summary").json()
    assert 0 <= payload["score"]["value"] <= 100
    assert payload["score"]["formula"]
    assert [row["name"] for row in payload["hot_spots"]["weak"]] == ["concurrency"]
    assert [row["name"] for row in payload["hot_spots"]["strong"]] == ["collections"]
    assert payload["band_matrix"]


def test_finish_writes_a_scorecard_next_to_the_session(client, tmp_path):
    session = make_session(client)
    client.patch(
        f"/api/sessions/{session['id']}/answers/java-conc-junior-01",
        json={"band": "senior", "note": "walked through it without prompting"},
        headers=JSON,
    )
    response = client.post(
        f"/api/sessions/{session['id']}/finish",
        json={"summary": "Good session.", "anonymise": False},
        headers=JSON,
    )
    assert response.status_code == 200

    written = tmp_path / "sessions" / session["id"] / "scorecard.md"
    text = written.read_text(encoding="utf-8")
    assert text == response.json()["markdown"]
    assert "# Interview Scorecard — A Petrov" in text
    assert "**senior** band on a **junior** question" in text
    assert "> walked through it without prompting" in text


def test_the_scorecard_keeps_facts_apart_from_the_interviewer_s_words(client, tmp_path):
    session = make_session(client)
    band(client, session["id"], "java-conc-junior-01", "mid")
    client.post(
        f"/api/sessions/{session['id']}/finish",
        json={"summary": "My own conclusion.", "strengths": "Reasons clearly."},
        headers=JSON,
    )
    text = (tmp_path / "sessions" / session["id"] / "scorecard.md").read_text()

    evidence = text.index("## Evidence")
    assessment = text.index("## Assessment (interviewer)")
    assert evidence < assessment
    assert "My own conclusion." in text[assessment:]
    assert "My own conclusion." not in text[:assessment]
    assert "Nothing in this section is generated." in text[assessment:]


def test_the_scorecard_carries_the_range_with_its_formula(client, tmp_path):
    session = make_session(client)
    band(client, session["id"], "java-conc-junior-01", "mid")
    client.post(f"/api/sessions/{session['id']}/finish", json={}, headers=JSON)
    text = (tmp_path / "sessions" / session["id"] / "scorecard.md").read_text()

    assert "/ 100" in text
    assert "0 is an intern, 100 an engineering tech lead." in text
    assert "sum(band points x level weight)" in text, "the formula is printed, not hidden"


def test_the_scorecard_lists_what_was_never_evidenced(client, tmp_path):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    client.patch(
        f"/api/sessions/{session['id']}/answers/{qid}", json={"skipped": True}, headers=JSON
    )
    client.post(f"/api/sessions/{session['id']}/finish", json={}, headers=JSON)
    text = (tmp_path / "sessions" / session["id"] / "scorecard.md").read_text()

    assert "## Gaps — no evidence collected" in text
    assert "was skipped" in text
    assert "was asked but never banded" in text


def test_there_is_no_hire_recommendation_anywhere(client, tmp_path):
    session = make_session(client)
    band(client, session["id"], "java-conc-junior-01", "lead")
    client.post(
        f"/api/sessions/{session['id']}/finish",
        json={"summary": "x", "recommendation": "Strong hire"},
        headers=JSON,
    )
    text = (tmp_path / "sessions" / session["id"] / "scorecard.md").read_text()
    for word in ("Strong hire", "No hire", "Lean hire", "Recommendation"):
        assert word not in text


def test_anonymise_replaces_the_name_in_the_file(client, tmp_path):
    session = make_session(client)
    client.post(
        f"/api/sessions/{session['id']}/finish", json={"anonymise": True}, headers=JSON
    )
    text = (tmp_path / "sessions" / session["id"] / "scorecard.md").read_text()
    assert "A Petrov" not in text
    assert "A. P." in text


def test_a_finished_session_is_listed_as_not_resumable(client):
    session = make_session(client)
    assert client.get("/api/sessions").json()["sessions"][0]["resumable"] is True
    client.post(f"/api/sessions/{session['id']}/finish", json={}, headers=JSON)
    assert client.get("/api/sessions").json()["sessions"][0]["resumable"] is False


def test_a_finished_session_refuses_further_edits(client):
    session = make_session(client)
    client.post(f"/api/sessions/{session['id']}/finish", json={}, headers=JSON)
    response = client.patch(
        f"/api/sessions/{session['id']}/answers/{session['items'][0]['qid']}",
        json={"band": "mid"},
        headers=JSON,
    )
    assert response.status_code == 409


def test_filters_that_match_nothing_are_a_clear_error(client):
    response = client.post(
        "/api/sessions",
        json={"candidate": "x", "role": "y", "mode": "sequential", "filters": {"categories": ["nope"]}},
        headers=JSON,
    )
    assert response.status_code == 400
    assert "matched no questions" in response.json()["detail"]


# --- resume -------------------------------------------------------------------------------------


def test_reloading_mid_interview_restores_the_session_exactly(client):
    """The browser holds nothing. A reload is a fresh GET, so this is the whole guarantee."""
    session = make_session(client)
    session_id = session["id"]
    first, second = session["items"][0]["qid"], session["items"][1]["qid"]

    client.patch(
        f"/api/sessions/{session_id}/answers/{first}",
        json={"band": "senior", "note": "first note", "elapsed_seconds": 140,
              "follow_ups_used": [0]},
        headers=JSON,
    )
    client.post(f"/api/sessions/{session_id}/next", json={}, headers=JSON)
    client.patch(
        f"/api/sessions/{session_id}/answers/{second}",
        json={"band": "weak", "note": "second note"},
        headers=JSON,
    )
    before = client.get(f"/api/sessions/{session_id}").json()

    # A reload is a new client against the same files on disk.
    fresh = TestClient(create_app(DEFAULT_PORT), headers={"Host": HOST})
    after = fresh.get(f"/api/sessions/{session_id}").json()

    assert after["position"] == before["position"] == 1
    assert after["items"][0]["answer"]["band"] == "senior"
    assert after["items"][0]["answer"]["note"] == "first note"
    assert after["items"][0]["answer"]["elapsed_seconds"] == 140
    assert after["items"][0]["answer"]["follow_ups_used"] == [0]
    assert after["items"][1]["answer"]["band"] == "weak"
    assert after["calibration"] == before["calibration"]
    assert [i["qid"] for i in after["items"]] == [i["qid"] for i in before["items"]]


# --- the executive summary ------------------------------------------------------------------


def test_finish_writes_an_executive_summary_beside_the_scorecard(client, tmp_path):
    session = make_session(client)
    band(client, session["id"], "java-conc-junior-01", "senior")
    band(client, session["id"], "java-conc-senior-01", "junior")
    response = client.post(
        f"/api/sessions/{session['id']}/finish",
        json={"summary": "Reasons well at the code level."},
        headers=JSON,
    )
    payload = response.json()

    written = tmp_path / "sessions" / session["id"] / "summary.md"
    assert written.is_file()
    text = written.read_text(encoding="utf-8")
    assert text == payload["summary_markdown"]
    assert payload["summary_download_name"] == "summary-a-petrov.md"
    assert text.startswith("# A Petrov — executive summary")


def test_the_executive_summary_is_about_the_candidate_not_the_interview(client, tmp_path):
    session = make_session(client)
    band(client, session["id"], "java-conc-junior-01", "senior")
    band(client, session["id"], "java-conc-senior-01", "junior")
    client.post(f"/api/sessions/{session['id']}/finish", json={}, headers=JSON)
    text = (tmp_path / "sessions" / session["id"] / "summary.md").read_text()

    assert "## Answer quality" in text
    assert "Met or beat the level asked on" in text
    for noise in ("Seed", "## Evidence", "sequential", "pool"):
        assert noise not in text


def test_the_executive_summary_is_served_before_the_interview_is_finished(client):
    session = make_session(client)
    band(client, session["id"], "java-conc-junior-01", "mid")
    response = client.get(f"/api/sessions/{session['id']}/executive-summary")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "executive summary" in response.text
