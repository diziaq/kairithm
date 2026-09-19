---
id: general-testing-suite-nobody-trusts-01
schema_version: 1
title: Forty minutes to run, and a quarter of the runs fail
category: general
topic: testing
level: senior
tags: [testing, correctness, operations, performance]
time_estimate_min: 8
order: 170
---

## Ask

Your team's test suite takes forty minutes, and roughly one run in four fails. Nobody
investigates those failures any more — people press the button again and it usually goes green
the second time. What do you do?

## Tests

Whether the candidate treats an unreliable suite as a correctness problem that is actively
costing the team, and can produce a plan with an order to it rather than a wish.

## Listen for

- Says a suite people re-run on failure has stopped being a signal, and that a real defect is now
  invisible
- Wants data first: which tests fail, how often, since when — rather than fixing whichever one
  they saw last
- Quarantines the worst offenders so the suite becomes trustworthy again while they are repaired
- Asks what makes them unreliable — shared state between tests, time and ordering, real network
  calls, waiting on a sleep
- Sets a rule for what happens to a quarantined test if nobody fixes it, so the quarantine does
  not become a graveyard
- Treats the forty minutes as a separate problem with separate options, and says which one hurts
  more

## Strong signals

- Points out that pressing the button again has trained the team to ignore exactly the class of
  defect the suite exists to catch
- Makes the failure rate visible — a chart, a weekly number — so the improvement can be argued
  for with evidence
- Asks whether a failure ever turned out to be real, and looks for a recent escaped bug the
  suite should have caught
- Gets the change agreed rather than doing it quietly at night

## Weak signals

- Adds waits or retries to the flaky tests and calls them fixed
- Deletes the failing tests
- Proposes rewriting the whole suite
- Treats it as an annoyance to live with

## Answer bands

### weak

- Suggests re-running automatically so nobody notices.
- Proposes deleting or permanently skipping whatever fails.
- Has no way of deciding which test to look at first.

### mid

- Collects which tests fail and how often before acting.
- Fixes the top offenders and explains what made them unreliable.
- Separates the run time problem from the reliability problem.

### senior

- States that the suite currently cannot fail meaningfully, and treats that as the cost being
  paid.
- Quarantines to restore the signal immediately, with a deadline and an owner on each exile.
- Names concrete sources of unreliability and the structural fix for each, not a wait.
- Attacks the forty minutes with options — parallelism, splitting by scope, moving slow cases out
  of the fast path — and says which is cheapest.

### lead

- Makes the case to whoever controls the roadmap in terms of escaped defects and lost hours, and
  secures the time.
- Sets a standard for new tests so the problem stops being refilled while it is being drained.
- Accepts a slower or smaller suite that is believed over a large one that is not, and says why.
- Puts a number on where they expect the failure rate to be in a month and reports against it.

## Follow-ups

- Two weeks in, the rate is down to one run in twenty and people are still pressing the button
  again. What now?
  probes: whether they see that trust is a habit and has to be rebuilt deliberately
- One of the tests you were about to set aside turns out to fail only when it runs after one
  particular other test. What does that tell you?
  probes: shared state and ordering as a cause, and whether that is a fault in the test or in
  the code
- Your manager offers a machine four times bigger instead of the work. Do you take it?
  probes: whether they can tell which of the two problems money solves
