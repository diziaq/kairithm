# Decisions

Choices made while building this, where the brief was open or where the build departed from it.
Each one names the option taken and the reason.

## Departures from the brief

### The rating scale was replaced by answer bands

The first brief used a 1 to 5 rating. The question-bank brief separates two things the number
had merged: `level`, the seniority a question is pitched at, and the band, an observable
description of how it was answered. Both are now explicit, and the gap between them is what
drives navigation. Nothing in the tool assigns a band.

The 1 to 5 keys on the keyboard still work; they now select weak, junior, mid, senior and lead.

### The hire recommendation was removed

The first brief asked for a Strong hire / No hire dropdown. The question-bank brief forbids the
tool producing a hire recommendation, and the operator asked for the same. It is gone from the
model, the API, the scorecard and the UI. The interviewer's own written assessment stays, under a
heading that says nobody but them wrote it.

### The per-topic averages were replaced by a profile and a 0-100 range

A mean of 1 to 5 ratings per topic was a score the tool computed and presented as fact. In its
place:

- a band distribution and a per-topic "hot spot" table, showing how far the assigned bands sat
  above or below the level those questions were set to;
- a single 0-100 range, requested by the operator, where 0 is an intern and 100 an engineering
  tech lead.

The question-bank brief forbids a numeric composite score. The operator asked for one explicitly,
so it is built — with the formula, every input row and a confidence label printed next to it, and
never as the only thing on the page. A number nobody can reproduce by hand is the thing worth
refusing; this one can be.

Skipped and unrated questions are left out of both sums, so a skip is never counted as a zero.

### The id is a field, not the file path

The first version derived a question's id from its directory and file name. Ids are now
referenced by links between cards and by finished sessions on disk, so a rename would silently
break both. `id` is a required frontmatter field. The file name is a convention the validator
warns about and nothing depends on.

### Link inverses are derived, not declared twice

`deeper` on one card implies `shallower` on the other. Requiring both would mean two edits per
edge across a bank of ninety cards, and the second one being forgotten would look like a missing
link rather than an oversight. The inverse is computed at load time. What the validator does
report is a pair that was declared explicitly in both files and points the wrong way, because
there the two files genuinely disagree.

### Answer bands live in the body, not the frontmatter

Bands are prose full of colons, hashes and backticks. In YAML every bullet would need hand
quoting, and `senior: Explains the mechanism: not the API` is a parse error rather than a
sentence. They are `###` sub-headings under `## Answer bands`. Frontmatter keeps only what is
filtered, sorted or linked on.

### The follow-up leak check is deliberately conservative

The brief asks for a warning when a follow-up repeats a term the guidance is waiting to hear. A
first version flagged any word over five letters shared with the guidance, which produced
"twenty", "cover" and "claim" — noise that would train an author to ignore the check. It now
flags only backticked identifiers, hyphenated compounds, internally capitalised names and long
words that are not ordinary English or ordinary shop talk, and it subtracts everything the card
already says in its own question, title, topic and tags. It catches "Did you consider
idempotency?" and passes "What changes if that operation gets retried?".

### Sessions stay in `sessions/`, not `interviews/`

The brief suggests an `interviews/<timestamp>-<name>/` directory. The repository already writes
one directory per interview, holding the session file and the scorecard, under `sessions/`.
Renaming it would cost the session-id pattern and the resolved-path containment check, which are
two of the four reasons this tool is safe without a password, and buys nothing.

### The SAP cards were checked against the decompiled library, not the documentation

Ten SAP/JCo cards carried `NEEDS-REVIEW` because the claims could not be settled from public
documentation. The operator supplied the shipping artefacts — `sapjco-3.1.14.jar` and
`sapidoc-3.1.4.jar` — so they were decompiled and read instead. That is a better authority than
the documentation, and it turned out to matter: the code contradicted the cards in eight places.

The two that were simply backwards:

- A card said metadata cached behind a destination is thrown away with it. `RepositoryManager`
  keys repositories by system key and has **no removal method at all**; metadata survives for the
  life of the process. Three cards were built on the wrong claim.
- A card said the turbo metadata path is used only when
  `jco.use_repository_roundtrip_optimization` is switched on. `JCoRuntime` seeds that property
  with `"1"`, and the classic path is taken only when it is explicitly `"0"`. So the function
  module named in a real authorisation error is most likely the opposite of what the card said.

Others: an unset `peak_limit` is `Integer.MAX_VALUE`, so a default destination has one idle
connection and *unbounded* concurrency; `expiration_time = 0` silently disables pooling
altogether; the CPIC keepalive properties reach only the registered-server path, not client
calls, so a card promising them was promising something the client cannot do.

