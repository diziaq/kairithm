---
id: caching-invalidation-cache-aside-race-01
schema_version: 2
title: A price that stays wrong until somebody edits it again
category: caching
topic: invalidation
level: senior
tags: [consistency, correctness, failure-modes]
time_estimate_min: 10
order: 110
links:
  deeper: [caching-invalidation-three-copies-one-customer-01]
  related: [database-consistency-read-your-writes-profile-01]
---

## Ask

Reads fill the cache on a miss. Writes update the row and then remove the key. About once a week
one product shows a price that is months old, and it stays wrong until somebody edits that product
again. Redis has not been restarted, nothing was evicted, and the entry has no time limit on it.
Why, and what do you change?

## Tests

Whether the candidate can reconstruct the interleaving that leaves a stale value behind, and then
tell the difference between a fix and a bound on the damage.

## Ideal minimal answer

A reader that missed before the write can land its old value in the cache after the removal, and
nothing then corrects it. A time limit only bounds how long that lasts. The fix is a conditional
fill: the store happens only if the value has not been overtaken since the read, by a version on
the value or by a token the cache handed out at the miss.

## Listen for

- Reconstructs the order explicitly: the reader's database read, the write, the removal, then the
  reader's store landing last with the older value
- Says why nothing repairs it: the entry has no expiry, and the only other thing that removes it is
  the next write to that product
- Separates a bound from a fix — an expiry limits how long a wrong entry is served and does nothing
  about it being written
- Rejects putting the new value into the cache on the write path, and can say why that is worse:
  two writes can reach the cache in the opposite order to the database
- Names a conditional fill: the value carries the row's version or its last-modified stamp and an
  older one is refused, or the miss issues a token that the removal cancels so a late store fails
- Says what each option costs on every read, and which one this team could actually operate
- Asks how wide the window is, and connects it to the slowest thing the reader does

## Expected knowledge

- A read that fills a cache is a read and then a store, with time in between
- Two processes can be inside that gap at once

## Strong signals

- Points out the window is as wide as the reader's own latency, so a slow query, a long pause or a
  retry turns "once a week" into something much more likely
- Asks what the cached value looks like, and whether it carries anything that could be compared
  against the row
- Says how they would prove this happened: the stale value should be exactly the value the row held
  before the last edit
- Wants to know how much a wrong price costs before choosing how much machinery to build
- Mentions that the same reasoning is why a cache-aside write removes rather than overwrites

## Weak signals

- Proposes storing the fill only when nothing is there yet, which is precisely the state the
  removal leaves behind, so the stale value still lands
- Proposes writing the new value into the cache on every write, presented as the safer option
- Adds a time limit and calls the problem solved
- Blames Redis, the network or a bad import without reconstructing an order of events
- Proposes a lock around every read of every key with no account of what that costs
- Sets the expiry, the version on the value and the token scheme side by side with fair trade-offs
  and will not say which one they would ship

## Answer bands

### mid

- Describes, once walked back through the order of events, a sequence in which an old value is
  stored after the removal.
- Proposes an expiry and says it limits the damage rather than removing the cause.

### senior

- Walks the interleaving in order and says which step lands last.
- Explains what would repair the entry and shows that nothing here does.
- Rejects the write path filling the cache before anyone offers it, and says what two concurrent
  writes would do.
- Proposes a conditional fill and identifies which part of it is doing the work.

### lead

- Prices the options against how often this happens and what a wrong price costs.
- Says when the expiry alone is the right answer, and under what conditions the conditional fill
  earns its complexity.
- Says what evidence would confirm it and what would make the next one visible within a day.
- Names who owns the rule and what the team has committed to keeping working.

## Follow-ups

- Once a week, one product, and it clears the moment anyone edits it. How would you prove that is
  what happened rather than a bad import?
  probes: evidence; that the stored value equals the row's pre-write value
- Someone proposes that a write should put the new value in rather than take the old one out. Two
  edits land in the same second. Walk me through it.
  probes: reordered stores; why removal is the safer default
- Suppose the fill is only allowed to store when there is nothing there already. Does that close
  the window?
  probes: the widely repeated set-if-absent fix, which fails because the removal has left the key
  absent
- The row normally reads in 40 ms, but the reader occasionally stalls for two seconds. What does
  that do to the odds?
  probes: the window is the reader's own latency, so rare becomes routine

## Sources

- https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf
- https://redis.io/docs/latest/commands/set/

## Notes

The figures, if asked: about 2,000 reads a second, a few hundred edits a day, the row reads in
around 40 ms, and product entries are written without an expiry.

**The fix candidates often quote is wrong.** `SET key value EX ttl NX` stores only when the key is
absent — and absent is exactly the state the write path's removal leaves behind, so the late store
succeeds and the stale price lands with a fresh lease of life. If a candidate offers it, the third
follow-up exists to see whether they can be talked through why it fails. Two things do work:
comparing a version carried on the value against the row's, and the lease scheme from Facebook's
memcache paper, where the miss hands out a 64-bit token bound to that key, an invalidation cancels
the token, and a store presenting a cancelled token is refused.

That paper is also the primary source for preferring removal over overwrite on the write path: "We
choose to delete cached data instead of updating it because deletes are idempotent."

The double-delete trick — remove the key, then remove it again after a delay longer than the
slowest read — is a real mitigation in the field and worth accepting if the candidate can say what
it costs and why it is a probability argument rather than a guarantee.
