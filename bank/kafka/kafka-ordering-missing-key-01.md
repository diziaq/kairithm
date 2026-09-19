---
id: kafka-ordering-missing-key-01
schema_version: 1
title: An account was closed before it was opened
category: kafka
topic: ordering
level: junior
tags: [ordering, correctness, failure-modes]
time_estimate_min: 6
order: 12
links:
  deeper: [kafka-ordering-retry-reorder-01]
---

## Ask

A service publishes account events to a topic with six partitions and sets no key on them. A
downstream reader complains that for one account it handled the "closed" event before the
"opened" one. Is Kafka broken?

## Tests

Whether the candidate knows the exact scope of the ordering guarantee and can connect it to how
the producer chose where to put each record.

## Listen for

- Says the sequence is guaranteed inside one partition, not across a topic
- Connects the absent key to the two events for one account being stored in different places
- Says putting the account identifier in the key would keep that account's events together and in
  sequence
- Notices the reader holds several partitions at once and works through them independently, so
  interleaving between them is expected

## Expected knowledge

- A partition is an append-only sequence and a reader walks it front to back
- A record with no key is not pinned to any one partition

## Strong signals

- Asks whether the two events were even produced in that order before blaming the transport
- Points out that pinning an account to one place costs the ability to spread that account's load
- Asks whether the two events came from the same process at all

## Weak signals

- Says a topic delivers records in the order they were sent
- Proposes sorting by timestamp inside the reader as the first and only fix
- Blames the number of partitions without ever mentioning the key

## Answer bands

### weak

- Asserts that a topic hands records over in the order they were sent.
- Suggests a fix without naming what decides where a record goes.
- Treats the report as a defect in the broker.

### junior

- States that the sequence holds inside one partition only.
- Ties the missing key to the two events landing in different places.
- Proposes keying on the account so its events stay together.

### mid

- Describes what a reader holding several partitions at once does, and why the mixing is legal.
- Names the cost of tying one account to one place.
- Checks the produce side first rather than assuming anything was shuffled in transit.

## Follow-ups

- They set the key and it mostly stops, but one account still does it about once a week. Where
  would you look?
  probes: producer-side retries, or two writers for the same account
- They ask whether running the whole topic on one partition would settle it for good. What do you
  say?
  probes: whether they can price a guarantee instead of simply granting it
- Two different services both publish events for the same account. Does keying fix that?
  probes: that a per-partition sequence says nothing about which writer got there first

## Sources

- https://kafka.apache.org/documentation/#intro_topics
- https://kafka.apache.org/documentation/#semantics
