---
id: kafka-offsets-restart-replay-01
schema_version: 1
title: A restarted consumer replays a week of records
category: kafka
topic: offsets
level: junior
tags: [operations, failure-modes, correctness]
time_estimate_min: 6
order: 16
links:
  deeper: [kafka-offsets-commit-window-01]
---

## Ask

A consumer is restarted after a routine deploy and immediately starts working through records
from a week ago, flooding a downstream API. Nothing was purged, the topic is unchanged, and the
code diff was one log line. What could cause that?

## Tests

Whether the candidate knows where a group's reading position lives, and what happens when there
is no position for it to resume from.

## Listen for

- Asks what group id the new deployment uses, since a group nobody has seen before has no stored
  position
- Knows `auto.offset.reset` decides what a group does when it has no stored position for a
  partition, and that `earliest` produces exactly this
- Distinguishes the position stored for the group in the cluster from anything kept on the pod
- Asks whether positions were being recorded at all before the restart

## Expected knowledge

- A group's position is stored in the cluster, one per partition
- Records stay available until they age out, whether or not anyone has read them

## Strong signals

- Asks whether the group id is built from something that changes on deploy, such as a hostname
- Points out the flooding is a second defect: the reader had no limit on its own rate either
- Asks how long the stored position itself survives when a group goes quiet

## Weak signals

- Believes a record disappears once it has been read
- Thinks the position lives only in the consumer's memory or on its disk
- Cannot say what a brand new group does the first time it starts

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
- Checks whether positions were being recorded at all before the restart.
- Treats the flood as its own defect and says what should have held it back.

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
