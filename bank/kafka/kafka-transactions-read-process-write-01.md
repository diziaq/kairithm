---
id: kafka-transactions-read-process-write-01
schema_version: 1
title: A reader still sees records that were rolled back
category: kafka
topic: transactions
level: senior
tags: [transactions, correctness, consistency, performance]
time_estimate_min: 10
order: 64
links:
  deeper: [kafka-transactions-zombie-fencing-01]
  related: [kafka-offsets-external-store-01]
---

## Ask

A consumer reads topic A, writes a derived record to topic B, and sends its position through the
same producer transaction. The writing side has been reviewed and is correct. A downstream team
still reports acting on records from transactions that were rolled back. What is missing?

## Tests

Whether the candidate knows that the effect of a transaction on a reader depends on the reader,
and can say what the broker actually stores for a transaction that was rolled back.

## Listen for

- Says the records from a rolled-back transaction are written into the partition and filtered out
  at read time, not removed
- Names the reading side's isolation setting as the missing piece, and knows which behaviour is
  the default
- Knows a reader configured for `read_committed` cannot go past the last stable point, so it takes
  on a delay
- Says sending the position through the producer is what makes the output and the position land
  together
- Points out that such a reader's apparent lag now includes anything an open transaction is
  holding back

## Expected knowledge

- A transaction covers records produced to topics in the cluster and the positions sent through it
- The producer carries an identity that lets a restarted one displace its own earlier incarnation

## Strong signals

- Says what one transaction left open does to every careful reader of that partition
- Points out the guarantee stops at the edge of the cluster, so a database write inside the loop
  is not covered
- Raises the latency and rate cost before recommending the arrangement anywhere else

## Weak signals

- Believes a rolled-back record is never written at all
- Thinks switching the producer on is sufficient for everybody
- Cannot say what the reading side has to do differently

## Answer bands

### mid

- Says the reading side has a setting deciding whether it sees output that was never confirmed.
- Connects the position travelling with the writes to why the loop is safe to run again.

### senior

- States that records from a rolled-back transaction are physically in the partition and filtered
  when read.
- Describes the delay the careful reader takes on, and where it comes from.
- Says what is inside the boundary and what is not, naming an external write as outside it.

### lead

- Weighs the added latency and reduced rate against what a duplicate would actually cost.
- Says what breaks operationally when one transaction is left open, and who notices first.
- Decides which parts of a pipeline are worth this machinery and which are not.

## Follow-ups

- One writing instance opens a transaction and is then frozen for ten minutes. What does the
  downstream team see meanwhile?
  probes: the stable point stalls, records are held back, lag appears to grow
- The same loop also writes a row into Postgres between the read and the write. Is that row
  covered?
  probes: where the edge of the guarantee is
- The team measures how many records a second the loop handles before and after, and it drops.
  Where did it go?
  probes: the markers written per transaction, smaller batches, and the extra round trips

## Sources

- https://kafka.apache.org/documentation/#consumerconfigs_isolation.level
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging

## Notes

The two non-obvious facts to hold the candidate to: records belonging to a transaction that was
rolled back are appended to the partition and filtered on read, and the default on the reading
side is to return them. Transactions are not opt-in for readers automatically.
