// The live interview screen: one card, the interviewer guidance, the band, the note, timers,
// shortcuts. Nothing here assigns a band and nothing advances on its own.

import { api, patchAnswerKeepalive } from "./api.js";
import {
  clear,
  el,
  formatClock,
  isTypingTarget,
  make,
  bulletList,
  renderBullets,
  renderSimpleMarkdown,
  setSaveState,
} from "./dom.js";

// The band the interviewer picks describes the answer. It is not the level of the question,
// and the two are shown side by side on purpose.
const BAND_LABELS = [
  ["weak", "Weak — no working account of it"],
  ["junior", "Junior — the basic rule, one example"],
  ["mid", "Mid — trade-offs, a failure case"],
  ["senior", "Senior — the mechanism, behaviour under load"],
  ["lead", "Lead — chooses from constraints, names the cost"],
];

// The levels a question can be pitched at. Fixed vocabulary, like the bands above.
const LEVELS = ["junior", "mid", "senior", "lead"];

const SUGGESTION_LABELS = {
  deeper: "deeper",
  shallower: "shallower",
  related: "related",
  prerequisite: "first",
  level: "at level",
};

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
  onBrowse: () => {},
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
    await api.patchAnswer(view.sessionId, view.question.id, { elapsed_seconds: questionElapsed() });
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

function renderBands() {
  const row = el("band-row");
  clear(row);
  BAND_LABELS.forEach(([value, label], position) => {
    const pressed = !view.answer.skipped && view.answer.band === value;
    const button = make("button", {
      attrs: { type: "button", "aria-pressed": String(pressed) },
      children: [
        make("span", { className: "k", text: String(position + 1) }),
        make("span", { text: label }),
      ],
    });
    button.addEventListener("click", () => setBand(value));
    row.appendChild(button);
  });
  const skipPressed = Boolean(view.answer.skipped);
  const skip = make("button", {
    className: "skip",
    attrs: {
      type: "button",
      "aria-pressed": String(skipPressed),
      title: "Your decision to move on. It records nothing about the candidate.",
    },
    children: [
      make("span", { className: "k", text: "0" }),
      make("span", { text: "Skip — no evidence recorded" }),
    ],
  });
  skip.addEventListener("click", () => setSkipped(!skipPressed));
  row.appendChild(skip);
}

// Next is gated on the interviewer having recorded something. A band is a judgement about the
// answer; a skip is a decision to move on that says nothing about the candidate. Either is a
// deliberate act, and walking past a question without one loses the evidence silently.
function answerIsRecorded() {
  return Boolean(view.answer && (view.answer.band || view.answer.skipped));
}

async function setBand(value) {
  view.answer = { ...view.answer, band: value, skipped: false };
  renderBands();
  await save({ band: value, skipped: false });
}

async function setSkipped(on) {
  view.answer = { ...view.answer, skipped: on, band: on ? null : view.answer.band };
  renderBands();
  await save({ skipped: on });
}

function rememberAnswer(answer) {
  const item = view.state && view.state.items && view.state.items[view.index];
  if (item) item.answer = answer;
}

async function save(patch) {
  setSaveState("saving");
  try {
    const result = await api.patchAnswer(view.sessionId, view.question.id, {
      ...patch,
      elapsed_seconds: questionElapsed(),
    });
    view.answer = result.answer;
    rememberAnswer(result.answer);
    if (result.calibration) view.state = { ...view.state, calibration: result.calibration };
    renderStatus();
    renderSkippedDock();
    setSaveState("saved");
    // The suggestion list is derived from the band that was just assigned, so it is refetched
    // rather than guessed at in the browser.
    refreshNav();
  } catch {
    setSaveState("error");
  }
}

function applyHintVisibility() {
  el("hint-zone").classList.toggle("hidden", !view.hintsVisible);
  el("hints-hidden-notice").classList.toggle("hidden", view.hintsVisible);
  el("btn-hints").textContent = view.hintsVisible ? "Hints off" : "Hints on";
}

function block(heading, build) {
  const node = make("div", { className: "hint-block" });
  node.appendChild(make("h3", { text: heading }));
  const body = make("div");
  if (!build(body)) return null;
  node.appendChild(body);
  return node;
}

