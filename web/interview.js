// The live interview screen: one question, the interviewer notes, rating, note, timers, shortcuts.

import { api, patchAnswerKeepalive } from "./api.js";
import { clear, el, formatClock, isTypingTarget, make, renderSimpleMarkdown, setSaveState } from "./dom.js";

const RATING_LABELS = [
  [1, "No understanding"],
  [2, "Shaky, needed prompting"],
  [3, "Solid, expected level"],
  [4, "Strong, went beyond"],
  [5, "Excellent, taught me something"],
];

const HINTS_KEY = "interview-runner.hints-visible";
const NOTE_DEBOUNCE_MS = 500;
const TIMER_PUSH_MS = 15000;

const view = {
  sessionId: null,
  state: null,
  index: 0,
  question: null,
  answer: {},
  hintsVisible: true,
  followUpsVisible: false,
  elapsedBase: 0,
  enteredAt: 0,
  totalBase: 0,
  noteTimer: null,
  tickTimer: null,
  pushTimer: null,
  pendingNote: null,
  onFinish: () => {},
};

function hintsVisibleFromStorage() {
  // Hints-off must survive a reload. A refresh during a shared screen must not put the answer key
  // back on the display.
  return localStorage.getItem(HINTS_KEY) !== "0";
}

function questionElapsed() {
  return view.elapsedBase + Math.floor((Date.now() - view.enteredAt) / 1000);
}

function totalElapsed() {
  return view.totalBase + Math.floor((Date.now() - view.enteredAt) / 1000);
}

function sumRecordedSeconds(state, exceptQid) {
  return state.items.reduce((total, item) => {
    if (item.qid === exceptQid) return total;
    return total + Number((item.answer && item.answer.elapsed_seconds) || 0);
  }, 0);
}

async function pushElapsed() {
  if (!view.question) return;
  try {
    await api.patchAnswer(view.sessionId, view.question.id, {
      elapsed_seconds: questionElapsed(),
    });
  } catch {
    setSaveState("error");
  }
}

// Flush anything the debounce still holds. Called before leaving a question, and when the page
// is about to go away.
export async function flushPending(useKeepalive = false) {
  clearTimeout(view.noteTimer);
  view.noteTimer = null;
  if (!view.question) return;
  const patch = { elapsed_seconds: questionElapsed() };
  if (view.pendingNote !== null) {
    patch.note = view.pendingNote;
    view.pendingNote = null;
  }
  try {
    if (useKeepalive) {
      patchAnswerKeepalive(view.sessionId, view.question.id, patch);
      return;
    }
    setSaveState("saving");
    await api.patchAnswer(view.sessionId, view.question.id, patch);
    setSaveState("saved");
  } catch {
    setSaveState("error");
  }
}

function renderRatings() {
  const row = el("rating-row");
  clear(row);
  for (const [value, label] of RATING_LABELS) {
    const pressed = !view.answer.skipped && view.answer.rating === value;
    const button = make("button", {
      attrs: { type: "button", "aria-pressed": String(pressed) },
      children: [make("span", { className: "k", text: String(value) }), make("span", { text: label })],
    });
    button.addEventListener("click", () => setRating(value));
    row.appendChild(button);
  }
  const skipPressed = Boolean(view.answer.skipped);
  const skip = make("button", {
    className: "skip",
    attrs: { type: "button", "aria-pressed": String(skipPressed) },
    children: [make("span", { className: "k", text: "0" }), make("span", { text: "Skipped" })],
  });
  skip.addEventListener("click", () => setSkipped(!skipPressed));
  row.appendChild(skip);
}

async function setRating(value) {
  view.answer = { ...view.answer, rating: value, skipped: false };
  renderRatings();
  await save({ rating: value, skipped: false });
}

async function setSkipped(on) {
  view.answer = { ...view.answer, skipped: on, rating: on ? null : view.answer.rating };
  renderRatings();
  await save({ skipped: on });
}

async function save(patch) {
  setSaveState("saving");
  try {
    const result = await api.patchAnswer(view.sessionId, view.question.id, {
      ...patch,
      elapsed_seconds: questionElapsed(),
    });
    view.answer = result.answer;
    setSaveState("saved");
  } catch {
    setSaveState("error");
  }
}

