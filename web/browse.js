// Browse the whole bank, and preview one card.
//
// The same screen serves two jobs. Opened from the home screen it is a reading view. Opened from
// the interview it is a picker: every row gets an "Ask this" button, so the interviewer is never
// confined to the questions the tool planned.
//
// The preview keeps the two audiences apart. `## Ask` is the only thing read to a candidate, so
// it sits in its own card at the top; everything else is fenced into an interviewer block that
// says so.

import { api } from "./api.js";
import { bulletList, clear, el, make, renderBullets, renderSimpleMarkdown } from "./dom.js";

const LINK_LABELS = {
  deeper: "Deeper",
  shallower: "Shallower",
  related: "Related",
  prerequisite: "Prerequisite",
};

const state = {
  bank: null,
  mode: "read", // "read" | "pick"
  categories: new Set(),
  levels: new Set(),
  topics: new Set(),
  tags: new Set(),
  search: "",
  selected: null,
  onPick: null,
  onClose: () => {},
};

let searchTimer = null;

function chip(label, isOn, onToggle) {
  const node = make("button", {
    text: label,
    className: "chip",
    attrs: { type: "button", "aria-pressed": String(isOn) },
  });
  node.addEventListener("click", () => onToggle(node.getAttribute("aria-pressed") !== "true"));
  return node;
}

function renderChips(container, values, selected, redraw) {
  clear(container);
  if (values.length === 0) {
    container.appendChild(make("span", { className: "hint", text: "none in the bank" }));
    return;
  }
  for (const value of values) {
    container.appendChild(
      chip(value, selected.has(value), (on) => {
        if (on) selected.add(value);
        else selected.delete(value);
        redraw();
        refresh();
      })
    );
  }
}

function filters() {
  return {
    categories: [...state.categories],
    levels: [...state.levels],
    topics: [...state.topics],
    include_tags: [...state.tags],
    search: state.search,
  };
}

async function refresh() {
  let result;
  try {
    result = await api.preview(filters(), "");
  } catch (error) {
    el("browse-count").textContent = `could not read the bank: ${error.message}`;
    return;
  }

  el("browse-count").textContent =
    `${result.count} of ${state.bank.count} card${result.count === 1 ? "" : "s"}` +
    (result.count ? ` · about ${result.estimated_minutes} minutes` : "");

  const list = el("browse-list");
  clear(list);
  if (result.questions.length === 0) {
    list.appendChild(make("li", { className: "hint", text: "Nothing matches these filters." }));
    return;
  }

  for (const question of result.questions) {
    list.appendChild(row(question));
  }

  // Keep a selection that survived the filter; otherwise open the first match.
  const stillThere = result.questions.some((q) => q.id === state.selected);
  select(stillThere ? state.selected : result.questions[0].id);
}

function row(question) {
  const open = make("button", {
    className: "browse-open",
    attrs: { type: "button" },
    children: [
      make("span", { className: "browse-row-title", text: question.title }),
      make("span", {
        className: "browse-row-meta",
        text: `${question.category} / ${question.topic} · ${question.level}` +
          (question.tags.length ? ` · ${question.tags.join(", ")}` : ""),
      }),
    ],
  });
  open.addEventListener("click", () => select(question.id));

  const item = make("li", { className: "browse-row", children: [open] });
  item.dataset.id = question.id;
  if (state.mode === "pick" && state.onPick) {
    const ask = make("button", { text: "Ask this", attrs: { type: "button" }, className: "primary" });
    ask.addEventListener("click", () => state.onPick(question.id));
    item.appendChild(ask);
  }
  return item;
}

async function select(questionId) {
  state.selected = questionId;
  for (const item of document.querySelectorAll("#browse-list .browse-row")) {
    item.classList.toggle("selected", item.dataset.id === questionId);
  }
  const panel = el("browse-preview");
  try {
    renderPreview(panel, await api.bankQuestion(questionId, true));
  } catch (error) {
    clear(panel);
    panel.appendChild(make("p", { className: "error", text: error.message }));
  }
}

function listBlock(heading, items) {
  if (!items || items.length === 0) return null;
  const block = make("div", { className: "hint-block" });
  block.appendChild(make("h3", { text: heading }));
  const body = make("div");
  renderBullets(body, items);
  block.appendChild(body);
  return block;
}

