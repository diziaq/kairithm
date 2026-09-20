---
id: microservices-scalability-autoscaled-into-database-01
schema_version: 1
title: The autoscaler is allowed to multiply a number nobody checked
category: microservices
topic: scalability
level: mid
tags: [performance, capacity, failure-modes, operations]
time_estimate_min: 8
order: 210
links:
  deeper: [microservices-scalability-one-tenant-dominates-01]
---

## Ask

Traffic triples on a Monday morning. Your service autoscales from four instances to forty, and
within a minute the database starts refusing connections. Each instance holds a pool of twenty.
Nobody changed the pool size, the database, or the query; the only thing that changed is how many
copies of the service are running. Since then the fleet has been flapping between twelve and forty
every few minutes. What happened, what is the flapping, and what do you change?

## Tests

Whether the candidate sees an autoscaler as a control loop that multiplies a per-instance number
against a fixed ceiling downstream, and can bound the product rather than tune one end of it.

## Listen for

- Does the arithmetic: forty times twenty is eight hundred, against a limit that is very likely a
  few hundred; at four instances it was eighty and nowhere near
- The per-instance twenty was chosen once, for a fleet size nobody wrote down, and the scaler is
  now free to multiply it by whatever number it likes
- Scaling out moved the bottleneck rather than removing it: the tier that scales is elastic and the
  thing behind it is not
- Explains the flapping as a loop — the refusals change how the instances look to the scaler, the
  scaler changes the instance count, and the instance count changes the refusals
- Asks what the scaler is keyed on, and notices that a signal with no relationship to the saturated
  resource can drive the loop in the wrong direction and never settle
- Bounds the total rather than the per-instance number: one pool shared in front of the database,
  or a per-instance size derived from the largest fleet the scaler is permitted to create
- Raising the database limit is not free — each connection costs memory and adds contention inside
  the database — and the same ceiling is simply hit at a larger fleet
- Asks whether the work was database-bound in the first place, because if it was, more instances
  were never going to help and were always going to hurt
- Notes that a small pool with an internal queue often beats a large pool, and says what that trades

## Expected knowledge

- A connection pool reserves capacity whether or not it is in use
- A database has a hard ceiling on concurrent connections, set well above the concurrency at which
  it is actually fastest
- An autoscaler is a feedback loop, and its input has to be related to the constraint before the
  loop can settle

## Strong signals

- Points out that the scaler's maximum and the database's limit are two numbers owned by two teams
  with nothing tying them together, and proposes tying them
- Wants to know the useful concurrency of the database — the point past which throughput stops
  rising — before choosing any number
- Says what should have alerted before the first refusal: connections in use as a fraction of the
  ceiling, not a count of errors

## Weak signals

- Raises the database connection limit and calls it done
- Blames the autoscaler and pins the instance count at whatever looks right today
- Adds retries on the connection failure
- Treats the flapping as a cooldown to be tuned, without asking what the scaler is keyed on

## Answer bands

### weak

- Does not connect the instance count to the connection count.
- Proposes a bigger database instance with no reasoning.
- Treats the refusals as a transient fault to be retried.

### junior

- Multiplies it out and identifies the ceiling being hit.
- Suggests reducing the pool size per instance.
- Picks a number that works for forty instances and does not notice the fleet can change again
  tomorrow.

### mid

- Bounds the product across the fleet — a shared pool, or a per-instance size derived from the
  scaler's own maximum — rather than tuning one instance in isolation.
- Explains why raising the database limit costs something inside the database instead of being free.
- Asks what the scaling signal is and whether it has anything to do with the saturated resource.

### senior

- Explains the flapping as a feedback loop and names an input that would make it settle.
- Reasons about useful concurrency at the database and sizes everything backwards from that number.
- Chooses where the queue should live and says what latency that buys or costs.
- Names who owns the scaler's maximum and who owns the database limit, and how the two are kept in
  step when either changes.

## Follow-ups

- Somebody raises the limit to two thousand. What do you expect to see?
  probes: a connection is not free; memory, contention, and throughput falling as concurrency rises
- The scaler is keyed on CPU. Walk me through what it does minute by minute while the database is
  refusing connections.
  probes: whether a signal unrelated to the constraint can drive the loop the wrong way
- Each instance now holds two, and requests queue inside the service instead. Better?
  probes: where the queue should live and which latency they are choosing to pay
- Marketing book a campaign and the fleet is allowed to reach two hundred. Does your fix still hold
  without anyone touching it?
  probes: whether the bound is expressed against the permitted maximum or against today's number

## Notes

The point of difference from any other bounded-resource question is that the multiplier is not a
constant — it is set by a control loop reacting to the symptom. If the candidate only sizes the
pool for forty instances, push them on who is allowed to change forty.
