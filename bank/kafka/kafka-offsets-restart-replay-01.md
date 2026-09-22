---
id: kafka-offsets-restart-replay-01
schema_version: 2
title: A restarted consumer replays a week of records
category: kafka
topic: offsets
level: junior
tags: [operations, failure-modes, correctness]
time_estimate_min: 6
order: 16
links:
  deeper: [kafka-offsets-commit-window-01]
  related: [microservices-retries-storm-after-outage-01]
---

## Ask

A consumer is restarted after a routine deploy and immediately starts working through records
from a week ago, flooding a downstream API. Nothing was purged, the topic is unchanged, and the
code diff was one log line. What could cause that?

## Tests

Whether the candidate knows where a group's reading position lives, and what happens when there
is no position for it to resume from.

## Ideal minimal answer

The group's position is stored in the cluster, one per partition, and the consumer carries on
from it, so a week of replay means there was no usable position for it: most likely a new or
changed group id, with `auto.offset.reset` set to `earliest`. Records stay in the topic whether
or not anyone has read them.

## Listen for

- Asks what group id the new deployment uses, since a group nobody has seen before has no stored
  position
- Knows `auto.offset.reset` is consulted only when there is no usable stored position for a
  partition — none at all, or one that no longer falls inside what the topic still holds — and
  that `earliest` produces exactly this
- Says the setting is never consulted on an ordinary restart with a valid stored position, so the
  question is what happened to that position
- Distinguishes the position stored for the group in the cluster from anything kept on the pod
- Asks whether positions were being recorded at all before the restart

## Expected knowledge

- A group's position is stored in the cluster, one per partition
- Records stay available until they age out, whether or not anyone has read them
- A stored position that has aged out, or that points before the start of what the topic still
  holds, is treated the same as having none

## Strong signals

- Asks whether the group id is built from something that changes on deploy, such as a hostname
- Points out the flooding is a second defect: the reader had no limit on its own rate either
- Asks how long the stored position itself survives when a group goes quiet

## Weak signals

- Believes a record disappears once it has been read
- Thinks the position lives only in the consumer's memory or on its disk
- Cannot say what a brand new group does the first time it starts
- Recounts a replay at a previous job and never says what to check on this consumer

## Answer bands

### weak

- Believes reading a record removes it, so a replay means something is broken.
- Names no place where a group's position is kept.
- Suggests clearing the topic.

### junior

- Says the position is stored per partition for the group, and the group carries on from it.
- Names a new or empty group id, plus the setting that decides where an unknown group begins.
- Knows records stay available regardless of who has read them.

### mid

- Asks whether the deploy changed the group id, and how that id is put together.
- Says that setting only comes into play when there is no usable position, so something must have
  removed or invalidated one.
- Checks whether positions were being recorded at all before the restart.
- Treats the flood as its own defect without being asked, and says what should have held it
  back.

## Follow-ups

- The group id definitely did not change. What else would put them back at the start of the week?
  probes: an expired stored position, a manual seek, or a tool someone ran
- What should happen the very first time a brand new reader starts on a busy topic?
  probes: whether they see the choice as a product decision rather than a default
- Next week they want to deliberately work through the last two days again. How would you do it
  safely?
  probes: a fresh group, or moving the position on purpose, and protecting whatever is downstream

## Sources

- https://kafka.apache.org/documentation/#consumerconfigs_auto.offset.reset
- https://kafka.apache.org/documentation/#brokerconfigs_offsets.retention.minutes
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-211%3A+Revise+Expiration+Semantics+of+Consumer+Group+Offsets

## Notes

Two things candidates state too broadly. `auto.offset.reset` is not "where a consumer starts"; it
is the fallback for a partition with no usable committed position, which means either no stored
offset for the group or one that is out of range for what the topic still holds. An ordinary
restart of a healthy group never reaches it.

How long a stored position survives is version-dependent and worth hedging rather than asserting:
the broker default was raised from a day to seven days in Kafka 2.0, and since KIP-211 offsets
for a group with live members are not aged out while the group is active — the clock starts when
the group empties. A candidate who says "it depends on the broker setting and the version" is
answering better than one who quotes a number.
