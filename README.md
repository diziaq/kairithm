# Interview Runner

A local tool for running a live technical interview. It picks questions from a file-based bank,
shows them one at a time with guidance only the interviewer sees, records an assessed band and an
evidence note for each, and writes a Markdown scorecard back into this repository.

The tool collects evidence. It never assigns a band, never advances on its own, and produces no
hire recommendation.

There is no database, no account and no network service. The question bank and the results are text
files you edit and commit.

## Run it

```bash
./init.sh          # creates .venv and installs the dependencies
./run.sh           # starts the tool and prints the address to open
```

The address is `http://127.0.0.1:8765/` unless you change it. `run.sh` passes its arguments to the
server, so `./run.sh --port 9000` works. Both scripts work from any directory and `init.sh` can be
run again at any time.

Python 3.11 or newer is required. Set `PYTHON` if the interpreter is not on the path as `python3`,
for example `PYTHON=/usr/local/bin/python3.12 ./init.sh`.

To run the tests, and to check the question bank:

```bash
./init.sh --dev
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m app.validate
```

## Add a question

Copy `bank/_template.md` into a category directory and edit it. The full field reference is in
[`docs/question-format.md`](docs/question-format.md).

```markdown
---
id: java-concurrency-visibility-flag-01
schema_version: 1
title: A flag one thread writes and another never sees
category: java              # the directory name, and it must match
topic: concurrency          # the narrower area
level: senior               # junior | mid | senior | lead — what the QUESTION aims at
tags: [memory-model, jmm]
time_estimate_min: 7
links:
  shallower: [java-concurrency-shared-counter-01]
---

## Ask

The only text read aloud.

## Tests

One sentence: what this card actually probes.

## Listen for

- The concrete thing whose presence means they understand it

## Answer bands

### mid

- Explains the trade-off and names a failure case.

### senior

- Explains the mechanism rather than the API surface.

## Follow-ups

- The situation you describe when the first answer is thin
  probes: interviewer-only, never read aloud
```

The rules the loader applies:

- `id`, `schema_version`, `title`, `category`, `topic`, `level`, `## Ask`, `## Tests`,
  `## Listen for` and `## Answer bands` are required. Everything else is optional.
- The `id` is the identity, not the file name. It is never reused and never renumbered, because
  links and finished sessions point at it.
- `category` must match the directory the file is in.
- Answer bands describe what the candidate does, not a verdict. "Excellent understanding" is
  rejected.
- A file whose name starts with `_` is ignored.
- A file the loader cannot use is listed as a problem on the home screen and skipped. One broken
  file never stops the tool, and it is never silently missing from the bank.

Run `.venv/bin/python -m app.validate` to check every card, every link and every band in one
command. It names the file, the card id and the field for each problem.

The bank is read again on every request. Edit a file, reload the browser, and the change is
live. The tool never writes to `bank/`.

## Selection modes

Stage 1 builds the pool: categories, topics, levels, tags to include or exclude, a cap on the
count, and an optional hand-picked list. Stage 2 picks the order:

| Mode | What it does |
|---|---|
| Sequential | The `order` field, then the id. The same every time. |
| Random | Shuffled with a seed. The seed is written to the session, so the run can be repeated. |
| Level ascending | Junior first, lead last. Ties are broken by the seed. |
| Adaptive | The next card follows the band you just assigned. See below. |
| Manual | The exact order ticked in stage 1. |

### Bands, levels and the calibration

`level` is the seniority a **question** is pitched at. A **band** describes how the candidate
answered it. The two are separate scales that meet at `junior`, and the gap between them is what
drives navigation:

| Band you assigned, against the question's level | What the tool suggests |
|---|---|
| Two or more below | `shallower`, and consider changing topic |
| One below | `shallower`, or the same level in an adjacent topic |
| Equal | `related` at the same level, or `deeper` to find the ceiling |
| Above | `deeper`, and the bar for that topic moves up |

The suggested level is always the band just observed, floored at `junior`. A `mid` answer to a
`senior` question therefore suggests `mid` next — not another `senior` question on that topic.

The running calibration is shown in the status bar and can be overridden by hand at any time.
Every suggestion is optional: the interviewer can ignore all of them, follow any link, or jump to
any card in the bank. Leaving the planned sequence and coming back loses nothing — bands, notes
and follow-up usage are all kept.

