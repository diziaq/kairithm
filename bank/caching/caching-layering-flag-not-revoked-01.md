---
id: caching-layering-flag-not-revoked-01
schema_version: 2
title: Three pods that did not get the message
category: caching
topic: layering
level: senior
tags: [consistency, operations, observability]
time_estimate_min: 9
order: 150
links:
  deeper: [caching-layering-hot-key-one-shard-01]
  related: [microservices-consistency-two-services-disagree-01]
---

## Ask

Feature flags are read from Redis and held in process for five minutes. Mid-incident you turn one
off. Redis shows it off straight away and the error rate drops by three quarters, then stays there.
Twelve pods are running, and you cannot tell which ones are still doing the old thing. What went
wrong, and what do you change?

## Tests

Whether the candidate spots a caching layer that the change never reaches, and concludes that some
values must not be held locally at all.

## Ideal minimal answer

Turning it off in Redis says nothing to the copy inside each process, and each pod keeps its own
answer for up to five minutes from whenever it last read. A switch you need during an incident is
read live, or the local copy has to be revocable — and either way each pod has to report the value
it is using.

## Listen for

- The local copy is a second cache that the change never reaches, and it ends on its own schedule,
  per pod, timed from when that pod last read
- The pods are not in step: each one's five minutes started at a different moment, so the tail is up
  to five minutes and nothing says which pod is where in it
- A switch whose whole purpose is to stop damage is the one thing you do not hold a local copy of —
  or you accept that it is not a switch
- If a local copy is kept, it needs a way to be revoked, and a bound underneath for when the
  revocation does not arrive
- Wants every pod to report the value it is actually using, so "which three" becomes a question with
  an answer
- Knows the notification itself can be missed — a dropped connection, a pod starting up — and that
  a missed one leaves a pod holding the old answer with nothing to correct it
- Asks what the local copy was buying before proposing to remove it

## Expected knowledge

- An in-process copy exists once per replica and ends per replica
- A broadcast reaches only the instances listening at that moment

## Strong signals

- Sorts the flags by what a late answer costs: an experiment can be five minutes behind, something
  that stops damage cannot
- Keeps the local layer for most flags and exempts one class, rather than making one rule for all
  of them
- Asks how many reads a second the local copy was absorbing, in figures, before removing it
- Wants the runbook to state, as a number, how long a flag change takes to be everywhere
- Says the same reasoning applies to anything read on the hot path and changed by a human under
  pressure

## Weak signals

- Shortens the local lifetime to thirty seconds and calls it fixed
- Restarts the fleet as the way to apply a flag change
- Adds a broadcast on change and treats delivery as certain
- Cannot say why the error rate fell by three quarters rather than to zero
- Proposes reading Redis on every request with no idea what that costs
- Tells the story of a flag that would not turn off at a previous job and never says what they
  would change about these twelve pods

## Answer bands

### mid

- Identifies the in-process copy as the reason some pods carry on.
- Says, when pushed on the timing, that the copies end independently, so the change lands over the
  following five minutes.

### senior

- Explains why you cannot tell which three, and asks for the value each pod is using.
- Concludes that a switch used during an incident is read live or made revocable.
- Says without being asked that a notification can be missed, and keeps a bound underneath it.
- Asks what the local layer was absorbing before proposing to take it away.

### lead

- Divides the flags into classes by what a late answer costs and applies a different rule to each.
- Puts a number on how long a change takes to reach every replica, and puts it where the incident
  channel can see it.
- Names who owns that number and what would make it worse without anyone noticing.

## Follow-ups

- You need this answered now, mid-incident: which three pods are still on the old path?
  probes: whether anything reports, per replica, the value being used
- Someone adds a message on change so every process drops its copy. One pod's connection was down
  for ten seconds during that. Then what?
  probes: a missed message leaves an entry with nothing to correct it, which is why a bound stays
- The reason for holding it locally was three thousand reads a second. Do you still take it out?
  probes: whether they keep the layer and exempt a class, rather than choosing between extremes
- The same pattern shows up for a list of blocked accounts. Same answer?
  probes: generalising by the cost of a late answer rather than by the kind of data

## Sources

- https://redis.io/docs/latest/develop/reference/client-side-caching/
- https://redis.io/docs/latest/develop/pubsub/keyspace-notifications/

## Notes

The figures, if asked: twelve pods, flags read on every request at roughly three thousand a second
in total, the in-process copy has a five minute life measured from the read, and there is no
mechanism that pushes a change to a pod.

Redis's own server-assisted client-side caching is the worked example of doing this properly and of
what it still costs. The server tracks which keys a connection has read and sends an invalidation
when one is modified, expires or is evicted — but the reference is explicit that a client which
loses its invalidation connection must flush its local cache, that it should ping that connection
to detect the loss, and that a maximum lifetime should be put on every locally held key "even if it
has no TTL" as protection against exactly this. Plain Pub/Sub is weaker still: it is documented as
fire and forget, so everything published while a subscriber is away is lost. The bound underneath
is therefore not timidity; it is what the vendor's own design does.

The conclusion to press for is the narrow one. Not "do not cache flags" — the read is on every
request and the cache is earning its place — but "the flag you reach for to stop an incident is the
one you do not hold locally", plus per-pod reporting so the question in the title has an answer.
