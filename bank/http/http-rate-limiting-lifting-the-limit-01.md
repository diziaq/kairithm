---
id: http-rate-limiting-lifting-the-limit-01
schema_version: 2
title: The database is healthy again and the limit is still on
category: http
topic: rate-limiting
level: lead
tags: [operations, failure-modes, scalability, observability]
time_estimate_min: 12
order: 130
links:
  related: [microservices-failure-handling-what-you-shed-first-01]
---

## Ask

You have been turning away sixty per cent of your traffic for two hours. The database behind it
has been healthy for twenty minutes and your team wants the limit lifted. Two hundred thousand
mobile clients are backed off, a partner's import is queued, and nothing has been served out of
cache in a while. How do you lift it?

## Tests

Whether the candidate treats restoring service as an operation with its own failure mode, rather
than as the absence of the limit.

## Ideal minimal answer

In steps, not at once. The traffic coming back is more expensive than the traffic that left —
nothing is warm, and the deferred work has to be caught up on top of live demand. Raise the
allowance, watch the database, then raise it again, with the queued work paced so it does not
compete with customers.

## Listen for

- Says that lifting it all at once is its own event, and that the database sees more than it did
  before the incident started
- Separates the three things that arrive at once: live traffic, the clients that were refused and
  are coming back, and the work that was put off
- Notices nothing is warm, so the first requests back cost more each than the same requests cost
  yesterday
- Moves in steps with something measured between them, rather than on a clock
- Paces the deferred work below live demand, and says what happens if it never catches up
- Asks what the refused clients were told, because a fleet that returns in the same second was
  scheduled by your own answers
- Decides how to stop and go back before starting, not while it is going wrong

## Expected knowledge

- A client that was refused has not gone away; it is waiting
- Work deferred during an incident is still work, and it has to run somewhere

## Strong signals

- Wants each step driven by a signal from the database and can say which one they would watch
- Points out the caches are refilled by the same traffic being let in, so the earliest step is the
  most expensive per request and the curve gets easier, not harder
- Treats telling people as part of the operation — the partner hears the window has moved before
  they discover it
- Asks what the incident has left unpaid: reports not run, webhooks not delivered, mail not sent

## Weak signals

- Takes the limit off because the database is healthy
- Steps up on a timer with nothing measured in between
- Lets the deferred work run flat out the moment there is room
- Describes how a previous recovery went without saying what to do here
- Lays out three ways to stage it and will not say which one they would use

## Answer bands

### mid

- Says to lift it gradually rather than at once, once asked what happens the moment it comes off.
- Names the queued work as load that still has to run somewhere.

### senior

- Raises without being asked that the returning traffic is heavier than what left, and says what
  the cold caches have to do with it.
- Steps up against a measured signal and names which one they would watch.
- Separates live traffic, returning clients and deferred work, and paces the last of the three.

### lead

- Fixes the step size and the condition for going back before starting, and says who is watching.
- Decides what deferred work is worth catching up and what is written off, and who agrees that.
- Says what partners and support are told, and when, rather than letting them find out.
- Names what would make this a rehearsed procedure instead of a judgement call at four o'clock.

## Follow-ups

- You raise the allowance a third of the way and the database starts answering as slowly as it
  did at the worst of it.
  probes: whether they set a condition for going back, and whether they will actually use it
- The partner's queued import has a contractual window that closed an hour ago.
  probes: whether deferred work gets renegotiated, or quietly run late and hoped about
- Someone argues for letting everything back in at once, on the grounds that two hours of
  refusals have already spread the clients out.
  probes: whether they can say what is different about the system now, not just about the traffic
- Your status page goes green the moment you start lifting. Is that right?
  probes: what recovered means to a customer whose request is still being turned away

## Sources

- https://sre.google/sre-book/addressing-cascading-failures/
- https://sre.google/sre-book/handling-overload/
- https://www.rfc-editor.org/rfc/rfc6585.html#section-4
- https://www.envoyproxy.io/docs/envoy/latest/configuration/operations/overload_manager/overload_manager

## Notes

Figures to release if asked: normal load is about 9,000 requests a second; the mobile fleet is
200,000 devices on a thirty-second poll with jittered backoff; the partner import is roughly four
hours of queued batches against a window that ended at 23:00; the cache was cold-started by the
failover at the beginning of the incident and its hit rate is currently under ten per cent.

The wrong answer a strong candidate gives is "the database is healthy, take the limit off" — it
is a defensible reading of the evidence and it causes the second outage. The distance between
`mid` and `senior` is whether the candidate volunteers that the returning workload is not the
workload that left, or only concedes it when asked.

This card is the recovery half of a pair. `microservices-failure-handling-what-you-shed-first-01`
asks who gets turned away and who hears it; this one starts after that decision has been made and
has been running for two hours. Do not use both in one interview — they share a scene, and the
second one will sound to the candidate like a question they have already answered.
