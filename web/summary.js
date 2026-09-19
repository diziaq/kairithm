// The screen between the last question and the file on disk. Nothing is written until Save.
//
// It opens with the whole interview at a glance — one headline figure, where the candidate sat
// against the level of each question, and where the answers landed — then lets the reader open
// any of it down to the individual question and the note taken at the time.
//
// Everything here is arithmetic over bands the interviewer assigned. The assessment boxes are
// the interviewer's own words and nothing fills them in.

import { api } from "./api.js";
import { renderBandMatrix, renderGapChart, renderRangeTrack, clearTooltip } from "./charts.js";
import { clear, el, make, setSaveState } from "./dom.js";

const BANDS = ["weak", "junior", "mid", "senior", "lead"];
const LEVELS = ["junior", "mid", "senior", "lead"];

const state = { sessionId: null, session: null, summary: null, onHome: () => {}, onBack: () => {} };

function table(headings, rows, className = "slist") {
  const node = make("table", { className });
  node.appendChild(make("tr", { children: headings.map((text) => make("th", { text })) }));
  for (const row of rows) {
    node.appendChild(
      make("tr", { children: row.map((cell) => make("td", { text: String(cell) })) })
    );
  }
  return node;
}

// Every chart ships with one of these. A value is never reachable only by hovering.
function tableTwin(label, headings, rows) {
  const box = make("details", { className: "twin" });
  box.appendChild(make("summary", { text: label }));
  box.appendChild(table(headings, rows));
  return box;
}

function gapLabel(meanGap) {
  if (meanGap > 0) return `+${meanGap.toFixed(1)} above`;
  if (meanGap < 0) return `${meanGap.toFixed(1)} below`;
  return "at the level asked";
}

function signed(value) {
  return value > 0 ? `+${value}` : String(value);
}

// --- the headline -----------------------------------------------------------------------------

function renderRange(summary, session) {
  const panel = el("summary-range");
  clear(panel);
  panel.classList.add("viz-panel");

  const score = summary.score;
  if (score.value === null) {
    panel.appendChild(
      make("p", { text: "No question carries a band yet, so there is nothing to summarise." })
    );
    return;
  }

  // The hero figure: one per view, the same sans as everything else, proportional figures.
  panel.appendChild(
    make("p", {
      className: "hero",
      children: [
        make("span", { className: "hero-value", text: String(score.value) }),
        make("span", { className: "hero-scale", text: "/ 100" }),
        make("span", { className: "hero-label", text: `reads as ${score.label}` }),
      ],
    })
  );
  panel.appendChild(
    make("p", {
      className: "hint",
      text:
        `0 is an intern, 100 an engineering tech lead. ${score.rated} banded answer(s), ` +
        `confidence ${score.confidence}.`,
    })
  );

  const track = make("div");
  panel.appendChild(track);
  renderRangeTrack(track, score);

  const items = new Map(session.items.map((item) => [item.qid, item]));
  panel.appendChild(
    tableTwin(
      "How this number is produced",
      ["Question", "Level asked", "Band assigned", "vs level"],
      summary.observations.map((row) => [
        (items.get(row.qid) && items.get(row.qid).question.title) || row.qid,
        row.level,
        row.band,
        signed(row.gap),
      ])
    )
  );
  panel.appendChild(make("p", { className: "hint mono", text: score.formula }));
}

// --- the picture --------------------------------------------------------------------------------

