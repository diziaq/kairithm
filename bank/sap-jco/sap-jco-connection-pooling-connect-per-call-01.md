---
id: sap-jco-connection-pooling-connect-per-call-01
schema_version: 1
title: A fresh logon for every single call
category: sap-jco
topic: connection-pooling
level: junior
tags: [performance, operations, integration]
time_estimate_min: 5
order: 40
links:
  deeper: [sap-jco-connection-pooling-logons-despite-pool-01]
---

## Ask

In a review you see that every request builds its own destination properties from scratch, logs
on to SAP, runs one function module, and throws the destination away. It works, and the tests
pass. What do you say in the review?

## Tests

Whether the candidate knows that JCo keeps a pool behind a named destination and that the pattern
in front of them defeats it, and can say what the waste costs on the SAP side.

## Listen for

- A logon is not free: SAP authenticates, sets up a user session and tears it down again, for
  every single request
- JCo pools connections per destination; reusing the named destination is what lets the pool do
  its job
- Building a new destination each time means the pool has nothing to reuse, so it degenerates to
  connect-and-disconnect
- The interface metadata cached behind the destination is thrown away with it, so some calls also
  pay for re-reading it
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

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
- https://github.com/rafaelfvalim/JcoAbapDojo/blob/main/ABAP_AS1.jcoDestination
