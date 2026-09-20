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

## Browse the bank

**Browse the bank** on the home screen lists every card with one filter row above it: free-text
search over titles, question text, topics and tags, then category, level, topic and tag chips.
Picking a card opens a preview.

The preview keeps the two audiences apart on purpose. The `## Ask` text sits in its own bordered
card under **Read this aloud**; everything else — what it tests, what to listen for, the signals,
the bands, the follow-ups with their `probes:` lines, the notes and sources — is fenced into a
block headed *Interviewer only, never read any of this out*. At the bottom, every card this one
connects to is one click away.

## Selection modes

Stage 1 builds the pool: categories, topics, levels, tags to include or exclude, a cap on the
count, and an optional hand-picked list. Stage 2 picks the order:

| Mode | Where the run opens, and how ties break |
|---|---|
| Sequential | The lowest `order` field, then the id. The same every time. |
| Random | A seeded shuffle. The seed is written to the session, so the run can be repeated. |
| Level ascending | Junior first, lead last, in blocks within each level. |
| Adaptive | The next card follows the band you just assigned. See below. |
| Manual | The exact order ticked in stage 1, untouched. |

### Questions arrive in blocks

Every mode except manual walks the pool by **relatedness**, so a session reads as a chain
instead of hopping between subjects. Open on Java concurrency and the next card is another Java
concurrency question, then the rest of Java, then whichever category is nearest — not SAP, then
Spring, then back to Java.

Nothing extra has to be authored for this. Four signals already in the bank are combined:

| Signal | Weight |
|---|---|
| Same topic | 0.8 |
| Same category | 0.5 |
| An explicit `links:` entry, any kind | 0.9 |
| Shared tags, by overlap | 0 to 0.35 |

They stack, and two consequences are deliberate. A same-topic card scores 1.3 and so beats a
cross-category link at 0.9, which means a topic is finished before the run leaves it. A `deeper`
link inside a topic scores 2.2 and wins outright, so an authored progression is followed exactly.

The mode decides only where the walk opens and how two equally related cards are separated, so
each mode still behaves like itself. Level ascending walks one chain per level and starts each
one next to where the previous level finished, so the run climbs and stays in blocks at the same
time. Every card records the reason it came next, and those reasons appear in the scorecard:

```
opens on java / concurrency
same topic, concurrency
concurrency → collections, still java
java → kafka via correctness
```

Tags are what connect areas nothing else joins, so tag cards with the ideas they share —
`idempotency`, `correctness`, `transactions` — not only with their technology.

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

That table is what the interview screen shows as the advice for the answer just given. The
**running calibration** — the level the next question is actually pitched at — is derived from
every band recorded so far, not from the last one alone, because a candidate sitting between two
levels answers above, then below, then above, and a tool with no memory chases that for the whole
interview.

| Rule | Why |
|---|---|
| The bar moves **one level per answer**, never a jump | One spectacular answer is evidence, not proof |
| Three answers **at** the level asked trigger one question a level up | Otherwise a candidate is only ever asked what they have already proved they can do, and the ceiling is never found |
| The bar **stops** once a level was held and the one above it was not | The ceiling has been located; the rest of the interview is worth more spent on coverage |
| Three answers **above** a settled ceiling reopen it | The bracket can be built on one unlucky topic; consistent contradiction falsifies it |
| Failing a question at a level they also hold is **not** a ceiling | That is inconsistency, not a wall |
| A ceiling is never called from fewer than three answers | One unlucky topic at the start is not a bracket |

The status bar shows the level, and one word for the state: `probing` while it is trying a step
up, `ceiling senior` once it has settled, `manual` if you have overridden it. The sentence beside
it says why.

Two rules keep the run from grinding one area:

- after four consecutive questions in one category it moves to the nearest other one;
- after two answers in a row two or more bands below, it leaves that category immediately —
  grinding the area somebody is worst at neither finds a ceiling nor collects usable evidence.

The running calibration can be overridden by hand at any time.
Every suggestion is optional: the interviewer can ignore all of them, follow any link, or jump to
any card in the bank. Leaving the planned sequence and coming back loses nothing — bands, notes
and follow-up usage are all kept.

Adaptive mode starts at `mid` unless you change it. It never repeats a card inside one session,
prefers a topic the session has not covered, and stops cleanly when the pool is used up. Every
served card records the target level and the reason, and both appear in the scorecard.

