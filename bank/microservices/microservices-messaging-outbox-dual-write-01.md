---
id: microservices-messaging-outbox-dual-write-01
schema_version: 1
title: An event without an order, and an order without an event
category: microservices
topic: messaging
level: mid
tags: [messaging, consistency, transactions, correctness]
time_estimate_min: 9
order: 110
links:
  deeper: [microservices-messaging-backlog-replay-expiry-01]
  related: [microservices-consistency-stale-read-after-write-01]
---

## Ask

Your service saves the order to its own database and then publishes an order-placed event. Two
bug reports came in this week. Sometimes a consumer gets an event for an order that is not in the
database. Sometimes an order is in the database and no event was ever published. Explain both,
then fix it.

## Tests

Whether the candidate recognises two writes to two systems with no common commit, and can produce
a fix whose failure modes they can state.

## Listen for

- Two separate writes with no single commit between them; a crash in the gap leaves the two
  disagreeing
- The order of the two writes decides which of the two bug reports you get, and both orders are
  wrong in one direction
- Publishing first can announce something that then rolls back; committing first can lose the
  announcement entirely
- Writes the event into the same transaction as the order, and has a separate step carry it
  onward afterwards
- That separate step can run twice, so consumers have to tolerate seeing the same event again
- Says how the carrying step is monitored: if it stalls, the database is right and everyone else
  is behind

## Expected knowledge

- A transaction covers one database and does not extend to a broker
- A consumer acting on an event that later disappears cannot be undone by the producer

## Strong signals

- Asks which of the two failure directions is actually worse for this business before choosing
- Notices that the fix adds delay between the order existing and the event arriving, and says who
  is affected
- Mentions what keeps the carried events in a sensible order

## Weak signals

- Wraps the publish inside the database transaction and believes that solves it
- Suggests publishing first and deleting the event if the commit fails
- Proposes a distributed transaction across the database and the broker with no cost attached

## Answer bands

### weak

- Treats the two reports as unrelated bugs.
- Suggests retrying the publish inside the same request and considers it closed.
- Cannot say what a crash between the two writes leaves behind.

### junior

- Identifies that there are two writes and no way to make them succeed or fail together.
- Sees that swapping their order just changes which report you get.
- Has no concrete fix beyond retrying.

### mid

- Puts the event in the same transaction as the order and describes the separate step that ships
  it.
- States that the shipping step can repeat and says what consumers must therefore do.
- Names what consumers see that they did not before: the event arrives later.

### senior

- Reasons about the shipping step as a component with its own failure modes, lag and alarm.
- Discusses what preserves order among the shipped events and what breaks it.
- Weighs this against the alternative of consumers reading the database directly, and rejects it
  with a reason.

## Follow-ups

- The publish succeeds and the commit then fails. Who has already acted on something that does not
  exist?
  probes: irreversibility and which direction of mistake is cheaper
- You take the second write out of the request path. What do the downstream teams notice?
  probes: lag, repeats, ordering, and whether they think about the consumer's experience
- How long after the order is saved should the event be out, and who notices if it is not?
  probes: treating the relaying step as a first-class thing with a signal and an owner

## Sources

- https://microservices.io/patterns/data/transactional-outbox.html
