---
id: kafka-delivery-acks-min-isr-01
schema_version: 2
title: Signing off the durability of a payments topic
category: kafka
topic: delivery-semantics
level: lead
tags: [consistency, operations, failure-modes, api-design]
time_estimate_min: 12
order: 82
links:
  shallower: [kafka-delivery-exactly-once-claim-01]
  related: [kafka-transactions-zombie-fencing-01]
---

## Ask

You are asked to sign off the durability setup for a payments topic. Replication factor is three,
`min.insync.replicas` is two, producers use `acks=all`. A broker is taken down for patching next
week. What are you actually promising the business, and where does the promise break?

## Tests

Whether the candidate can separate the number of copies, the confirmation the producer waits for
and the minimum in-sync set, and say what each one does during a real outage.

## Ideal minimal answer

With three copies, a floor of two and producers waiting on every copy currently in sync, a write
the producer was told about is on at least two brokers, so the patch window survives; below the
floor the partition refuses writes rather than quietly taking a fragile one. Then say what the
paying caller does with a refused write, and who is allowed to accept less.

## Listen for

- Separates the three: how many copies exist, how many must confirm before the producer is told,
  and how few in-sync copies make the partition refuse writes
- Says that with three copies and a minimum of two, one broker down still takes writes; when two
  of a partition's copies fall behind, produce requests fail rather than quietly accepting a
  fragile write
- Knows `acks=all` waits for the copies currently in sync, not for every copy in the assignment,
  which is why the minimum has to be set as well
- Says an unclean leader election would trade the promise for availability, and asks whether it is
  enabled
- Talks about what the producer does when writes are refused: retries, a filling buffer, and
  back-pressure reaching the caller

## Expected knowledge

- A copy drops out of the in-sync set when it falls too far behind the leader
- A produce request waiting for all in-sync copies fails when that set is smaller than the
  configured minimum
- The minimum is set on the topic and is unrelated to how many copies the topic has; it is only
  consulted when the producer is waiting for all of them

## Strong signals

- Points out that with the minimum at one, waiting for all in-sync copies promises nothing beyond
  the leader's own copy, because the set is allowed to shrink to the leader and writes still
  succeed
- Notices that a producer asking only for the leader's confirmation bypasses the minimum
  altogether, so one team's client setting can undo the topic's guarantee
- Asks where the three copies physically sit before calling them three independent failures
- Says what the calling service sees when the topic refuses writes, and whether that is acceptable
  for payments

## Weak signals

- Uses the number of copies and the confirmation setting interchangeably
- Believes `acks=all` waits for every copy in the assignment
- Cannot say what happens when the in-sync set falls below the minimum

## Answer bands

### mid

- Describes each of the three settings separately and roughly correctly.
- Says one broker down is survivable with this setup.

### senior

- Says exactly when produce requests start failing, and what the producer does at that moment.
- Explains why the confirmation setting on its own does not deliver the promise without the
  minimum.
- Asks where the copies are placed before treating three as three independent failures.

### lead

- States the promise in business terms: what is lost, and under which combination of failures.
- Decides what the calling service should do when the topic refuses writes, and who is told.
- Names the condition under which they would accept a weaker setup, and what they would watch.

## Follow-ups

- A second broker in the same rack goes down during the patch window. What does the calling
  service see?
  probes: writes refused, and what the caller is supposed to do with that
- Someone proposes tightening the setup so that all three copies must be in step before a write is
  taken. Talk me through next week.
  probes: that a stricter minimum removes all tolerance for a single failure
- The team turns on the option that lets a copy which has fallen behind take over when no current
  one is left. What have they agreed to?
  probes: unclean leader election, and silent data loss, without being handed the term
- One of the teams publishing to this topic changes its client so that a single copy having the
  record is enough for it to move on. Does the promise you signed off still hold?
  probes: that the topic-level floor is only consulted for producers waiting on the whole in-sync
  set, so a single client setting can quietly undo it

## Sources

- https://kafka.apache.org/documentation/#replication
- https://kafka.apache.org/documentation/#topicconfigs_min.insync.replicas
- https://kafka.apache.org/documentation/#design_uncleanleader

## Notes

The three settings are independent and candidates routinely merge them. Replication factor is how
many copies exist; `acks` is what the producer waits for; `min.insync.replicas` is the point at
which the partition stops accepting writes. `acks=all` means all copies *currently in sync*, not
every copy in the assignment, which is why it is meaningless without the minimum — the in-sync
set may legitimately be one.

Two further points to hold a candidate to. `min.insync.replicas` is a topic (or broker default)
setting and carries no relationship to the replication factor: setting it to three on a topic
with three copies removes all tolerance for a single failure, and setting it above the
replication factor makes the partition unwritable. And it is enforced only for producers waiting
on all in-sync copies — `acks=1` or `acks=0` ignores it entirely, so the topic-level guarantee
depends on every client asking for it.
