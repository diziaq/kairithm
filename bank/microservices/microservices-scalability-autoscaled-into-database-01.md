---
id: microservices-scalability-autoscaled-into-database-01
schema_version: 1
title: Forty instances, twenty connections each, one database
category: microservices
topic: scalability
level: mid
tags: [performance, failure-modes, operations, correctness]
time_estimate_min: 8
order: 210
links:
  deeper: [microservices-scalability-one-tenant-dominates-01]
---

## Ask

Traffic triples, your service autoscales from four instances to forty, and the database starts
refusing connections almost immediately. Each instance holds a pool of twenty. What happened, and
what do you change?

## Tests

Whether the candidate sees that scaling a stateless tier multiplies its demand on the shared tier
behind it, and can bound that demand.

## Listen for

- Does the arithmetic: forty times twenty is eight hundred, against a limit that is very likely a
  few hundred
- Scaling out moved the bottleneck rather than removing it; the shared thing behind is now the
  constraint
- Bounds the total rather than the per-instance number — a pool shared in front of the database,
  or a per-instance size derived from the maximum fleet size
- Raising the database limit is not free: each connection costs memory and adds contention inside
  the database
- Asks whether the work was database-bound in the first place, because if it was, more instances
  were never going to help
- Notes that a small pool with an internal queue is often better than a large pool, and says what
  that trades

## Expected knowledge

- A connection pool reserves capacity whether or not it is in use
- A database has a hard ceiling on concurrent connections, set well below what is healthy

## Strong signals

- Points out that the autoscaler and the database limit are two settings owned by two teams with
  no relationship between them
- Asks what the scaler is keyed on and whether that signal has anything to do with the bottleneck
- Wants to know the useful concurrency of the database before choosing any number

## Weak signals

- Raises the database connection limit and calls it done
- Blames the autoscaler and pins the instance count
- Adds retries on the connection failure

## Answer bands

### weak

- Does not connect the instance count to the connection count.
- Proposes a bigger database instance with no reasoning.
- Treats the refusals as a transient fault to be retried.

### junior

- Multiplies it out and identifies the ceiling being hit.
- Suggests reducing the pool size per instance.
- Does not notice that the fleet size can change again tomorrow.

### mid

- Bounds the total across the fleet rather than tuning one instance in isolation.
- Explains why raising the limit costs something inside the database.
- Asks whether the scaling signal is related to the actual bottleneck.

### senior

- Reasons about useful concurrency at the database and sizes everything from that number.
- Chooses where the queue should live and says what latency that buys or costs.
- Names who owns each of the settings involved and how they are kept consistent.

## Follow-ups

- Somebody raises the limit to two thousand. What do you expect to see?
  probes: a connection is not free; memory, contention, and throughput falling as concurrency rises
- Each instance now holds two, and requests queue inside the service instead. Better?
  probes: where the queue should live and which latency they are choosing to pay
- The scaler is keyed on CPU. Is that the right signal here?
  probes: scaling on a number unrelated to the resource that is actually saturated