export function renderPreview(panel, card) {
  clear(panel);

  panel.appendChild(
    make("p", {
      className: "hint",
      text: `${card.category} / ${card.topic} · level ${card.level}` +
        (card.time_estimate_min ? ` · about ${card.time_estimate_min} min` : "") +
        (card.tags.length ? ` · ${card.tags.join(", ")}` : ""),
    })
  );
  panel.appendChild(make("h2", { text: card.title }));

  // Read aloud. Everything below the divider is not.
  const ask = make("div", { className: "preview-ask" });
  ask.appendChild(make("p", { className: "preview-ask-label", text: "Read this aloud" }));
  const askText = make("div");
  renderSimpleMarkdown(askText, card.question);
  ask.appendChild(askText);
  panel.appendChild(ask);

  if (card.tests === undefined) {
    panel.appendChild(
      make("p", { className: "hint", text: "Interviewer notes are switched off." })
    );
  } else {
    const guidance = make("div", { className: "preview-guidance" });
    guidance.appendChild(
      make("p", {
        className: "preview-guidance-label",
        text: "Interviewer only — never read any of this out",
      })
    );

    if (card.ideal_answer) {
      const block = make("div", { className: "hint-block" });
      block.appendChild(make("h3", { text: "Ideal minimal answer" }));
      block.appendChild(make("p", { className: "ideal-answer", text: card.ideal_answer }));
      guidance.appendChild(block);
    }
    if (card.tests) {
      const block = make("div", { className: "hint-block" });
      block.appendChild(make("h3", { text: "What this tests" }));
      block.appendChild(make("p", { text: card.tests }));
      guidance.appendChild(block);
    }
    for (const [heading, items] of [
      ["Listen for", card.listen_for],
      ["Expected knowledge", card.expected_knowledge],
      ["Strong signals", card.strong_signals],
      ["Weak signals", card.weak_signals],
    ]) {
      const block = listBlock(heading, items);
      if (block) guidance.appendChild(block);
    }

    const bands = card.answer_bands || {};
    if (Object.keys(bands).length > 0) {
      const block = make("div", { className: "hint-block" });
      block.appendChild(make("h3", { text: "Answer bands" }));
      const body = make("div");
      for (const [name, bullets] of Object.entries(bands)) {
        const list = bulletList(bullets);
        if (!list) continue;
        body.appendChild(make("p", { className: "band-name", text: name }));
        body.appendChild(list);
      }
      block.appendChild(body);
      guidance.appendChild(block);
    }

    if ((card.follow_ups || []).length > 0) {
      const block = make("div", { className: "hint-block" });
      block.appendChild(make("h3", { text: "Follow-ups" }));
      const list = make("ul");
      for (const followUp of card.follow_ups) {
        const item = make("li", { text: followUp.text });
        if (followUp.probes) {
          item.appendChild(
            make("span", { className: "probes", text: `probes: ${followUp.probes}` })
          );
        }
        list.appendChild(item);
      }
      block.appendChild(list);
      guidance.appendChild(block);
    }

    if (card.notes) {
      const block = make("div", { className: "hint-block" });
      block.appendChild(make("h3", { text: "Notes" }));
      const body = make("div");
      renderSimpleMarkdown(body, card.notes);
      block.appendChild(body);
      guidance.appendChild(block);
    }
    const sources = listBlock("Sources", card.sources);
    if (sources) guidance.appendChild(sources);
    for (const extra of card.extra || []) {
      const block = make("div", { className: "hint-block" });
      block.appendChild(make("h3", { text: extra.heading }));
      const body = make("div");
      renderSimpleMarkdown(body, extra.body);
      block.appendChild(body);
      guidance.appendChild(block);
    }
    panel.appendChild(guidance);
  }

  const links = card.resolved_links || {};
  const anyLinks = Object.values(links).some((ids) => ids.length > 0);
  if (anyLinks) {
    const block = make("div", { className: "preview-links" });
    block.appendChild(make("h3", { text: "Where this connects" }));
    for (const [kind, label] of Object.entries(LINK_LABELS)) {
      const targets = links[kind] || [];
      if (targets.length === 0) continue;
      const line = make("p", { children: [make("span", { className: "link-kind", text: label })] });
      for (const target of targets) {
        const jump = make("button", {
          className: "linky",
          text: `${target.title} (${target.level})`,
          attrs: { type: "button" },
        });
        jump.addEventListener("click", () => select(target.id));
        line.appendChild(jump);
      }
      block.appendChild(line);
    }
    panel.appendChild(block);
  }

  panel.appendChild(make("p", { className: "hint mono", text: card.id }));
}

function clearFilters() {
  state.categories.clear();
  state.levels.clear();
  state.topics.clear();
  state.tags.clear();
  state.search = "";
  el("in-search").value = "";
  drawAll();
  refresh();
}

function drawAll() {
  renderChips(el("browse-categories"), state.bank.categories, state.categories, drawAll);
  renderChips(el("browse-levels"), state.bank.levels, state.levels, drawAll);
  renderChips(el("browse-topics"), state.bank.topics, state.topics, drawAll);
  renderChips(el("browse-tags"), state.bank.tags, state.tags, drawAll);
}

export async function openBrowse(bank, options = {}) {
  state.bank = bank;
  state.mode = options.onPick ? "pick" : "read";
  state.onPick = options.onPick || null;
  state.onClose = options.onClose || (() => {});
  state.selected = null;

  el("browse-title").textContent =
    state.mode === "pick" ? "Pick any question" : "Browse the bank";
  el("btn-browse-close").textContent = state.mode === "pick" ? "Back to the interview" : "Back";

  drawAll();
  await refresh();
}

export function initBrowse() {
  el("in-search").addEventListener("input", (event) => {
    state.search = event.target.value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(refresh, 150);
  });
  el("btn-browse-clear").addEventListener("click", clearFilters);
  el("btn-browse-close").addEventListener("click", () => state.onClose());
}
