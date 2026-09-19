You are extending an existing interview-assistant repository.

Your task: inspect the repository, understand its architecture and conventions,
then extend it into a practical interview question-bank and session system.

The repository is the source of truth for implementation decisions. Do not
impose a new architecture. Reuse existing structure, naming, tooling and
idioms. Introduce new abstractions only when they solve a real problem you
can name.

Work in the stages defined in section 0. Stop where instructed. Do not run
ahead.

================================================================
# 0. STAGES AND STOP POINTS
================================================================

## Stage A — Discovery (no code changes)

Inspect and write up:

1. Full repository structure.
2. How the frontend is built and served; how static assets reach the browser.
3. Whether a backend/server process exists, and what it can do
   (in particular: can it write to the filesystem?).
4. Existing persistence of any kind (files, browser storage, anything).
5. Any existing question / card / session / deck format already present.
6. Current extension points: routing, state management, data loading.
7. How the project is run, built, linted and tested. Which test runner.
8. Dependency constraints: what is already available that you should reuse
   rather than adding (YAML parser, markdown renderer, schema validator,
   router, state library).

Output a short written architecture summary (not a file dump).

Then propose:
- the card storage format you chose, and why it fits THIS repo;
- where sessions will be persisted, and why that is possible in THIS repo;
- the directory layout you intend to add.

**STOP. Report and wait for approval before writing code.**

## Stage B — Schema and loader

Implement the schema, the loader, the validator, and the schema
documentation. Add 3 pilot cards only (one Java junior, one Java senior,
one Kafka senior) to exercise the format.

**STOP. Report and wait for approval.**

## Stage C — UI integration

Browse, preview, session start, in-session view, adaptive navigation,
session persistence, scorecard export.

**STOP. Report and wait for approval.**

## Stage D — Full initial question bank

Author the remaining cards per section 7.

**STOP. Final report per section 18.**

================================================================
# 1. GUIDING PRINCIPLE
================================================================

**Filesystem is the knowledge base. The UI is the session layer.**

The question bank must be:
- plain text, human-readable, hand-editable;
- stored in the repository and diff-friendly in Git;
- loadable by the browser without a build step wherever possible;
- completely independent from interview session data.

An engineer with no access to the UI must be able to copy a card file, edit
it in any text editor, reload the browser, and see the new question.

You choose the concrete format (YAML / Markdown+frontmatter / JSON) based on
what already exists in the repository and what parsers are already
available. Justify the choice in Stage A. Do not add a database.

================================================================
# 2. CARD SCHEMA
================================================================

Define exactly ONE card schema. Include a `schema_version` field so the
format can evolve.

Required fields:

| Field              | Meaning |
|--------------------|---------|
| `id`               | Stable unique slug, e.g. `java-concurrency-happens-before-01`. Never reused, never renumbered. |
| `schema_version`   | Integer. |
| `title`            | Short human label for lists and navigation. |
| `question`         | The text the interviewer actually asks. |
| `category`         | Top-level bucket: `general`, `java`, `spring`, `microservices`, `kafka`, `sap-jco`. |
| `topic`            | Narrower area within the category, e.g. `concurrency`, `transactions`, `delivery-semantics`. |
| `level`            | Target seniority of the question: `junior` \| `mid` \| `senior` \| `lead`. |
| `tests`            | One sentence: what capability this question actually probes. |
| `answer_bands`     | See section 3. |
| `listen_for`       | Concrete technical concepts whose presence indicates real understanding. |

Optional fields:

| Field               | Meaning |
|---------------------|---------|
| `tags`              | Free-form list for filtering. |
| `expected_knowledge`| Concepts the candidate is expected to have. |
| `strong_signals`    | Not required for a pass, but indicate depth or real production experience. |
| `weak_signals`      | Typical memorised, shallow or actively wrong answers. |
| `follow_ups`        | See section 4. |
| `links`             | See section 5. |
| `time_estimate_min` | Rough minutes. |
| `notes`             | Interviewer-only context, caveats, common misconceptions. |
| `sources`           | Reference links, where the claim is non-obvious. |

Do not make a field mandatory unless it is genuinely useful on every card.

## Schema documentation

Create a documentation file (e.g. `docs/question-format.md`) covering:
- every field, its type, and allowed values;
- a complete annotated example card;
- a minimal copy-paste template for a new card;
- how IDs are constructed and why they must never change;
- how links work;
- how the answer-band model works and how to write good bands;
- the validation command and how to read its errors.

