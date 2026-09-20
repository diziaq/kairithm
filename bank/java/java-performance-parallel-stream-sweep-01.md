---
id: java-performance-parallel-stream-sweep-01
schema_version: 1
title: A sweep that made everything parallel
category: java
topic: performance
level: mid
tags: [performance, correctness, failure-modes]
time_estimate_min: 8
order: 700
links:
  related: [microservices-scalability-autoscaled-into-database-01]
  deeper: [java-performance-local-cache-proposal-01]
---

## Ask

Someone ran a sweep across the codebase turning every `stream()` into `parallelStream()`. Since
then: throughput on one endpoint is worse, an unrelated scheduled job started missing its window,
and one report occasionally prints a total that is wrong. Unpick that for me.

## Tests

Whether the candidate can attribute three unlike symptoms to one change, and reason about where the
work actually runs.

## Listen for

- All of these tasks run in one pool shared by the whole process, so slow work in one place delays
  unrelated work somewhere else
- Anything that waits on input or output occupies a worker without using it; the pool is sized for
  work that keeps a core busy
- The wrong total points at shared mutable state being updated from several workers, or at combining
  results in a way that depends on the order they finish
- Splitting has to be cheap and the per-element work large enough to pay for the hand-off; a short
  list, or a source that can only be walked front to back, loses
- The default size comes from the processors the JVM believes it has, which under a CPU quota may
  not be the machine's count

## Expected knowledge

- The pool the stream framework uses by default, and that it is not created per call
- Why a reduction must be associative and stateless for the result not to depend on the split

## Strong signals

- Asks for the measurement that justified the sweep, and notes there was not one
- Points out the total can come out right in every test and wrong under load
- Would revert the sweep wholesale and reintroduce it only where a number supports it

## Weak signals

- "Parallel is faster on a multi-core machine"
- Fixes the wrong total by locking around the accumulation and keeps the parallelism
- Talks only about how big the collection is, never about what the elements do

## Answer bands

### weak

- Treats the three symptoms as three unrelated incidents.
- Says parallel work is unpredictable, with no mechanism.
- Cannot explain how a scheduled job is affected by a change to an endpoint.

### junior

- Knows the change makes work run on several threads and that shared state is now dangerous.
- Connects the wrong total to concurrent updates.
- Does not connect the unrelated job to the same cause.

### mid

- Identifies the shared pool as the link between the endpoint and the scheduled job.
- Explains why blocking work is particularly bad in that pool.
- Names the conditions under which the change would have paid off, and notes they were not checked.

### senior

- Separates the correctness fault from the two performance faults and treats them differently.
- Says the result being right in testing is weak evidence, and why.
- Proposes reverting by default and requiring a measurement per site, rather than fixing case by
  case.

## Follow-ups

- The job that started missing its window does not use streams at all. How is it affected?
  probes: whether they locate the shared resource rather than blaming the nearest code
- The report's total is right on every run of the test suite. Would you sign it off?
  probes: races invisible at small sizes; repeatability as weak evidence
- Where would this change genuinely have paid off?
  probes: work that keeps a core busy, a source that divides cheaply, and a measurement

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ForkJoinPool.html#commonPool()
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html
