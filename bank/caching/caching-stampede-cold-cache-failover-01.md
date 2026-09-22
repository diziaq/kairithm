---
id: caching-stampede-cold-cache-failover-01
schema_version: 2
title: Thirty seconds without a cache, eleven minutes without a service
category: caching
topic: stampede
level: senior
tags: [failure-modes, operations, performance]
time_estimate_min: 10
order: 140
links:
  related: [microservices-failure-handling-cascade-slow-dependency-01]
---

## Ask

Redis failed over at midday. It was back in about thirty seconds, empty. The service was down for
eleven minutes: the database saturated and stayed saturated. The database is sized for the two per
cent of reads that used to reach it. A team proposes a warm-up script that loads the ten thousand
most-used keys after any restart. What do you do?

## Tests

Whether the candidate recognises a cache the service cannot run without, protects the database from
an empty one, and can judge pre-population against its own failure modes.

## Ideal minimal answer

The database is sized on the assumption the cache is there, so an empty cache is an outage rather
than a slow patch — fifty times the read load arrives in one step. Bound what can reach the
database at once and decide what the callers beyond that bound are given. Warming helps the first
seconds and cannot be depended on.

## Listen for

- Does the arithmetic: two per cent reaching the database means fifty times that when none is
  served, and the database has no headroom for it
- Says why it was eleven minutes and not thirty seconds: timed-out requests are retried, fills
  queue behind each other, and a saturated database stays saturated once it is behind
- Bounds the concurrency reaching the database — one fill in flight per key, a small pool, a queue
  with a limit — and says what happens to the requests beyond the bound
- Says what the service should do with no cache at all: a reduced answer, an older answer, or
  failing fast, and that somebody has to choose
- Warming only covers keys that can be predicted, the list goes stale, and it does not remove the
  need for the bound
- Names the other events with the same shape: a flush, a deploy that changes the key format, a
  scale-out, a node lost, a cluster resharding
- Wants it rehearsed — kill the cache deliberately and measure — rather than reasoned about

## Expected knowledge

- Read amplification is the inverse of the hit rate
- Retries against a saturated dependency add load rather than shifting it

## Strong signals

- Does the arithmetic before proposing anything at all
- Points out the warm-up script is code that only ever runs during an incident, so it will be
  broken when it is needed
- Asks whether restoring a snapshot brings back values hours old, and which of those would be wrong
  to serve
- Separates making the cache more reliable from protecting the database, and says which they would
  buy first
- Suggests letting traffic back gradually so the cache fills before full load arrives
- Puts the drill on a calendar with an owner

## Weak signals

- Approves the warm-up script as the fix
- Proposes a bigger database without working out what "no cache" costs
- Makes the cache highly available and stops there
- Says thirty seconds is too short to matter, given the outage was eleven minutes
- Adds retries or raises timeouts on the fill path
- Recounts how an empty cache was diagnosed at a previous job and never says what they would change
  about this service
- Sets warming and the bound side by side with fair trade-offs and will not say which one they
  would build first

## Answer bands

### mid

- Says the empty cache sent every read to the database and the database cannot take that.
- Notices, once asked why it was not over in thirty seconds, that the outage outlasted the failover
  by a long way.

### senior

- Does the amplification arithmetic and states the multiple.
- Bounds what reaches the database and says what the callers beyond the bound get.
- Volunteers the account of the eleven minutes — retries and queueing — rather than calling it
  slowness.
- Names the other ways the cache empties, including ones nobody schedules.

### lead

- Decides what the service does with no cache and gets that agreed with the people who own the
  product.
- Weighs warming against the bound and says which one is the protection and which is a nicety.
- Commits to a rehearsal, the measurement it produces, and who owns the number.
- Says what capacity they are buying deliberately and what they are choosing not to buy.

## Follow-ups

- The failover took thirty seconds. Why was anything still broken ten minutes later?
  probes: retries and queueing holding a saturated dependency down
- Product ask what a user should see in the first minute after the cache disappears. What do you
  offer them?
  probes: a degraded answer as an explicit decision with an owner
- The script gets written. What makes you doubt it will work the next time this happens?
  probes: code that only runs in an incident; a key list that goes stale
- Someone points out the same thing happens, smaller, on every deploy. Does that change what you do
  first?
  probes: frequency against severity, and whether the bound is worth it either way

## Sources

- https://sre.google/sre-book/addressing-cascading-failures/
- https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/

## Notes

The figures, if asked: about 9,000 reads a second at midday, hit rate 98 per cent, so the database
normally sees 180 a second and it tops out around 900. With nothing cached it was asked for 9,000.
Nobody has ever measured what happens with the cache gone.

Google's SRE book is the citation for the distinction that carries this card: a *latency* cache
makes things faster, a *capacity* cache is a hard dependency, and "a service using a capacity cache
cannot sustain its expected load under an empty cache". Its mitigations are the ones to listen for
— overprovision for the empty case, reject requests when overloaded, degrade gracefully, and
"slowly increase the load" so the cache warms before full traffic arrives.

On warming: restoring from a Redis snapshot really does bring a cache back warm, and it brings back
values as old as the snapshot, which is a correctness decision and not an operational one. A
candidate who reaches for it and names the staleness has answered better than one who rejects
warming on principle.

This is deliberately not the deploy-warm-up question — the readiness and slow-start version of
that lives in the Spring category. Keep this one on the cache being load-bearing capacity.