A developer must be able to create a valid new question by copying the
example and editing it, without reading any source code.

================================================================
# 3. ANSWER-BAND MODEL
================================================================

**Critical distinction, do not collapse these two concepts:**

- `level` = the seniority the QUESTION is aimed at.
- `answer_bands` = observable descriptions of how a candidate might ANSWER it.

Bands: `weak`, `junior`, `mid`, `senior`, `lead`.

Rules:

1. Include only the bands that are meaningful for that question. A junior
   question usually needs `weak`, `junior`, `mid` — inventing a "lead" band
   for a trivial question produces noise. A lead question may start at `mid`.
2. Every band must describe **observable behaviour**, not a verdict.

   Forbidden: `senior: excellent understanding`.

   Required, e.g.:
```
   weak:
     - Recites a definition with no example.
     - Confuses the mechanism with a superficially similar one.
   junior:
     - States the basic definition correctly.
     - Gives one simple working example.
   mid:
     - Explains the main trade-offs.
     - Names common failure cases from experience.
   senior:
     - Explains the underlying mechanism, not just the API surface.
     - Discusses operational consequences under load or failure.
   lead:
     - Connects the topic to system design decisions.
     - Chooses between alternatives based on stated constraints.
     - Explains the organisational or maintenance cost of each option.
```
3. The interviewer assigns a band from evidence. The system never assigns one.
4. The tool collects evidence. It does **not** produce a hire/no-hire
   recommendation, a numeric composite score, or a percentile. Do not build
   one, even if it seems helpful.

================================================================
# 4. FOLLOW-UP QUESTIONS
================================================================

Follow-ups are **contextual probes within the current question**, not new
questions. They exist for the case where the candidate's answer is on the
right track but omitted something specific.

They must guide the candidate to elaborate without handing them the term.

Good:  "What changes if that operation gets retried?"
Bad:   "Did you consider idempotency?"

(The second is acceptable only if the explicit purpose of the card is to
test whether the candidate knows the word `idempotency` — mark such cards
with a note.)

**Apply this mechanical check to every follow-up you write:**

> If the follow-up contains a term that appears in `expected_knowledge`,
> `listen_for`, or `answer_bands` for that card, it leaks the answer.
> Rewrite it to describe the *situation* instead of naming the *concept*.

Each follow-up should optionally record what it is trying to surface
(`probes:`), so the interviewer knows why they are asking it. That field is
interviewer-facing and must never be read aloud.

2–4 follow-ups per card. Prefer ones that branch naturally from a plausible
partial answer.

================================================================
# 5. LINKS AND NAVIGATION
================================================================

Cards reference each other by ID only. Never embed another card's content.

Supported link types:

```
links:
  deeper:       [ ... ]   # harder question, same topic
  shallower:    [ ... ]   # foundational question, same topic
  related:      [ ... ]   # same level, adjacent topic
  prerequisite: [ ... ]   # should be understood first
```

Symmetry rule: if A lists B under `deeper`, B should list A under
`shallower`. The validator must report asymmetric pairs. You may either
auto-derive the inverse at load time or require it explicitly — pick one,
document it, and be consistent.

The UI must let the interviewer jump along any of these links at any time.

================================================================
# 6. ADAPTIVE NAVIGATION
================================================================

This is the feature that matters most. Implement it precisely.

During a question, the interviewer marks the answer with a band
(`weak` | `junior` | `mid` | `senior` | `lead`).

The system compares the **assessed band** against the **question's level**
and surfaces suggestions:

| Assessed band vs question level | Suggest |
|--------------------------------|---------|
| Two or more below              | `shallower`, or a lower-level question in the same topic. Consider changing topic. |
| One below                      | `shallower`, or same-level `related` in a different topic |
| Equal                          | `related` at the same level, or `deeper` to probe the ceiling |
| Above                          | `deeper`; raise the default level for subsequent questions in this topic |

Concretely: a `mid` answer to a `senior` question means the next question
should **not** be another `senior` question on that topic. Drop down or move
sideways. The point is to keep the candidate in a productive zone and to find
their ceiling efficiently, not to repeatedly confirm a failure.

Hard constraints:

