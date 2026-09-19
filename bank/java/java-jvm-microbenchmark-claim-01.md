---
id: java-jvm-microbenchmark-claim-01
schema_version: 1
title: Forty times faster, measured in a main method
category: java
topic: jvm-internals
level: mid
tags: [performance, testing, correctness]
time_estimate_min: 7
order: 300
links:
  deeper: [java-jvm-class-identity-plugin-01]
  related: [java-performance-parallel-stream-sweep-01]
---

## Ask

A colleague opens a pull request with a benchmark in a `main` method: a loop of a million calls
around each of two implementations, `System.nanoTime` either side, and the conclusion "the new one
is forty times faster". How much of that number do you believe, and what would you ask for?

## Tests

Whether the candidate knows that a number produced by a running JVM describes that particular run,
and can name what sits between the source and the measurement.

## Listen for

- Early on the code runs interpreted and is only compiled once it has been executed enough; if the
  two halves are not in the same state, the number compares compilation states
- A result nobody consumes can be deleted entirely, so forty times can be the cost of doing nothing
- Values the loop feeds in are fixed and can be folded away; the real call site sees varied input
- One run, one process, no repeat, no spread; a collection can land in the middle and is charged to
  whichever half was running
- Asks for a harness built for this, and for the measurement to be shaped like the production call
  site

## Expected knowledge

- The compiler works from profiles gathered while the program runs, in tiers
- A purpose-built harness exists for the JVM, and why it needs somewhere to sink the result

## Strong signals

- Asks what the input distribution is and whether one implementation is being handed a friendly case
- Points out that running both in one process can pollute the profile at a shared call site
- Says that a forty-fold win on a path worth 0.1% of the request is not worth the review time either
  way

## Weak signals

- Accepts the number because the loop is long
- Offers a preliminary loop as the entire answer
- Measures in milliseconds and is satisfied

## Answer bands

### weak

- Takes the number at face value and comments on the code style instead.
- Says benchmarking is hard, with no specific objection.
- Suggests running it again on a quieter machine as the fix.

### junior

- Says the code needs to run for a while before it is fast, so the start of the loop is misleading.
- Knows the two halves should be measured the same way.
- Does not question whether the work is being done at all.

### mid

- Names at least two distinct ways the number can be wrong: the compilation state, and the work
  being optimised away or constant-folded.
- Asks for repeats and some measure of spread rather than a single figure.
- Wants the input to look like production input.

### senior

- Explains why an unused result licenses the compiler to remove the computation, and what a sink
  changes.
- Separates "this microbenchmark is unsound" from "this path does not matter", and asks the second
  question first.
- Says what they would accept as evidence instead, including measuring the endpoint under load.

## Follow-ups

- They change it to run the loop once and throw the result away before timing a second loop. Are we
  done?
  probes: whether a single correction is treated as sufficient; dead code and folding remain
- The new implementation wins in the loop, ships, and the endpoint's timing is unchanged. What
  happened?
  probes: the measured path not mattering; the loop's shape differing from the real call site
- Where would you want the number to come from instead?
  probes: a harness with a sink and repeated forks, or an end-to-end measurement under load

## Sources

- https://github.com/openjdk/jmh
- https://shipilev.net/blog/2014/nanotrusting-nanotime/
