---
id: sap-jco-connection-pooling-capacity-across-nodes-01
schema_version: 1
title: The pool will protect SAP, says a colleague
category: sap-jco
topic: connection-pooling
level: lead
tags: [capacity, backpressure, operations, failure-modes]
time_estimate_min: 10
order: 200
---

## Ask

Your service runs two instances today, each with a JCo pool whose peak limit is twenty. Next
month it runs twelve, and nobody is changing the pool settings. A colleague says that is fine
because the pool will protect SAP from the extra load. What actually happens to a call when the
pool is full, and where does the limit on concurrent calls into SAP really live?

## Tests

Whether the candidate knows what a JCo pool actually bounds and what a caller experiences when it
is exhausted, and can choose deliberately between the places a system-wide limit could be
enforced instead — each with an operational cost.

## Listen for

- Does the arithmetic out loud: twenty per instance is two hundred and forty concurrent calls
  after the move, and nobody will have edited a configuration file to make that happen
- The pool settings are per destination inside one JVM; JCo has no idea the other eleven exist,
  so scaling out multiplies the effective limit rather than sharing it
- Says what a caller actually gets when the peak limit is already allocated: it waits, and that
  wait has its own bound, which is not a bound on the call itself; when the wait runs out the
  caller gets an exception, not a connection
- Distinguishes the two numbers: one caps how many connections may be active at once, the other
  caps how many idle ones are kept open — only the first is a concurrency limit at all
- Names the candidate places to put the real limit, and what each costs somebody: a per-instance
  number plus a pinned replica count; a shared limiter or semaphore the instances coordinate
  through; a queue in front so the work is bounded rather than the callers; or leaving it to
  SAP's own quotas and accepting that the rejection arrives as an error
- Is explicit that a JCo pool protects nothing on the SAP side — it bounds this JVM, and the far
  side is defended only by what the far side enforces
- Decides what a caller gets when the limit bites, and treats that as the design, not as an
  accident: fail fast, shed, or wait with a bound

## Expected knowledge

- `jco.destination.peak_limit` and `jco.destination.pool_capacity` and which one does what
- A pool that is exhausted makes the caller wait, and that wait is itself bounded by a setting
- A concurrency limit only exists once it has been configured; an unset limit is not a small one

## Strong signals

- Points out that a shared limiter buys an accurate global cap and costs a dependency that can
  itself fail, and says what happens to SAP traffic when it does
- Would rather the work were bounded than the workers: a bounded queue in front of the calls
  survives a changing instance count without any arithmetic
- Wants the effective concurrency measured and graphed, because a limit nobody can observe is a
  belief
- Asks what the SAP side will actually do when it is overrun, rather than assuming it degrades
  gracefully
- Points out that dividing twenty by twelve only holds while the instance count is fixed, and
  asks who owns it

## Weak signals

- Multiplies the pool because more instances are coming
- Divides twenty by twelve and considers the problem closed, with nothing said about exhaustion
- Believes an exhausted pool is always a reason to raise the limit
- Treats the pool number as a limit on what SAP will receive

## Answer bands

### mid

- Notices the totals do not fit and asks how many calls SAP can take.
- Reduces the per-instance limit to match the new instance count.

### senior

- Explains both pool numbers correctly and that they apply inside one JVM only.
- Shows why a per-instance number breaks once the instance count is dynamic.
- Decides what happens on exhaustion and implements it deliberately rather than leaving it to a
  default.

### lead

- Puts up more than one place the limit could live and picks one against the constraint given,
  saying what the choice costs to operate.
- Says plainly which of those options still holds if the coordinating component is down, and
  what the fallback is.
- Makes the effective global concurrency an observable number, not an inference from
  configuration.
- Will not ship the scale-out on an unenforced limit, and says what they would tell whoever
  asked for the twelve instances.

## Follow-ups

- Somebody proposes a shared counter that every instance checks before it calls. What have you
  just made load-bearing?
  probes: whether they see the coordination point as a new failure mode with its own outage
- The deployment goes out anyway and an hour later the far side is refusing work. What is the
  first thing you change, and how long does it take to take effect?
  probes: whether a limit can be moved without a full redeploy, and what the rollback is