Four flags were resolved outright. `jco.destination.pool_check_connection` exists, is **off by
default** (`JCoRuntime.toBoolean` returns false for a null), and when on makes
`PoolingFactory.getClient` probe with `SAP_CMKEEPALIVE` before handing a connection out — where
`isAlive()` is only a local handle check. A pooled connection is reused without a new logon
because `connect()`, and therefore `RfcOpen`, runs only when the connection is not already open.
A throwing `commit` callback becomes `RFC_FAILURE "Commit fault"` and triggers `rollback` on the
same TID. `JCoCustomRepository` is unchanged in 3.1.

Four flags remain, all genuinely outside the client library: what SAP does at the instant a
client vanishes mid-call, whether the application server times out an idle stateful session, the
tRFC scheduler's re-send timing, and product licensing. A jar cannot settle any of them.

Nobody had opened the IDoc jar. It is far thinner than the cards assumed, which sharpened both of
them: `IDocDocument.getStatus()` is a raw two-character field with no constants or validation
anywhere, so status semantics are entirely ABAP-side; every `JCoIDoc.send` overload takes a TID
and dispatches transactionally, which is the mechanical reason a re-send duplicates; and
`checkSyntax()` exists but `send` never calls it.

### The bank was read card by card, and about a quarter of it was wrong

The validator proves a card is well-formed, not that it is right or that it earns its place. So
every one of the 158 cards was read against the section 8 bar — what capability it tests, what
evidence to collect, what a shallow answer sounds like, what a strong answer adds — and 45 were
changed.

A mechanical pass first ruled out the things a machine can see: no near-duplicates (the closest
of 12,403 card pairs scored 0.198 on shared vocabulary), no copy-paste band prose, no lecture
prompts, no malformed bands. All of that came back clean, which is exactly why the reading pass
was necessary — everything it found was invisible to the checks.

What reading found, and a machine could not:

- **Three cards were factually wrong.** A Kafka schema-evolution card had the compatibility
  direction backwards — an old reader drops a writer field it does not know, so the scenario as
  written could not happen. A Spring card claimed `@Component` on a record fails silently when it
  fails loudly. A Java comparator card used a fifty-row sample, which is *above* the sort's
  insertion-sort threshold, so the card contradicted its own explanation.
- **Cards bled into their neighbours.** A follow-up on one card was another card's weak signal
  verbatim; two cards shared a `lead` band; a Spring follow-up was the self-invocation card in
  substance. Each was invisible from inside the card that contained it.
- **Arithmetic did not add up.** "153 queries" decomposed to 152.
- **Bands did not escalate.** Several `mid` and `senior` bands could have been swapped without a
  reader noticing, which means they were not bands.
- **Tags were subjects, not ideas.** The whole `idempotency` ladder was missing the `idempotency`
  tag, which in this tool is not cosmetic — tags are what carry a session across categories.

Two cross-category duplicates survived their own reviews because each reviewer was told not to
touch the other card, and had to be resolved afterwards: a microservices cascade card that was a
Spring card with a different label, and a JCo pooling card that had drifted onto the
microservices autoscaling card's ground. Both are now distinct; the closest pair in the bank fell
from 0.198 to 0.170 after the pass.

Ten SAP/JCo cards carried `NEEDS-REVIEW`. Four were resolved with verified answers, one new flag
was added for a claim that had been asserted without basis, and the rest were resharpened to name
the exact unverified sentence. Seven remain, which is the honest number.

### The running calibration has memory; the brief's table does not

The brief's section 6 table is a function of one answer, and it is still implemented exactly that
way — `calibrate()` — and still shown as the advice for the answer just given.

Deriving the *running* calibration from that one answer as well was a mistake, and scripted
interviews made it obvious. A candidate whose real level sits between two bands answers above,
then below, then above. The old calibration followed every swing: a strong senior spent twelve of
fourteen questions alternating senior and lead, six `above` and six `one_below`, re-confirming a
ceiling it had already located at question two.

So `track()` replays the whole run and moves one step at a time, and stops once a level was held
and the one above it was not. Four scripted candidates, before and after:

| | before | after |
|---|---|---|
| strong senior, questions to find the ceiling | never | 3 |
| strong senior, categories seen in 20 questions | 2 | 6 |
| junior, consecutive questions in their worst category | 7 | 4 |
| solid mid, questions above their level (ceiling probe) | 0 | 1 |

Three rules earned their place by failing first:

- **Settling had to be reversible.** The first version settled and stayed. A borderline senior
  bracketed at `mid` by one bad topic then answered above it eight times running and was never
  re-tested. Three answers above a settled ceiling now reopen it.
