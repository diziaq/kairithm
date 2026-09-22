---
id: caching-stampede-ten-minute-spike-01
schema_version: 2
title: Two bad seconds every ten minutes
category: caching
topic: stampede
level: mid
tags: [performance, failure-modes, observability]
time_estimate_min: 8
order: 130
links:
  deeper: [caching-stampede-cold-cache-failover-01]
  related: [microservices-scalability-autoscaled-into-database-01]
---

## Ask

A pricing lookup is cached for ten minutes. Every ten minutes, for about two seconds, database CPU
hits a hundred per cent and p99 goes to six seconds. Over the last hour the hit rate was 99.4 per
cent, so the team says the cache is doing its job and the database needs a bigger instance. What is
happening?

## Tests

Whether the candidate sees that one expiry makes every caller miss at the same instant, and can
tell a change in how often the spike happens from a change in how big it is.

## Ideal minimal answer

Every caller of that key misses in the same instant, so the database takes the whole arrival rate
for as long as one query lasts. The hit rate is averaged over the ten minutes and hides it. Let one
request recompute while the rest wait or are served the value that just went, and refresh before it
goes rather than after.

## Listen for

- The entry has a single expiry and every holder of the key misses together, so the database sees
  the full arrival rate for the duration of one query
- The hit rate is an average over the window and the damage is in two seconds of it, so it cannot
  be the evidence that nothing is wrong
- A longer expiry makes the spike rarer and not one bit smaller; a shorter one makes it more often
- One request does the work and the others wait on it or are handed the value that has just gone
- Refresh before the entry goes rather than when it has gone: a background refresh on a schedule,
  or each caller having a small chance of refreshing early
- With twelve replicas, a guard inside one process turns thousands of requests into twelve queries,
  not one, so the coordination has to sit where the cache is if one query is the goal
- Notices the query itself gets slower under the pile-on, so part of the two seconds is
  self-inflicted
- Keeps this apart from many keys written at the same moment, which is what spreading the lifetimes
  fixes

## Expected knowledge

- An entry goes at a moment, not gradually
- Several requests for a missing entry each do the work unless something stops them

## Strong signals

- Asks whether it is one key or many keys created at the same instant, because the fix differs
- Points out that adding a random offset to the lifetime does nothing at all for a single key
- Wants misses counted per key rather than a hit rate for the whole service
- Asks what the waiting caller should be given if the recompute is slow, and treats that as
  somebody's decision rather than the framework's
- Says what would have shown this on a dashboard: the database's query rate, not the cache's hit
  rate

## Weak signals

- Reads the 99.4 per cent as proof the cache is healthy
- Raises the lifetime to an hour and calls it fixed
- Adds retries to the lookups that fail during the spike
- Buys a database big enough to absorb a spike that a single query could have served
- Names a mitigation without saying which of the two properties of the spike it changes

## Answer bands

### weak

- Reads the hit rate as evidence that nothing is wrong.
- Proposes a bigger database with no other reasoning.
- Cannot connect the two seconds to the ten minutes.

### junior

- Connects the spike to the moment the entry goes.
- Says the requests all reach the database at once.

### mid

- Says every holder of the key misses at the same instant and the database takes the whole arrival
  rate.
- Proposes that one request recomputes while the rest wait or take the previous value.
- Says, once a longer lifetime is put to them, that it changes how often this happens and not how
  big it is.

### senior

- Separates one key from many keys created together and picks the mitigation accordingly.
- Notices for themselves that a guard inside each process leaves one query per replica, and says
  where the coordination has to live.
- Chooses what a waiting caller is given, and says whose decision that is.
- Asks for misses per key, and says what should have been on the dashboard instead.

## Follow-ups

- The team sets it to an hour instead. Describe the next day.
  probes: rarer and exactly as large; whether they keep frequency and amplitude apart
- There are twelve replicas, and the guard you just described lives inside each one. How many
  queries reach the database?
  probes: where deduplication has to sit once there is more than one process
- The recompute takes two seconds. What should the eighteen hundred callers waiting on it be given?
  probes: serving the value that just went as a deliberate choice, and who signs off on it
- Tomorrow the same shape appears on a service with forty thousand keys, all first written during a
  deploy. Same fix?
  probes: spreading the lifetimes, which is the right answer there and useless for one key

## Sources

- http://www.vldb.org/pvldb/vol8/p886-vattani.pdf
- https://github.com/ben-manes/caffeine/wiki/Refresh
- https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf

## Notes

The figures, if the candidate asks: one key, about 900 requests a second across twelve replicas,
the underlying query takes 180 ms on an idle database and several seconds while the pile-on is
happening. The hit rate is measured across the whole service over an hour — the six two-second
windows are about a third of a per cent of the hour's requests on their own, and the rest of the
missing 0.6 per cent is a long tail of keys asked for once. That arithmetic is the point: the
number cannot go far below 99 per cent no matter how bad the spike is, so it is not evidence
either way.

Three named mechanisms, if you want to check depth after the candidate has described one.
Caffeine's `refreshAfterWrite` returns the old value while a single reload runs — "The old value
(if any) is still returned while the key is being refreshed" — and `LoadingCache.get` documents
that a second caller "simply waits for that thread to finish and returns its loaded value", which
is the in-process version of one-query-per-key. Facebook's memcache leases give one client per key
a token every ten seconds and tell the rest to wait, which took a peak database query rate on
herd-prone keys from 17K/s to 1.3K/s. Probabilistic early expiry (the XFetch paper) gives each
reader a rising chance of refreshing as the expiry approaches, which removes the cliff without
coordination.

A candidate who reaches for a random offset on the lifetime has solved a different problem — that
one is for many keys sharing a creation time, which is the last follow-up.
