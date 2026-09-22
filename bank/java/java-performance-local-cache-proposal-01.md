---
id: java-performance-local-cache-proposal-01
schema_version: 2
title: An in-process cache in front of an 80ms lookup
category: java
topic: performance
level: lead
tags: [performance, consistency, operations, observability]
time_estimate_min: 10
order: 710
links:
  related: [sap-jco-idoc-error-ownership-01]
---

## Ask

A team wants to put an in-process cache in front of a lookup that costs 80ms and runs on every
request. They have picked a library and sized it at a hundred thousand entries. What has to be true
before you say yes, and what do you make them build alongside it?

## Tests

Whether the candidate treats a cache as production machinery with its own failure modes, and can
say what evidence would justify adding one.

## Ideal minimal answer

Makes how out-of-date an answer may be a decision taken with the people who own the data and
written down, not a tuning knob, and lets the cost of a wrong answer set how much machinery is
justified. Requires the hit rate and eviction figures visible, and a way to turn it off without
a release, before approving.

## Listen for

- Asks how the keys are distributed and what hit rate to expect; a long tail of one-off keys pays
  the cost and buys nothing
- How wrong is an out-of-date answer allowed to be, and for how long — that is a product question,
  not a tuning knob
- Every instance keeps its own copy, so two replicas can answer the same key differently, and the
  fleet's hit rate is worse than one instance's looks
- What happens on deploy when every instance starts cold at once, and what stops fifty threads
  recomputing the same key the moment it expires
- The memory cost of a hundred thousand of these entries, measured rather than guessed, against the
  heap the service actually has
- Wants hit rate, eviction counts and load times visible, and a way to turn it off without a release
- Asks what else would fix it: the 80ms itself, a shared cache, or not doing the lookup on every
  request

## Expected knowledge

- Bounded caches, eviction, and expiry measured from the write versus from the last read
- A cache changes what answers the system gives, not only how fast it gives them

## Strong signals

- Wants the key to make it impossible to serve one tenant's data to another
- Asks who gets paged when an out-of-date entry produces a wrong answer, and how they would even
  recognise it as that
- Names the second-day problem: a changed entry format meeting a warm cache after a rollback

## Weak signals

- Justifies it with the 80ms alone
- Picks the size because it is a round number
- Treats invalidation as an afternoon's work
- Lists everything that could go wrong with the cache and never says whether they are approving it

## Answer bands

### mid

- Asks for the expected hit rate and how out-of-date an answer may be.
- Wants a bound and an expiry rather than an unbounded structure.
- Asks for metrics on whether it is working.

### senior

- Reasons about per-instance copies and what that does to consistency between replicas.
- Raises the cold start and the rush on a key that has just expired.
- Measures the memory rather than assuming, and checks it against the heap.
- Offers at least one alternative that removes the need for the cache.

### lead

- Makes the tolerance for out-of-date answers a decision taken with the people who own the data, and
  written down.
- Requires the switch-off path, the metrics and the alarm before approving.
- Asks what a wrong answer costs and lets that set how much machinery is justified.
- Says under which measured result they would remove it again, and who is accountable for checking.

## Follow-ups

- The underlying data changes a few times a day, unpredictably, and nothing notifies the service.
  What do you do about that?
  probes: expiry versus active invalidation; making staleness an explicit product decision
- It ships and the hit rate is twelve per cent. What does that tell you?
  probes: key distribution; removing it rather than tuning it
- The lookup it sits in front of starts failing. What should the cache do then?
  probes: serving old data on failure as a deliberate choice; not converting an outage into a cold
  start for everyone
