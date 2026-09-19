# Interview Runner

A local tool for running a live technical interview. It picks questions from a file-based bank,
shows them one at a time with notes only the interviewer sees, records a rating and a note for each,
and writes a Markdown scorecard back into this repository.

There is no database, no account and no network service. The question bank and the results are text
files you edit and commit.

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
```

The command prints the address to open, by default `http://127.0.0.1:8765/`. Use `--port` to change
the port.

To run the tests:

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -q
```

## Add a question

Copy `bank/_template.md` into a topic directory and edit it. The directory name is the topic. The
file name is the question id, so `bank/java/gc-tuning.md` has the id `java/gc-tuning`.

```markdown
---
title: What does `volatile` actually guarantee?
difficulty: 3
tags: [concurrency, memory-model]
time_minutes: 5
order: 20
---

## Ask

The text you read to the candidate.

## Look for

- What a real answer contains

## Red flags

- What a weak answer contains

## Follow-ups

- The question to ask when the first answer is too general
```

Rules the loader applies:

- `title` and `difficulty` are required. Difficulty is a whole number from 1 to 5.
- Every other field is optional. `order` sets the position in sequential mode.
- The four headings above are recognised. Any other `##` heading is kept and shown under its own
  title.
- A file whose name starts with `_` is ignored.
- A file the loader cannot read is listed as a warning on the home screen and skipped. One broken
  file never stops the tool.

The bank is read again at the start of every session. Edit a file, start a new session, and the
change is live. The tool never writes to `bank/`.

## Selection modes

Stage 1 builds the pool: topics, tags to include or exclude, a difficulty range, a cap on the count,
and an optional hand-picked list. Stage 2 picks the order:

| Mode | What it does |
|---|---|
| Sequential | The `order` field, then the file name. The same every time. |
| Random | Shuffled with a seed. The seed is written to the session, so the run can be repeated. |
| Difficulty ascending | Lowest difficulty first. Ties are broken by the seed. |
| Adaptive | The next question follows the rating just given. See below. |
| Manual | The exact order ticked in stage 1. |

Adaptive mode starts at difficulty 2, unless you change it. A rating of 4 or 5 raises the target
difficulty by one. A rating of 1 or 2 lowers it by one. A rating of 3 holds it, and so does a skip.
The target is kept between 1 and 5. If no question is left at the target, the tool takes the nearest
level that still has one. Inside a level it prefers a question with a tag this session has not
covered yet, so the mode does not stay on one subject. A question is never asked twice in one
session. Every served question records the target and the reason, and both appear in the scorecard.

Stage 3 picks the pacing: untimed, a budget per question, or a budget for the whole session. A
question over its budget turns the card border red. The tool never advances on its own.

## Keyboard

| Key | Action |
|---|---|
| `1` to `5` | Set the rating |
| `0` | Mark the question skipped |
| `n` or `→` | Next question |
| `p` or `←` | Previous question |
| `f` | Show or hide the follow-ups |
| `h` | Show or hide every interviewer note |
| `/` | Move the cursor to the note field |
| `Esc` | Leave the note field |

Shortcuts do nothing while the cursor is in a text field.

Press `h` before you share your screen. It removes the whole interviewer zone, and the server stops
sending the hint text at all. The setting is remembered, so a page reload does not put the answer
key back on screen.

## Saving and recovery

There is no save button. Ratings and notes are written as you make them, and the status in the top
right shows `saving`, `saved` or `save failed`.

The session file is the record. It is written with a temporary file and a rename, so the file on
disk is always either the state before a change or the state after it. Killing the server during an
interview loses nothing. Start it again and the session is listed as resumable, with the same
question order, position, ratings, notes and times.

## Output

Ending an interview opens a summary screen. Nothing is written until you press **Save & close**.
That writes two files into `sessions/<date>_<time>_<candidate>_<role>/`:

- `scorecard.md`, ready to paste into a hiring thread;
- `session.json`, the full state, including per-question times, the seed and the reason each
  question was served.

The **anonymise** tick replaces the candidate name with initials in `scorecard.md`.

## Security model

The tool has no authentication. That is safe only because of the four measures below, so do not
remove any of them.

1. The server binds to `127.0.0.1`. The address is fixed in `app/config.py` and there is no setting
   to change it.
2. The server checks the `Host` header of every request and answers only for `127.0.0.1` and
   `localhost`. This blocks DNS rebinding, where a site the user visits resolves its own name to
   `127.0.0.1` and then talks to this tool as if it owned it.
3. A request that changes state must use `Content-Type: application/json`. A web page cannot send
   that to another origin without a preflight, and this server sends no CORS headers, so the
   preflight fails. **Do not add CORS headers.** That single change would let any website drive
   this tool.
4. A session id from a URL is matched against a strict pattern and the resolved path is checked to
   be inside `sessions/`. Anything else is refused.

## Layout

```
run.py              entry point
app/config.py       paths, port, the host allow list
app/storage.py      atomic writes and path containment
app/bank.py         reading and validating the question bank
app/selection.py    pool building, ordering, adaptive rules
app/session.py      session state
app/report.py       scorecard rendering
app/main.py         routes and the two security middlewares
web/                the browser code: plain HTML, CSS and ES modules, no build step
bank/               the question bank, one file per question
sessions/           one directory per interview
```

The browser code has no build step and no dependencies. Edit the files in `web/` and reload the
page.
