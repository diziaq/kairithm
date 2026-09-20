# The question format

One card is one file: `bank/<category>/<id>.md`. Markdown with a YAML frontmatter block.

Copy `bank/_template.md`, edit it, save, reload the browser. That is the whole workflow. The
tool reads the bank fresh on every request and never writes to `bank/`.

Check your work at any point:

```bash
.venv/bin/python -m app.validate
```

---

## Where each field lives, and why

Short machine-read values go in the **frontmatter**: they are filtered on, sorted by and linked
through.

Everything a human reads goes in a **`##` section**. Prose about a technical topic is full of
colons, hashes and backticks, and putting it in YAML would mean hand-quoting every line. The
sections are also what the interview screen renders directly.

---

## Frontmatter

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | slug | yes | Stable unique identity. Lower-case words joined by single hyphens. |
| `schema_version` | integer | yes | Currently `1`. |
| `title` | string | yes | Short label for lists, navigation and the scorecard. |
| `category` | enum | yes | `general`, `java`, `spring`, `microservices`, `kafka`, `database`, `sap-jco`. Must match the directory. |
| `topic` | string | yes | Narrower area inside the category: `concurrency`, `transactions`, `delivery-semantics`. |
| `level` | enum | yes | `junior`, `mid`, `senior`, `lead`. The seniority **the question** aims at. |
| `tags` | list | no | Free-form. Used for filtering, and to chain related cards — see below. |
| `time_estimate_min` | integer | no | Rough minutes. Drives the pacing display. |
| `order` | integer | no | Position in sequential mode. Cards without it sort last. |
| `links` | mapping | no | See [Links](#links). |
| `allow_term_leak` | boolean | no | Silences the follow-up leak warning. See [Follow-ups](#follow-ups). |

## Sections

| Heading | Fills | Required | Read aloud |
|---|---|---|---|
| `## Ask` | `question` | yes | **yes — the only section that is** |
| `## Tests` | `tests` | yes | no |
| `## Listen for` | `listen_for` | yes | no |
| `## Answer bands` | `answer_bands` | yes | no |
| `## Expected knowledge` | `expected_knowledge` | no | no |
| `## Strong signals` | `strong_signals` | no | no |
| `## Weak signals` | `weak_signals` | no | no |
| `## Follow-ups` | `follow_ups` | no | the question text only |
| `## Notes` | `notes` | no | no |
| `## Sources` | `sources` | no | no |

`## Ask` fills the field called `question`. The heading says what to do with the text; `question`
is the name used in the API, in `session.json` and in every validator message.

Any other `##` heading is kept and shown under its own title, so a card can carry something the
schema did not anticipate without being rejected.

Bullet sections are read as bullets. A line indented under a bullet continues it. A section
written as a paragraph instead becomes a single item rather than an error.

### Tags carry weight

Tags are not only a filter. The tool serves questions in blocks by relatedness, and a shared tag
is the only signal that connects two cards in different categories. Tag a card with the ideas it
shares — `idempotency`, `correctness`, `transactions`, `retries` — and not only with its
technology, or the run will jump from the end of one category to an unrelated one.

Explicit `links:` are stronger than any tag. Same topic is stronger still, so a topic is always
finished before the run moves on.

### A topic that spans all four levels is worth more than a topic with two cards

Adaptive mode climbs and drops the level as the interview goes. When a topic has a card at every
level the run can follow a candidate up and down *inside one subject*, which is both a better
conversation and better evidence. 12 topics currently span junior → mid → senior → lead; most of the rest
span three or two. If you are deciding where to add a card, completing a ladder beats starting a
new topic.

Check any topic with:

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from app.bank import load_bank
b = load_bank()
print(sorted({q.level for q in b.questions.values()
              if q.category=='java' and q.topic=='concurrency'}))
"
```

---

## IDs

`java-concurrency-happens-before-01`

The set of categories is not fixed in code — it is the set of directories under `bank/`. Adding
a category means adding a directory and cards whose `category` field matches its name; nothing
else has to change. Keep the list short enough that an interviewer can pick from it in one
glance.

Roughly `<category>-<topic>-<subject>-<number>`, but the only hard rule is lower-case words
joined by single hyphens.

**An id is never reused and never renumbered.** Other cards link to it, and finished sessions on
disk record it. Renaming an id silently breaks every link pointing at the card and disconnects
old scorecards from the bank. The file name is only a convention — the validator warns if it
disagrees with the id, and nothing breaks if you move the file.

If a card is wrong, edit it or delete it. Do not recycle its id for a different question.

---

## Level and band — do not collapse these

- **`level`** is a property of the *question*: the seniority it is pitched at.
- **`answer_bands`** describe how a *candidate* might answer it.

The bands are `weak`, `junior`, `mid`, `senior`, `lead`. `weak` has no matching level, so the two
scales meet at `junior`.

During an interview the interviewer assigns a band from what they heard. The tool compares that
band against the question's level and suggests where to go next. A `mid` band on a `senior`
question means drop down or move sideways — not another `senior` question on that topic.

**Nothing in the tool ever assigns a band.**

### Writing bands

Include only the bands that are meaningful for that card. A junior question usually needs
`weak`, `junior`, `mid`; inventing a `lead` band for a simple question just adds noise. A lead
question may start at `mid`.

Every bullet must describe **observable behaviour** — something the candidate says or does.

Rejected by the validator:

```markdown
### senior

- Excellent understanding.
```

Accepted:

```markdown
### senior

- Explains the underlying mechanism, not just the API surface.
- Discusses what happens under load or during a failure.
```

The check is crude on purpose: a bullet made only of verdict words (`good`, `solid`,
`understanding`, `competent`, …), or shorter than three words, is an error. If a real bullet is
caught by it, the bullet is probably still too vague to be useful six months later.

---

## Follow-ups

Follow-ups are **probes inside the current question**, not new questions. They exist for when an
answer is on the right track but left something out.

They must lead the candidate to elaborate **without handing over the term**.

| | |
|---|---|
| Good | "What changes if that operation gets retried?" |
| Bad | "Did you consider idempotency?" |

Two to four per card. Each may carry an interviewer-only `probes:` line saying what it is meant
to surface. **`probes` is never read aloud** — it is shown in italics next to the follow-up on
the interview screen, and it is the one place where naming the concept is correct.

```markdown
## Follow-ups

- The consumer dies after the row is written but before it reports its position. What does the
  table look like when it comes back?
  probes: at-least-once behaviour, and whether they reach for a repeatable write
```

### The leak check

The validator warns when a follow-up repeats a distinctive term from `Listen for`,
`Expected knowledge` or a band. It only flags terms that actually give something away:
backticked identifiers, hyphenated compounds, internally capitalised names, and long words that
are not ordinary English. Vocabulary the card already uses in `## Ask`, its title, topic or tags
is never flagged — a follow-up has to be able to refer to its own subject.

It is a **warning**, never an error. If a card exists specifically to test whether the candidate
knows a word, set `allow_term_leak: true` and say so in `## Notes`.

---

## Links

Cards reference each other by id. Never paste another card's content.

```yaml
links:
  deeper:       [java-concurrency-safe-publication-01]   # harder, same topic
  shallower:    [java-concurrency-thread-basics-01]      # foundational, same topic
  related:      [kafka-delivery-ordering-01]             # same level, adjacent topic
  prerequisite: [java-memory-model-basics-01]            # should be understood first
```

**Inverses are derived at load time.** Writing `deeper: [B]` on card A is enough for B to offer A
as `shallower`; `related` works both ways. You declare each edge once, in whichever file it reads
more naturally.

The validator reports:

- a link pointing at an id that is not in the bank — **error**;
- a card linking to itself — **error**;
- a pair where *both* files declare `deeper` (or both `shallower`) at each other — **error**,
  because the two files disagree and one of them is wrong;
- `deeper` pointing at a card of a lower level — **warning**.

The interview screen lets the interviewer follow any link at any moment, and jump to any card in
the whole bank whether it is linked or not.

---

## A complete card

```markdown
---
id: kafka-delivery-exactly-once-claim-01
schema_version: 1
title: A team claims their pipeline is exactly once
category: kafka
topic: delivery-semantics
level: senior
tags: [transactions, correctness, consumers]
time_estimate_min: 8
order: 30
links:
  related: [java-concurrency-visibility-flag-01]
---

## Ask

A team tells you their Kafka pipeline is exactly once, end to end, and lands every event in a
Postgres table. What do you ask them before you believe it?

## Tests

Whether the candidate treats a delivery guarantee as a property of a specific boundary that
somebody has to implement, rather than a setting switched on for a whole system.

## Listen for

- Asks where the consumer records its progress relative to the database write
- Knows a Kafka transaction stops at the edge of the cluster

## Expected knowledge

- Offset commits, and that the committed position is what a new owner resumes from

## Strong signals

- Asks about the schema of the target table before asking about configuration

## Weak signals

- Accepts the claim because a configuration property is set

## Answer bands

### weak

- Repeats the claim back, or names a configuration property as the whole answer.

### mid

- Asks about the ordering of the database write and the offset commit.
- Describes what happens when the process dies in the window between them.

### senior

- Puts the boundary in the right place and says what the guarantee covers on each side.
- Lets the cost of the damage set how much machinery is worth building.

### lead

- Weighs transactions against a repeatable write in throughput and who gets paged.

## Follow-ups

- The consumer dies after the row is in Postgres but before it reports its position. What does
  the table look like after it comes back?
  probes: at-least-once behaviour, and whether they reach for a repeatable write
- Suppose a repeat costs almost nothing to the business. Does your answer change?
  probes: whether the cost of the damage drives how much machinery is justified

## Sources

- https://kafka.apache.org/documentation/#semantics

## Notes

A Kafka transaction covers records produced and offsets committed within the cluster. It does
not extend to an external store.
```

---

## Running the validator

```bash
.venv/bin/python -m app.validate            # the shipped bank
.venv/bin/python -m app.validate path/to/bank
.venv/bin/python -m app.validate --quiet    # errors only
```

Exit code is `1` if there is any error, `0` if there are only warnings. It is also asserted by
the test suite (`tests/test_validate.py`), and the same list appears on the tool's home screen —
a card that fails is reported there, never quietly missing from the bank.

Each line names the file, the card id and the field:

```
error: bank/java/java-gc-pauses-01.md [java-gc-pauses-01] (links.deeper): `deeper` points at
  'java-gc-tuning-02', which is not a card in the bank
warning: bank/kafka/kafka-rebalance-01.md [kafka-rebalance-01] (follow_ups): follow-up 'Did you
  consider idempotency?' names idempotency, which the guidance is waiting to hear; describe the
  situation instead, or set `allow_term_leak: true` if the card exists to test the word
```

| Severity | Meaning |
|---|---|
| `error` | The card is unusable, or the bank is inconsistent. Fix before committing. |
| `warning` | Worth a look. The card still loads and is served normally. |

---

## Evolving the schema

`schema_version` is checked on every card. A card declaring a version this tool does not read is
reported as an error rather than being parsed on a guess. To change the shape of a card, raise
`SCHEMA_VERSION` in `app/bank.py`, teach the loader both shapes, and migrate the bank in one
commit.