function applyHintVisibility() {
  el("hint-zone").classList.toggle("hidden", !view.hintsVisible);
  el("hints-hidden-notice").classList.toggle("hidden", view.hintsVisible);
  el("btn-hints").textContent = view.hintsVisible ? "Hints off" : "Hints on";
}

function renderQuestion() {
  const question = view.question;
  const tags = question.tags.length ? ` · ${question.tags.join(", ")}` : "";
  const target =
    view.state.mode === "adaptive" && view.targetDifficulty !== null
      ? ` · served at target ${view.targetDifficulty}`
      : "";
  el("ask-meta").textContent = `${question.topic} · difficulty ${question.difficulty}${tags}${target}`;
  renderSimpleMarkdown(el("ask-text"), question.ask);

  renderSimpleMarkdown(el("look-for"), question.look_for || "");
  renderSimpleMarkdown(el("red-flags"), question.red_flags || "");
  renderSimpleMarkdown(el("follow-ups"), question.follow_ups || "");

  const extras = el("extra-sections");
  clear(extras);
  for (const section of question.extra || []) {
    const block = make("div", { className: "hint-block" });
    block.appendChild(make("h3", { text: section.heading }));
    const body = make("div");
    renderSimpleMarkdown(body, section.body);
    block.appendChild(body);
    extras.appendChild(block);
  }

  el("follow-ups").classList.toggle("hidden", !view.followUpsVisible);
  el("btn-followups").textContent = view.followUpsVisible ? "hide" : "show";

  el("note").value = view.answer.note || "";
  renderRatings();
  applyHintVisibility();
}

function renderStatus() {
  const total = view.state.items.length;
  el("position").textContent = `${view.index + 1} / ${total}`;
  el("mode-label").textContent = view.state.mode;

  const pacing = view.state.pacing || { kind: "untimed" };
  const budgetSeconds = (view.budgetMinutes || 0) * 60;
  if (pacing.kind === "per_question" && budgetSeconds > 0) {
    el("budget-label").textContent = `budget ${view.budgetMinutes}m`;
  } else if (pacing.kind === "total") {
    const left = Math.max(0, Number(pacing.total_minutes || 0) * 60 - totalElapsed());
    el("budget-label").textContent = `${formatClock(left)} left · ${total - view.index - 1} after this`;
  } else {
    el("budget-label").textContent = "";
  }

  el("btn-prev").disabled = view.index === 0;
  const lastServed = view.index >= total - 1;
  el("btn-next").disabled = lastServed && view.state.mode !== "adaptive";
  if (view.state.adaptive_exhausted && lastServed) el("btn-next").disabled = true;
}

function tick() {
  const seconds = questionElapsed();
  el("q-timer").textContent = formatClock(seconds);
  el("total-timer").textContent = `total ${formatClock(totalElapsed())}`;

  const pacing = view.state.pacing || { kind: "untimed" };
  const budgetSeconds = (view.budgetMinutes || 0) * 60;
  const over = pacing.kind === "per_question" && budgetSeconds > 0 && seconds > budgetSeconds;
  el("ask-card").classList.toggle("over-budget", over);
  el("q-timer").classList.toggle("over", over);
  if (pacing.kind === "total") renderStatus();
}

async function loadPosition(index) {
  const payload = await api.getQuestion(view.sessionId, index, view.hintsVisible);
  view.index = payload.index;
  view.question = payload.question;
  view.answer = payload.answer || {};
  view.targetDifficulty = payload.target_difficulty;
  view.budgetMinutes = payload.budget_minutes;
  view.elapsedBase = Number(view.answer.elapsed_seconds || 0);
  view.totalBase = sumRecordedSeconds(view.state, view.question.id) + view.elapsedBase;
  view.enteredAt = Date.now();
  renderQuestion();
  renderStatus();
  tick();
}

async function goTo(index) {
  await flushPending();
  view.state = await api.goto(view.sessionId, index);
  await loadPosition(view.state.position);
}