- **The bracket had to be tightened.** "Some level held, some level failed" settles on
  inconsistency — failing one question at a level you otherwise hold is not a wall. Only the
  level immediately above the best held one counts.
- **Breadth had to be forced.** Relatedness alone let a candidate spend a whole interview in one
  category. Four consecutive questions in one category is the cap, and two answers in a row two
  or more bands below leave it at once.
- **Settling needed a floor.** A run that opened in a speciality the candidate had never touched
  bracketed a ceiling off two answers, then spent two more climbing back out of it. Three
  answers minimum.

The same four candidates, run against a pool matching the role, now land where they should:
junior 20, solid mid 50, borderline senior 67, strong senior 90 — and the labels read junior,
mid, senior and lead respectively.

### The pool is part of the measurement

The same four candidates score about a band lower against the whole bank than against a pool
matching the role, because questions from a speciality they have never worked in still count as
evidence. The ordering holds either way, so the tool is not wrong — but the figure only means
what it says if stage 1 selects the categories the job needs. That is now stated in the README
next to the numbers rather than left for an operator to discover.

Rejected: down-weighting categories where a candidate scores badly. It would make the figure
unreproducible by hand, and it would hide exactly the finding an interviewer needs to see.

### The charts are hand-built SVG, and there are three of them

The browser code has no dependencies and no build step, and that is the reason it can be edited
and reloaded. Three chart forms do not justify giving that up, so they are built with
`createElementNS` like everything else is built with `createElement`.

Each form was picked from the job its data does rather than from what looks impressive:

| Data | Form | Why not something else |
|---|---|---|
| One headline value on a fixed scale | Hero figure + a position track | A one-bar bar chart is the classic way to miss the point |
| How far each topic sat from its level | Diverging bars, blue/red, gray at zero | The job is polarity, not magnitude |
| Answers per level/band pair | Heatmap, one hue, more-is-darker | Categorical colour here would burn the free channel on nothing |

The diverging pair was validated against this application's own surfaces rather than eyeballed:
colour-blind separation dE 23.8 light / 25.7 dark, normal-vision dE 31.6 / 31.9, both poles over
3:1 contrast in both modes. The dark-mode sequential ramp is re-stepped for the dark surface, not
flipped, so the "near zero" end recedes towards the background in both modes.

Every chart carries a table with the same figures next to it. A value that can only be reached by
hovering is not reachable at all on a phone, on a printout, or by keyboard.

### Suggestions key off what was answered, not what was queued

The first version excluded every card in the session from the suggestion list. In adaptive mode
that is the same thing, because cards are served one at a time. In every other mode the whole
pool is queued from the first second, so the panel was permanently empty — the feature that
matters most in the brief, silently dead in four of five modes.

Suggestions now exclude the cards that carry a band or a skip, plus wherever the interviewer is
standing. A card further down the plan is a perfectly good thing to offer next, and jumping to it
just moves the position.

The list also widens to the nearest level when the calibrated one is exhausted. "Always visible"
is not satisfied by a panel that empties two-thirds of the way through a pool.

### Questions are ordered by relatedness, in every mode

An interview that jumps from Java concurrency to SAP RFC to Spring transactions costs the
candidate a context switch on every question and costs the interviewer the thread. Every mode
except manual now walks the pool nearest-first, so the session arrives in blocks.

Considered and rejected: a hand-authored ordering per category. It would have to be maintained by
hand across ninety cards, and it would go stale the moment a card was added. The bank already
carries four signals of relatedness — topic, category, explicit links and tags — so the walk uses
those. Nothing new has to be written on a card for it to slot into the right place.

The weights are in `app/affinity.py` with the reasoning next to them. The one that matters: same
topic scores higher than a cross-category link, so a topic is always finished before the run
leaves it.

Adaptive picks the nearest card at the target level rather than, as it did first, the card in a
topic the session had not covered. That earlier rule was the opposite of what is wanted: it
deliberately jumped subjects. The one case where the run does leave a topic is when the
calibration says so after an answer two or more bands below the question — and even then it takes
the nearest exit, not an unrelated card.

Manual mode is untouched. Re-sorting an order somebody picked by hand would throw the work away.

### Next is gated on a band or a skip

Moving on without recording anything loses the evidence silently, and afterwards nobody can tell
a bad answer from a question that was never really asked. `Next` is disabled until the
interviewer has either assigned a band or skipped.