function renderHints(question) {
  const zone = el("hint-zone");
  clear(zone);
  if (!view.hintsVisible) return;

  const blocks = [];

  if (question.tests) {
    blocks.push(
      block("What this tests", (body) => {
        body.appendChild(make("p", { text: question.tests }));
        return true;
      })
    );
  }
  blocks.push(block("Listen for", (body) => renderBullets(body, question.listen_for)));
  blocks.push(
    block("Expected knowledge", (body) => renderBullets(body, question.expected_knowledge))
  );
  blocks.push(block("Strong signals", (body) => renderBullets(body, question.strong_signals)));
  blocks.push(block("Weak signals", (body) => renderBullets(body, question.weak_signals)));

  blocks.push(
    block("Answer bands", (body) => {
      const bands = question.answer_bands || {};
      const names = Object.keys(bands);
      if (names.length === 0) return false;
      for (const name of names) {
        const list = bulletList(bands[name]);
        if (!list) continue;
        body.appendChild(make("p", { className: "band-name", text: name }));
        body.appendChild(list);
      }
      return true;
    })
  );

  blocks.push(
    block("Follow-ups", (body) => {
      const followUps = question.follow_ups || [];
      if (followUps.length === 0) return false;
      const toggle = make("button", {
        className: "linky",
        text: view.followUpsVisible ? "hide" : "show",
        attrs: { type: "button" },
      });
      toggle.addEventListener("click", toggleFollowUps);
      body.appendChild(toggle);

      const list = make("ul", { className: view.followUpsVisible ? "" : "hidden" });
      followUps.forEach((followUp, position) => {
        const item = make("li");
        const used = (view.answer.follow_ups_used || []).includes(position);
        const box = make("input", { attrs: { type: "checkbox", title: "mark as used" } });
        box.checked = used;
        box.addEventListener("change", () => toggleFollowUpUsed(position, box.checked));
        item.appendChild(box);
        item.appendChild(make("span", { text: ` ${followUp.text}` }));
        // `probes` says why the interviewer is asking it. It is never read aloud.
        if (followUp.probes) {
          item.appendChild(make("span", { className: "probes", text: `probes: ${followUp.probes}` }));
        }
        list.appendChild(item);
      });
      body.appendChild(list);
      return true;
    })
  );

  if (question.notes) {
    blocks.push(
      block("Notes", (body) => {
        renderSimpleMarkdown(body, question.notes);
        return true;
      })
    );
  }
  for (const section of question.extra || []) {
    blocks.push(
      block(section.heading, (body) => {
        renderSimpleMarkdown(body, section.body);
        return true;
      })
    );
  }

  for (const node of blocks) if (node) zone.appendChild(node);
}

async function toggleFollowUpUsed(position, on) {
  const current = new Set(view.answer.follow_ups_used || []);
  if (on) current.add(position);
  else current.delete(position);
  view.answer = { ...view.answer, follow_ups_used: [...current].sort((a, b) => a - b) };
  await save({ follow_ups_used: view.answer.follow_ups_used });
  renderHints(view.question);
}

function renderQuestion() {
  const question = view.question;
  const tags = question.tags.length ? ` · ${question.tags.join(", ")}` : "";
  const target =
    view.targetLevel ? ` · served at target ${view.targetLevel}` : "";
  el("ask-meta").textContent =
    `${question.category} / ${question.topic} · level ${question.level}${tags}${target}`;
  renderSimpleMarkdown(el("ask-text"), question.question);

  renderHints(question);
  el("note").value = view.answer.note || "";
  renderBands();
  applyHintVisibility();
}

function renderStatus() {
  const total = view.state.items.length;
  el("position").textContent = `${view.index + 1} / ${total}`;
  el("mode-label").textContent = view.state.mode;

  const calibration = view.state.calibration || {};
  el("calibration-label").textContent = calibration.target_level
    ? `calibration ${calibration.target_level}${calibration.override ? " (manual)" : ""}`
    : "";
  el("calibration-label").title = (calibration.latest && calibration.latest.advice) || "";

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
  const gated = !answerIsRecorded();
  const atTheEnd =
    (lastServed && view.state.mode !== "adaptive") ||
    (view.state.adaptive_exhausted && lastServed);

  // A disabled button that says nothing reads as a broken one. Whenever Next will not move,
  // say which of the two reasons it is, and what to do instead.
  el("btn-next").disabled = gated || atTheEnd;
  const gate = el("next-gate");
  if (gated) {
    gate.textContent = "Assign a band, or skip the question, before moving on.";
  } else if (atTheEnd) {
    gate.textContent =
      `That was the last question in the pool — ${total} of ${total}. ` +
      `End the interview, or use "Pick any question" to carry on with anything in the bank.`;
  }
  gate.classList.toggle("hidden", !(gated || atTheEnd));
}

// --- calibration and suggestions ----------------------------------------------------------------
//
// Everything in this zone is advisory. Nothing here moves the interview until the interviewer
// clicks, and every card in the bank stays reachable through "Pick any question".

async function refreshNav() {
  let payload;
  try {
    payload = await api.suggestions(view.sessionId);
  } catch {
    return; // A failed suggestion fetch must never interrupt an interview in progress.
  }
  view.state = { ...view.state, calibration: payload.calibration };
  renderCalibration(payload.calibration);
  renderSuggestions(payload.suggestions);
}

function renderCalibration(calibration) {
  el("calibration-now").textContent = calibration.target_level;
  el("calibration-why").textContent = calibration.override
    ? "set by hand — the bands are being ignored"
    : calibration.note || "No band assigned yet.";

  // One word for the state the run is in, so the interviewer can see the bar stop moving.
  const state = el("calibration-state");
  const label = calibration.override
    ? "manual"
    : calibration.settled
      ? `ceiling ${calibration.ceiling}`
      : calibration.probing
        ? "probing"
        : "";
  state.textContent = label;
  state.className = label ? `calibration-state state-${label.split(" ")[0]}` : "hidden";

  el("in-calibration").value = calibration.override || "";
}