Stage 3 picks the pacing: untimed, a budget per question, or a budget for the whole session. A
question over its budget turns the card border red. The tool never advances on its own.

### Match the pool to the role

The pool decides what the range means. Four scripted candidates, the same fourteen questions
each, run twice — once against a pool matching the role, once against the whole bank including
two specialities they had never worked in:

| Candidate | Pool matched the role | Whole bank |
|---|---|---|
| junior | 20, reads junior | 8, reads weak |
| solid mid | 50, reads mid | 46, reads mid |
| borderline senior | 67, reads senior | 62, reads mid |
| strong senior | 90, reads lead | 90, reads lead |

Matched to the role, every candidate lands on the level they actually are. Against the whole bank
they drop, because questions from a speciality they have never worked in still count as evidence —
and the further a candidate is from that speciality the more it costs them. The ordering survives either way, but the number only means
what it says if the categories in stage 1 are the ones the job needs.

## During the interview

Under the note field sits the navigation zone. Nothing in it moves the interview until you click.

**The calibration** is on the left: the level the tool would pitch the next question at, with the
reason underneath. It follows the bands you assign, and the dropdown beside it overrides that by
hand for the rest of the session — or hands control back with *follow the bands*.

**Suggested next** is a row of cards, best first. Links out of the current question come first, in
whatever order the calibration asks for — after an answer below the level asked that is
`shallower`, after one above it that is `deeper` — then cards at the calibrated level, nearest
first by relatedness. Each carries the reason it is being offered. The list never goes empty
while the pool has cards left: if nothing remains at the calibrated level it widens to the
nearest one.

**Pick any question** opens the browse screen as a picker, so the whole bank stays reachable
whether or not it was in the pool. Jumping to a card that was already served moves the position
rather than asking it twice, and nothing recorded is lost either way.

## Keyboard

| Key | Action |
|---|---|
| `1` to `5` | Assign the band: weak, junior, mid, senior, lead |
| `0` | Skip the question |
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

## Skipping, and why Next is gated

**Next does nothing until you have either assigned a band or skipped the question.** Walking past
a question without recording anything loses the evidence silently, and an hour later nobody can
tell whether it went badly or was never really asked.

Skip is the other way out, and it is a different kind of statement. A band is a judgement about
the answer; **a skip is your decision to move on and records nothing about the candidate**. It is
coloured as a warning rather than as a sixth band, it never enters the range or the profile, and
it is never counted as a zero. Skipped questions are listed in the scorecard under
"Gaps — no evidence collected".

A skipped question is parked, not discarded. Nothing re-serves it on its own — adaptive mode will
not bring it back, and the running order steps past it. A counter appears at the bottom right of
the interview screen; click it for the list, and click any entry to go back to that question. It
is still a live question: assign a band and the skip clears.

## Saving and recovery

There is no save button. Ratings and notes are written as you make them, and the status in the top
right shows `saving`, `saved` or `save failed`.

The session file is the record. It is written with a temporary file and a rename, so the file on
disk is always either the state before a change or the state after it. Killing the server during an
interview loses nothing. Start it again and the session is listed as resumable, with the same
question order, position, ratings, notes and times.

## Output

Ending an interview opens a summary screen: the range with its position on the 0-100 scale, a
diverging bar chart of how far each topic sat above or below the level its questions were set to,
a heatmap of where the answers landed, and then the whole thing openable down to each category,
topic and question with the note taken at the time.

The charts are hand-built SVG — the browser code still has no dependencies and no build step.
Every one of them has a table beside it holding the same figures, so nothing is reachable only by
hovering. The diverging blue/red pair was checked against this application's own light and dark
surfaces rather than assumed: worst-case colour-blind separation dE 23.8 light and 25.7 dark,
normal-vision dE 31.6 and 31.9, both poles clearing 3:1 contrast. Nothing is written until you press **Save & close**. That writes three files into
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
app/affinity.py     relatedness between cards, and the walk that turns a pool into blocks
app/main.py         routes and the two security middlewares
web/                the browser code: plain HTML, CSS and ES modules, no build step
web/browse.js       browsing the bank, and previewing one card
web/charts.js       the three SVG chart forms on the summary screen
bank/               the question bank, one file per card
docs/               the card format reference
sessions/           one directory per interview
```

The browser code has no build step and no dependencies. Edit the files in `web/` and reload the
page.
