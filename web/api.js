// Every call to the server goes through here.
// Mutating calls always send application/json, because the server refuses anything else.

const JSON_HEADERS = { "Content-Type": "application/json" };

async function request(method, path, body) {
  const options = { method, headers: {} };
  if (method !== "GET") {
    options.headers = JSON_HEADERS;
    options.body = JSON.stringify(body ?? {});
  }
  const response = await fetch(path, options);
  const text = await response.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { detail: text };
    }
  }
  if (!response.ok) {
    const detail = payload && payload.detail ? payload.detail : `${response.status}`;
    throw new Error(detail);
  }
  return payload;
}

export const api = {
  bank: () => request("GET", "/api/bank"),
  preview: (filters, excludeAskedTo) =>
    request("POST", "/api/bank/preview", { filters, exclude_asked_to: excludeAskedTo || "" }),
  listSessions: () => request("GET", "/api/sessions"),
  createSession: (setup) => request("POST", "/api/sessions", setup),
  getSession: (id) => request("GET", `/api/sessions/${encodeURIComponent(id)}`),
  getQuestion: (id, index, hints) =>
    request("GET", `/api/sessions/${encodeURIComponent(id)}/question/${index}?hints=${hints ? 1 : 0}`),
  patchAnswer: (id, qid, patch) =>
    request("PATCH", `/api/sessions/${encodeURIComponent(id)}/answers/${qid}`, patch),
  next: (id) => request("POST", `/api/sessions/${encodeURIComponent(id)}/next`, {}),
  goto: (id, index) => request("POST", `/api/sessions/${encodeURIComponent(id)}/goto`, { index }),
  finish: (id, payload) => request("POST", `/api/sessions/${encodeURIComponent(id)}/finish`, payload),
};

// A last write that must survive the page going away. sendBeacon cannot set a JSON content type
// on every browser, so this uses keepalive on fetch, which can.
export function patchAnswerKeepalive(id, qid, patch) {
  return fetch(`/api/sessions/${encodeURIComponent(id)}/answers/${qid}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(patch),
    keepalive: true,
  });
}
