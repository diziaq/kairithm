---
id: caching-invalidation-three-copies-one-customer-01
schema_version: 2
title: Three services, one customer, three answers
category: caching
topic: invalidation
level: lead
tags: [ownership, consistency, operations]
time_estimate_min: 12
order: 120
links:
  related: [microservices-ownership-paged-for-someone-elses-data-01]
---

## Ask

Three services each keep their own copy of a customer record: one in Redis for an hour, one in
process for five minutes, one in a search index rebuilt nightly. A customer changes their address
and gets three different answers for a day. The teams want to replace all three time limits with
an event published whenever a customer changes. What are you agreeing to own?

## Tests

Whether the candidate can turn a choice about invalidation into per-copy requirements, an operable
failure story and a named owner, rather than a preference between two mechanisms.

## Ideal minimal answer

Ask which copy has a freshness requirement and get a number from whoever owns the data — they are
unlikely to be the same. A time limit heals itself; a missed event leaves a copy wrong with no end,
so the team now owns detection and a rebuild path, and a bound stays underneath. Decide that before
approving anything.

## Listen for

- Asks what each copy is used for and what a day-old address actually costs, and gets a number from
  the people who own the customer record
- An expiry fails safe because it ends by itself; a lost event fails silently and the copy stays
  wrong indefinitely, which is a new class of incident with no natural end
- Keeps a bounded expiry underneath the events, not as belt and braces but as the thing that caps
  the worst case when the notification path is the broken part
- Names what the team now has to build and keep running: a version or sequence on the change so an
  older one cannot win, catch-up for a consumer that was down, and a way to rebuild any copy on
  demand
- Says who owns correctness for each copy — the service that owns the record, or each consumer —
  and where that is written down
- Asks how anyone finds out a copy is wrong: a sampled comparison against the source with an alarm,
  rather than a customer ticket
- Treats the nightly index as a separate decision that may not need changing at all

## Expected knowledge

- A published message can be lost, repeated, or arrive out of order
- An expiry bounds staleness with nobody doing anything

## Strong signals

- Says the in-process copy is the hard one, because there is one per replica and a single
  notification has to reach every one of them
- Refuses to make all three uniform, and lets each copy's freshness follow what its callers do with
  the answer
- Puts the rebuild job before the notification pipeline, because that is what gets reached for at
  three in the morning
- Wants the record's version carried on every copy so two of them can be compared cheaply
- Asks what happens on the day the notification pipeline is down and the expiries have been removed
- Knows that a fire-and-forget channel drops everything published while a subscriber is away, so
  catch-up has to come from somewhere durable

## Weak signals

- Prefers events because they are more correct, with no account of a lost one
- Removes the expiries entirely
- Proposes one shared cache for all three services without asking who runs it or what happens when
  it is unavailable
- Treats the nightly index the same as the two in-memory copies
- Accepts "all three within a second" as a requirement without asking who needs it
- Weighs expiries against a published change fairly, in both directions, and never says what they
  would approve

## Answer bands

### mid

- Says the three copies have different lifetimes, so they will disagree for up to a day.
- Sees that a notification on change could take the place of waiting for an expiry.

### senior

- Names loss, repetition and ordering, and what each one does to a copy.
- Keeps a bound underneath the notifications and says what it is there for.
- Says how a wrong copy would be discovered before a customer finds it.
- Separates the nightly index from the two in-memory copies.

### lead

- Turns freshness into a per-copy requirement agreed with the people who own the record, and
  refuses to make it uniform.
- Makes the rebuild path and the drift check conditions of approval, not follow-up work.
- Names who owns correctness for each copy and what happens when the notification path is the thing
  that is broken.
- Says what they would not build, and what measured result would make them revisit it.

## Follow-ups

- Six months in, one of the three was down for two hours during a deploy. What does it serve when
  it comes back?
  probes: catch-up, and the fact that a missed notification has no natural end
- The teams offer to drop the hourly limit now that changes arrive within a second. What do you
  say?
  probes: whether the bound stays underneath as the worst-case cap
- The nightly index is a day behind by design. Who gets to decide that is acceptable?
  probes: pushing the freshness decision to the owners of the data rather than the owner of the
  cache
- How does anyone find out one of the three is wrong before a customer does?
  probes: sampled comparison against the source, with an alarm, as a deliverable

## Sources

- https://redis.io/docs/latest/develop/pubsub/keyspace-notifications/
- https://redis.io/docs/latest/develop/reference/client-side-caching/
- https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf

## Notes

If the candidate asks: the Redis copy backs a customer-facing profile page, the in-process copy
backs an internal risk check running on twelve replicas, and the index backs a support search
screen. Nobody has ever written down a freshness requirement for any of the three.

Two primary facts worth holding a candidate to. Redis Pub/Sub — the usual vehicle for an
invalidation broadcast, including keyspace notifications — is documented as *fire and forget*: "if
your Pub/Sub client disconnects, and reconnects later, all the events delivered during the time the
client was disconnected are lost". In a cluster, keyspace events are node-specific and are not
broadcast across nodes, so a subscriber has to attach to every node. Redis's own server-assisted
client-side caching makes the same concession from the other direction: if any connection is lost
the client must flush its local cache, and the reference advises "putting a max TTL on every key
… even if it has no TTL" as protection against exactly this. That is the evidence for keeping a
bound underneath the events.

The lead-level move is not choosing events. It is refusing one policy for three copies with three
different jobs, and naming the owner and the repair path for each.
