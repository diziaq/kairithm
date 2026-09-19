---
id: sap-jco-connection-pooling-capacity-across-nodes-01
schema_version: 1
title: Twelve pods, twenty connections each, thirty work processes
category: sap-jco
topic: connection-pooling
level: lead
tags: [capacity, performance, operations, backpressure]
time_estimate_min: 10
order: 200
---

## Ask

You are scaling the service from two instances to twelve. Each one has a JCo pool with a peak
limit of twenty, and the SAP instance has thirty dialog work processes. What do you do before
that deployment goes out?

## Tests

Whether the candidate can reason about a client-side limit that is replicated per JVM against a
shared server-side capacity, and turn it into an agreement rather than a setting.

## Listen for

- Does the arithmetic out loud: twelve times twenty is two hundred and forty possible concurrent
  calls against a system that can run thirty at a time
- Knows the pool settings are per destination per JVM, so scaling the service multiplies them,
  and the per-instance number has to be divided by the instance count
- Distinguishes the two numbers: one caps how many idle connections are kept open, the other
  caps how many can be active at once
- The pool is a client-side limit; the real constraint is SAP's capacity, and it is shared with
  interactive users and every other interface
- The conversation with Basis: how much of that capacity may this interface use, whether the RFC
  load should go to its own application server or logon group, and that they can keep a number
  of dialog processes reserved so RFC traffic never takes the last one
- Prefers to be refused quickly on their own side than to queue inside SAP: pool exhaustion
  should drive backpressure, not a bigger limit

## Expected knowledge

- `jco.destination.pool_capacity` and `jco.destination.peak_limit` and which one does what
- A dialog work process serves one request at a time

## Strong signals

- Says what the service does when the pool is exhausted — shed, slow down, or fail fast — rather
  than letting callers pile up behind it
- Uses the message server and a logon group for balancing rather than pinning one application
  server
- Wants a load test against a realistically sized system before believing any number
- Frames it as a shared budget somebody has to allocate, and asks who that is

## Weak signals

- Multiplies the pool because more instances are coming
- Treats the pool number as the answer without asking what is on the other side
- Believes an exhausted pool is always a reason to raise the limit

## Answer bands

### mid

- Notices the totals do not fit and asks how many calls SAP can take.
- Reduces the per-instance limit accordingly.

### senior

- Explains both pool numbers correctly and how they scale with instance count.
- Names the shared server-side constraint and who else is competing for it.
- Decides what happens on exhaustion and implements it deliberately.

### lead

- Turns it into an agreed budget with Basis, with a number both sides can monitor.
- Proposes where the RFC load should land in the landscape, not only how much of it there is.
- Says who is paged when the cap is hit and work goes late, and what the business impact is.
- Refuses to scale out until the far side's capacity has been confirmed, and says so to whoever
  asked for twelve.

## Follow-ups

- The deployment goes out anyway and Basis call you an hour later. What is the first thing you
  change, and how long does it take to take effect?
  probes: whether a limit can be moved without a full redeploy, and what the rollback is
- Autoscaling can take it to thirty instances at peak. How does that change your answer?
  probes: a per-instance limit is the wrong control when the instance count is dynamic
- SAP says they can add work processes. Is that the fix?
  probes: memory, database and licence cost of capacity, and whether the bottleneck moves
- How would you know, a month from now, that the agreed share is still being respected?
  probes: making the budget observable rather than a promise

## Notes

Verified: `jco.destination.peak_limit` is the maximum number of connections that can be active
simultaneously for a destination, `jco.destination.pool_capacity` the maximum number of idle
connections kept open, and both apply per JVM. Defaults vary by version — do not test on them.

Verified: the SAP side can be configured to keep a minimum number of dialog work processes free
of RFC load, so interactive users are not starved.

## Sources

- https://help.sap.com/doc/saphelp_ewm900/9.0/en-US/08/0b6835b2334756a1e9e1abb86dcf61/content.htm
- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
