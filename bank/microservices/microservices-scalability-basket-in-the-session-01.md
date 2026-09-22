---
id: microservices-scalability-basket-in-the-session-01
schema_version: 2
title: A colleague has a change ready that turns the pinning off
category: microservices
topic: scalability
level: mid
tags: [capacity, operations, failure-modes, consistency]
time_estimate_min: 8
order: 630
links:
  deeper: [microservices-scalability-throughput-falls-with-more-workers-01]
  related:
    [
      microservices-messaging-live-updates-one-in-six-01,
      microservices-consistency-stale-read-after-write-01,
    ]
---

## Ask

The basket lives in the HTTP session, in memory, and the load balancer pins each shopper to one of
six instances. Every deploy loses baskets, and one instance sits at eighty per cent CPU while the
others idle. A colleague has a one-line change ready that turns the pinning off. What happens on
Monday if you merge it?

## Tests

Whether the candidate works out what the change does to a specific shopper's next request, and can
sequence a move of the state rather than switching the symptom off.

## Ideal minimal answer

The basket is still in one instance's memory, so with the pinning gone a shopper's next click can
land anywhere and five times in six her basket is empty — worse than today. Move the basket out to
a shared store first, run both paths until nothing reads the in-memory one, and only then stop
pinning.

## Listen for

- Says what a specific shopper sees on her next click: a different instance, no basket, items
  gone, five times out of six
- Sees that the pinning is holding the current design together, so removing it first inverts the
  order of the work
- Puts the basket somewhere every instance can read — a store with a key per shopper, or the
  client carrying it — and says which and why
- Sequences the change: write to both places, read from the new one with the old as a fallback,
  watch until the old path is unused, then drop the pinning, then delete the in-memory copy
- Says what happens to shoppers who are mid-session on the day of each step
- Separates the two complaints: baskets die on deploy because the state is in memory, and one
  instance is hot because pinning outlives the traffic pattern — the same cause, two symptoms
- Notices that lost baskets on deploy also need the instance to finish its in-flight requests and
  leave the pool cleanly, which is not fixed by moving the state
- Treats the pinning as a tool with a cost rather than a mistake, and says what it was buying —
  no network hop for basket reads, no store to run, no serialisation

## Expected knowledge

- In-memory state on one instance is not visible to the others and does not survive a restart
- A load balancer can send each shopper to the same instance, and that decision is what makes
  in-memory state appear to work
- Moving state to a shared store adds a call, a failure mode and something else to run

## Strong signals

- Asks how long a basket lives and how many shoppers are mid-basket at any moment before planning
  anything
- Wants a measurement that shows the old path is dead before removing it, rather than a date
- Asks whether a basket should be a stored order that survives the browser closing, which is a
  product question the ticket did not ask
- Notices the hot instance will not immediately cool, because the pinned shoppers stay pinned
  until their sessions end

## Weak signals

- Merges it and adds instances, because more instances spread the load
- Says sessions are an anti-pattern and the change is therefore right
- Replicates sessions between all six instances without pricing what that does at sixty
- Lengthens the session timeout so fewer baskets are lost
- Tells the story of a previous migration and never says what to do with this change

## Answer bands

### weak

- Approves the change because pinning is bad practice.
- Cannot say what a shopper's next request would find.
- Treats the hot instance and the lost baskets as two unrelated problems.

### junior

- Says the basket is in memory on one instance, so removing the pinning would lose it.
- Wants the basket kept somewhere shared instead.
- Has no order of work, and does not say what happens to shoppers mid-basket.

### mid

- Describes what the shopper's next click returns, with the one-in-six arithmetic.
- Puts the state in a shared store and sequences the steps so the old path is retired last.
- Says what happens to shoppers who are mid-basket during the change, once asked.
- Connects the hot instance and the lost baskets to the same cause.

### senior

- Raises unasked that the deploy still drops in-flight requests, and names what else has to
  change for that.
- Wants evidence that nothing reads the old path before removing it, and says what evidence.
- States what the pinning was worth, so the decision is a trade and not a correction.
- Asks whether the basket should outlive the session at all, as a product question.

## Follow-ups

- It goes in on Monday and her next click reaches a different instance. What is on her screen?
  probes: specific data lost on a specific request, and the one-in-six arithmetic
- The pinning stays, and instead each instance copies its baskets to the other five. What do you
  make of that?
  probes: the cost of copying state around, and what it does at six instances versus sixty
- The basket is in a shared store now, and a deploy still fails the requests that were in flight.
  What else has to change?
  probes: finishing in-flight work and leaving the pool cleanly, as a separate cause
- What was the pinning giving you, that you now have to pay for another way?
  probes: whether they can state the benefit honestly instead of treating it as a mistake

## Sources

- https://docs.spring.io/spring-session/reference/index.html
- https://docs.aws.amazon.com/elasticloadbalancing/latest/application/sticky-sessions.html
- https://kubernetes.io/docs/reference/networking/virtual-ips/#session-affinity

## Notes

Pinning a shopper to an instance is a legitimate tool with a known cost, not an error — it is how
in-memory state survives at all, and it is required by some protocols. The card is about the order
of operations: the state moves first, the pinning goes last. A candidate who argues from a rule
("sessions are an anti-pattern") and approves the merge has failed it regardless of which side of
the argument they landed on.

Figures to release when asked: six instances, baskets average eleven minutes, about four hundred
shoppers mid-basket at peak, deploys twice a day, the hot instance is the one that has been up
longest.
