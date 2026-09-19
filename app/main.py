"""FastAPI application: routes, and the two middlewares that make "no authentication" safe."""

from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .bank import Bank, load_bank
from .report import RECOMMENDATIONS, render_scorecard, scorecard_filename
from .selection import ADAPTIVE, PoolFilters, build_pool
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

    @app.get("/api/bank")
    def api_bank() -> dict[str, Any]:
        bank = read_bank()
        return {
            "topics": bank.topics,
            "tags": bank.tags,
            "difficulty_histogram": bank.difficulty_histogram(),
            "count": len(bank.questions),
            "questions": [q.summary() for q in bank.questions.values()],
            "warnings": [{"path": w.path, "problem": w.problem} for w in bank.warnings],
        }

    @app.post("/api/bank/preview")
    def api_bank_preview(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        bank = read_bank()
        raw_filters = dict(payload.get("filters") or {})
        candidate = str(payload.get("exclude_asked_to") or "").strip()
        if candidate:
            already = set(raw_filters.get("exclude_ids") or []) | set(previously_asked_ids(candidate))
            raw_filters["exclude_ids"] = sorted(already)
        pool = build_pool(bank, PoolFilters.from_dict(raw_filters))
        minutes = sum(q.time_minutes or config.DEFAULT_QUESTION_MINUTES for q in pool)
        return {
            "count": len(pool),
            "estimated_minutes": minutes,
            "questions": [q.summary() for q in pool],
            "warnings": [{"path": w.path, "problem": w.problem} for w in bank.warnings],
        }

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
            "target_difficulty": item.get("target_difficulty"),
            "reason": item.get("reason"),
            "budget_minutes": session.default_minutes_for(question),
            "question": question.public(include_hints=bool(hints)),
            "answer": session.answer_for(item["qid"]),
        }

    @app.patch("/api/sessions/{session_id}/answers/{question_id:path}")
    def api_patch_answer(
        session_id: str, question_id: str, patch: dict[str, Any] = Body(...)
    ) -> dict[str, Any]:
        session = get_session(session_id)
        if session.finished:
            raise HTTPException(409, "this session is finished")
        if question_id not in {item["qid"] for item in session.items}:
            raise HTTPException(404, f"{question_id} is not part of this session")
        answer = session.set_answer(question_id, patch)
        session.save()
        return {"qid": question_id, "answer": answer, "revision": session.data["revision"]}

    @app.post("/api/sessions/{session_id}/next")
    def api_next(
        session_id: str, payload: dict[str, Any] = Body(default_factory=dict)
    ) -> dict[str, Any]:
        session = get_session(session_id)
        bank = read_bank()
        if session.finished:
            raise HTTPException(409, "this session is finished")

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
        """Move to any served position. The interview screen uses this for previous and for jumps."""
        session = get_session(session_id)
        bank = read_bank()
        if session.finished:
            raise HTTPException(409, "this session is finished")
        try:
            index = int(payload.get("index"))
        except (TypeError, ValueError) as error:
            raise HTTPException(400, "index must be a whole number") from error
        if not 0 <= index < len(session.items):
            raise HTTPException(400, f"no question at position {index}")
        session.data["position"] = index
        session.save()
        return session.as_state(bank)

    @app.post("/api/sessions/{session_id}/finish")
    def api_finish(session_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        session = get_session(session_id)
        bank = read_bank()
        recommendation = str(payload.get("recommendation") or "Inconclusive")
        if recommendation not in RECOMMENDATIONS:
            raise HTTPException(400, f"recommendation must be one of {list(RECOMMENDATIONS)}")
        session.data["finish"] = {
            "recommendation": recommendation,
            "summary": str(payload.get("summary") or ""),
            "strengths": str(payload.get("strengths") or ""),
            "concerns": str(payload.get("concerns") or ""),
            "follow_up_areas": str(payload.get("follow_up_areas") or ""),
            "anonymise": bool(payload.get("anonymise")),
        }
        session.data["finished_utc"] = utc_now()
        markdown = render_scorecard(session, bank)
        write_text_atomic(session.scorecard_path, markdown)
        session.save()
        return {
            "id": session.id,
            "path": str(session.scorecard_path),
            "download_name": scorecard_filename(session),
            "markdown": markdown,
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

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(config.WEB_ROOT / "index.html")

    app.mount("/web", StaticFiles(directory=config.WEB_ROOT), name="web")
    return app
