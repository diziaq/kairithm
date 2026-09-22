---
id: caching-layering-hot-key-one-shard-01
schema_version: 2
title: One key the cluster cannot spread
category: caching
topic: layering
level: lead
tags: [performance, ownership, operations]
time_estimate_min: 11
order: 160
links:
  related: [microservices-scalability-one-tenant-dominates-01, java-performance-local-cache-proposal-01]
---

## Ask

A six-node Redis cluster serves the catalogue. One key — the homepage payload — takes about forty
per cent of all reads, and the node holding it sits at ninety per cent CPU with p99 climbing. The
team has doubled the cluster twice, which changed nothing, and now wants to double it again. What
do you tell them, and what do you do instead?

## Tests

Whether the candidate knows a single key is served by one node however many nodes there are, and
can choose a fix whose staleness and ownership they are willing to name.

## Ideal minimal answer

A key maps to one slot and a slot is served by one node, so more nodes cannot split one key and the
extra capacity sits idle. Move those reads somewhere else — a short-lived copy inside each
application replica, replicas of that shard serving the read, or the value under several names —
and say what each costs in staleness and who maintains it.

## Listen for

- One key hashes to one slot and one slot is served by one node; adding nodes moves slots around and
  cannot divide a single key
- Says where the capacity comes from instead: a copy inside each application replica for a second or
  two, replicas of that shard serving the read, or the same value under several names with the
  caller picking one
- Each of those buys throughput with either staleness or a fan-out on every write, and says which
  one they are paying
- A per-replica copy is the cheapest and hands the invalidation problem back, once per replica, to
  somebody who has to own it
- Notices the node is at ninety per cent because of one key, so everything else sharing that node is
  now at risk too, and asks what that is
- Asks whether the payload is the right size and shape at all — a smaller value, or fields fetched
  separately, may remove the problem without touching the topology
- Wants hot keys found deliberately rather than inferred, and knows that needs the frequency-based
  policy in place to work

## Expected knowledge

- A cluster spreads keys, not requests for one key
- Replicas can serve a read when a slightly old answer is acceptable

## Strong signals

- Works out what one node can serve against the read rate for that key before choosing anything
- Points out that splitting the value across ten names multiplies the write path and the
  invalidation by ten, and asks who keeps them in step
- Says a homepage payload probably belongs in front of Redis entirely, and asks whose team that
  makes it
- Names the measurement that would have stopped the second doubling being paid for
- Asks what else lives on that node and what its loss would take with it
- Rejects co-locating keys under a shared tag as a fix here, and can say why it is the opposite of
  what is needed

## Weak signals

- Doubles the cluster a third time, or proposes a different hashing scheme
- Talks about spreading load across shards without engaging with one key having one home
- Adds a local copy with no bound and no account of who sees an old homepage
- Proposes a shared tag to group the key with others
- Chooses one option without naming what it costs or who runs it

## Answer bands

### mid

- Says one key lives on one node, so more nodes do not help that key.
- Suggests holding a copy closer to the caller.

### senior

- Chooses between a per-replica copy, replica reads and several names, with the staleness or write
  cost of each.
- Asks what else is on that node and what the failure would take with it.
- Wants the hot key measured rather than assumed, and knows what has to be in place to measure it.

### lead

- Stops the third doubling and says what the first two bought.
- Picks one option, names who owns its invalidation, and says how it is monitored.
- Agrees how old the homepage is allowed to be with the people who own the page.
- Asks whether this value should be served outside Redis altogether, and what that moves to another
  team.

## Follow-ups

- They double it a third time anyway. What do the graphs look like on Monday?
  probes: whether they hold the line that one key has one home
- Somebody suggests writing the value under ten different names and picking one at random per read.
  What have you just taken on?
  probes: fan-out on write, and ten entries that have to be retired together
- The copy you would keep inside each application instance: how long for, and who decided that?
  probes: staleness as an owned decision rather than a constant in the code
- What would have told you this before the second doubling was paid for?
  probes: per-key measurement, and knowing the setting it depends on

## Sources

- https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/
- https://redis.io/docs/latest/develop/tools/cli/
- https://redis.io/docs/latest/commands/readonly/

## Notes

The figures, if asked: roughly 80,000 reads a second across the cluster, 40 per cent of them for
one key, six primaries each with one replica, and the payload is about 8 KB of JSON.

The primary facts. A cluster has 16,384 hash slots, `HASH_SLOT = CRC16(key) mod 16384`, and while
the cluster is stable "a single hash slot will be served by a single node" — so the number of nodes
is irrelevant to one key, and a twelve-node cluster has the same ceiling for it as a six-node one.
Replicas can take the read if the client sends `READONLY`, which the spec describes as telling the
replica "that the client is ok reading possibly stale data". Hash tags exist to force keys onto the
*same* slot, which is why offering them here is a sign the candidate has the mechanism backwards.
And `redis-cli --hotkeys` "only works when maxmemory-policy is \*lfu", which is the detail that
separates someone who has actually gone looking for a hot key from someone who has read about one.

The value size is deliberate and under-remarked: 32,000 reads a second of an 8 KB value is about a
quarter of a gigabyte a second leaving one node, so this is a network problem as much as a CPU one,
and a candidate who asks for the value size before choosing a fix has found the cheapest lever in
the room.
