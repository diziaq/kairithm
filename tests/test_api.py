import pytest
from fastapi.testclient import TestClient

from app.config import DEFAULT_PORT
from app.main import create_app

HOST = f"127.0.0.1:{DEFAULT_PORT}"
JSON = {"Content-Type": "application/json", "Host": HOST}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app import config, storage

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
        "filters": {"topics": ["java"]},
        "pacing": {"kind": "untimed"},
    }
    setup.update(overrides)
    response = client.post("/api/sessions", json=setup, headers=JSON)
    assert response.status_code == 200, response.text
    return response.json()


def test_a_foreign_host_header_is_refused(client):
    response = client.get("/api/bank", headers={"Host": "evil.test"})
    assert response.status_code == 421


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
    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code in (400, 404), response.text


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


def test_the_bank_endpoint_lists_topics_and_warnings(client):
    payload = client.get("/api/bank").json()
    assert payload["count"] >= 6
    assert "java" in payload["topics"]
    assert payload["warnings"] == []


def test_preview_counts_the_pool(client):
    payload = client.post(
        "/api/bank/preview", json={"filters": {"topics": ["java"]}}, headers=JSON
    ).json()
    assert payload["count"] == 3
    assert payload["estimated_minutes"] > 0


def test_a_session_round_trips_through_disk(client):
    created = make_session(client)
    fetched = client.get(f"/api/sessions/{created['id']}").json()
    assert fetched["id"] == created["id"]
    assert fetched["seed"] == 12345
    assert len(fetched["items"]) == 3


def test_answers_are_saved_and_read_back(client):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    response = client.patch(
        f"/api/sessions/{session['id']}/answers/{qid}",
        json={"rating": 4, "note": "good answer", "elapsed_seconds": 91},
        headers=JSON,
    )
    assert response.status_code == 200
    state = client.get(f"/api/sessions/{session['id']}").json()
    answer = state["items"][0]["answer"]
    assert answer["rating"] == 4
    assert answer["note"] == "good answer"
    assert answer["elapsed_seconds"] == 91


def test_marking_skipped_clears_the_rating(client):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    client.patch(f"/api/sessions/{session['id']}/answers/{qid}", json={"rating": 5}, headers=JSON)
    client.patch(
        f"/api/sessions/{session['id']}/answers/{qid}", json={"skipped": True}, headers=JSON
    )
    state = client.get(f"/api/sessions/{session['id']}").json()
    assert state["items"][0]["answer"]["skipped"] is True
    assert state["items"][0]["answer"]["rating"] is None


def test_an_answer_for_a_question_outside_the_session_is_refused(client):
    session = make_session(client)
    response = client.patch(
        f"/api/sessions/{session['id']}/answers/kafka/ordering-and-keys",
        json={"rating": 3},
        headers=JSON,
    )
    assert response.status_code == 404


def test_hints_are_left_out_of_the_response_when_they_are_off(client):
    session = make_session(client)
    with_hints = client.get(f"/api/sessions/{session['id']}/question/0?hints=1").json()
    assert "look_for" in with_hints["question"]
    assert "follow_ups" in with_hints["question"]

    without = client.get(f"/api/sessions/{session['id']}/question/0?hints=0").json()
    assert "look_for" not in without["question"]
    assert "red_flags" not in without["question"]
    assert "follow_ups" not in without["question"]
    assert "extra" not in without["question"]
    assert without["question"]["ask"]


def test_next_and_goto_move_the_position(client):
    session = make_session(client)
    state = client.post(f"/api/sessions/{session['id']}/next", json={}, headers=JSON).json()
    assert state["position"] == 1
    state = client.post(f"/api/sessions/{session['id']}/goto", json={"index": 0}, headers=JSON).json()
    assert state["position"] == 0
    bad = client.post(f"/api/sessions/{session['id']}/goto", json={"index": 99}, headers=JSON)
    assert bad.status_code == 400


