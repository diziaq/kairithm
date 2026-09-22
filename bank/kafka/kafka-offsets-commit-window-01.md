---
id: kafka-offsets-commit-window-01
schema_version: 2
title: A handful of duplicate rows after every deploy
category: kafka
topic: offsets
level: mid
tags: [idempotency, correctness, failure-modes]
time_estimate_min: 8
order: 42
links:
  deeper: [kafka-offsets-external-store-01]
  related: [kafka-retries-delay-topic-ordering-01]
---

## Ask

Every time this consumer is redeployed, the team finds a handful of duplicate rows in the target
table — never many, always some. The consumer writes each record to the table and lets the client
record its position on a timer. Walk me through how one of those duplicate rows is created.

## Tests

Whether the candidate can place the recording of the position relative to the side effect and
describe the exact window a shutdown has to land in.

## Ideal minimal answer

The rows go into the table and the process stops before the position is recorded, so whoever
picks the partition up starts behind and writes those rows again. The recording runs on a timer
while records are being fetched, so it never lines up with what the handler finished; the repair
is a write that lands on the same row instead of a new one.

## Listen for

- Describes the sequence: fetch a batch, write the rows, record the position; a shutdown between
  the write and the recording brings those records back
- Knows an automatic commit happens on a timer while fetching, so what is recorded does not line
  up with what the handler has finished
- Says the repeat is by design, and the fix belongs in the write rather than in the recording
- Names a keyed or conditional write, so a repeat lands on the same row instead of making a new
  one
- Asks whether shutdown is graceful, and whether anything is recorded on the way out

## Expected knowledge

- The recorded position is where the next owner of that partition carries on from
- At-least-once is what you get unless the effect and the position move together

## Strong signals

- Points out that recording first and writing afterwards swaps duplicate rows for missing ones,
  and asks which the business would rather have
- Notices that "always some, never many" matches one batch in flight rather than a systemic fault
- Asks what natural identity the row already has before inventing one

## Weak signals

- Proposes recording after every single record as a complete fix
- Believes an automatic commit confirms that the records were handled
- Suggests a nightly clean-up job and stops there
- Lays out duplicate rows against missing rows and will not say which the team should take

## Answer bands

### weak

- Calls it a defect in the client library.
- Cannot describe the order of the write and the recording of the position.
- Says duplicates are unavoidable and moves on.

### mid

- Walks the batch through: rows written, process stops, position not yet recorded, same records
  again.
- Says a timer-driven recording does not line up with what the handler actually finished.
- Proposes a write that can be repeated without changing the result.

### senior

- Puts a bound on the damage: at most one batch, set by how often the position is recorded.
- Raises the mirror-image failure before it is put to them — recording first and losing rows — and
  asks which one the business can live with.
- Says where the natural identity of the row comes from, rather than inventing a new column.

## Follow-ups

- They switch to noting the position by hand after each row is written. Did the duplicate rows go
  away?
  probes: the window shrinks but never closes, and what it costs in rate
- Another team has the opposite complaint after their deploys: rows missing. What are they doing
  differently?
  probes: the mirror failure, where the position is recorded before the effect
- The target table has no column of its own that is unique. What do you write into it?
  probes: whether they reach for the record's coordinates or for a business key

## Sources

- https://kafka.apache.org/documentation/#semantics
- https://kafka.apache.org/documentation/#consumerconfigs_enable.auto.commit
