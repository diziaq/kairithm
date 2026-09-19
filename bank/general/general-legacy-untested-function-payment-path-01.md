---
id: general-legacy-untested-function-payment-path-01
schema_version: 1
title: Six hundred lines, no tests, in the payment path
category: general
topic: legacy
level: mid
tags: [testing, correctness, maintainability]
time_estimate_min: 8
order: 120
links:
  deeper: [general-legacy-rewrite-in-four-months-01]
---

## Ask

You have to change the behaviour of a six-hundred-line function that nobody currently on the
team wrote. It has no tests, and it sits in the path that takes customers' money. How do you get
from where you are to a change you would be willing to release on a Friday afternoon?

## Tests

Whether the candidate builds a safety net before changing behaviour, and can sequence the work
so that at no point are they changing two things at once.

## Listen for

- Pins the current behaviour down before touching it — tests written against what it does today,
  not against what it ought to do
- Accepts the existing behaviour, bugs included, as the baseline the tests record
- Captures real inputs from production or from logs, because invented ones will miss the cases
  that matter
- Keeps restructuring and behaviour change as two separate steps, each releasable
- Asks what the function is allowed to be slow at, and what must not change from the caller's
  point of view
- Wants a way to tell in production whether the new path behaves like the old one

## Strong signals

- Proposes running old and new side by side and comparing outputs on live traffic before
  switching
- Puts the change behind a switch so it can be turned off without a deploy
- Says which parts of the six hundred lines they will not touch, and why that restraint is part
  of the plan
- Asks who else calls it, and whether the behaviour they are about to change is relied on
  somewhere unexpected

## Weak signals

- Starts by tidying the function because it is unpleasant to read
- Writes tests for what the function should do and treats the differences as bugs to fix in
  passing
- Relies on reading it carefully instead of executing it
- Rewrites it from the ticket description alone

## Answer bands

### weak

- Reads it, makes the change, and relies on review to catch mistakes.
- Cleans it up and changes the behaviour in the same commit.
- Says it is too risky to touch and asks someone else.

### junior

- Writes some tests before changing anything.
- Makes the smallest possible change rather than restructuring.
- Asks a colleague or the original author, if anyone can be found.

### mid

- Records the current behaviour in tests first, including behaviour that looks wrong.
- Uses real inputs rather than invented ones to build those tests.
- Separates the restructuring commit from the behaviour commit and releases them apart.
- Names what has to be watched after release, and for how long.

### senior

- Compares old and new against live traffic before anything depends on the new path.
- Puts a switch in front of the change so reverting does not require a release.
- Identifies every caller and asks which of them depends on an accident of the current
  behaviour.
- Decides how much of the mess to leave alone, and states that as a deliberate limit on scope.

## Follow-ups

- One of your tests shows the function already gets a rounding case wrong, and has for years.
  What do you do with that?
  probes: whether they preserve the baseline and raise it separately, or silently change two
  things at once
- You cannot run it locally at all because it talks to three things you do not have. Where does
  that leave the plan?
  probes: seams, the smallest possible way in, and whether they can make it executable
- It is Friday afternoon, the change is ready, and the person who knows this area is on holiday
  for two weeks. Do you release?
  probes: what they need in place to make the release boring, rather than a rule about Fridays