def test_adaptive_escalates_after_high_ratings_and_falls_back_after_low_ones(client):
    session = make_session(
        client, mode="adaptive", start_difficulty=2, filters={"topics": ["java", "kafka", "sap"]}
    )
    session_id = session["id"]
    targets = []
    for rating in (5, 5, 1, 1):
        state = client.get(f"/api/sessions/{session_id}").json()
        current = state["items"][state["position"]]
        targets.append(current["target_difficulty"])
        client.patch(
            f"/api/sessions/{session_id}/answers/{current['qid']}",
            json={"rating": rating},
            headers=JSON,
        )
        client.post(f"/api/sessions/{session_id}/next", json={}, headers=JSON)

    final = client.get(f"/api/sessions/{session_id}").json()
    targets.append(final["items"][final["position"]]["target_difficulty"])

    assert targets[0] == 2
    assert targets[1] > targets[0], "a rating of 5 must raise the target"
    assert targets[2] > targets[1], "a second 5 must raise it again"
    assert targets[3] < targets[2], "a rating of 1 must lower the target"
    assert targets[4] < targets[3], "a second 1 must lower it again"


def test_revising_a_rating_changes_the_next_adaptive_question_not_the_past(client):
    session = make_session(client, mode="adaptive", filters={"topics": ["java", "kafka", "sap"]})
    session_id = session["id"]
    first_qid = session["items"][0]["qid"]

    client.patch(f"/api/sessions/{session_id}/answers/{first_qid}", json={"rating": 5}, headers=JSON)
    after_high = client.post(f"/api/sessions/{session_id}/next", json={}, headers=JSON).json()
    assert after_high["items"][1]["target_difficulty"] == 3

    client.post(f"/api/sessions/{session_id}/goto", json={"index": 0}, headers=JSON)
    client.patch(f"/api/sessions/{session_id}/answers/{first_qid}", json={"rating": 1}, headers=JSON)
    state = client.get(f"/api/sessions/{session_id}").json()

    assert len(state["items"]) == 2, "questions already asked are kept"
    assert state["items"][0]["answer"]["rating"] == 1


def test_finish_writes_a_scorecard_next_to_the_session(client, tmp_path):
    session = make_session(client)
    qid = session["items"][0]["qid"]
    client.patch(
        f"/api/sessions/{session['id']}/answers/{qid}",
        json={"rating": 4, "note": "clear and specific"},
        headers=JSON,
    )
    response = client.post(
        f"/api/sessions/{session['id']}/finish",
        json={"recommendation": "Hire", "summary": "Good session.", "anonymise": False},
        headers=JSON,
    )
    assert response.status_code == 200
    payload = response.json()
    written = tmp_path / "sessions" / session["id"] / "scorecard.md"
    assert written.is_file()
    text = written.read_text(encoding="utf-8")
    assert text == payload["markdown"]
    assert "# Interview Scorecard — A Petrov" in text
    assert "- **Recommendation:** Hire" in text
    assert "> clear and specific" in text
    assert "**4 / 5**" in text


def test_anonymise_replaces_the_name_in_the_file(client, tmp_path):
    session = make_session(client)
    client.post(
        f"/api/sessions/{session['id']}/finish",
        json={"recommendation": "Lean hire", "anonymise": True},
        headers=JSON,
    )
    text = (tmp_path / "sessions" / session["id"] / "scorecard.md").read_text(encoding="utf-8")
    assert "A Petrov" not in text
    assert "A. P." in text


def test_an_unknown_recommendation_is_refused(client):
    session = make_session(client)
    response = client.post(
        f"/api/sessions/{session['id']}/finish",
        json={"recommendation": "Definitely"},
        headers=JSON,
    )
    assert response.status_code == 400


def test_a_finished_session_is_listed_as_not_resumable(client):
    session = make_session(client)
    listed = client.get("/api/sessions").json()["sessions"]
    assert listed[0]["resumable"] is True
    client.post(
        f"/api/sessions/{session['id']}/finish", json={"recommendation": "Hire"}, headers=JSON
    )
    listed = client.get("/api/sessions").json()["sessions"]
    assert listed[0]["resumable"] is False


def test_filters_that_match_nothing_are_a_clear_error(client):
    response = client.post(
        "/api/sessions",
        json={"candidate": "x", "role": "y", "mode": "sequential", "filters": {"topics": ["nope"]}},
        headers=JSON,
    )
    assert response.status_code == 400
    assert "matched no questions" in response.json()["detail"]
