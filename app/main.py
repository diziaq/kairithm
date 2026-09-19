"""FastAPI application: routes, and the two middlewares that make "no authentication" safe."""

from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .bank import Bank, load_bank
from .levels import BANDS, LEVELS
from .report import render_scorecard, render_summary, scorecard_filename, summary_filename
from .scoring import band_matrix, by_category, by_topic, hot_spots, score
from .selection import ADAPTIVE, PoolFilters, build_pool, suggest
from .session import (
    Session,
    create_session,
    ensure_sessions_root,
    list_sessions,
    load_session,
    previously_asked_ids,
    utc_now,
)
from .storage import UnsafePath, write_text_atomic
from .validate import validate_bank

MUTATING_METHODS = {"POST", "PATCH", "PUT", "DELETE"}
JSON_CONTENT_TYPE = "application/json"


def read_bank() -> Bank:
    """Read the bank from disk for this request. There is no cache, so an edit takes effect now."""
    return load_bank()


def create_app(port: int = config.DEFAULT_PORT) -> FastAPI:
    app = FastAPI(title="Interview Runner", docs_url=None, redoc_url=None, openapi_url=None)
    hosts = config.allowed_hosts(port)

    @app.middleware("http")
    async def reject_foreign_host(request: Request, call_next):
        """Refuse any Host header that is not loopback.

        The bind to 127.0.0.1 stops other machines. It does not stop DNS rebinding, where an
        attacker's name resolves to 127.0.0.1 after their page has loaded. This check does.
        """
        if request.headers.get("host", "") not in hosts:
            return PlainTextResponse("host not allowed", status_code=421)
        return await call_next(request)

    @app.middleware("http")
    async def require_json_for_mutations(request: Request, call_next):
        """Refuse a mutating request that is not application/json.

        A browser sends an HTML form as form data, text or multipart, and those three need no
        preflight. Any page on any site could then drive this tool. Requiring JSON forces a
        preflight, and there are no CORS headers here for that preflight to succeed against.
        """
        if request.method in MUTATING_METHODS:
            content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
            if content_type != JSON_CONTENT_TYPE:
                return JSONResponse(
                    {"detail": f"mutating requests must use {JSON_CONTENT_TYPE}"},
                    status_code=415,
                )
        return await call_next(request)

    def get_session(session_id: str) -> Session:
        try:
            return load_session(session_id)
        except UnsafePath as error:
            raise HTTPException(400, str(error)) from error
        except (OSError, ValueError) as error:
            raise HTTPException(404, f"no such session: {session_id}") from error

    def live_session(session_id: str) -> Session:
        session = get_session(session_id)
        if session.finished:
            raise HTTPException(409, "this session is finished")
        return session

    # --- the bank ------------------------------------------------------------------------

    @app.get("/api/bank")
    def api_bank() -> dict[str, Any]:
        bank = read_bank()
        problems = validate_bank(bank)
        return {
            "categories": bank.categories,
            "topics": bank.topics,
            "tags": bank.tags,
            "levels": list(LEVELS),
            "bands": list(BANDS),
            "level_histogram": bank.level_histogram(),
            "count": len(bank.questions),
            "questions": [q.summary() for q in bank.questions.values()],
            "problems": [p.as_dict() for p in problems],
            "error_count": sum(1 for p in problems if p.severity == "error"),
        }

    @app.get("/api/bank/questions/{question_id}")
    def api_bank_question(question_id: str, hints: int = 1) -> dict[str, Any]:
        """Preview one card outside any session."""
        bank = read_bank()
        question = bank.get(question_id)
        if question is None:
            raise HTTPException(404, f"no card with id {question_id}")
        data = question.public(include_hints=bool(hints))
        data["resolved_links"] = {
            kind: [
                {"id": qid, "title": bank.get(qid).title, "level": bank.get(qid).level}
                for qid in ids
                if bank.get(qid)
            ]
            for kind, ids in bank.resolved_links(question_id).items()
        }
        return data

    @app.post("/api/bank/preview")
    def api_bank_preview(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        bank = read_bank()
        raw_filters = dict(payload.get("filters") or {})
        candidate = str(payload.get("exclude_asked_to") or "").strip()
        if candidate:
            already = set(raw_filters.get("exclude_ids") or []) | set(previously_asked_ids(candidate))
            raw_filters["exclude_ids"] = sorted(already)
        pool = build_pool(bank, PoolFilters.from_dict(raw_filters))
        minutes = sum(q.time_estimate_min or config.DEFAULT_QUESTION_MINUTES for q in pool)
        return {
            "count": len(pool),
            "estimated_minutes": minutes,
            "questions": [q.summary() for q in pool],
        }

    # --- sessions ------------------------------------------------------------------------

    @app.get("/api/sessions")
    def api_sessions() -> dict[str, Any]:
        return {"sessions": list_sessions()}

    @app.post("/api/sessions")
    def api_create_session(setup: dict[str, Any] = Body(...)) -> dict[str, Any]:
        bank = read_bank()
        ensure_sessions_root()
        candidate = str(setup.get("exclude_asked_to") or "").strip()
        if candidate:
            filters = dict(setup.get("filters") or {})
            already = set(filters.get("exclude_ids") or []) | set(previously_asked_ids(candidate))
            filters["exclude_ids"] = sorted(already)
            setup = {**setup, "filters": filters}
        try:
            session = create_session(bank, setup)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        return session.as_state(bank)

    @app.get("/api/sessions/{session_id}")
    def api_get_session(session_id: str) -> dict[str, Any]:
        return get_session(session_id).as_state(read_bank())

    @app.get("/api/sessions/{session_id}/question/{index}")
    def api_get_question(session_id: str, index: int, hints: int = 1) -> dict[str, Any]:
        session = get_session(session_id)
        bank = read_bank()
        if not 0 <= index < len(session.items):
            raise HTTPException(404, f"no question at position {index}")
        item = session.items[index]
        question = bank.get(item["qid"])
        if question is None:
            raise HTTPException(
                410, f"{item['qid']} is in this session but is no longer in the bank"
            )
        return {
            "index": index,
            "total": len(session.items),
            "target_level": item.get("target_level"),
            "reason": item.get("reason"),
            "budget_minutes": session.default_minutes_for(question),
            "question": question.public(include_hints=bool(hints)),
            "answer": session.answer_for(item["qid"]),
        }

    @app.patch("/api/sessions/{session_id}/answers/{question_id}")
    def api_patch_answer(
        session_id: str, question_id: str, patch: dict[str, Any] = Body(...)
    ) -> dict[str, Any]:
        session = live_session(session_id)
        if question_id not in set(session.served_ids()):
            raise HTTPException(404, f"{question_id} is not part of this session")
        try:
            answer = session.set_answer(question_id, patch)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        session.save()
        bank = read_bank()
        return {
            "qid": question_id,
            "answer": answer,
            "revision": session.data["revision"],
            "calibration": session.as_state(bank)["calibration"],
        }

    # --- navigation ----------------------------------------------------------------------

    @app.get("/api/sessions/{session_id}/suggestions")
    def api_suggestions(session_id: str) -> dict[str, Any]:
        """What the tool would offer next. Always advisory; nothing here moves the interview."""
        session = get_session(session_id)
        bank = read_bank()
        position = int(session.data.get("position", 0))
        current = None
        if 0 <= position < len(session.items):
            current = bank.get(session.items[position]["qid"])

        latest, source, per_topic = session.replay_calibration(bank)
        target = session.target_level(bank)
        suggestions = suggest(
            bank=bank,
            current=current,
            calibration=latest,
            target_level=target,
            served_ids=session.served_ids(),
            pool=session.pool(bank) or None,
        )
        return {
            "calibration": {
                "target_level": target,
                "override": session.data.get("calibration_override"),
                "from_question": source,
                "latest": latest.as_dict() if latest else None,
                "by_topic": per_topic,
            },
            "suggestions": [
                {**s.as_dict(), **(bank.get(s.question_id).summary())}
                for s in suggestions
                if bank.get(s.question_id)
            ],
        }

    @app.post("/api/sessions/{session_id}/calibration")
    def api_set_calibration(
        session_id: str, payload: dict[str, Any] = Body(...)
    ) -> dict[str, Any]:
        """Override the running calibration by hand, or clear the override with null."""
        session = live_session(session_id)
        raw = payload.get("level")
        if raw is not None and str(raw).lower() not in LEVELS:
            raise HTTPException(400, f"level must be null or one of {', '.join(LEVELS)}")
        session.data["calibration_override"] = None if raw is None else str(raw).lower()
        session.save()
        return session.as_state(read_bank())

    @app.post("/api/sessions/{session_id}/next")
    def api_next(
        session_id: str, payload: dict[str, Any] = Body(default_factory=dict)
    ) -> dict[str, Any]:
        session = live_session(session_id)
        bank = read_bank()

        position = int(session.data.get("position", 0))
        target = position + 1
        if session.mode == ADAPTIVE and target >= len(session.items):
            if session.append_adaptive_item(bank) is None:
                session.data["adaptive_exhausted"] = True
                session.save()
                return session.as_state(bank)
        if target >= len(session.items):
            session.save()
            return session.as_state(bank)
        session.data["position"] = target
        session.save()
        return session.as_state(bank)

    @app.post("/api/sessions/{session_id}/goto")
    def api_goto(session_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        """Move to any position already served. Covers previous, next and a jump backwards."""
        session = live_session(session_id)
        bank = read_bank()
        try:
            index = int(payload.get("index"))
        except (TypeError, ValueError) as error:
            raise HTTPException(400, "index must be a whole number") from error
        if not 0 <= index < len(session.items):
            raise HTTPException(400, f"no question at position {index}")
        session.data["position"] = index
        session.save()
        return session.as_state(bank)

    @app.post("/api/sessions/{session_id}/jump")
    def api_jump(session_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        """Serve any card in the bank next, whether or not it was in the pool.

        The interviewer is never confined to the plan. A card already served is not appended
        again; the position moves to where it already is, so no state is lost.
        """
        session = live_session(session_id)
        bank = read_bank()
        question_id = str(payload.get("question_id") or "")
        if bank.get(question_id) is None:
            raise HTTPException(404, f"no card with id {question_id}")

        served = session.served_ids()
        if question_id in served:
            session.data["position"] = served.index(question_id)
        else:
            session.append_item(bank, question_id, str(payload.get("reason") or "picked by hand"))
            session.data["position"] = len(session.items) - 1
        session.save()
        return session.as_state(bank)

    # --- finishing -----------------------------------------------------------------------

    @app.get("/api/sessions/{session_id}/summary")
    def api_summary(session_id: str) -> dict[str, Any]:
        """The aggregates the summary screen draws. Arithmetic over recorded bands, nothing more."""
        session = get_session(session_id)
        bank = read_bank()
        observations = session.observations(bank)
        topics = by_topic(observations)
        return {
            "id": session.id,
            "score": score(observations).as_dict(),
            "by_category": [row.as_dict() for row in by_category(observations)],
            "by_topic": [row.as_dict() for row in topics],
            "hot_spots": {key: [row.as_dict() for row in rows] for key, rows in hot_spots(topics).items()},
            "band_matrix": band_matrix(observations),
            "observations": [
                {
                    "qid": o.qid,
                    "category": o.category,
                    "topic": o.topic,
                    "level": o.level,
                    "band": o.band,
                    "gap": o.gap,
                }
                for o in observations
            ],
        }

    @app.post("/api/sessions/{session_id}/finish")
    def api_finish(session_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        session = get_session(session_id)
        bank = read_bank()
        session.data["finish"] = {
            "summary": str(payload.get("summary") or ""),
            "strengths": str(payload.get("strengths") or ""),
            "concerns": str(payload.get("concerns") or ""),
            "follow_up_areas": str(payload.get("follow_up_areas") or ""),
            "anonymise": bool(payload.get("anonymise")),
        }
        session.data["finished_utc"] = utc_now()
        markdown = render_scorecard(session, bank)
        brief = render_summary(session, bank)
        write_text_atomic(session.scorecard_path, markdown)
        write_text_atomic(session.summary_path, brief)
        session.save()
        return {
            "id": session.id,
            "path": str(session.scorecard_path),
            "summary_path": str(session.summary_path),
            "download_name": scorecard_filename(session),
            "summary_download_name": summary_filename(session),
            "markdown": markdown,
            "summary_markdown": brief,
        }

    @app.get("/api/sessions/{session_id}/scorecard")
    def api_scorecard(session_id: str) -> PlainTextResponse:
        session = get_session(session_id)
        bank = read_bank()
        markdown = (
            session.scorecard_path.read_text(encoding="utf-8")
            if session.scorecard_path.is_file()
            else render_scorecard(session, bank)
        )
        return PlainTextResponse(markdown, media_type="text/markdown; charset=utf-8")

    @app.get("/api/sessions/{session_id}/executive-summary")
    def api_executive_summary(session_id: str) -> PlainTextResponse:
        """One page about the candidate. No mode, no seed, no timings."""
        session = get_session(session_id)
        bank = read_bank()
        markdown = (
            session.summary_path.read_text(encoding="utf-8")
            if session.summary_path.is_file()
            else render_summary(session, bank)
        )
        return PlainTextResponse(markdown, media_type="text/markdown; charset=utf-8")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(config.WEB_ROOT / "index.html")

    app.mount("/web", StaticFiles(directory=config.WEB_ROOT), name="web")
    return app
