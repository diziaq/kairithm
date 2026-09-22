---
id: java-testing-flaky-timing-test-01
schema_version: 2
title: One CI run in twenty, and an annotation that reruns it
category: java
topic: testing
level: junior
tags: [testing, failure-modes, correctness]
time_estimate_min: 5
order: 900
links:
  deeper: [java-testing-mocks-assert-the-calls-01]
  related: [java-concurrency-shared-counter-01, spring-testing-leaky-state-01]
---

## Ask

A test fails roughly one CI run in twenty and never on anyone's laptop. It starts a task, sleeps two
hundred milliseconds, then asserts the task has finished. The team's fix is an annotation that
reruns a failing test three times before giving up. What is your view?

## Tests

Whether the candidate can separate a badly written test from broken code, and see what a rerun does
to the signal the suite is there to give.

## Ideal minimal answer

Says the fixed sleep encodes a guess about how fast the machine is, and the shared build machine
is slower, which is why it fails there and never on a laptop. Would wait for the task to finish,
with a generous ceiling, instead of waiting a set period, and says the rerun hides the failure
rather than fixing it.

## Listen for

- A fixed sleep encodes a guess about speed; the build machine is shared and slower, so the guess
  fails there first and not on a laptop
- Rerunning turns a genuine intermittent fault and a badly written test into the same green tick
- Wants the test to wait for the thing to happen, with a generous ceiling, rather than to wait a
  fixed time
- Says the sleep also costs everybody two hundred milliseconds on every single run, not only when it
  fails
- Asks first whether the production code carries the same guess about timing

## Expected knowledge

- Waiting on a signal — a latch, a future, or polling until a condition holds — instead of sleeping
- Handing the clock to the code under test rather than letting it read the real one

## Strong signals

- Does the arithmetic: one in twenty across a suite of hundreds means a red build most days
- Distinguishes a test that is unreliable from a test that is correctly catching a rare defect, and
  says how to tell which one this is
- Would isolate it with an owner and a date rather than leave it rerunning indefinitely

## Weak signals

- Makes the sleep longer and closes the ticket
- Blames the build hardware and stops
- Deletes the test
- Weighs the rerun against fixing the test and will not say whether the annotation should stay

## Answer bands

### weak

- Accepts the rerun because the build goes green.
- Says tests are unreliable and moves on.
- Suggests a longer sleep as the fix.

### junior

- Says the sleep assumes how fast the machine is and that the build machine is slower.
- Would wait for the result instead of waiting a fixed period.
- Sees that the rerun hides the failure rather than fixing it.

### mid

- Asks of their own accord whether the code or the test is at fault, before touching either.
- Replaces the wait with something that finishes as soon as the work does, and fails loudly after a
  ceiling.
- Talks about what a rerun does to everyone's trust in the suite, and what it would cost to keep.

## Follow-ups

- The rerun goes in and the build is green for a month. What have you got?
  probes: whether they see the signal has been switched off rather than repaired
- How would you make the test fail every single time, if the code really is broken?
  probes: controlling time or the scheduling points instead of hoping for the bad ordering
- The same suite has forty tests like this. Where do you start?
  probes: prioritising by cost and risk, and ownership rather than a blanket rule