- A caller reports the request hung for forty seconds and then failed. The SAP team say they
  never saw the call at all. Where was it?
  probes: waiting for a connection versus waiting for SAP, and which setting bounds which
- How would you know, a month from now, that the limit is still being enforced?
  probes: making the cap observable rather than a number in a file nobody reads

## Notes

The discriminator is the control-placement question, not the arithmetic. A candidate who divides
twenty by twelve has done the easy half; the interesting half is that the divisor is no longer a
constant, and that every fix for it buys accuracy with a new dependency.

Do not run this card in the same interview as the work-process starvation card. That one is about
negotiating a share of a shared SAP instance with evidence; this one is about what the client-side
pool does and where a real limit can be enforced. They look alike and are not.

The scale-out here is a fixed, planned one on purpose. There is a card in the microservices
category about an autoscaler that multiplies a per-instance pool against a fixed ceiling and then
flaps; that one is about the control loop, this one is about what JCo's two pool numbers mean and
what a caller experiences when the pool is full. Keeping the autoscaler out of this Ask is what
stops the two reading as the same question.

Verified in the decompiled JCo 3.1.14. `jco.destination.peak_limit` bounds the connections that
may be **allocated — checked out and in use — at once**: `com.sap.conn.jco.rt.PoolingFactory.getClient`
creates a new connection only while `getNumUsed() < peakLimit`, where `getNumUsed()` is the size
of the allocated list in `com.sap.conn.jco.rt.ClientFactory`. `jco.destination.pool_capacity`
bounds only the **idle** list: it is the limit of the `available` ring buffer, enforced in
`PoolingFactory.setCapacity`. Only the first is a concurrency limit at all, which is the
distinction this card turns on.

Verified, and the sharpest thing to have in hand for this card: **an unset `peak_limit` is
unlimited.** `com.sap.conn.jco.rt.RfcDestination.setProperties` reads it defaulting to whatever
`pool_capacity` was, and then `if (peakLimit == Integer.MIN_VALUE || peakLimit == 0) peakLimit =
Integer.MAX_VALUE;`. So a destination with nothing configured gets one pooled idle connection and
an effectively unbounded number of concurrent ones, and `max_get_client_time` never comes into
play because the peak-limit test is always true. The colleague in the Ask is wrong twice over: the
pool does not protect SAP, and on a destination where nobody set the number it is not bounding
anything either. A candidate who asks "is the limit actually configured on all twelve?" has found
the real risk.

Verified: what the caller gets at exhaustion is `com.sap.conn.jco.JCoException` with group 106,
`JCO_ERROR_RESOURCE`, and the message `"Connection pool <destination> is exhausted. The current
pool size peak limit is N connections."` followed by a per-connection dump from
`ClientFactory.describeAllocatedClients` saying how long each allocated connection has been
executing or idle and which function it is on. Note that a `max_get_client_time` expiry and an
instant refusal throw the **same** exception with the same group, key and message — the two cannot
be told apart from the exception, only from how long the caller waited. That is worth knowing
before promising an incident channel that the two are distinguishable.

Verified: the bounded wait is `jco.destination.max_get_client_time`, default 30000 ms
(`RfcDestination.setProperties`). `PoolingFactory.getClient` waits on a monitor for at most that
long in total, decrementing the remaining budget each pass, so a caller can never block forever
there. Set it to 0 or a negative number and there is no wait at all — the exhaustion exception is
thrown immediately. Waiters are served first-in-first-out. It is not a timeout on the call itself,
which is the distinction candidates routinely get wrong.

One honest caveat on the card's central claim: that these limits do not coordinate across JVMs is
a consequence of the pool being an in-process object — `PoolingFactory` is an ordinary Java object
holding Java lists, with no coordination of any kind in it — not a sentence SAP publishes.

Current defaults in 3.1.14, from `RfcDestination.setProperties`: `pool_capacity` 1,
`peak_limit` unlimited as above, `max_get_client_time` 30000 ms, `expiration_time` 60000 ms,
`expiration_check_period` 60000 ms. Defaults have moved between versions, so do not build the
question on one or hold a candidate to it.

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
