---
id: caching-invalidation-cached-absence-01
schema_version: 2
title: A new product that cannot be found for ten minutes
category: caching
topic: invalidation
level: mid
tags: [correctness, consistency, performance]
time_estimate_min: 8
order: 100
links:
  deeper: [caching-invalidation-cache-aside-race-01]
---

## Ask

A lookup service was being hammered by requests for product codes that do not exist — about a
third of its traffic. The team started caching the not-found answer for ten minutes, and database
load halved. Since then support gets tickets saying a brand new product cannot be found for a
while after it is created. What is going on, and what do you do?

## Tests

Whether the candidate treats an absence as a cached fact with its own removal path and its own
lifetime, rather than as the absence of a cached fact.

## Ideal minimal answer

"Not found" is a stored value like any other, and nothing on the path that creates a product
removes it, so the row exists while the cache still says it does not. Either creating a product
removes that entry, or the not-found entry gets a much shorter life than a real one. Say which of
those is the fix.

## Listen for

- A not-found answer is a value sitting in the cache, and the thing that creates the product is
  what has to take it out
- Nothing on the create path knows that code was ever asked for, so someone has to make it
  responsible for the key
- An absent answer deserves a shorter life than a present one: it is cheap to recompute and being
  wrong about it is visible to a customer immediately
- Separates "we hold nothing for this key" from "we hold an entry that says there is nothing", and
  says how the code tells the two apart
- Asks where the missing codes come from — a crawler, a broken integration, someone typing — because
  a stream of one-off keys never gets read twice and only costs memory
- Wants a cap or a bound on how many of these entries can pile up

## Expected knowledge

- To cache a miss you have to store something that stands for absence
- A time limit caps how long a wrong entry is served; it does not stop one being written

## Strong signals

- Asks whether the creating code can even build the cache key, and notices it may sit in a
  different service from the cache
- Reaches for a compact summary of which codes exist — a filter consulted before the cache — rather
  than an entry per code that will never exist
- Wants the hit rate on absent answers reported separately from the hit rate on real ones
- Says how a support ticket like this should have been visible as a metric instead

## Weak signals

- Removes the not-found entries and accepts the original database load
- Extends the ten minutes because the hit rate improves
- Stores the absence as an empty value that the read path cannot distinguish from a miss, so the
  database is queried anyway
- Tells support that it clears itself in ten minutes

## Answer bands

### weak

- Treats it as a database or replication problem and looks there.
- Proposes shortening every time limit in the service.
- Cannot say what is held for a code that does not exist.

### junior

- Identifies that the old answer is still being served after the product exists.
- Suggests a shorter life for those entries.

### mid

- Puts the removal on the path that creates a product, and names which component does it.
- Chooses a bound for the absent answers and says what it costs.
- Separates a stored absence from an empty cache slot when pushed on what the read path sees.

### senior

- Asks, before anyone suggests it, where the codes that do not exist come from, and what those
  entries cost in memory.
- Splits the two hit rates in the metrics before tuning anything.
- Takes both — removal on create as the fix, a short life as the backstop — and says which is which.

## Follow-ups

- Products are created by a different service from the one holding the cache. Who does what now?
  probes: whether the removal can actually be placed on the write path, and who owns that across a
  team boundary
- Most of the codes being asked for turn out to be junk from a crawler. Does that change your
  answer?
  probes: entries that are never read twice; memory and a bound rather than correctness
- Two weeks later the same symptom appears for a product that was deleted rather than created. Walk
  me through it.
  probes: the mirror case, and whether their fix covered both directions

## Sources

- https://www.rfc-editor.org/rfc/rfc2308.html#section-5
- https://redis.io/docs/latest/develop/reference/eviction/

## Notes

The figures, if asked: about 1,200 lookups a second, of which roughly a third are codes that have
never existed; products are created a few dozen times a day by a separate catalogue service; the
entry for a real product has a ten minute life too.

RFC 2308 settled the same argument for DNS in 1998 and is worth knowing as prior art: a negative
answer is cached, its lifetime comes from the zone's own minimum, and the RFC recommends a ceiling
that is "not be greater than that applied to positive answers", suggesting one to three hours and
noting that values over a day "have been found to be problematic". The shape of the answer here is
the same — bound the absence at least as tightly as the presence, and give the create path the job
of clearing it.

Redis counts a lookup for a key that is not there as a keyspace miss, so a service that caches
absences on top of Redis will show a hit rate that mixes two different things; splitting them is
the measurement the strong candidate asks for.