async function goNext() {
  await flushPending();
  const before = view.state.items.length;
  view.state = await api.next(view.sessionId);
  if (view.state.adaptive_exhausted && view.state.items.length === before && view.index >= before - 1) {
    el("budget-label").textContent = "no questions left in the pool";
    return;
  }
  await loadPosition(view.state.position);
}

function onNoteInput(event) {
  view.pendingNote = event.target.value;
  setSaveState("saving");
  clearTimeout(view.noteTimer);
  view.noteTimer = setTimeout(async () => {
    const note = view.pendingNote;
    view.pendingNote = null;
    try {
      const result = await api.patchAnswer(view.sessionId, view.question.id, {
        note,
        elapsed_seconds: questionElapsed(),
      });
      view.answer = result.answer;
      setSaveState("saved");
    } catch {
      setSaveState("error");
    }
  }, NOTE_DEBOUNCE_MS);
}

function toggleHints(force) {
  view.hintsVisible = force === undefined ? !view.hintsVisible : force;
  localStorage.setItem(HINTS_KEY, view.hintsVisible ? "1" : "0");
  applyHintVisibility();
  // Refetch, so the answer key is not sitting in the page while it is switched off.
  loadPosition(view.index).catch(() => setSaveState("error"));
}

function toggleFollowUps() {
  view.followUpsVisible = !view.followUpsVisible;
  el("follow-ups").classList.toggle("hidden", !view.followUpsVisible);
  el("btn-followups").textContent = view.followUpsVisible ? "hide" : "show";
}

function onKeyDown(event) {
  if (el("screen-interview").classList.contains("hidden")) return;

  if (event.key === "Escape" && document.activeElement === el("note")) {
    el("note").blur();
    event.preventDefault();
    return;
  }
  if (isTypingTarget(event)) return;

  if (event.key === "/") {
    el("note").focus();
    event.preventDefault();
    return;
  }
  if (event.key >= "1" && event.key <= "5") {
    setRating(Number(event.key));
    event.preventDefault();
  } else if (event.key === "0") {
    setSkipped(!view.answer.skipped);
    event.preventDefault();
  } else if (event.key === "n" || event.key === "ArrowRight") {
    if (!el("btn-next").disabled) goNext();
    event.preventDefault();
  } else if (event.key === "p" || event.key === "ArrowLeft") {
    if (view.index > 0) goTo(view.index - 1);
    event.preventDefault();
  } else if (event.key === "f") {
    toggleFollowUps();
    event.preventDefault();
  } else if (event.key === "h") {
    toggleHints();
    event.preventDefault();
  }
}

export async function openInterview(sessionId, state, handlers) {
  view.sessionId = sessionId;
  view.state = state;
  view.onFinish = handlers.onFinish;
  view.hintsVisible = hintsVisibleFromStorage();
  view.followUpsVisible = false;
  await loadPosition(state.position || 0);

  clearInterval(view.tickTimer);
  view.tickTimer = setInterval(tick, 1000);
  clearInterval(view.pushTimer);
  view.pushTimer = setInterval(pushElapsed, TIMER_PUSH_MS);
}

export function stopInterviewTimers() {
  clearInterval(view.tickTimer);
  clearInterval(view.pushTimer);
  view.tickTimer = null;
  view.pushTimer = null;
}

export function currentSessionId() {
  return view.sessionId;
}

export function initInterview(handlers) {
  el("btn-next").addEventListener("click", () => goNext());
  el("btn-prev").addEventListener("click", () => goTo(view.index - 1));
  el("btn-hints").addEventListener("click", () => toggleHints());
  el("btn-followups").addEventListener("click", () => toggleFollowUps());
  el("btn-finish").addEventListener("click", async () => {
    await flushPending();
    stopInterviewTimers();
    handlers.onFinish(view.sessionId);
  });
  el("note").addEventListener("input", onNoteInput);
  document.addEventListener("keydown", onKeyDown);

  // The two exit paths a debounce loses work on.
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flushPending(true);
  });
  window.addEventListener("pagehide", () => flushPending(true));
}