- Suggestions are **always visible and always optional**. Never auto-advance.
- The interviewer can ignore every suggestion and pick any question from the
  whole bank at any moment.
- Leaving the planned sequence and returning to it must not lose any state:
  notes, bands, and follow-up usage are all preserved.
- Track and display a running "current calibration" (the level the system
  would suggest next) so the interviewer can see the bar moving, and override
  it manually.

The system is an assistant. It never conducts the interview.

================================================================
# 7. INITIAL QUESTION BANK
================================================================

Three conceptual tiers, applied across categories:

- **Warm-up / general** — technical maturity across contexts: debugging
  approach, trade-off reasoning, production incidents, design reasoning,
  testing philosophy, code review, dealing with legacy.
- **Topic** — a technology or engineering area.
- **Deep-dive** — specialist knowledge within a topic.

Counts (Stage D):

### General / warm-up — 8 cards
Spread across levels. These open the conversation and calibrate before
entering a specific technology.

### Java — 20 cards (5 each: junior, mid, senior, lead)
Spread across areas; do not stack five cards on one topic. Cover:
collections, concurrency, the memory model, JVM internals and GC, exceptions,
generics, performance and profiling, API design, testing, runtime behaviour.

### Spring — 16 cards (4 per level)
Dependency injection, bean lifecycle, configuration and profiles,
transactions and propagation, proxying and its limits, Spring Boot
auto-configuration, web layer, persistence, testing, production
troubleshooting.

### Microservices architecture — 16 cards (4 per level)
Service boundaries, consistency models, distributed transactions and sagas,
failure handling, idempotency, observability, retries and backoff, messaging,
API evolution and versioning, scalability, operational ownership.

### Kafka — 16 cards (4 per level)
Partitioning, ordering guarantees, consumer groups, offsets and commits,
delivery semantics, rebalancing, retries, dead-letter patterns, transactions
and exactly-once, schema evolution, performance and tuning.

### SAP / JCo — 16 cards (4 per level)
RFC fundamentals, sRFC, tRFC, qRFC, JCoDestination, JCoRepository,
JCoFunction, connection management and pooling, stateful JCo sessions, BAPI,
IDoc, SAP-side troubleshooting, work processes, performance, and real
integration failure modes seen on the customer side.

**SAP/JCo accuracy guard:** use the terminology exactly. Do not invent
SAP-specific behaviour to make a question sound advanced. If you are not
confident a technical claim is correct, either omit the card or write it and
mark it `notes: NEEDS-REVIEW — unverified claim about <X>`. A flagged card is
acceptable; a confidently wrong one is not. Cite `sources` for non-obvious
claims.

================================================================
# 8. QUESTION QUALITY BAR
================================================================

Every card must earn its place. For each one you must be able to state:
what capability it tests, what evidence the interviewer should collect, what
a shallow answer looks like, and what a strong answer adds.

Reject:
- trivia and pure memorisation ("what is the default initial capacity of X");
- questions with no useful discriminating power between levels;
- near-duplicates of another card;
- questions so broad they cannot be evaluated ("tell me about microservices").

Prefer questions that open naturally into follow-ups and branch to other
cards.

================================================================
# 9. UI
================================================================

Add the smallest coherent set of features. Match the existing UI's patterns
and styling; do not introduce a new design system or component library.

**Browse** — list and filter by category, topic, level, tags. Free-text search.

**Preview a card** — question, interviewer guidance, answer bands,
follow-ups, linked questions. Clearly separate what is read aloud from what
is interviewer-only.

**Start an interview** — capture candidate name, role, selected categories/
topics, target level, question count, and selection mode. Support at least:
1. sequential
2. random
3. difficulty-based (ascending within selected topics)
4. adaptive (section 6)

**During an interview** — current question, interviewer hints, answer bands,
one-tap band assignment, free-text evidence notes per question, follow-ups
(with a record of which were used), suggested deeper / shallower / related
next questions, skip, and jump-to-any-question.

**Resume** — reloading the browser mid-interview must restore the session
exactly. Make this explicit and test it.

================================================================
# 10. SESSION PERSISTENCE
================================================================

Sessions are stored separately from the question bank, one unit per
interview. If the repository has a backend that can write files, prefer a
per-interview directory:

```
interviews/
  2026-09-19T16-42-10-john-doe/
    session.<ext>
    scorecard.md
```

