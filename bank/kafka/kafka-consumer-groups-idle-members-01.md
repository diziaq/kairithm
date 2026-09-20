---
id: kafka-consumer-groups-idle-members-01
schema_version: 1
title: Six pods, three partitions, three doing nothing
category: kafka
topic: consumer-groups
level: junior
tags: [operations, performance, failure-modes]
time_estimate_min: 6
order: 14
links:
  deeper: [kafka-consumer-groups-flapping-member-01]
  related: [kafka-partitioning-hot-partition-01, microservices-retries-storm-after-outage-01]
---

## Ask

A team is behind on a topic, so they scale their consumer deployment from three pods to six. Lag
does not move at all, and three of the pods log nothing from the moment they start. The topic has
three partitions. What do you tell them?

## Tests

Whether the candidate knows what a group hands out to its members, and what actually limits how
wide a consumer can be scaled.

## Listen for

- Says a partition is the unit handed out, so a group cannot put more members to work than the
  topic has partitions
- Says the three extra pods are given nothing and sit there holding a place in the group
- To go wider they need more partitions, or more work done per record inside each pod
- Asks whether all six pods really share the same group id

## Expected knowledge

- A group divides the partitions of the subscribed topics among its members
- Two separate groups on one topic each get their own full copy of the records

## Strong signals

- Asks whether the lag is spread evenly or sitting on one partition, before suggesting anything
- Points out that the extra pods are not free, because each one arriving makes the group hand
  everything out again
- Asks how long one record takes to handle, since that may be the real ceiling

## Weak signals

- Suggests scaling further
- Believes records are handed out one at a time to whichever pod is free
- Cannot say what a member with nothing assigned to it does

## Answer bands

### weak

- Suggests adding more pods, or blames the broker for not sharing the work.
- Describes records as being dealt out one at a time to free workers.
- Has no account of why three pods would be silent.

### junior

- States that a partition goes to exactly one member, so three members can never be busy here.
- Says the number of partitions caps how many pods can do anything.
- Suggests raising the partition count, or making each pod do more per record.

### mid

- Asks whether the lag sits on one partition, which would point somewhere else entirely.
- Notes that every pod arriving or leaving makes the group redistribute, so scaling is not free.
- Separates "not enough readers" from "each record takes too long".

## Follow-ups

- Someone suggests giving each pod its own group id so that they all get work. What happens then?
  probes: that a second group gets a full copy of everything, not a share
- They add partitions, lag finally falls, and a report that used to be right is now wrong. What
  changed?
  probes: connects the width change back to per-key sequence
- The three busy pods each take four hundred milliseconds per record. Is adding partitions still
  the right move?
  probes: whether they can locate the limit in the handler rather than in the topic

## Sources

- https://kafka.apache.org/documentation/#intro_consumers
