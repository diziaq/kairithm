---
id: caching-eviction-mixed-workload-01
schema_version: 2
title: Sessions that vanish when the cache fills up
category: caching
topic: eviction
level: mid
tags: [failure-modes, correctness, operations]
time_estimate_min: 8
order: 170
links:
  related: [java-gc-retained-map-oom-01]
---

## Ask

One Redis instance holds cached query results with a five-minute life, login sessions, and the
counters the rate limiter uses. It is capped at twelve gigabytes, set to evict the
least-recently-used key across all keys. Memory reached the cap last night. Users were logged out
at random and the rate limiter let a burst straight through. What happened, and what do you change?

## Tests

Whether the candidate knows which keys a policy is permitted to remove, and treats one instance
holding cache and non-cache data as the defect rather than the setting.

## Ideal minimal answer

Across-all-keys means Redis may remove the sessions and the counters too — they are keys like any
other, and it took them. Put the cache in its own instance, separate from the data the application
treats as authoritative, rather than hunting for a policy that makes one instance safe for both.

## Listen for

- The policy as configured may evict any key, so the sessions and the counters were candidates
  exactly like the cached rows
- What the application saw: a session that is simply gone looks the same as one that ended, so the
  user is logged out; a counter that is gone reads as zero, so the limit resets and the burst is
  allowed
- The cached rows carry a life and the other two do not, and no single policy on one shared instance
  makes that safe — the fix is separate instances
- Considers the variant that only evicts keys carrying a life, and knows the trap: with nothing
  eligible it behaves like refusing to evict at all, and the application starts getting errors
  instead
- Knows what refusing to evict actually does — reads keep working, commands that add data are
  rejected — and that it is a different incident with different symptoms
- Asks what the cap is set against, and whether room was left for the buffers that are not counted
  towards it
- Wants the eviction count and the headroom on a graph, with an alarm before the cap rather than
  after

## Expected knowledge

- A policy decides which keys may be removed, and the across-all-keys variants include keys with no
  life set
- The cap and the eviction it triggers are per instance; logical databases inside one instance share
  both

## Strong signals

- Says the real defect is one instance holding data the application can afford to lose alongside
  data it cannot
- Points out the cap has to leave room for the replication and client buffers, which are not counted
  against it
- Asks whether a session store should be a cache at all, and what the product wants to happen when
  one is lost
- Works out whether twelve gigabytes was ever enough for the working set, rather than raising it
- Knows the frequency-based variants exist and treats choosing between them as tuning, not as the
  fix

## Weak signals

- Raises the cap and calls it fixed
- Switches to the variant that only touches keys with a life, and declares the sessions safe
- Blames the five-minute life rather than the policy
- Cannot say what a client sees when nothing can be removed
- Moves the sessions to a different logical database inside the same instance

## Answer bands

### weak

- Treats the logouts as a session bug and looks in the application.
- Asks for more memory with no account of which keys went.

### junior

- Connects the cap being reached to keys being removed.
- Says the policy is allowed to take anything.

### mid

- Names what each lost key did to a user: the logout, and the limit resetting.
- Separates the cache from the data that has to survive, into its own instance.
- Says that having no life set is no protection under this policy.

### senior

- Knows the trap in the life-only variant and what a client sees when nothing is eligible.
- Sets the cap with headroom for the buffers rather than to the size of the box.
- Asks for the eviction counter and an alarm ahead of the cap.
- Questions whether the working set ever fitted, and says how they would find out.

## Follow-ups

- Someone switches the setting so that a key with no time limit is left alone. Sessions have one.
  Better?
  probes: that this still takes sessions, and what happens when nothing is eligible at all
- The instance fills up again and nothing at all is allowed to go. What does the application see?
  probes: reads succeeding while writes are rejected; a different incident with different symptoms
- The rate limiter let a burst through. Say why, in terms of what was in there.
  probes: whether a missing counter is understood as permission rather than as a slow path
- Twelve gigabytes: how would you find out whether that number was ever the right one?
  probes: working-set arithmetic and eviction counts instead of raising the cap

## Sources

- https://redis.io/docs/latest/develop/reference/eviction/
- https://github.com/redis/redis/blob/7.4.0/redis.conf

## Notes

Pinning the specifics, because this is a card where a vague answer sounds fine. Redis's own
documentation: `allkeys-lru` evicts the least recently used key among *all* keys; `volatile-lru`,
`volatile-lfu`, `volatile-random` and `volatile-ttl` only consider keys that have an expiration
set, and "the `volatile-xxx` policies behave like `noeviction` if no keys have an associated
expiration"; `noeviction` means "the server will return an error when you try to execute commands
that cache new data … commands that only read existing data still work as normal". LRU and LFU are
both approximations over a sample, tuned by `maxmemory-samples`, which defaults to 5. In the
shipped `redis.conf` the default policy is `noeviction` and `maxmemory` is unset — and `maxmemory 0`
means no limit at all on 64-bit systems, which is the other half of the failure this card could
have described.

Two things the documentation says that a candidate can earn credit for. The memory used by the
replication and AOF buffers "is not included in the total that is compared to `maxmemory`", so the
cap must be set below the available RAM. And on this exact scenario, Redis's own advice is not a
policy at all: the `volatile-*` policies "are mainly useful when you want to use a single Redis
instance for both caching and for a set of persistent keys. However, you should consider running
two separate Redis instances in a case like this, if possible."

Do not accept a comparison of eviction algorithms as an answer; the question is which keys the
configured policy is allowed to take and what the application sees when it takes them. Redis 8.6
added least-recently-modified variants of the same policies, which changes nothing above.
