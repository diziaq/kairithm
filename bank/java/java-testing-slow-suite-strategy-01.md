---
id: java-testing-slow-suite-strategy-01
schema_version: 1
title: Twenty-eight minutes, and nobody runs it before pushing
category: java
topic: testing
level: lead
tags: [testing, operations, maintainability]
time_estimate_min: 10
order: 910
links:
  related: [spring-testing-context-cache-01]
---

## Ask

Your build takes twenty-eight minutes, and twenty-two of that is tests that each start their own
database container. Nobody runs it before pushing any more. Someone has proposed swapping the
container for an in-memory database. What do you do instead, and in what order?

## Tests

Whether the candidate can find the time inside a JVM build rather than inside the tests it runs,
and say where a substitute for the real database stops telling the truth about this code.

## Listen for

- Asks where the twenty-two minutes actually goes before moving anything: starting the container,
  migrating the schema, loading a context, or the test bodies themselves
- The container is per test because each test wants a clean database; one container for the whole
  run plus isolation per test — a schema each, a transaction rolled back, truncation between —
  buys most of the time back without changing what is covered
- Looks at the build itself: how many JVMs are forked, whether classes run in parallel, whether
  anything is being rebuilt and rerun that did not change
- A substitute engine runs different SQL — dialect, generated keys, constraint and isolation
  behaviour — and whatever stops being exercised stops failing silently, which is worse than slow
- Asks what these tests actually assert: logic that only needs a database because it was written
  inside the persistence layer can be moved out and tested without one
- Splits the loop: a fast set before pushing, the full set on the branch, and says what each is
  allowed to block
- Names who owns the duration afterwards and what stops it drifting back

## Expected knowledge

- Reusing an expensive fixture across a run, and what has to be true of the tests before that is
  safe
- Forked JVMs and parallel test execution in a build tool, and the shared state that defeats them
- Where a stand-in for the database is honest, and where it stops telling the truth

## Strong signals

- Asks whether any failure in the slow set was ever one the fast set could not have caught
- Converts the delay into developer minutes per day and uses that to get the work funded
- Sets a target duration and a check that fails the build when it is exceeded

## Weak signals

- Takes the in-memory database as the plan, with nothing said about the SQL it will not run
- Buys a bigger build machine and stops there
- Moves the slow tests to a nightly run and calls it solved, without saying who reads the result

## Answer bands

### mid

- Measures where the build time goes before changing anything.
- Shares one container across tests rather than starting one per test.
- Separates a quick set from the full set.

### senior

- Names the isolation that makes a shared container safe — a schema per class, or a transaction
  rolled back after each test — and says what breaks without it.
- Says what the in-memory substitute stops testing, and that the loss shows up in production
  rather than in the build.
- Turns on parallel execution only after saying what shared state would break under it.
- Asks what each group of tests is buying before moving or deleting any of it.

### lead

- Sequences the work and says what is done in week one against week six.
- Would move logic out of the persistence layer so that fewer tests need a database at all, and
  says what that refactor costs and who does it.
- Puts a number on the cost to the team and uses it to get the work funded.
- Leaves behind a mechanism — an owner, a budget, a failing check — not just a faster build.
- Says which of the options they are rejecting and why, including the one they were handed.

## Follow-ups

- The in-memory database goes in and the build drops to six minutes. Six weeks later a query that
  the tests are happy with fails in production. Walk me back through that.
  probes: dialect and behaviour the substitute does not reproduce; coverage lost without a failing
  test to announce it
- You move to one container for the whole run and three tests start failing every so often. What
  have you just exposed?
  probes: tests that silently depended on a clean database; isolation as the precondition for
  sharing anything
- Two of the slowest have never failed for a real reason in two years. Delete them?
  probes: judgement about what a test buys; absence of failure as evidence both ways

## Notes

Keep this one on the build and on the code: where the minutes are, what a shared fixture demands
of the tests, and what the substitute engine no longer runs. The team's relationship with a suite
it has stopped trusting is a separate question and is asked elsewhere — if the candidate goes
there, take the detour but come back to where the twenty-two minutes went.
