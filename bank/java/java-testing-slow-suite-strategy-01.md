---
id: java-testing-slow-suite-strategy-01
schema_version: 1
title: Twenty-eight minutes, and nobody runs it before pushing
category: java
topic: testing
level: lead
tags: [testing, operations, performance]
time_estimate_min: 10
order: 910
links:
  related: [spring-testing-context-cache-01]
---

## Ask

Your team's build takes twenty-eight minutes, twenty-two of which are tests that each start a
container with a real database. People have stopped running it before pushing, and the main branch
is red about a third of the time. What do you do, and in what order?

## Tests

Whether the candidate can turn a feedback-loop problem into a sequenced plan, weighing what the slow
tests buy against what they cost the team every day.

## Listen for

- Measures first: which tests, how much of the time each, and how often any of them has ever caught
  something
- Asks what risk the database tests cover, and whether a handful of them cover it as well as all of
  them do
- Splits the loop: a fast set before pushing, the full set on the branch, and says what each one is
  allowed to block
- Reuses the costly setup — one container per class or per run, with data kept separate per test —
  instead of one per test
- Treats the red main branch as the first problem, because a broken signal makes everything else
  unmeasurable
- Names who owns the duration afterwards and what stops it drifting back

## Expected knowledge

- Where a stand-in for the database is honest, and where it stops telling the truth
- Running tests at the same time, and what has to be true of the tests before that is safe

## Strong signals

- Refuses to delete tests before knowing what they cover, and says how they would find out
- Converts the delay into developer minutes per day and uses that to justify the work
- Sets a target number and a check that fails when it is exceeded

## Weak signals

- "Replace the database with a stand-in" as the whole plan
- Buys a bigger build machine and stops there
- Moves the slow tests to a nightly run and calls it solved, without saying who reads the result

## Answer bands

### mid

- Profiles the build before changing it.
- Reuses setup across tests and runs what can be run at the same time.
- Separates a quick set from the full set.

### senior

- Asks what each group of tests is buying before moving or deleting any of it.
- Fixes the unreliable main branch first and explains why that comes before speed.
- Describes the data isolation that makes shared setup safe.
- Says which failures the fast set is allowed to miss, and where they are caught instead.

### lead

- Sequences the work and says what is done in week one against week six.
- Puts a number on the cost to the team and uses it to get the work funded.
- Leaves behind a mechanism — an owner, a budget, a failing check — not just a faster build.
- Says what they would not do, and why a nightly run is a weaker answer than it looks.

## Follow-ups

- Someone proposes moving them all to a nightly run. Argue the other side.
  probes: when a fault is found versus how long it takes to trace; who reads the nightly result
- You get it down to nine minutes. A month later it is back at twenty. What went wrong?
  probes: no owner, no budget, no check — a one-off effort with no mechanism behind it
- Two of the slowest have never failed for a real reason in two years. Delete them?
  probes: judgement about what a test buys; absence of failure as evidence both ways
