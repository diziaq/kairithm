---
id: sap-jco-connection-pooling-connect-per-call-01
schema_version: 2
title: A fresh logon for every single call
category: sap-jco
topic: connection-pooling
level: junior
tags: [performance, operations, integration]
time_estimate_min: 5
order: 40
links:
  related: [general-code-review-hard-to-follow-01]
  deeper: [sap-jco-connection-pooling-logons-despite-pool-01]
---

## Ask

In a review you see that every request builds its own destination properties from scratch, logs
on to SAP, runs one function module, and throws the destination away. It works, and the tests
pass. What do you say in the review?

## Tests

Whether the candidate knows that JCo keeps a pool behind a named destination and that the pattern
in front of them defeats it, and can say what the waste costs on the SAP side.

## Ideal minimal answer

Building a fresh destination for every request means a full logon to SAP each time, which SAP
has to authenticate and set up a session for. JCo already pools connections behind a named
destination, so the fix is to get the destination once by name and reuse it, letting the pool
hold the connections.

## Listen for

- A logon is not free: SAP authenticates, sets up a user session and tears it down again, for
  every single request
- JCo pools connections per destination; reusing the named destination is what lets the pool do
  its job
- Building a new destination each time means the pool has nothing to reuse, so it degenerates to
  connect-and-disconnect
- A destination is not really "thrown away" either: the runtime holds on to it, so a new name per
  request leaves a trail of destinations and pools behind inside the process
- Under load this is visible to the SAP side as a stream of logons, not as your problem alone

## Expected knowledge

- `JCoDestinationManager.getDestination(name)` is the normal way in, and the destination is a
  long-lived handle
- Pool behaviour is configured per destination, not per call

## Strong signals

- Asks to see it under real concurrency before agreeing it "works"
- Mentions that logon volume is something Basis notices and asks about

## Weak signals

- "It works, ship it"
- Wants to build a home-made connection cache instead of using the destination
- Thinks the cost is only the network handshake

## Answer bands

### weak

- Sees nothing wrong, or objects only to code style.
- Cannot say what a logon costs anybody.

### junior

- Says the connection should be reused and that JCo already keeps them for you.
- Names the repeated logon as the waste.

### mid

- Explains what the destination owns behind it and what is discarded along with it.
- Says what the SAP side sees when this runs at a few hundred requests a minute.
- Can say when connect-per-call is acceptable — a tiny job run once a day — instead of treating
  it as always wrong.

## Follow-ups

- The author says it is fine because the tests are green. What test would change their mind?
  probes: whether they reach for a concurrency or load test rather than a functional one
- After the fix, the first request of the morning is still slow and the rest are fast. Why?
  probes: warm-up, pool filling, and metadata being read once
- Traffic doubles. Which number would you change, and what limits how far you can take it?
  probes: sets up the capacity conversation without handing them the answer

## Notes

A candidate who has only used JCo through a framework may not know the pool exists. Give credit
for reasoning about logon cost even if they cannot name the configuration.

Correction to a claim this card used to make, checked against the decompiled JCo 3.1.14: the
interface metadata is **not** thrown away with the destination. Repositories live in
`com.sap.conn.jco.rt.RepositoryManager`, keyed by system key rather than by destination name, and
there is no method on that class that removes one — `releaseRepository` only detaches the
destination from the repository's own list. So the metadata survives for the life of the process
and the second call to the same system does not pay to re-read it. Do not credit or expect that
answer, and do not offer it yourself.

What is true, and is the better version of the same point: the destination is not discarded
either. `com.sap.conn.jco.rt.DefaultDestinationManager` caches destinations in a per-tenant
`Hashtable` and removes one only in `removeFromCache`, which runs when the data provider fires a
`deleted` event. Dropping the Java reference frees nothing. So a service that invents a fresh
destination name per request accumulates a destination and a `PoolingFactory` per name inside the
runtime, with no eviction — a slow leak on top of the logon storm. A candidate who gets to "the
library is keeping these, not me" is above the level of this card.

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
- https://github.com/rafaelfvalim/JcoAbapDojo/blob/main/ABAP_AS1.jcoDestination