If there is no such backend, persist in the browser and provide an explicit
export that produces the same file set for committing. Decide in Stage A and
justify it.

A session records: candidate name, role, start/end timestamps, interviewer,
selected question IDs, actual order asked, assigned band per question,
evidence notes, follow-ups used, skipped questions, free-text interviewer
comments, and final assessment.

Store question IDs, not full question definitions. Snapshot only the minimum
needed for historical integrity if a card later changes — at least the card
`id` plus the `question` text as asked, so an old session stays readable.

================================================================
# 11. SCORECARD
================================================================

Export a human-readable Markdown scorecard: metadata, topics covered,
questions asked with assigned bands, evidence, strong areas, weak areas,
gaps where no evidence was collected, follow-up items for the next round,
and the interviewer's final written assessment.

**Keep facts separate from conclusions, structurally:**

```
Evidence:
- Candidate explained consumer-group rebalancing.
- Mentioned partition ownership and offset commit timing.

Assessment (interviewer):
- Solid Kafka operational knowledge.
```

Everything under Evidence is what was observed. Everything under Assessment
is the interviewer's own words. The system never writes into the Assessment
section and never promotes its own suggestions into evidence.

================================================================
# 12. MANUAL EDITING WORKFLOW
================================================================

The application must never become the only way to modify the bank. This
workflow must work and must be documented:

```
copy an existing card file
edit the fields
save
refresh the browser
the new question appears
```

If the repo's build pipeline makes hot reload impossible, document the one
command required and keep it to one command.

================================================================
# 13. VALIDATION
================================================================

Provide a validator runnable as a single command (wired into the existing
scripts/test setup). It must catch at least:

- missing or malformed `id`
- duplicate `id` across the whole bank
- missing `question` text
- invalid `level`, `category`, or band name
- links pointing to non-existent IDs
- asymmetric `deeper` / `shallower` pairs
- empty or verdict-only answer bands (e.g. a band whose text is just "good")
- follow-ups that leak a term from `listen_for` / `expected_knowledge`
  (report as a warning, not an error)
- unparseable card files

Errors must name the file, the card ID, and the field. A malformed card must
surface as a visible error — in the CLI and in the UI — and must never be
silently dropped from the bank.

================================================================
# 14. TESTS
================================================================

Use the repository's existing test runner and conventions. Small,
deterministic, no network. Cover:

- loading and parsing card files
- schema validation, including each failure mode in section 13
- duplicate ID detection
- link resolution and symmetry
- each selection strategy
- difficulty ordering
- adaptive navigation: assert the suggestion table in section 6 directly,
  including the mid-answer-to-senior-question case
- session persistence and resume-after-reload
- scorecard generation

================================================================
# 15. ANTI-GOALS
================================================================

Do not:
- add a database, ORM, or migration system;
- call any LLM or external API at runtime;
- add authentication, user accounts, or multi-tenancy;
- rewrite the build system, switch frameworks, or restructure existing code
  beyond what the integration requires;
- auto-assign answer bands or generate a hire recommendation;
- auto-advance the interview without interviewer action;
- add a dependency that duplicates something already in the repo;
- generate the full question bank before the schema is approved in Stage B.

================================================================
# 16. NON-NEGOTIABLE CHECKS BEFORE FINISHING
================================================================

- every card validates
- every ID unique and stable
- every link resolves, pairs symmetric
- every category and level from section 7 populated to the stated counts
- every card has observable, non-verdict answer bands
- no follow-up leaks its own answer (run the section 4 check over all cards)
- adaptive navigation demonstrably follows the section 6 table
- a card can be added by hand and appears after reload
- browser reload mid-interview loses nothing
- a completed interview produces a readable Markdown scorecard
- no database or unnecessary infrastructure introduced
- existing tests still pass

================================================================
# 17. FINAL REPORT
================================================================

No generic project-management summary. Report exactly:

1. What you found in the existing repository — architecture, conventions,
   constraints that shaped your decisions.
2. The architecture you chose and why, including format and persistence
   decisions and what you rejected.
3. The card schema, as the actual documented fields.
4. UI features added and where they attach to the existing UI.
5. Categories and cards added, with counts per category and level.
6. Tests and validation run, and their actual output.
7. Deliberate limitations, known gaps, cards flagged NEEDS-REVIEW, and
   recommended follow-up work.
