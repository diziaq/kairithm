---
id: microservices-messaging-ordering-out-of-order-address-01
schema_version: 1
title: Two events arrive the wrong way round and a parcel goes astray
category: microservices
topic: messaging
level: lead
tags: [messaging, ordering, correctness, scalability]
time_estimate_min: 10
order: 120
links:
  related: [microservices-distributed-transactions-compensation-cannot-undo-01]
---

## Ask

A customer changes their address and then places an order. The two events are handled the wrong
way round and the parcel goes to the old address. The team's proposed fix is to process the entire
stream one message at a time, in strict sequence, for everybody. Talk me through what you would do
instead.

## Tests

Whether the candidate can scope an ordering requirement to where it actually exists and make
handlers tolerate arriving out of sequence, rather than buying a global guarantee at the cost of
throughput.

## Listen for

- Global sequencing is a throughput ceiling bought for a problem that only exists between events
  about the same customer
- Scopes the requirement: everything about one customer travels the same path, everything else
  runs in parallel
- Makes the handler stop caring — a version or a source timestamp on the record, so an older
  update is discarded rather than applied
- Any guarantee holds only within one hop; a fan-out, a set-aside-and-replay, or a second
  producer breaks it again
- Asks whether the two events even have a defined order at source, or whether the system merely
  assumes one
- Names what the single-file design costs in practice: one slow message stops everybody, and
  capacity cannot be added

## Expected knowledge

- Parallelism and strict sequence are in direct tension
- Two producers writing about the same entity have no shared clock

## Strong signals

- Distinguishes "these events must be applied in order" from "the result must be the same
  whatever the order", and prefers the second where it is reachable
- Asks how large the ordering scope has to be and whether the business really needs it across
  entities
- Points out that the address on the parcel should have been resolved at one moment, not
  assembled from two independent updates

## Weak signals

- Accepts the single-file fix and discusses how to make it fast
- Says the broker guarantees ordering and stops there
- Adds a delay before processing so the earlier event has time to arrive

## Answer bands

### mid

- Sees that the requirement applies per customer and not across the whole stream.
- Proposes routing everything about one customer down one path.
- Has not considered what happens after a failed message is replayed later.

### senior

- Makes the handler reject a stale update on its own, so correctness does not rest on arrival
  sequence.
- Says where the guarantee stops holding and names at least one path that breaks it.
- Quantifies what the single-file proposal costs in throughput and in recovery time.

### lead

- Pushes the question back to the source: what does the business actually require to be true, and
  between which facts.
- Chooses a design and states the residual cases it does not cover, rather than claiming none.
- Weighs the cost of changing a design already in production against the size of the exposure.
- Says how the team would detect a stale update being applied, months from now.

## Follow-ups

- A message is set aside after five failures, fixed by hand, and put back an hour later. What does
  your design do with it?
  probes: whether the scheme survives replay; version checks over arrival sequence
- Two different services produce events about that customer. Who decides which one came first?
  probes: clocks, causality, a single owner for the fact
- The team's proposal is already live and keeps up comfortably today. What do you tell them?
  probes: judgement about when a ceiling matters and the cost of changing later

## Notes

Keep this away from any one broker's mechanics. If the candidate reaches for partition counts and
consumer groups, bring them back to the requirement and what the handler does.
