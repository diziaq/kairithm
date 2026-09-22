---
id: microservices-consistency-stale-read-after-write-01
schema_version: 2
title: Save succeeds, reload shows the old address
category: microservices
topic: consistency
level: mid
tags: [consistency, correctness, observability, api-design]
time_estimate_min: 8
order: 150
links:
  deeper: [microservices-consistency-two-services-disagree-01]
---

## Ask

A user edits their delivery address, gets a green tick, reloads the page, and sees the old
address. The write went to one service; the page is rendered from a read model that trails it by a
few hundred milliseconds. Support has logged it as "the save button does not work". What do you
do?

## Tests

Whether the candidate can name the gap between a write and the copy that is read, and fix the
user's experience without making the whole system wait.

## Ideal minimal answer

Nothing is broken: the write landed and the page is reading a copy that has not caught up, so
the user cannot yet see their own change. Fix it just for them — render what they submitted, or
read that one case from the owning service — rather than making every read wait, and ask how far
behind the copy runs at its worst.

## Listen for

- Names the gap precisely: the user cannot see their own write yet, even though nothing is broken
- Distinguishes data that is wrong from data that is merely behind
- Fixes it for the person who just wrote — show them what they submitted, or read that one case
  from the authoritative side — rather than making every read wait
- Rejects making the copy update synchronously without first asking what that costs everything
  else
- Wants to know how far behind the copy runs, normally and at its worst, and whether anyone
  measures it
- Says the interface can be honest: a green tick that means "accepted" is a design choice with
  consequences

## Expected knowledge

- A copy maintained asynchronously is behind by a variable amount, not a fixed one
- A user's own write is the case where being behind is most visible

## Strong signals

- Asks which other consumers read that copy and whether the same delay is acceptable to each
- Points out that under a backlog the delay is not a few hundred milliseconds any more, and asks
  what the page does then

## Weak signals

- Adds a wait in the page before reloading
- Declares the read model a mistake and proposes reading from the writing service everywhere
- Treats it purely as a support-communication problem

## Answer bands

### weak

- Calls it a caching bug and clears a cache.
- Suggests a fixed delay before the page reloads.
- Cannot say why the two views disagree.

### junior

- Explains that the page reads from a copy that has not caught up.
- Knows the write itself succeeded and the tick was not a lie.
- Proposes reading from the authoritative service to fix it, without weighing the cost.

### mid

- Solves it for the user who just wrote, and leaves everyone else on the copy.
- Argues against making the copy synchronous, with a concrete cost.
- Asks how far behind the copy actually runs and wants that measured.

### senior

- Treats the acceptable delay as a per-consumer decision and names, without being handed one, a
  consumer with a tighter requirement.
- Describes what happens when the copy falls badly behind, and what the system does then.
- Says what the interface should promise, and makes that a deliberate product decision.

## Follow-ups

- The team's fix is for the page to pause half a second before reloading. What do you say?
  probes: whether they recognise a timing hack and can say what it fails to guarantee
- The same copy also feeds the label printer in the warehouse. Does the delay matter there too?
  probes: per-consumer tolerance rather than one global answer
- How do you find out how far behind it is right now?
  probes: measuring the gap as a first-class operational signal
