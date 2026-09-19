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

const id = (value) => encodeURIComponent(value);

export const api = {
  bank: () => request("GET", "/api/bank"),
  bankQuestion: (questionId, hints) =>
    request("GET", `/api/bank/questions/${id(questionId)}?hints=${hints ? 1 : 0}`),
  preview: (filters, excludeAskedTo) =>
    request("POST", "/api/bank/preview", { filters, exclude_asked_to: excludeAskedTo || "" }),

  listSessions: () => request("GET", "/api/sessions"),
  createSession: (setup) => request("POST", "/api/sessions", setup),
  getSession: (sid) => request("GET", `/api/sessions/${id(sid)}`),
  getQuestion: (sid, index, hints) =>
    request("GET", `/api/sessions/${id(sid)}/question/${index}?hints=${hints ? 1 : 0}`),
  patchAnswer: (sid, qid, patch) =>
    request("PATCH", `/api/sessions/${id(sid)}/answers/${id(qid)}`, patch),

  suggestions: (sid) => request("GET", `/api/sessions/${id(sid)}/suggestions`),
  setCalibration: (sid, level) => request("POST", `/api/sessions/${id(sid)}/calibration`, { level }),
  next: (sid) => request("POST", `/api/sessions/${id(sid)}/next`, {}),
  goto: (sid, index) => request("POST", `/api/sessions/${id(sid)}/goto`, { index }),
  jump: (sid, questionId, reason) =>
    request("POST", `/api/sessions/${id(sid)}/jump`, { question_id: questionId, reason }),

  summary: (sid) => request("GET", `/api/sessions/${id(sid)}/summary`),
  finish: (sid, payload) => request("POST", `/api/sessions/${id(sid)}/finish`, payload),
};

// A last write that must survive the page going away. sendBeacon cannot set a JSON content type
// on every browser, so this uses keepalive on fetch, which can.
export function patchAnswerKeepalive(sessionId, qid, patch) {
  return fetch(`/api/sessions/${id(sessionId)}/answers/${id(qid)}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(patch),
    keepalive: true,
  });
}
