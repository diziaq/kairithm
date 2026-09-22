---
id: kafka-retries-delay-topic-ordering-01
schema_version: 2
title: A delay topic that reorders the account
category: kafka
topic: retries
level: mid
tags: [retries, ordering, correctness]
time_estimate_min: 8
order: 46
links:
  related: [kafka-dead-letter-unread-topic-01]
---

## Ask

To stop one bad record blocking a partition, a team moves any record that fails onto a separate
topic, which a second consumer reads five minutes later and tries again. The records are account
updates, keyed by account. What did they just give up?

## Tests

Whether the candidate sees that taking a record off its partition takes it out of sequence, and
can say for which kinds of update that is survivable.

## Ideal minimal answer

They gave up sequence for the account: the delayed record is applied five minutes late, after
updates for the same account that were written after it. That is tolerable when an update carries
the whole value and wrong when it is a change relative to the current one. Ask what happens when
the second attempt fails as well.

## Listen for

- Says the delayed record is now applied after updates for the same account that came later
- Asks whether an update carries the whole value or a change relative to the current one, because
  the second kind cannot be applied out of sequence
- Points out the main partition is unblocked, which was the goal, and the sequence is the price
- Suggests a version or a timestamp in the payload so a stale update can be rejected on arrival
- Asks what happens when the second attempt fails as well, and whether the wait grows

## Expected knowledge

- Records for one key stay in sequence only while they stay on their own partition
- A second topic has its own partitions and its own reader, with no relationship to the first

## Strong signals

- Separates updates that can be applied in any order from ones that cannot, and says which
  workloads may use this pattern at all
- Asks whether the original failure was even temporary, since a permanent one will simply circle
- Mentions holding back later records for that same account instead of letting them past

## Weak signals

- Sees only the benefit
- Says it is fine because the record was not lost
- Cannot say what happens to a later update for the same account

## Answer bands

### weak

- Says nothing is lost because the record is still somewhere.
- Cannot describe what happens when a later update for the same account arrives first.
- Treats the pattern as universally safe.

### mid

- States that the delayed record is applied out of sequence for its account.
- Names, once given an example of a relative change, the kind of update this breaks and the kind
  it does not.
- Asks what happens when the second attempt fails too.

### senior

- Puts a condition on the pattern: safe when an update carries the whole value and the reader can
  reject a stale one.
- Offers unasked the alternative of holding everything for that account back instead, and prices
  it.
- Asks whether the failure was temporary at all, and what stops a permanent one circling forever.

## Follow-ups

- The update in question is "add fifty to the balance", not "set the balance to two hundred". Does
  the plan still work?
  probes: whether they can say why a relative change cannot be applied out of sequence
- The second attempt fails as well. Where does the record go now?
  probes: bounded attempts, growing waits, and a final resting place
- An auditor asks you to prove no account ever ended on the wrong figure. What would you show
  them?
  probes: whether the design leaves any evidence behind at all

## Sources

- https://kafka.apache.org/documentation/#intro_topics