function renderProfile(summary, session) {
  const panel = el("summary-profile");
  clear(panel);
  panel.classList.add("viz-panel");
  if (summary.observations.length === 0) return;

  const spots = summary.hot_spots;
  const ordered = [...spots.strong, ...spots.at_bar, ...spots.weak];

  if (ordered.length > 0) {
    panel.appendChild(make("h2", { text: "Hot spots" }));
    panel.appendChild(
      make("p", {
        className: "hint",
        text:
          "How far the bands you assigned sat above or below the level those questions were " +
          "set to. Nothing here is a score — it is where the candidate cleared the bar and " +
          "where they did not.",
      })
    );
    const chart = make("div");
    panel.appendChild(chart);
    renderGapChart(chart, ordered);
    panel.appendChild(
      tableTwin(
        "The same figures as a table",
        ["Topic", "Asked", "Deepest band", "Held at", "vs level"],
        ordered.map((row) => [
          row.name,
          row.asked,
          row.deepest_band,
          row.hardest_level_held || "—",
          gapLabel(row.mean_gap),
        ])
      )
    );
  }

  if (summary.band_matrix.length > 0) {
    panel.appendChild(make("h2", { text: "Where the answers landed" }));
    const chart = make("div");
    panel.appendChild(chart);
    renderBandMatrix(chart, summary.band_matrix, LEVELS, BANDS);
    panel.appendChild(
      tableTwin(
        "The same figures as a table",
        ["Question level", "Band assigned", "Answers"],
        summary.band_matrix.map((cell) => [cell.level, cell.band, cell.count])
      )
    );
  }

  panel.appendChild(make("h2", { text: "Open it up" }));
  panel.appendChild(renderDrilldown(summary, session));
}

// --- the drill-down -------------------------------------------------------------------------------

function renderDrilldown(summary, session) {
  const container = make("div", { className: "drill" });
  const items = new Map(session.items.map((item) => [item.qid, item]));

  const topicsByCategory = new Map();
  for (const observation of summary.observations) {
    if (!topicsByCategory.has(observation.category)) topicsByCategory.set(observation.category, new Set());
    topicsByCategory.get(observation.category).add(observation.topic);
  }
  const topicRows = new Map(summary.by_topic.map((row) => [row.name, row]));

  for (const category of summary.by_category) {
    const box = make("details", { className: "drill-category" });
    box.appendChild(
      make("summary", {
        children: [
          make("span", { className: "drill-name", text: category.name }),
          make("span", {
            className: "drill-meta",
            text:
              `${category.asked} asked · range ${category.score} · deepest ${category.deepest_band} · ` +
              gapLabel(category.mean_gap),
          }),
        ],
      })
    );

    for (const topic of [...(topicsByCategory.get(category.name) || [])].sort()) {
      const row = topicRows.get(topic);
      if (!row) continue;
      const inner = make("details", { className: "drill-topic" });
      inner.appendChild(
        make("summary", {
          children: [
            make("span", { className: "drill-name", text: topic }),
            make("span", {
              className: "drill-meta",
              text: `${row.asked} asked · deepest ${row.deepest_band} · ${gapLabel(row.mean_gap)}`,
            }),
          ],
        })
      );

      for (const observation of summary.observations.filter((o) => o.topic === topic)) {
        const item = items.get(observation.qid);
        const entry = make("div", { className: "drill-question" });
        entry.appendChild(
          make("p", {
            className: "drill-question-title",
            text: (item && item.question.title) || observation.qid,
          })
        );
        entry.appendChild(
          make("p", {
            className: "hint",
            text:
              `${observation.band} band on a ${observation.level} question · ` +
              `${signed(observation.gap)} vs the level asked`,
          })
        );
        const note = item && item.answer && item.answer.note;
        if (note) entry.appendChild(make("blockquote", { text: note }));
        inner.appendChild(entry);
      }
      box.appendChild(inner);
    }
    container.appendChild(box);
  }
  return container;
}

// --- per-question editing --------------------------------------------------------------------------

