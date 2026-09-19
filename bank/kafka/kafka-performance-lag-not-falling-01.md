---
id: kafka-performance-lag-not-falling-01
schema_version: 1
title: Lag climbs all day and clears itself at midnight
category: kafka
topic: performance
level: senior
tags: [performance, observability, operations]
time_estimate_min: 10
order: 68
links:
  deeper: [kafka-performance-mixed-workloads-01]
---

## Ask

A consumer group's lag climbs steadily from nine in the morning and only clears around midnight.
Adding pods has not helped, processor use on the pods sits at thirty per cent, the brokers are
quiet, and the topic has twelve partitions. Where do you take this?

## Tests

Whether the candidate can localise a shortfall across the arrival rate, the number of partitions,
the fetch and the handler, using evidence rather than a list of settings.

## Listen for

- Establishes first whether records simply arrive faster than the group can handle them, by
  comparing the two rates directly
- Asks whether the lag sits on all twelve partitions or a few, which separates skew from capacity
- Asks how many pods there are against the twelve partitions, since that caps how many can help
- Reads low processor use alongside a growing backlog as time spent waiting on something else,
  and says what to measure next
- Asks how many records come back per fetch, and whether the handler makes one blocking call per
  record

## Expected knowledge

- Lag is the distance between the end of a partition and the position recorded for the group
- A partition is handled by one member, so pods beyond the partition count do nothing

## Strong signals

- Wants the spread of the handler's duration, not its mean
- Asks whether the clearing at midnight is simply arrivals falling away rather than anything
  getting faster
- Refuses to touch fetch or batch settings until they know where the time is going

## Weak signals

- Suggests more pods again
- Reaches for client settings before knowing where the time goes
- Cannot say what lag is measured from

## Answer bands

### mid

- Compares how fast records arrive with how fast they are handled.
- Checks whether the pods already outnumber the twelve partitions.

### senior

- Separates skew on a few partitions from a shortfall across the whole group, and names the graph
  that would tell them apart.
- Reads low processor use with a growing backlog as waiting, and says what they would measure
  next.
- Notices the overnight clearing is explained by arrivals falling off, not by the group speeding
  up.

### lead

- Sets out the order they would investigate in, and what each step rules out.
- Decides between widening the topic, batching the outbound calls and shedding load, from what the
  measurement shows.
- Says what should have alerted somebody at ten in the morning instead of at midnight.

## Follow-ups

- The handler makes one database call per record and waits for the answer. What would you try?
  probes: batching, concurrency inside the handler, and what each costs in sequence
- The graph shows two of the twelve partitions carrying the entire backlog. Does that change your
  plan?
  probes: skew, and that total capacity was never the problem
- What would you have wanted on a screen so this was noticed at ten rather than at midnight?
  probes: alerting on the trend and the rate of change rather than on a threshold

## Sources

- https://kafka.apache.org/documentation/#monitoring
- https://kafka.apache.org/documentation/#intro_consumers
