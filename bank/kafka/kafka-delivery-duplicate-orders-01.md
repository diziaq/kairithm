---
id: kafka-delivery-duplicate-orders-01
schema_version: 1
title: The duplicates halved and then stopped falling
category: kafka
topic: delivery-semantics
level: mid
tags: [idempotency, retries, failure-modes, correctness]
time_estimate_min: 8
order: 24
links:
  deeper: [kafka-delivery-exactly-once-claim-01]
---

## Ask

Support finds a few orders a week that were acted on twice downstream, always on the nights we
restart brokers for patching. The topic is keyed by order id across six partitions, and last
month the team switched on the producer setting that is meant to stop a retry storing the same
record twice. The rate halved, then stuck. Where are the ones that are left coming from?

## Tests

Whether the candidate can tell a record written to the log twice apart from one record handed to
the application twice, and say which of the two that producer setting touches at all.

## Listen for

- Splits the problem in two — two records sitting in the partition, or one record given to the
  handler twice — and says what they would look at to decide which one support is describing
- Says the producer setting only drops a repeat of a batch the same producer already sent, per
  partition, and only while that process is alive
- Names what gets past it: a pod recycled mid-flight, so the next process is a new sender as far
  as the broker is concerned, or the service itself catching a timeout and calling send again
- Knows a send that timed out may already be stored, so treating it as a failure and sending
  again is exactly how a second record appears
- Brings the group into it: the reading position is written separately from the work, so a member
  that loses its partitions during the restart leaves a position behind what was already handled
- Puts the repair where it can work — an identity carried on the event that the handler or the
  table can check — rather than reaching for another producer setting

## Expected knowledge

- The producer numbers what it sends per partition so the broker can drop a repeat it has already
  stored
- The reading position a group keeps is what the next owner of the partition carries on from
- At-least-once is what you get when the effect and the position are written one after the other

## Strong signals

- Asks support where in the topic the two events sit before theorising about causes
- Asks what the service does when a send times out, and whether anything above it retries the
  whole request
- Says an order event's identity has to be settled when the event is created, not when it is sent

## Weak signals

- Believes that setting makes the pipeline exactly once
- Says repeats are impossible now, so the report must be mistaken
- Cannot say what a timed-out send leaves behind
- Reaches for a nightly clean-up job and stops there

## Answer bands

### weak

- Says the setting should have covered it and offers nothing else.
- Treats a send that timed out as a send that never happened.
- Cannot say what the handler sees when a pod dies partway through a batch.

### junior

- Says the same record can reach the handler more than once, and gives a retry as one cause.
- Knows the reader keeps a place in each partition and that it can go backwards after a restart.

### mid

- Tells two records in the partition apart from one record read twice, and says what they would
  look at to decide which it is.
- Says the setting covers a resend made by that producer inside one process, and names a restart
  or the service's own retry as what escapes it.
- Moves the fix into the handler or the table: a key on the event that a second pass lands on
  instead of writing a new row.

### senior

- Follows one order through the patching window, from the send call to the handler, and says
  which step made the copy.
- Says what the group does when the broker it talks to for that goes away, and which work in
  flight gets done again by somebody else.
- Weighs what a second copy actually costs the business before deciding how much machinery to
  add.

## Follow-ups

- One of the two events came out of a pod that had just been recycled. Does that change your
  answer?
  probes: that a fresh process is a new sender to the broker, so the numbering the setting leans
  on starts over
- The send call timed out, the service logged it as failed and sent the order again. How many are
  in the topic?
  probes: that a timeout says nothing about whether the broker kept it
- Both copies downstream sit at the same place in the same partition. What does that tell you?
  probes: one record delivered twice, which clears the producer and points at where the reader
  left off

## Sources

- https://kafka.apache.org/documentation/#semantics
- https://kafka.apache.org/documentation/#producerconfigs_enable.idempotence
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging

## Notes

Be exact here. The idempotent producer removes duplicates caused by the client retrying a produce
request: the broker tracks a producer id with a sequence number per partition and discards a batch
it has already appended. It does not deduplicate a record the application chooses to send twice,
and a fresh producer instance is issued a new producer id, so it is not protection across a
restart — a configured transactional id changes fencing, not that. It has been on by default since
Kafka 3.0, which is why teams often believe it is doing more than it is.
