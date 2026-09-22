---
id: http-dns-ttl-after-the-move-01
schema_version: 2
title: Twenty-six hours later, four per cent is still arriving
category: http
topic: dns
level: senior
tags: [operations, failure-modes, observability]
time_estimate_min: 10
order: 165
links:
  related: [database-cloud-databases-aurora-failover-four-hour-outage-01]
---

## Ask

You moved a service to a new address last Tuesday. The record's time-to-live was 3600 seconds.
Twenty-six hours after the change, four per cent of traffic was still arriving at the old
machine, and one team's fleet never moved at all. You have to plan the next move, which is in
three weeks. What do you do differently?

## Tests

Whether the candidate treats a time-to-live as a cache lifetime they can shorten in advance,
and plans the cut-over from observed traffic instead of from an assumed propagation delay.

## Ideal minimal answer

Lower the time-to-live at least one full old lifetime before the change, so callers are already
refreshing quickly when you cut over, keep the old address serving, and decide it is done from
the traffic still arriving there rather than from a clock. Expect a tail: some callers resolve
once at startup and never ask again.

## Listen for

- A shortened lifetime only takes effect after the old one has expired everywhere, so it has to
  be lowered ahead of the change, not with it
- Keep the old address serving and drive the decision from what is still arriving on it
- The tail is not all misbehaving resolvers: a caller that resolves once when it starts, or
  holds connections open, never asks again
- A runtime can keep its own lookup cache on its own schedule, independent of the record — worth
  checking rather than assuming
- Wants the old machine instrumented by caller, so the stuck fleet can be named and contacted
  rather than waited out
- Raise the lifetime again afterwards: a short one is a standing cost and a standing dependency
  on the resolver being reachable
- Asks whether the move needs to be a record change at all — a stable name, or something in
  front, moves the target without touching it

## Expected knowledge

- A time-to-live tells a resolver how long it may reuse an answer; it is a cache lifetime, not a
  schedule for a change to spread
- A name is resolved when a connection is opened; an open connection is never re-resolved

## Strong signals

- Gives the sequence with timings: lower it, wait a full old lifetime, verify, cut over, watch
  the old address, restore it
- Knows a failed lookup is cached too, on a separate and often longer schedule, so a brief bad
  answer outlives the mistake
- Names concrete client-side caches to check rather than saying "the client might cache" — the
  runtime's resolver cache, the connection pool, a sidecar, the container's own resolver
- Decides what the old machine does when they want the tail to end — refuse, redirect, or fail
  loudly — and who that breaks
- Notices four per cent may be one large caller rather than a broad tail, and that this changes
  the whole plan

## Weak signals

- Waits longer
- Says the change takes 24 to 48 hours to spread, as though that were a property of the system
- Switches the old machine off on the planned date and calls the stragglers someone else's
  problem
- Lowers the lifetime at the same moment as the change
- Blames the caller without having instrumented anything
- Recounts how a move at a previous job took three days to settle, without saying what the next
  one here should look like

## Answer bands

### mid

- Says the lifetime should have been lowered before the change rather than at it.
- Keeps the old address running until traffic stops.

### senior

- Gives the sequence with timings and explains why the lowering has to precede the cut by a full
  old lifetime.
- Separates resolver caching from caching inside the caller's own runtime and connections.
- Instruments the old address to find out who the remaining traffic belongs to.
- Restores the lifetime afterwards and says why.

### lead

- Decides what the old address does at the end, and who is told when.
- Asks whether the estate should depend on record changes for moves at all, and proposes what
  would replace it.
- Names what he would put in place so the next team does not have to know any of this.

## Follow-ups

- Give me the sequence and the timings, starting two days before the move.
  probes: whether the lowering precedes the cut by a full old lifetime, and whether they verify
  before cutting
- Who is the four per cent? How do you find that out before the next move rather than after?
  probes: instrumenting the old address by caller, and contacting them
- The old machine is switched off, and one team's service goes on failing for another hour after
  that. What could still be holding on?
  probes: a lookup cached inside the process, or connections opened before the change — neither
  is the resolver
- You leave it at sixty seconds permanently. What have you signed up for?
  probes: query volume, and a hard dependency on resolution succeeding on every new connection

## Sources

- https://www.rfc-editor.org/rfc/rfc1035.html#section-3.2.1
- https://www.rfc-editor.org/rfc/rfc2308.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/net/doc-files/net-properties.html
- https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/sun/net/InetAddressCachePolicy.java

## Notes

Figures to release if asked: the record's lifetime was 3600 seconds; the change went out at
10:00 on Tuesday; at 12:00 on Wednesday the old machine was still taking about 4% of normal
traffic; roughly 40 services call this one; the fleet that never moved is six JVMs that have not
been restarted in two months.

The mechanism a candidate should reach: lowering a lifetime is itself subject to the old
lifetime, because resolvers holding the previous answer will not see the new one until theirs
expires. So a lowering done at the same moment as the move buys nothing at all. The correct
sequence is lower, wait out the old value, verify, then move.

On the client side, verified: the Java runtime keeps its own successful-lookup cache and the
record's own lifetime is not consulted. The default policy is 30 seconds in the OpenJDK
implementation, and "cache forever" when a security manager is installed — the Oracle networking
properties page documents the value as "-1 (forever) if a security manager is installed, and
implementation-specific when no security manager is installed". Failed lookups are cached
separately, defaulting to 10 seconds, and RFC 2308 bounds negative caching by the zone's SOA
minimum. A long-running JVM that resolved once and then pooled its connections is a
perfectly ordinary explanation for a fleet that never moved.

`database-cloud-databases-aurora-failover-four-hour-outage-01` is the same machinery from the
debugging side, during an incident. This card is the planning side. They pair well in a
scorecard and badly in the same interview.
