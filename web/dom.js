// Small DOM helpers. Text always goes in as text, never as markup, because the question bank and
// the notes are files a person edits.

export const el = (id) => document.getElementById(id);

export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

export function make(tag, options = {}) {
  const node = document.createElement(tag);
  if (options.text !== undefined) node.textContent = options.text;
  if (options.className) node.className = options.className;
  if (options.attrs) {
    for (const [key, value] of Object.entries(options.attrs)) node.setAttribute(key, value);
  }
  if (options.children) options.children.forEach((child) => node.appendChild(child));
  return node;
}

// Renders the small part of Markdown the bank uses: blank-line paragraphs, and "- " bullets.
// Anything else stays literal text. A full Markdown parser is not worth the risk here.
export function renderSimpleMarkdown(container, text) {
  clear(container);
  const blocks = String(text || "").split(/\n{2,}/);
  for (const block of blocks) {
    const lines = block.split("\n").filter((line) => line.trim() !== "");
    if (lines.length === 0) continue;
    if (lines.every((line) => /^\s*[-*]\s+/.test(line))) {
      const list = make("ul");
      for (const line of lines) {
        list.appendChild(make("li", { text: line.replace(/^\s*[-*]\s+/, "") }));
      }
      container.appendChild(list);
    } else {
      container.appendChild(make("p", { text: lines.join(" ") }));
    }
  }
}

export function formatClock(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, "0")}`;
}

export function showScreen(name) {
  for (const section of document.querySelectorAll(".screen")) {
    section.classList.toggle("hidden", section.id !== `screen-${name}`);
  }
  window.scrollTo(0, 0);
}

let saveTimer = null;
export function setSaveState(state) {
  const node = el("save-state");
  node.dataset.state = state;
  node.textContent = { idle: "ready", saving: "saving", saved: "saved", error: "save failed" }[state];
  clearTimeout(saveTimer);
  if (state === "saved") saveTimer = setTimeout(() => setSaveState("idle"), 1600);
}

// True when the keystroke belongs to a text field or carries a modifier, so a shortcut must not run.
export function isTypingTarget(event) {
  if (event.ctrlKey || event.metaKey || event.altKey) return true;
  const node = event.target;
  if (!node) return false;
  const tag = node.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || node.isContentEditable;
}
