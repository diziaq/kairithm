---
id: kafka-offsets-external-store-01
schema_version: 1
title: Keeping the read position next to the data
category: kafka
topic: offsets
level: senior
tags: [consistency, transactions, observability, operations]
time_estimate_min: 10
order: 62
---

## Ask

A consumer reads a topic with twelve partitions and writes aggregates into Postgres. Someone
proposes storing the read position for each partition in the same Postgres transaction as the
aggregate, instead of sending it back to Kafka. Would you let them, and what breaks if you do?

## Tests

Whether the candidate can move the commit boundary into the sink deliberately, and name what
stops working once the position no longer lives in the cluster.

## Listen for

- Sees that one database transaction covering both the aggregate and the position makes a repeat
  harmless for this sink
- Knows the consumer must then seek to the stored position whenever partitions are handed to it,
  rather than resuming from the group's own record
- Says lag figures and any tool that reads the group's recorded position go blind or report
  nonsense
- Points out the position has to be kept per partition and re-read every time the work moves
- Notes the group still has to exist to divide the partitions up, even though its recorded
  position is no longer the truth

## Expected knowledge

- A listener runs when partitions are taken away from a member and when new ones are given to it
- Lag is computed from the end of a partition minus the position recorded for the group

## Strong signals

- Asks what happens the very first time, when the table is empty, and what the consumer should do
  then
- Names the operational cost: whoever is on call now has a second place to look
- Says plainly that the guarantee covers this one sink and nothing else the consumer touches

## Weak signals

- Calls the result exactly-once with no qualification
- Forgets that work moves between members, so the stored position has to be re-read
- Does not notice that any monitoring breaks

## Answer bands

### mid

- Sees that putting the position in the same write makes a repeat harmless for this table.
- Says the consumer has to start from what the table says rather than from where the group left
  off.

### senior

- Describes the seek per partition when work is handed over, and what has to run when it is taken
  away.
- Names lag monitoring as the first casualty and says what they would put in its place.
- States which sink the guarantee covers, and that a second sink gets nothing from it.

### lead

- Weighs this against a plain repeatable write and says which teams could maintain each.
- Decides from who carries the pager and how many places the consumer writes to.
- Says what would have to become true for them to go back to the ordinary arrangement.

## Follow-ups

- A partition is handed to a different pod in the middle of the afternoon. What does that pod have
  to do before it touches a single record?
  probes: re-reading the stored position for that partition before consuming
- The on-call screen has shown zero for this group for a week and nobody noticed. Why?
  probes: what the lag figure is actually computed from
- The consumer starts writing to a search index as well as the table. What still holds?
  probes: that the boundary covers exactly one store

## Sources

- https://kafka.apache.org/documentation/#semantics
- https://kafka.apache.org/28/javadoc/org/apache/kafka/clients/consumer/ConsumerRebalanceListener.html

## Notes

The group is still used to divide partitions among members; only the source of truth for the
position moves. Candidates often miss that the group's own recorded position then goes stale,
which is what silently breaks the lag dashboards.
