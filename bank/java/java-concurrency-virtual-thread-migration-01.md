---
id: java-concurrency-virtual-thread-migration-01
schema_version: 2
title: The pool that was holding the whole system back
category: java
topic: concurrency
level: lead
tags: [failure-modes, performance, operations]
time_estimate_min: 10
order: 30
links:
  related: [microservices-scalability-one-tenant-dominates-01]
  shallower: [java-concurrency-visibility-flag-01]
---

## Ask

A team replaced their two-hundred-thread request executor with one virtual thread per request.
Median latency improved. Then the next time a downstream dependency slowed down, the service
degraded far harder than it used to, and one endpoint came out slower rather than faster. What do
you go and look at?

## Tests

Whether the candidate sees a bounded thread pool as a de facto limit on everything behind it, and
can reason about what a concurrency change moves rather than removes.

## Ideal minimal answer

Says the old pool was the admission limit nobody wrote down, so every arriving request now
reaches the database, the dependency and the heap at once. Decides what should happen when
demand exceeds capacity before picking a mechanism, and names what must be in place first: a
load test against a slow dependency, explicit limits per class of work, and a way back.

## Listen for

- The old pool was silently the throttle; with it gone, every arriving request now reaches the
  database, the dependency and the heap at the same time
- Asks what else is bounded: connection pool size, the rate the dependency will accept, memory per
  request in flight, queue depth
- The limit has to be put back deliberately, where it belongs, not restored by making threads costly
  again
- For the slower endpoint, looks for work that blocks while holding a monitor, which ties up the
  carrier instead of releasing it, and for long stretches of pure computation
- Per-request state that used to be reused across a pooled thread is now created per request, so
  anything sized by thread count has changed
- A thread dump and the thread-count graph no longer mean what they used to mean

## Expected knowledge

- Virtual threads run on a small set of carriers, and blocking on I/O gives the carrier back while
  some other kinds of blocking do not
- Putting virtual threads in a fixed pool defeats the point; bounding how much work is in flight is
  a separate concern from how threads are created

## Strong signals

- Asks what should happen when demand exceeds capacity — shed, queue, or degrade — and picks the
  mechanism from that answer
- Wants a load test that includes a slow dependency, not only a healthy one
- Asks which release they are on, because the behaviour of blocking inside a monitor differs between
  them

## Weak signals

- "Virtual threads are faster" with no account of what changed
- Puts the virtual threads into a fixed-size pool to get the old behaviour back
- Reads a rising thread count as the fault itself
- Sets out shedding, queueing and degrading side by side and will not say which one this service
  should do

## Answer bands

### mid

- Says the number of threads is no longer the limit and that more work now runs at once.
- Names one resource behind the service that is still bounded.
- Suggests capping concurrency somewhere, without saying where or on what.

### senior

- Volunteers that the pool was doing admission control as a side effect, and that this was never
  written down anywhere.
- Traces the harder degradation to queueing moving to the next bounded resource.
- Has a hypothesis for the slower endpoint involving what the request does while it waits.

### lead

- Decides the overload behaviour first and then chooses the mechanism, rather than the reverse.
- Says what has to be in place before the change goes back out: a load test with a slow dependency,
  explicit limits per class of work, and a way back.
- Names the signals that stopped being meaningful and what replaces them on the dashboards.
- Weighs the change against what it is buying, given the median was not the problem.

## Follow-ups

- The database side is a pool of twenty connections and nobody touched it. What does a traffic spike
  look like now?
  probes: waiting moves from the executor queue to the connection pool; timeouts stacking up there
- Some requests are cheap and some are very heavy. Anything you would do about that?
  probes: bounding per class of work, fairness, shedding rather than admitting everything
- What would you want to be able to see before you let this go out a second time?
  probes: in-flight counts per bounded resource, and what replaces the old thread-count signal

## Notes

On Java 21 a virtual thread that blocks inside a `synchronized` block pins its carrier, which can
starve the scheduler; JEP 491 in JDK 24 removed that for monitors. Ask which release the team is on
before diagnosing the slow endpoint — the answer differs.

## Sources

- https://openjdk.org/jeps/444
- https://openjdk.org/jeps/491
