// The three-stage setup wizard, plus the live preview of the resulting question list.

import { api } from "./api.js";
import { clear, el, make } from "./dom.js";

const MODES = [
  ["sequential", "Sequential", "The order field, then the id. The same every time."],
  ["random", "Random", "Shuffled with a seed. The seed is recorded, so the run can be repeated."],
  ["level_asc", "Level ascending", "Junior first, lead last. Ties broken by the seed."],
  [
    "adaptive",
    "Adaptive",
    "The next card follows the band you just assigned. A band above the question's level raises " +
      "the bar, a band below drops it, and a topic not yet covered wins the tie. Nothing advances " +
      "on its own.",
  ],
  ["manual", "Manual", "The exact order ticked in stage 1."],
];

const PACING = [
  ["untimed", "Untimed", "A clock runs. Nothing nags."],
  ["per_question", "Per-question budget", "The card border shifts when a question runs over. It never advances by itself."],
  ["total", "Total session budget", "Shows the time left and how many questions remain."],
];

const state = {
  bank: null,
  categories: new Set(),
  topics: new Set(),
  levels: new Set(),
  includeTags: new Set(),
  excludeTags: new Set(),
  manual: false,
  manualIds: [],
  mode: "sequential",
  pacing: "untimed",
  previewQuestions: [],
};

let previewTimer = null;
let onStarted = () => {};

function chip(label, isOn, onToggle, className) {
  const node = make("button", {
    text: label,
    className: `chip${className ? " " + className : ""}`,
    attrs: { type: "button", "aria-pressed": String(isOn) },
  });
  node.addEventListener("click", () => {
    onToggle(node.getAttribute("aria-pressed") !== "true");
  });
  return node;
}

function renderChips(container, values, selected, onToggle, className) {
  clear(container);
  if (values.length === 0) {
    container.appendChild(make("span", { className: "hint", text: "none in the bank" }));
    return;
  }
  for (const value of values) {
    container.appendChild(chip(value, selected.has(value), (on) => onToggle(value, on), className));
  }
}

function toggleSet(set, value, on, redraw) {
  if (on) set.add(value);
  else set.delete(value);
  redraw();
  schedulePreview();
}

function renderModes() {
  const container = el("mode-list");
  clear(container);
  for (const [value, label] of MODES) {
    const input = make("input", { attrs: { type: "radio", name: "mode", value } });
    input.checked = state.mode === value;
    input.addEventListener("change", () => {
      state.mode = value;
      renderModeExtras();
      schedulePreview();
    });
    container.appendChild(make("label", { children: [input, make("span", { text: label })] }));
  }
  renderModeExtras();
}

function renderModeExtras() {
  const found = MODES.find(([value]) => value === state.mode);
  el("mode-explain").textContent = found ? found[2] : "";
  el("start-level-row").classList.toggle("hidden", state.mode !== "adaptive");
}

function renderPacing() {
  const container = el("pacing-list");
  clear(container);
  for (const [value, label, explain] of PACING) {
    const input = make("input", { attrs: { type: "radio", name: "pacing", value } });
    input.checked = state.pacing === value;
    input.addEventListener("change", () => {
      state.pacing = value;
      el("per-question-row").classList.toggle("hidden", value !== "per_question");
      el("total-row").classList.toggle("hidden", value !== "total");
    });
    container.appendChild(
      make("label", {
        children: [input, make("span", { text: label }), make("span", { className: "hint", text: explain })],
      })
    );
  }
}

function currentFilters() {
  const limit = Number(el("in-limit").value);
  const filters = {
    categories: [...state.categories],
    topics: [...state.topics],
    levels: [...state.levels],
    include_tags: [...state.includeTags],
    exclude_tags: [...state.excludeTags],
    limit: Number.isFinite(limit) && limit > 0 ? limit : null,
  };
  if (state.manual && state.manualIds.length > 0) filters.manual_ids = state.manualIds;
  return filters;
}

function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(refreshPreview, 150);
}

async function refreshPreview() {
  const excludeAsked = el("in-exclude-asked").checked ? el("in-candidate").value : "";
  // The manual list itself is built from the filtered pool, so the preview request never carries
  // manual ids. Otherwise the list could only ever shrink.
  const filters = currentFilters();
  delete filters.manual_ids;
  let result;
  try {
    result = await api.preview(filters, excludeAsked);
  } catch (error) {
    el("preview-summary").textContent = `preview failed: ${error.message}`;
    return;
  }
  state.previewQuestions = result.questions;
  state.manualIds = state.manualIds.filter((id) => result.questions.some((q) => q.id === id));

  const shown = state.manual ? state.manualIds.length : result.count;
  const minutes = state.manual
    ? state.manualIds
        .map((id) => result.questions.find((q) => q.id === id))
        .reduce((total, q) => total + (q && q.time_estimate_min ? q.time_estimate_min : 5), 0)
    : result.estimated_minutes;
  el("preview-summary").textContent =
    `${shown} question${shown === 1 ? "" : "s"}, about ${minutes} minutes` +
    (state.manual ? ` (picked from ${result.count} matching)` : "");

  renderPreviewList(result.questions);
}