function renderQuestions(session) {
  const container = el("summary-questions");
  clear(container);
  session.items.forEach((item, index) => {
    const row = make("div", { className: "qrow" });
    const answer = item.answer || {};
    const verdict = answer.skipped
      ? "skipped"
      : answer.band
        ? `${answer.band} band on a ${item.question.level} question`
        : "not banded";
    row.appendChild(
      make("h4", { text: `${index + 1}. ${item.question.title || item.qid} — ${verdict}` })
    );
    row.appendChild(
      make("p", {
        className: "hint",
        text: `${item.qid} · ${item.question.category} / ${item.question.topic}${
          item.reason ? " · " + item.reason : ""
        }`,
      })
    );

    const bandRow = make("div", { className: "row" });
    for (const value of [...BANDS, null]) {
      const isSkip = value === null;
      const pressed = isSkip ? Boolean(answer.skipped) : !answer.skipped && answer.band === value;
      const button = make("button", {
        text: isSkip ? "skip" : value,
        className: isSkip ? "skip" : "",
        attrs: { type: "button", "aria-pressed": String(pressed) },
      });
      button.addEventListener("click", async () => {
        const patch = isSkip ? { skipped: !pressed } : { band: value, skipped: false };
        await patchAndRedraw(item.qid, patch);
      });
      bandRow.appendChild(button);
    }
    row.appendChild(bandRow);

    const note = make("textarea", { attrs: { rows: "3", placeholder: "Evidence note" } });
    note.value = answer.note || "";
    let timer = null;
    note.addEventListener("input", () => {
      setSaveState("saving");
      clearTimeout(timer);
      timer = setTimeout(async () => {
        try {
          await api.patchAnswer(state.sessionId, item.qid, { note: note.value });
          setSaveState("saved");
        } catch {
          setSaveState("error");
        }
      }, 500);
    });
    row.appendChild(note);
    container.appendChild(row);
  });
}

async function redraw() {
  clearTooltip();
  state.session = await api.getSession(state.sessionId);
  state.summary = await api.summary(state.sessionId);
  renderRange(state.summary, state.session);
  renderProfile(state.summary, state.session);
  renderQuestions(state.session);
}

async function patchAndRedraw(qid, patch) {
  setSaveState("saving");
  try {
    await api.patchAnswer(state.sessionId, qid, patch);
    await redraw();
    setSaveState("saved");
  } catch {
    setSaveState("error");
  }
}

function download(markdown, name) {
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = make("a", { attrs: { href: url, download: name } });
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function saveAndClose() {
  el("finish-error").textContent = "";
  try {
    const result = await api.finish(state.sessionId, {
      summary: el("in-summary").value,
      strengths: el("in-strengths").value,
      concerns: el("in-concerns").value,
      follow_up_areas: el("in-followup-areas").value,
      anonymise: el("in-anonymise").checked,
    });
    el("finish-path").textContent =
      `Written to ${result.summary_path} and ${result.path}. The executive summary is below.`;
    // The short one is what gets read first, so it is the one on screen.
    el("finish-preview").textContent = result.summary_markdown;
    el("finish-result").classList.remove("hidden");
    el("btn-save-close").disabled = true;

    el("btn-download-summary").onclick = () =>
      download(result.summary_markdown, result.summary_download_name);
    el("btn-download").onclick = () => download(result.markdown, result.download_name);
  } catch (error) {
    el("finish-error").textContent = error.message;
  }
}

export async function openSummary(sessionId, handlers) {
  state.sessionId = sessionId;
  state.onHome = handlers.onHome;
  await redraw();

  const finish = state.session.finish || {};
  el("in-summary").value = finish.summary || "";
  el("in-strengths").value = finish.strengths || "";
  el("in-concerns").value = finish.concerns || "";
  el("in-followup-areas").value = finish.follow_up_areas || "";
  el("in-anonymise").checked = Boolean(finish.anonymise);
  el("btn-save-close").disabled = false;
  el("finish-result").classList.add("hidden");
}

export function initSummary(handlers) {
  el("btn-save-close").addEventListener("click", saveAndClose);
  el("btn-back-to-interview").addEventListener("click", () => handlers.onBack(state.sessionId));
  el("btn-home").addEventListener("click", () => handlers.onHome());
}