function renderSuggestions(suggestions) {
  const list = el("suggestions");
  clear(list);
  if (!suggestions || suggestions.length === 0) {
    list.appendChild(
      make("li", { className: "hint", text: "Nothing left to suggest from this pool." })
    );
    return;
  }
  for (const suggestion of suggestions) {
    const open = make("button", {
      className: "suggestion",
      attrs: { type: "button", title: suggestion.reason },
      children: [
        make("span", {
          className: `suggestion-kind kind-${suggestion.kind}`,
          text: SUGGESTION_LABELS[suggestion.kind] || suggestion.kind,
        }),
        make("span", { className: "suggestion-title", text: suggestion.title }),
        make("span", {
          className: "suggestion-meta",
          text: `${suggestion.level} · ${suggestion.topic}`,
        }),
      ],
    });
    open.addEventListener("click", () => jumpTo(suggestion.id, `suggested: ${suggestion.reason}`));
    list.appendChild(make("li", { children: [open] }));
  }
}

export async function jumpTo(questionId, reason) {
  await flushPending();
  view.state = await api.jump(view.sessionId, questionId, reason);
  await loadPosition(view.state.position);
}

async function setCalibration(level) {
  try {
    view.state = await api.setCalibration(view.sessionId, level || null);
    await refreshNav();
  } catch {
    setSaveState("error");
  }
}

// --- the skipped dock ------------------------------------------------------------------------
//
// A skipped question is parked, not discarded. Nothing re-serves it, and it is one click away
// for the whole session.

function skippedItems() {
  if (!view.state || !view.state.items) return [];
  return view.state.items
    .map((item, index) => ({ ...item, index }))
    .filter((item) => item.answer && item.answer.skipped);
}

function renderSkippedDock() {
  const skipped = skippedItems();
  el("skipped-dock").classList.toggle("hidden", skipped.length === 0);
  el("skipped-count").textContent = String(skipped.length);

  const list = el("skipped-list");
  clear(list);
  for (const item of skipped) {
    const open = make("button", {
      className: "linky",
      text: item.question.title || item.qid,
      attrs: { type: "button" },
    });
    open.addEventListener("click", () => {
      toggleSkippedPopup(false);
      goTo(item.index);
    });
    const entry = make("li", { children: [open] });
    entry.appendChild(
      make("span", {
        className: "hint",
        text: ` ${item.question.category} / ${item.question.topic} · ${item.question.level}`,
      })
    );
    list.appendChild(entry);
  }
  if (skipped.length === 0) toggleSkippedPopup(false);
}

function toggleSkippedPopup(force) {
  const popup = el("skipped-popup");
  const show = force === undefined ? popup.classList.contains("hidden") : force;
  popup.classList.toggle("hidden", !show);
  el("btn-skipped").setAttribute("aria-expanded", String(show));
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
  view.targetLevel = payload.target_level;
  view.budgetMinutes = payload.budget_minutes;
  view.elapsedBase = Number(view.answer.elapsed_seconds || 0);
  view.totalBase = sumRecordedSeconds(view.state, view.question.id) + view.elapsedBase;
  view.enteredAt = Date.now();
  renderQuestion();
  renderStatus();
  renderSkippedDock();
  refreshNav();
  tick();
}

async function goTo(index) {
  await flushPending();
  view.state = await api.goto(view.sessionId, index);
  await loadPosition(view.state.position);
}

async function goNext() {
  if (!answerIsRecorded()) return;
  await flushPending();
  const before = view.state.items.length;
  view.state = await api.next(view.sessionId);
  if (view.state.adaptive_exhausted && view.state.items.length === before && view.index >= before - 1) {
    renderStatus();
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
  renderHints(view.question);
}

function onKeyDown(event) {
  if (el("screen-interview").classList.contains("hidden")) return;

  if (event.key === "Escape" && !el("skipped-popup").classList.contains("hidden")) {
    toggleSkippedPopup(false);
    event.preventDefault();
    return;
  }
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
    setBand(BAND_LABELS[Number(event.key) - 1][0]);
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
  if (handlers.onBrowse) view.onBrowse = handlers.onBrowse;
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
  el("btn-skipped").addEventListener("click", () => toggleSkippedPopup());

  const override = el("in-calibration");
  clear(override);
  override.appendChild(make("option", { text: "follow the bands", attrs: { value: "" } }));
  for (const level of LEVELS) {
    override.appendChild(make("option", { text: level, attrs: { value: level } }));
  }
  override.addEventListener("change", (event) => setCalibration(event.target.value));

  el("btn-browse-jump").addEventListener("click", () => handlers.onBrowse(view.sessionId));
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
