// The screen between the last question and the file on disk. Nothing is written until Save.
//
// The figures here are arithmetic over the bands the interviewer assigned. The assessment boxes
// are the interviewer's own words and nothing fills them in.

import { api } from "./api.js";
import { clear, el, make, setSaveState } from "./dom.js";

const BANDS = ["weak", "junior", "mid", "senior", "lead"];

const state = { sessionId: null, session: null, summary: null, onHome: () => {}, onBack: () => {} };

function table(headings, rows, className = "slist") {
  const node = make("table", { className });
  node.appendChild(make("tr", { children: headings.map((text) => make("th", { text })) }));
  for (const row of rows) {
    node.appendChild(make("tr", { children: row.map((cell) => make("td", { text: String(cell) })) }));
  }
  return node;
}

function gapLabel(meanGap) {
  if (meanGap > 0) return `+${meanGap.toFixed(1)} above`;
  if (meanGap < 0) return `${meanGap.toFixed(1)} below`;
  return "at the bar";
}

function renderRange(summary, session) {
  const panel = el("summary-range");
  clear(panel);

  const score = summary.score;
  if (score.value === null) {
    panel.appendChild(
      make("p", { text: "No question carries a band yet, so there is nothing to summarise." })
    );
    return;
  }

  panel.appendChild(
    make("p", {
      className: "range",
      children: [
        make("strong", { text: `${score.value} / 100` }),
        make("span", { text: ` — reads as ${score.label}` }),
      ],
    })
  );
  panel.appendChild(
    make("p", {
      className: "hint",
      text:
        `0 is an intern, 100 an engineering tech lead. ${score.rated} banded answer(s), ` +
        `confidence ${score.confidence}. Seed ${session.seed}, mode ${session.mode}.`,
    })
  );

  const details = make("details");
  details.appendChild(make("summary", { text: "How this number is produced" }));
  details.appendChild(make("p", { className: "hint", text: score.formula }));
  details.appendChild(
    table(
      ["Question", "Level", "Band", "vs level"],
      summary.observations.map((row) => [
        row.qid,
        row.level,
        row.band,
        row.gap > 0 ? `+${row.gap}` : String(row.gap),
      ])
    )
  );
  panel.appendChild(details);
}

function renderProfile(summary) {
  const panel = el("summary-profile");
  clear(panel);
  if (summary.observations.length === 0) return;

  const spots = summary.hot_spots;
  if (spots.strong.length > 0 || spots.weak.length > 0) {
    panel.appendChild(make("h2", { text: "Hot spots" }));
    panel.appendChild(
      make("p", {
        className: "hint",
        text:
          "How far the bands you assigned sat above or below the level those questions were " +
          "set to.",
      })
    );
    const rows = [...spots.strong, ...spots.at_bar, ...spots.weak];
    panel.appendChild(
      table(
        ["Topic", "Asked", "Deepest band", "Held at", "vs level"],
        rows.map((row) => [
          row.name,
          row.asked,
          row.deepest_band,
          row.hardest_level_held || "—",
          gapLabel(row.mean_gap),
        ])
      )
    );
  }

  if (summary.by_category.length > 0) {
    panel.appendChild(make("h2", { text: "By category" }));
    panel.appendChild(
      table(
        ["Category", "Asked", "Range", "Deepest band", "vs level"],
        summary.by_category.map((row) => [
          row.name,
          row.asked,
          row.score,
          row.deepest_band,
          gapLabel(row.mean_gap),
        ])
      )
    );
  }
}

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
  state.session = await api.getSession(state.sessionId);
  state.summary = await api.summary(state.sessionId);
  renderRange(state.summary, state.session);
  renderProfile(state.summary);
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