function renderPreviewList(questions) {
  const list = el("preview-list");
  clear(list);
  list.className = state.manual ? "preview preview-manual" : "preview";

  const ordered = state.manual
    ? [
        ...state.manualIds.map((id) => questions.find((q) => q.id === id)).filter(Boolean),
        ...questions.filter((q) => !state.manualIds.includes(q.id)),
      ]
    : questions;

  ordered.forEach((question) => {
    const meta = make("span", {
      className: "d",
      text: ` ${question.level} · ${question.topic}${
        question.tags.length ? " · " + question.tags.join(", ") : ""
      }`,
    });
    const item = make("li");

    if (state.manual) {
      const picked = state.manualIds.includes(question.id);
      const box = make("input", { attrs: { type: "checkbox" } });
      box.checked = picked;
      box.addEventListener("change", () => {
        if (box.checked) state.manualIds.push(question.id);
        else state.manualIds = state.manualIds.filter((id) => id !== question.id);
        refreshPreview();
      });
      item.appendChild(box);
      if (picked) {
        const position = state.manualIds.indexOf(question.id);
        const up = make("button", { text: "↑", attrs: { type: "button", title: "move up" } });
        up.disabled = position === 0;
        up.addEventListener("click", () => moveManual(position, -1));
        const down = make("button", { text: "↓", attrs: { type: "button", title: "move down" } });
        down.disabled = position === state.manualIds.length - 1;
        down.addEventListener("click", () => moveManual(position, 1));
        item.appendChild(up);
        item.appendChild(down);
      }
    }

    item.appendChild(make("span", { text: question.title }));
    item.appendChild(meta);
    list.appendChild(item);
  });
}

function moveManual(position, delta) {
  const target = position + delta;
  if (target < 0 || target >= state.manualIds.length) return;
  const copy = [...state.manualIds];
  [copy[position], copy[target]] = [copy[target], copy[position]];
  state.manualIds = copy;
  refreshPreview();
}

async function start() {
  el("setup-error").textContent = "";
  const seedRaw = el("in-seed").value.trim();
  const setup = {
    candidate: el("in-candidate").value.trim(),
    role: el("in-role").value.trim(),
    interviewer: el("in-interviewer").value.trim(),
    context: el("in-context").value.trim(),
    mode: state.mode,
    seed: seedRaw === "" ? null : Number(seedRaw),
    start_level: el("in-start-level").value,
    filters: currentFilters(),
    exclude_asked_to: el("in-exclude-asked").checked ? el("in-candidate").value.trim() : "",
    pacing: {
      kind: state.pacing,
      default_minutes: Number(el("in-default-minutes").value) || 5,
      total_minutes: Number(el("in-total-minutes").value) || 45,
    },
  };

  if (state.manual && state.manualIds.length === 0) {
    el("setup-error").textContent = "Manual pick is on but no question is ticked.";
    return;
  }

  try {
    const session = await api.createSession(setup);
    onStarted(session.id);
  } catch (error) {
    el("setup-error").textContent = error.message;
  }
}

export function initSetup(bank, handlers) {
  state.bank = bank;
  onStarted = handlers.onStarted;

  state.categories = new Set();
  state.topics = new Set();
  state.levels = new Set();
  state.includeTags = new Set();
  state.excludeTags = new Set();
  state.manualIds = [];

  const startLevel = el("in-start-level");
  clear(startLevel);
  for (const level of bank.levels) {
    startLevel.appendChild(make("option", { text: level, attrs: { value: level } }));
  }
  startLevel.value = bank.levels.includes("mid") ? "mid" : bank.levels[0];

  const draw = (container, values, selected, className) => {
    const redraw = () =>
      renderChips(
        el(container),
        values,
        selected,
        (value, on) => toggleSet(selected, value, on, redraw),
        className
      );
    return redraw;
  };

  const drawCategories = draw("category-list", bank.categories, state.categories);
  const drawTopics = draw("topic-list", bank.topics, state.topics);
  const drawLevels = draw("level-list", bank.levels, state.levels);
  const drawInclude = draw("include-tag-list", bank.tags, state.includeTags);
  const drawExclude = draw("exclude-tag-list", bank.tags, state.excludeTags, "exclude");

  drawCategories();
  drawTopics();
  drawLevels();
  drawInclude();
  drawExclude();
  renderModes();
  renderPacing();

  el("in-limit").addEventListener("input", schedulePreview);
  el("in-candidate").addEventListener("input", schedulePreview);
  el("in-exclude-asked").addEventListener("change", schedulePreview);
  el("in-manual").addEventListener("change", (event) => {
    state.manual = event.target.checked;
    if (state.manual) {
      state.mode = "manual";
      renderModes();
    }
    refreshPreview();
  });

  el("btn-start").addEventListener("click", start);
  el("btn-cancel-setup").addEventListener("click", handlers.onCancel);

  refreshPreview();
}
