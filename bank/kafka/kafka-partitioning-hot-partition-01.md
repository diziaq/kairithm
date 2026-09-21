---
id: kafka-partitioning-hot-partition-01
schema_version: 2
title: One partition takes eighty per cent of the traffic
category: kafka
topic: partitioning
level: junior
tags: [performance, ordering, observability]
time_estimate_min: 6
order: 10
links:
  deeper: [kafka-partitioning-second-writer-other-client-01]
  related: [kafka-ordering-missing-key-01]
---

## Ask

A topic has twelve partitions and the team runs twelve consumer pods. The dashboard shows one
partition taking about eighty per cent of the records, one pod falling further behind all day,
and the other eleven pods nearly idle. What is going on, and what do you look at first?

## Tests

Whether the candidate can connect the record key to the partition a record lands in, and sees
why adding more pods cannot move this particular graph.

## Ideal minimal answer

The record key decides where a record is stored, so one dominant key value puts eighty per cent
of the traffic in one place. That partition is read by exactly one member of the group, so no
extra pod can be pointed at it. Ask what the key is and how the values are spread before
changing anything.

## Listen for

- Asks what is used as the record key, and whether one value dominates the traffic
- Says the key decides where a record lands, so every record carrying the same key goes to the
  same place
- Knows a partition is read by exactly one member of a group, so no other pod can help with the
  busy one
- Notes that records with no key are spread out instead, and asks whether a key was needed here
  at all

## Expected knowledge

- A record carries an optional key, and that key selects where the record is stored
- Each partition of a subscribed topic is handled by one member of the group at a time

## Strong signals

- Asks to see the spread of key values before touching any setting
- Points out that raising the count moves existing keys somewhere else, which is its own problem
- Separates a skewed key from a slow handler as two causes of the same shape of graph

## Weak signals

- Suggests starting more pods in a group that already has one per partition
- Proposes raising the partition count as the whole fix, without ever looking at the key
- Describes the spread of load as random

## Answer bands

### weak

- Blames the broker or the network without asking what is inside the records.
- Proposes starting more pods, with no account of who reads what.
- Describes the load as arriving randomly and landing wherever there is room.

### junior

- Names the key as what decides where a record is stored.
- Says one dominant key value explains a single busy partition.
- Says no amount of extra capacity can be pointed at the busy partition, because one member reads
  it from end to end.

### mid

- Asks for the spread of key values, and how many distinct ones there are, before proposing a fix.
- Explains that raising the count changes where existing keys land, and says what that costs.
- Separates a skewed key from a slow handler, and says which graph would tell them apart.

## Follow-ups

- Overnight someone doubles the number of partitions. What can a reader that keeps a running
  total per customer no longer rely on?
  probes: that the mapping from key to partition moves, and what that does to per-key sequence
- Suppose the records carried no key at all. Would the graph look the same?
  probes: whether they know what happens when there is nothing to hash
- The busy key is one large customer that the business will not let you split. What now?
  probes: whether they can move that workload aside instead of trying to rebalance the hash

## Sources

- https://kafka.apache.org/documentation/#intro_consumers
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-480%3A+Sticky+Partitioner

## Notes

Records with no key are not strictly round-robined in current clients: the default partitioner
sticks to one partition until a batch is sent, then picks another. Either answer is fine here —
what matters is that the candidate knows a keyless record is not pinned for life.
