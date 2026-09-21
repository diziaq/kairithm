---
id: kafka-partitioning-widen-live-topic-01
schema_version: 2
title: Doubling the partition count on a live topic
category: kafka
topic: partitioning
level: lead
tags: [operations, ordering, consistency]
time_estimate_min: 10
order: 80
links:
  related: [kafka-rebalancing-stateful-restore-01]
---

## Ask

An order-events topic has run on six partitions for two years. Throughput has outgrown it and
someone proposes going to twenty-four partitions next Tuesday. You own the decision. What do you
weigh, and how would you actually carry it out?

## Tests

Whether the candidate treats the partition count as a published contract with every reader of the
topic rather than a capacity dial that can be turned at will.

## Ideal minimal answer

A key is mapped over the live count, so from Tuesday a key lands somewhere new while its older
records stay where they are, and any reader keeping state per key sees that key from two places.
Choose between widening this topic and standing up a replacement at the new width, name who has
to be told and what they change, and say how it is backed out.

## Listen for

- Says the key is mapped over the live count, so a given key stops landing where it used to
- Points out that per-key sequence holds only inside one partition, so records for one order can
  sit in two places at once after the change
- Knows the count can be raised on an existing topic but never lowered
- Asks who reads the topic and whether any reader keeps state built up per key
- Names the alternative: stand up a replacement topic at the new width and cut over, rather than
  growing this one
- Asks whether the width is really the limit, or whether one slow handler is

## Expected knowledge

- A keyed record is placed by a hash of the key over the current count
- A group cannot usefully run more members than there are partitions on the topic

## Strong signals

- Asks what the cleanup policy is, and notices that widening a compacted topic leaves an old value
  for a key stranded where nobody will look for it again
- Wants a quiet window or a drain first, and can say how they would know the topic is drained
- Asks what the reporting store is keyed by before agreeing to anything

## Weak signals

- Treats it as a one-line admin command with no effect on readers
- Believes existing records are redistributed when the count grows
- Cannot say what a reader holding per-key state would do with the same key arriving elsewhere

## Answer bands

### mid

- Says the count can only be raised, and that new records for a key may land somewhere new.
- Notes that a reader keeping something per key will now see that key from two places.

### senior

- Walks one key through the change and says where each of its records sits before and after.
- Asks what state each reader keeps, and what a drain or a cutover would have to look like.
- Questions whether the width is the real limit before agreeing to change it at all.

### lead

- Chooses between growing this topic and standing up a replacement, and states the condition that
  decides which.
- Names who has to be told, what they have to change, and how the whole thing is backed out.
- Says what they would watch for a week afterwards to know it worked.

## Follow-ups

- One reader keeps a running total per customer in local storage. What does its output look like
  on Tuesday afternoon?
  probes: whether per-key state survives the change; the two-places problem made concrete
- The week after, someone asks to go back to six. What do you tell them?
  probes: that the count cannot be lowered, and what the real escape route is
- The billing team is one of the readers. What do you need from them before Tuesday?
  probes: treats the count as a contract with other teams rather than an internal setting

## Sources

- https://kafka.apache.org/documentation/#basic_ops_modify_topic
- https://kafka.apache.org/documentation/#compaction

## Notes

Adding partitions does not move records that are already stored. Everything written before the
change stays where it is; only the placement of new records changes.
