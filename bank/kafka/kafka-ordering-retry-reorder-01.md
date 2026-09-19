---
id: kafka-ordering-retry-reorder-01
schema_version: 1
title: A device is stuck offline after a burst of timeouts
category: kafka
topic: ordering
level: senior
tags: [ordering, idempotency, retries, correctness]
time_estimate_min: 9
order: 60
---

## Ask

A producer writes device state changes to one topic, keyed by device id. During a burst of broker
timeouts, support reports a device whose status went to "offline" and stayed there, even though
the last change the service sent was "online". The key was set correctly and only one process
writes that device. What happened?

## Tests

Whether the candidate knows that per-partition sequence can still be broken by the producer's own
retries, and can say precisely what prevents it.

## Listen for

- Names the mechanism: several requests outstanding at once, the first one fails, and it is
  retried after the second has already been written
- Knows `max.in.flight.requests.per.connection` and `retries` together decide whether this is
  possible
- Says an idempotent producer keeps the sequence per partition with up to five requests
  outstanding, because the broker rejects a batch that arrives out of sequence
- Separates this from the reader: the records really are stored in the wrong order, so no
  reader-side sort is an honest fix
- Asks whether the writing process was restarted, and what that does to any sequence it was
  keeping

## Expected knowledge

- A produce request carries a batch, and several can be outstanding on one connection
- `enable.idempotence` exists, and what it is claimed to do

## Strong signals

- States exactly what an idempotent producer prevents — a retried batch being stored twice, and a
  swap within one partition — and what it does not cover
- Suggests carrying a version or a timestamp in the payload so a stale state can be rejected, and
  says why that is a different kind of guarantee
- Asks whether more than one process could ever write the same device

## Weak signals

- Says the broker reordered the records
- Claims the key alone guarantees the sequence
- Proposes sorting inside the consumer without noticing the stored data is already wrong

## Answer bands

### mid

- Says the records were stored in that order rather than shuffled on the way out.
- Connects a failed and retried write to a later write arriving first.

### senior

- Names the two producer settings whose combination allows the swap, and says what each one does.
- States what an idempotent producer guarantees on one partition and where that guarantee stops.
- Rejects a reader-side sort as a fix for data already stored wrongly, or takes it only as a
  stated compromise.

### lead

- Weighs a version field in the payload against tightening the producer, in cost and in who has to
  change their code.
- Says how the team would notice the next occurrence instead of waiting for a support ticket.
- Decides how far this matters for the value of the data involved.

## Follow-ups

- They fix it by allowing only one request in flight at a time. What did that cost them?
  probes: throughput, and whether they know a cheaper option exists
- The service is scaled to three copies behind a load balancer, any of which may handle a given
  device. Does your fix still hold?
  probes: that a per-process sequence number says nothing across processes
- What would you put on a screen so nobody has to phone support next time?
  probes: observability of the failure rather than only the fix

## Sources

- https://kafka.apache.org/documentation/#producerconfigs_enable.idempotence
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging

## Notes

Be precise if the candidate is: an idempotent producer removes duplicates caused by its own
retries and keeps the per-partition sequence, with up to five requests outstanding. It says
nothing about two separate processes writing the same key.
