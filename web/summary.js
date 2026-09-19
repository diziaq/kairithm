// The screen between the last question and the file on disk. Nothing is written until Save.

import { api } from "./api.js";
import { clear, el, make, setSaveState } from "./dom.js";

const RECOMMENDATIONS = [
  "Strong hire",
  "Hire",
  "Lean hire",
  "Lean no",
  "No hire",
  "Inconclusive",
];

const state = { sessionId: null, session: null, onHome: () => {}, onBack: () => {} };

function averages(session, key) {
  const totals = new Map();
  for (const item of session.items) {
    const rating = item.answer && item.answer.rating;
    if (rating == null) continue;
    const buckets = key === "topic" ? [item.question.topic] : item.question.tags || [];
    for (const bucket of buckets) {
      if (!totals.has(bucket)) totals.set(bucket, []);
      totals.get(bucket).push(Number(rating));
    }
  }
  return [...totals.entries()]
    .map(([name, values]) => [name, values.reduce((a, b) => a + b, 0) / values.length, values.length])
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

function renderAverages(session) {
  const panel = el("summary-averages");
  clear(panel);
  const answered = session.items.filter((i) => i.answer && i.answer.rating != null).length;
  const skipped = session.items.filter((i) => i.answer && i.answer.skipped).length;
  panel.appendChild(
    make("p", {
      className: "hint",
      text: `${session.items.length} asked · ${answered} rated · ${skipped} skipped · seed ${session.seed} · mode ${session.mode}`,
    })
  );
  for (const [label, key] of [["Topic", "topic"], ["Tag", "tag"]]) {
    const rows = averages(session, key);
    if (rows.length === 0) continue;
    const table = make("table", { className: "slist" });
    const head = make("tr", {
      children: [
        make("th", { text: label }),
        make("th", { text: "Avg" }),
        make("th", { text: "Asked" }),
      ],
    });
    table.appendChild(head);
    for (const [name, avg, count] of rows) {
      table.appendChild(
        make("tr", {
          children: [
            make("td", { text: name }),
            make("td", { text: avg.toFixed(1) }),
            make("td", { text: String(count) }),
          ],
        })
      );
    }
    panel.appendChild(table);
  }
}

function renderQuestions(session) {
  const container = el("summary-questions");
  clear(container);
  session.items.forEach((item, index) => {
    const row = make("div", { className: "qrow" });
    const rating = item.answer && item.answer.rating;
    const skipped = item.answer && item.answer.skipped;
    const verdict = skipped ? "skipped" : rating == null ? "not rated" : `${rating} / 5`;
    row.appendChild(
      make("h4", { text: `${index + 1}. ${item.question.title || item.qid} — ${verdict}` })
    );
    row.appendChild(
      make("p", {
        className: "hint",
        text: `${item.qid} · difficulty ${item.question.difficulty ?? "?"}${
          item.reason ? " · " + item.reason : ""
        }`,
      })
    );

    const ratingRow = make("div", { className: "row" });
    for (const value of [1, 2, 3, 4, 5, 0]) {
      const isSkip = value === 0;
      const pressed = isSkip ? Boolean(skipped) : !skipped && rating === value;
      const button = make("button", {
        text: isSkip ? "skip" : String(value),
        attrs: { type: "button", "aria-pressed": String(pressed) },
      });
      button.addEventListener("click", async () => {
        const patch = isSkip ? { skipped: !pressed } : { rating: value, skipped: false };
        await patchAndRedraw(item.qid, patch);
      });
      ratingRow.appendChild(button);
    }
    row.appendChild(ratingRow);

    const note = make("textarea", { attrs: { rows: "3", placeholder: "Note" } });
    note.value = (item.answer && item.answer.note) || "";
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

async function patchAndRedraw(qid, patch) {
  setSaveState("saving");
  try {
    await api.patchAnswer(state.sessionId, qid, patch);
    state.session = await api.getSession(state.sessionId);
    renderAverages(state.session);
    renderQuestions(state.session);
    setSaveState("saved");
  } catch {
    setSaveState("error");
  }
}

async function saveAndClose() {
  el("finish-error").textContent = "";
  try {
    const result = await api.finish(state.sessionId, {
      recommendation: el("in-recommendation").value,
      summary: el("in-summary").value,
      strengths: el("in-strengths").value,
      concerns: el("in-concerns").value,
      follow_up_areas: el("in-followup-areas").value,
      anonymise: el("in-anonymise").checked,
    });
    el("finish-path").textContent = `Written to ${result.path}`;
    el("finish-preview").textContent = result.markdown;
    el("finish-result").classList.remove("hidden");
    el("btn-save-close").disabled = true;

    el("btn-download").onclick = () => {
      const blob = new Blob([result.markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = make("a", { attrs: { href: url, download: result.download_name } });
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    };
  } catch (error) {
    el("finish-error").textContent = error.message;
  }
}

export async function openSummary(sessionId, handlers) {
  state.sessionId = sessionId;
  state.onHome = handlers.onHome;
  state.session = await api.getSession(sessionId);

  const select = el("in-recommendation");
  clear(select);
  for (const value of RECOMMENDATIONS) {
    select.appendChild(make("option", { text: value, attrs: { value } }));
  }
  const finish = state.session.finish || {};
  select.value = finish.recommendation || "Inconclusive";
  el("in-summary").value = finish.summary || "";
  el("in-strengths").value = finish.strengths || "";
  el("in-concerns").value = finish.concerns || "";
  el("in-followup-areas").value = finish.follow_up_areas || "";
  el("in-anonymise").checked = Boolean(finish.anonymise);
  el("btn-save-close").disabled = false;
  el("finish-result").classList.add("hidden");

  renderAverages(state.session);
  renderQuestions(state.session);
}

export function initSummary(handlers) {
  el("btn-save-close").addEventListener("click", saveAndClose);
  el("btn-back-to-interview").addEventListener("click", () => handlers.onBack(state.sessionId));
  el("btn-home").addEventListener("click", () => handlers.onHome());
}
