// Entry point: loads the bank, shows the home screen, and moves between the four screens.

import { api } from "./api.js";
import { clear, el, make, showScreen } from "./dom.js";
import { initBrowse, openBrowse } from "./browse.js";
import { initSetup } from "./setup.js";
import { initInterview, jumpTo, openInterview, stopInterviewTimers } from "./interview.js";
import { initSummary, openSummary } from "./summary.js";

let bank = null;

function renderBankSummary() {
  const panel = el("bank-summary");
  clear(panel);
  const histogram = bank.levels
    .map((level) => `${level}:${bank.level_histogram[level]}`)
    .join("  ");
  panel.appendChild(
    make("p", {
      text:
        `${bank.count} cards · ${bank.categories.length} categories · ` +
        `${bank.topics.length} topics · ${bank.tags.length} tags`,
    })
  );
  panel.appendChild(
    make("p", { className: "hint", text: `categories: ${bank.categories.join(", ")}` })
  );
  panel.appendChild(make("p", { className: "hint", text: `levels: ${histogram}` }));

  // A card the loader could not use is reported here rather than quietly missing from the bank.
  const problems = el("bank-problems");
  clear(problems);
  problems.classList.toggle("hidden", bank.problems.length === 0);
  if (bank.problems.length > 0) {
    const warnings = bank.problems.length - bank.error_count;
    problems.appendChild(
      make("p", {
        text: `${bank.error_count} error(s) and ${warnings} warning(s) in the bank:`,
      })
    );
    const list = make("ul");
    for (const problem of bank.problems) {
      const where = [problem.path, problem.card_id, problem.field].filter(Boolean).join(" · ");
      list.appendChild(
        make("li", {
          className: problem.severity === "error" ? "problem-error" : "",
          text: `${problem.severity}: ${where} — ${problem.problem}`,
        })
      );
    }
    problems.appendChild(list);
  }
}

async function renderSessions() {
  const panel = el("session-list");
  clear(panel);
  const { sessions } = await api.listSessions();
  if (sessions.length === 0) {
    panel.appendChild(make("p", { className: "hint", text: "No sessions yet." }));
    return;
  }
  const table = make("table", { className: "slist" });
  table.appendChild(
    make("tr", {
      children: ["Session", "Role", "Mode", "Asked", "Banded", "", ""].map((text) =>
        make("th", { text })
      ),
    })
  );
  for (const session of sessions) {
    const open = make("button", { text: session.resumable ? "Resume" : "Open", attrs: { type: "button" } });
    open.addEventListener("click", () =>
      session.resumable ? goInterview(session.id) : goSummary(session.id)
    );
    const card = make("button", { text: "Scorecard", attrs: { type: "button" } });
    card.addEventListener("click", () => {
      window.open(`/api/sessions/${encodeURIComponent(session.id)}/scorecard`, "_blank");
    });
    table.appendChild(
      make("tr", {
        children: [
          make("td", { text: `${session.candidate || "unnamed"} · ${session.id}` }),
          make("td", { text: session.role || "" }),
          make("td", { text: session.mode }),
          make("td", { text: String(session.served) }),
          make("td", { text: String(session.answered) }),
          make("td", {
            children: [
              make("span", {
                className: `pill${session.resumable ? " resumable" : ""}`,
                text: session.resumable ? "resumable" : "finished",
              }),
            ],
          }),
          make("td", { children: [open, card] }),
        ],
      })
    );
  }
  panel.appendChild(table);
}

// The screen is in the address, so a reload during an interview comes back to the same question.
function setHash(value) {
  if (window.location.hash !== value) {
    window.history.replaceState(null, "", value || window.location.pathname);
  }
}

async function goHome() {
  stopInterviewTimers();
  setHash("");
  bank = await api.bank();
  renderBankSummary();
  await renderSessions();
  showScreen("home");
}

async function ensureBank() {
  if (!bank) bank = await api.bank();
  return bank;
}

// Opened from home it reads; opened from an interview it picks. The interviewer is never
// confined to the questions the tool planned.
async function goBrowse(sessionId) {
  stopInterviewTimers();
  setHash(sessionId ? `#pick=${encodeURIComponent(sessionId)}` : "#browse");
  await ensureBank();
  showScreen("browse");
  await openBrowse(bank, {
    onPick: sessionId
      ? async (questionId) => {
          setHash(`#session=${encodeURIComponent(sessionId)}`);
          showScreen("interview");
          await jumpTo(questionId, "picked by hand");
        }
      : null,
    onClose: sessionId ? () => goInterview(sessionId) : goHome,
  });
}

function goSetup() {
  setHash("#new");
  initSetup(bank, { onStarted: goInterview, onCancel: goHome });
  showScreen("setup");
}

async function goInterview(sessionId) {
  const state = await api.getSession(sessionId);
  setHash(`#session=${encodeURIComponent(sessionId)}`);
  showScreen("interview");
  await openInterview(sessionId, state, { onFinish: goSummary, onBrowse: goBrowse });
}

async function goSummary(sessionId) {
  stopInterviewTimers();
  setHash(`#summary=${encodeURIComponent(sessionId)}`);
  showScreen("summary");
  await openSummary(sessionId, { onHome: goHome, onBack: goInterview });
}

async function openFromHash() {
  const hash = window.location.hash;
  const session = hash.match(/^#session=(.+)$/);
  const summary = hash.match(/^#summary=(.+)$/);
  const pick = hash.match(/^#pick=(.+)$/);
  if (session) return goInterview(decodeURIComponent(session[1]));
  if (summary) return goSummary(decodeURIComponent(summary[1]));
  if (pick) return goBrowse(decodeURIComponent(pick[1]));
  if (hash === "#browse") return goBrowse(null);
  if (hash === "#new") {
    await ensureBank();
    return goSetup();
  }
  return goHome();
}

function start() {
  el("btn-new-session").addEventListener("click", goSetup);
  el("btn-browse-bank").addEventListener("click", () => goBrowse(null));
  initBrowse();
  initInterview({ onFinish: goSummary, onBrowse: goBrowse });
  initSummary({ onHome: goHome, onBack: goInterview });
  openFromHash().catch(async (error) => {
    // A stale link in the address bar must not leave a blank page.
    setHash("");
    await goHome().catch(() => {
      el("bank-summary").textContent = `cannot reach the server: ${error.message}`;
    });
  });
}

start();