Adaptive mode starts at `mid` unless you change it. It never repeats a card inside one session,
prefers a topic the session has not covered, and stops cleanly when the pool is used up. Every
served card records the target level and the reason, and both appear in the scorecard.

Stage 3 picks the pacing: untimed, a budget per question, or a budget for the whole session. A
question over its budget turns the card border red. The tool never advances on its own.

## Keyboard

| Key | Action |
|---|---|
| `1` to `5` | Assign the band: weak, junior, mid, senior, lead |
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

Ending an interview opens a summary screen showing the range, the hot spots and every question
asked. Nothing is written until you press **Save & close**. That writes three files into
`sessions/<date>_<time>_<candidate>_<role>/`:

- `summary.md`, one page about the candidate;
- `scorecard.md`, the full record;
- `session.json`, the full state, including per-question times, follow-ups used, the seed, and the
  reason each card was served.

The **anonymise** tick replaces the candidate name with initials in both Markdown files.

### summary.md

The one to send first. Clear statements about the candidate and nothing else — the range, how
many questions were met or beaten, the deepest answer, the strong and weak areas, and what was
never established. No mode, no seed, no timings, no per-question walkthrough: how the interview
was run is not evidence about the person. Where the interviewer wrote a summary, it is quoted at
the end and attributed.

```markdown
# A Petrov — executive summary

**62 / 100 — answers read as mid.** Interviewed for Senior Java.

Evidence: 9 banded answer(s) across 3 categories (java, kafka, spring). Confidence **good**.

## Answer quality

- Met or beat the level asked on **6 of 9** questions.
- Deepest answer: **senior** on a senior question (kafka / delivery-semantics).
- Bands assigned: junior ×2, mid ×4, senior ×3.

## Strong

- **kafka / delivery-semantics** — reached senior, 1 band above the level asked (3 asked).

## Weak

- **spring / transactions** — reached junior, 2 bands below the level asked (2 asked).

## Not established

No banded evidence in: microservices, sap-jco.
```

### scorecard.md

The full record: metadata, the range with every input row behind it, the band distribution, the
hot spots, then every question asked with the text as it was asked, the band, the follow-ups used
and the evidence notes.

It keeps facts and conclusions apart structurally. Everything above
`## Assessment (interviewer)` is either something you recorded or arithmetic over it. Everything
under it is your own prose, and the tool never writes into that section.

### The 0-100 range

The scorecard opens with a single figure. 0 is an intern, 100 an engineering tech lead. It is a
weighted mean of the bands you assigned:

```
sum(band points x level weight) / sum(level weight)

band points     weak 0, junior 25, mid 50, senior 75, lead 100
level weights   junior 1, mid 2, senior 3, lead 4
```

A band earned on a harder question weighs more, because it says more about the ceiling. Skipped
and unrated questions are left out of both sums, so a skip is never counted as a zero. The
formula and every input row are printed next to the figure, in the scorecard and on screen, so it
can be checked by hand.

It is an approximation over judgements a person made, not a measurement. It is shown with a
confidence label derived from how many questions were banded and how many categories they
spanned, and it is never the only thing on the page: the band distribution, the per-topic hot
spots and the raw evidence sit beside it.

There is no hire recommendation, and nothing in the tool assigns a band.

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
init.sh             creates the virtual environment and installs the dependencies
run.sh              starts the tool
run.py              entry point
app/config.py       paths, port, the host allow list
app/storage.py      atomic writes and path containment
app/levels.py       levels, bands, and the navigation table that connects them
app/bank.py         reading and parsing the question bank
app/validate.py     checking the bank; the CLI and the home-screen list share it
app/selection.py    pool building, ordering, adaptive picking, suggestions
app/scoring.py      the 0-100 range and the per-area profile
app/session.py      session state
app/report.py       scorecard rendering
app/main.py         routes and the two security middlewares
web/                the browser code: plain HTML, CSS and ES modules, no build step
bank/               the question bank, one file per card
docs/               the card format reference
sessions/           one directory per interview
```

The browser code has no build step and no dependencies. Edit the files in `web/` and reload the
page.
