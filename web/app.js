// Entry point: loads the bank, shows the home screen, and moves between the four screens.

import { api } from "./api.js";
import { clear, el, make, showScreen } from "./dom.js";
import { initSetup } from "./setup.js";
import { initInterview, openInterview, stopInterviewTimers } from "./interview.js";
import { initSummary, openSummary } from "./summary.js";

let bank = null;

function renderBankSummary() {
  const panel = el("bank-summary");
  clear(panel);
  const histogram = Object.entries(bank.difficulty_histogram)
    .map(([level, count]) => `d${level}:${count}`)
    .join("  ");
  panel.appendChild(
    make("p", {
      text: `${bank.count} questions · ${bank.topics.length} topics · ${bank.tags.length} tags`,
    })
  );
  panel.appendChild(make("p", { className: "hint", text: `topics: ${bank.topics.join(", ")}` }));
  panel.appendChild(make("p", { className: "hint", text: `difficulty: ${histogram}` }));

  const warnings = el("bank-warnings");
  clear(warnings);
  warnings.classList.toggle("hidden", bank.warnings.length === 0);
  if (bank.warnings.length > 0) {
    warnings.appendChild(
      make("p", { text: `${bank.warnings.length} file(s) were skipped or need attention:` })
    );
    const list = make("ul");
    for (const warning of bank.warnings) {
      list.appendChild(make("li", { text: `${warning.path} — ${warning.problem}` }));
    }
    warnings.appendChild(list);
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
      children: ["Session", "Role", "Mode", "Asked", "Rated", "", ""].map((text) =>
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

function goSetup() {
  setHash("#new");
  initSetup(bank, { onStarted: goInterview, onCancel: goHome });
  showScreen("setup");
}

async function goInterview(sessionId) {
  const state = await api.getSession(sessionId);
  setHash(`#session=${encodeURIComponent(sessionId)}`);
  showScreen("interview");
  await openInterview(sessionId, state, { onFinish: goSummary });
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
  if (session) return goInterview(decodeURIComponent(session[1]));
  if (summary) return goSummary(decodeURIComponent(summary[1]));
  if (hash === "#new") {
    bank = await api.bank();
    return goSetup();
  }
  return goHome();
}

function start() {
  el("btn-new-session").addEventListener("click", goSetup);
  initInterview({ onFinish: goSummary });
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