Skip is deliberately not a sixth band. It is the interviewer's decision to move on and says
nothing about the candidate, so it is coloured as a warning, never enters the range or the
profile, and is never counted as a zero. Assigning a band clears a skip, because a band says the
question was answered after all; without that the two flags could both be set and the band would
be dropped from the evidence without a word.

Skipped questions are parked rather than discarded: nothing re-serves them, and a counter at the
bottom right of the interview screen opens the list so any of them can be returned to on purpose.

### Adaptive back-navigation keeps every question already asked

The brief says that going back and changing a rating "re-derives the remaining queue". Taken
literally that would discard questions already asked and rated, because in adaptive mode the queue
only ever holds what has been served.

The tool derives the next target difficulty by replaying every recorded answer in served order. So
revising an old rating changes the next question, and nothing already asked is lost. This meets the
intent and cannot destroy work.

### Four security measures the brief did not ask for

The brief says "no auth" and "binds to 127.0.0.1 only". A loopback bind alone does not make a tool
without authentication safe, because the attacker is the user's own browser. Added:

- a `Host` header check, against DNS rebinding;
- `application/json` required on every request that changes state, so a cross-site form cannot
  reach the tool;
- a strict pattern and a resolved-path check on any session id taken from a URL;
- no CORS headers at all.

These are described in the README under "Security model". Removing any of them removes the reason
the tool is safe without a password.

### Session writes are atomic

The brief requires that killing the server mid-interview loses nothing. A plain write cannot give
that, because opening a file in write mode empties it first. Every write goes to a temporary file
in the same directory, is flushed to the disk, and is then renamed over the target.
`tests/test_crash_safety.py` starts the real server, kills it with `SIGKILL`, restarts it and checks
the state. It also checks that a failure during the write leaves the old file intact.

### Pending edits are flushed before the page can lose them

Autosave is debounced by 500 ms, as the brief describes. On its own that loses the last keystrokes
when the interviewer types and immediately presses `n`. The pending write is flushed before moving
to another question, when the page becomes hidden, and on `pagehide`.

### Hints-off survives a reload

The brief makes hints-off a keystroke. It does not say what happens after a refresh. The setting is
kept in `localStorage`, because the feature exists for screen sharing and a refresh that puts the
answer key back on the display would defeat it. The server also drops the hint fields from the
response when hints are off, so the text is not in the page at all.

### The screen is in the address bar

`#session=<id>` and `#summary=<id>` are written as you move. A reload during an interview returns
to the same question instead of the home screen, and a running interview can be bookmarked.

### Ending the interview stays a click

The brief lists the shortcuts and does not give one to "End interview". None was added. Every other
key changes something that can be changed back. Leaving the question screen by a stray keystroke,
while talking to a candidate, is the one move worth a deliberate click. Everything up to that point
is reachable from the keyboard.

### An extra endpoint: `POST /api/sessions/{id}/goto`

The brief lists `next` but requires navigation to previous questions. One endpoint taking an index
covers previous, next and a jump, and keeps the position on the server where the rest of the state
lives.

### Eight seed questions across four topics

The brief asks for about six across two topics. Four topics exercise the topic filter and the
adaptive rule that prefers an uncovered tag. The questions are real ones, not placeholders.

## Choices where the brief was open

| Question | Choice | Reason |
|---|---|---|
| Markdown inside a question body | Only paragraphs and `- ` bullets are rendered | The bank is a local file, but rendering it as HTML would still be building markup from file content. Everything is inserted as text. |
| Where `exclude_asked_to` is applied | On the server, when the session is created | The browser would have to be trusted to apply it, and the same filter is needed by the preview. |
| Seed when the field is left blank | The server picks one and records it | A run has to be repeatable even when nobody thought about the seed. |
| Session directory name collision | A short random suffix is added | Two interviews with the same candidate and role in the same minute must not share a directory. |
| A question that leaves the bank mid-session | The session keeps the id and the endpoint answers 410 | Losing the rating because a file was renamed would be worse than a clear error. |
| Per-question elapsed time | Pushed to the server every 15 seconds and on every move | A crash then costs at most 15 seconds of one timer, not the whole question. |
| Rating scale wording | Labels on the buttons, with the number as a small key hint | The brief asks for labels. The number is still needed, because the shortcut is the number. |
| Averages in the scorecard | Skipped and unrated questions are left out of the mean | Counting a skip as zero would report a score nobody gave. |
| Tests | `pytest`, in `requirements-dev.txt` | The runtime dependency list in the brief stays at four packages. |

## Deliberately not built

The non-goals in the brief hold: no authentication, no database, no cloud, no npm or build step, no
question editing in the tool, no second user, no candidate view, no generated questions and no
automatic grading.
