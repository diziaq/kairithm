---
id: kafka-partitioning-second-writer-other-client-01
schema_version: 2
title: The same key, two writers, two partitions
category: kafka
topic: partitioning
level: senior
tags: [correctness, ordering, failure-modes, configuration]
time_estimate_min: 9
order: 70
links:
  deeper: [kafka-partitioning-widen-live-topic-01]
---

## Ask

An order topic has been written by one Java service for two years, keyed on the order id. Last
month a second team added a writer in Python for a subset of orders — same topic, same key. Since
then a downstream reader that keeps a running total per order has been reporting wrong figures,
and only ever for orders that came through the new writer. What is your first hypothesis?

## Tests

Whether the candidate knows that where a record lands is worked out by the producing client
before the record is ever sent, so "same key, same place" is something every writer has to agree
to rather than something the topic provides.

## Ideal minimal answer

Where a record lands is worked out inside the producing process, so the two writers put one order
id in two places: either the key becomes different bytes, or the same bytes go through a
different rule. The new writer has to place records the way the old one does, and what is already
written stays put and is repaired as data.

## Listen for

- Asks which client library the new writer uses, and whether it places records the same way as
  the old one
- Says the placement is decided in the producing process, before anything leaves it, so two
  writers can disagree about where one key belongs
- Names the two things that must match for two writers to agree: how the key becomes bytes, and
  what is then done with those bytes to pick a number
- Says the running total for one order is now being built in two places by two readers, neither
  of which ever sees the whole order
- Asks whether the key is byte-for-byte identical in both writers before reaching for anything
  cleverer — an id carried as text in one and as a number in the other is enough on its own
- Would settle it by looking at where one specific order's records actually sit, rather than
  arguing about libraries
- Knows the repair is to make the new writer place records the way the old one does, and that
  what is already written stays exactly where it was put

## Expected knowledge

- A keyed record is placed by hashing the key over the current partition count
- The rule that does the hashing is a choice made on the producer, not a property of the topic
- A record's position relative to others is only defined within one partition

## Strong signals

- Asks whether the topic is compacted, and sees that two records for one key in two partitions
  both survive, so the compacted view of that key stops being a single value
- Points out that the same fault arrives from a second Java service carrying a rule of its own, or
  from anything that names the destination outright — the language is a clue, not the cause
- Wants the placement rule written down and tested by both teams, not repaired once in one
  repository
- Says what the repair looks like for the orders already split in two, and treats that as data to
  be put right rather than a setting to be changed
- Asks how long the new writer has been live, because that bounds how much has to be repaired

## Weak signals

- Says one key can only ever be in one place, so the report must be wrong
- Blames the cluster, or the readers being reassigned
- Proposes raising the partition count
- Tells the reader to sort or de-duplicate afterwards without asking why the records are apart

## Answer bands

### weak

- Asserts that one key can only ever be in one place, so the report must be a mistake elsewhere.
- Blames the cluster, or a recent reshuffle of work among the readers.
- Proposes changing the partition count.

### mid

- Asks what the new writer is built on, and whether the key is constructed the same way in both.
- Says the two writers may be putting one order in two places, leaving the reader with two halves
  of a total.
- Looks at where one order's records actually sit before changing anything.

### senior

- States that the placement is computed inside the producing process, so agreement between
  writers is arranged rather than inherited.
- Separates the two ways writers can disagree: different bytes for the key, and a different rule
  applied to the same bytes.
- Names what has to change in the new writer, and says the records already written do not move.
- Says how the orders that are already split get put right, and how far back that reaches.

### lead

- Makes the placement rule a contract both teams test against, rather than a fix in one codebase.
- Says what would have caught this in the week it started instead of after a month of wrong
  figures.
- States what the topic's owner has to publish so the next team to write to it does not repeat it.

## Follow-ups

- They correct the new writer and deploy on Friday. On Monday one of the affected orders is still
  wrong. Why?
  probes: that what was already written does not move; the remaining work is data repair

- The same thing turns up two months later and this time both writers are Java. Where do you look?
  probes: whether they see the language as a clue rather than the cause — a rule of its own, or a
  destination named outright

- The order id is numeric. One writer carries it as text and the other as a number. Does that
  matter here?
  probes: the bytes, before anything is done with them — whether they get there unprompted

- Somebody proposes that every writer simply names the destination itself, so there is nothing to
  disagree about. What have you signed up for?
  probes: that this pins the topic's width into every producer, and what widening then costs

## Sources

- https://kafka.apache.org/documentation/#producerconfigs_partitioner.class
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-794%3A+Strictly+Uniform+Sticky+Partitioner
- https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md

## Notes

This is not a trivia test about hash functions. A candidate who says "I would check that both
clients place a key the same way, and check the key bytes first" has the answer. The specifics
below are the interviewer's background, to be released if asked and never demanded.

Verified: the Java producer places a keyed record with a murmur2 hash of the key bytes taken
modulo the partition count. Verified: librdkafka — which the Confluent Python, Go, .NET and C++
clients are built on — defaults its `partitioner` to `consistent_random`, a CRC32 hash of the key,
and offers `murmur2_random`, which its own documentation describes as functionally equivalent to
the Java default. So the two disagree until somebody changes one of them.

`kafka-python` is a third implementation again, with its own default. Check which hash a given
client uses rather than assuming from the language — that is the whole lesson of the card, and
assuming Python means CRC32 is the same error in the other direction.

KIP-794 changed how records *without* a key are batched and placed; records with a key are still
placed by hashing the key over the current count. Do not let that be conflated.

Keep this on the producing side. How many readers can work in parallel belongs to the
consumer-groups card, and changing the partition count of a live topic belongs to the harder card
on this topic — here the fault is created before the record is ever sent.
