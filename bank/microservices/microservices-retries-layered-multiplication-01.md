---
id: microservices-retries-layered-multiplication-01
schema_version: 1
title: Three layers each retry three times
category: microservices
topic: retries
level: mid
tags: [retries, failure-modes, performance, operations]
time_estimate_min: 8
order: 90
links:
  related: [microservices-idempotency-key-scope-and-lifetime-01, sap-jco-troubleshooting-first-call-after-idle-01]
---

## Ask

The mobile SDK retries three times. The API gateway retries three times. Your service retries a
failing database call three times. A user taps once. How many times can that query hit the
database, and what would you do about it?

## Tests

Whether the candidate multiplies retries across layers instead of adding them, and can pick one
place for the behaviour to live.

## Listen for

- Does the arithmetic out loud: the layers compose, so one tap becomes twenty-seven attempts
- Repeating at more than one layer is almost always a mistake; one layer owns it and the others
  pass the failure straight up
- Picks the layer deliberately and gives a reason — closeness to the failure, or knowing whether
  a repeat is safe
- Caps repeats as a share of total traffic rather than a fixed count per request, so the extra
  load is bounded when everything is failing at once
- Passes a deadline down, so a hop with no time left does not start work at all
- A repeat of a slow call runs alongside the first, so it adds load exactly when there is none to
  spare

## Expected knowledge

- A failure at the bottom surfaces at every layer above it
- The caller has usually stopped waiting long before the innermost attempts finish

## Strong signals

- Asks whether the database failure was transient at all before deciding to repeat anything
- Wants to measure attempts per request at each hop, rather than trusting the configuration
- Notices that a gateway repeat may land on a different instance, so the work is duplicated as
  well as repeated

## Weak signals

- Adds three and three and three
- Tunes the counts down a bit and calls it fixed
- Treats retrying at every layer as defence in depth

## Answer bands

### weak

- Answers three, or nine, and does not see the composition.
- Treats retries at each layer as independently sensible.
- Has no view on which layer should own the behaviour.

### junior

- Gets to twenty-seven or explains the multiplication.
- Says it is too many and wants to reduce the counts.
- Does not yet say which layer keeps them.

### mid

- Chooses one layer to retry and makes the others propagate the failure, with a reason for the
  choice.
- Connects the extra attempts to load arriving when the system is least able to take it.
- Brings in the caller's deadline and what a hop should do when it has already passed.

### senior

- Replaces per-request counts with a bound on retries as a fraction of traffic, and says how it
  behaves during a full outage.
- Wants the attempt count observable per hop so the configuration can be checked against reality.
- Ties the decision to whether the operation is safe to repeat at all.

## Follow-ups

- Which layer keeps it, and why that one?
  probes: proximity to the failure versus knowing whether the operation is safe to repeat
- Your service calls a third party whose client library quietly does its own repeats. How would
  you even find out?
  probes: measuring attempts versus requests at a boundary you do not control
- The gateway team refuse to turn theirs off. What can you do on your side alone?
  probes: budgets, concurrency caps, failing fast, shedding

## Sources

- https://grpc.io/blog/deadlines/
- https://sre.google/sre-book/handling-overload/
