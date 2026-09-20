---
id: general-code-review-approved-then-outage-01
schema_version: 1
title: You approved it, and two weeks later it took the site down
category: general
topic: code-review
level: senior
tags: [correctness, testing, operations, failure-modes]
time_estimate_min: 8
order: 180
links:
  related: [java-collections-comparator-contract-01]
---

## Ask

A change you approved caused an outage two weeks after it shipped. Reading it again, the defect
is visible — if you know what to look for. What, if anything, do you change about the way your
team reviews?

## Tests

Whether the candidate reasons about what review can and cannot reliably catch, and moves the
defence to where it belongs instead of asking everyone to look harder.

## Listen for

- Asks what class of defect this was, and whether a reader could be expected to see it at all
- Says plainly which faults review catches — naming, missing cases, an obviously wrong condition
  — and which it does not: timing, load, data at scale, the interaction with the rest of the
  system
- Moves the defence to a test, a type, a check at the boundary, an alert, or a staged rollout
- Considers the conditions of the review: how big the change was, how much context the reviewer
  had, how many were open at once
- Refuses to make it about individual carelessness, including their own
- Asks what the gap of two weeks means — what made the failure invisible until then

## Strong signals

- Proposes a change that makes this defect impossible to write, rather than easier to spot
- Distinguishes the review of the code from the review of the design, and notes that the design
  is the cheaper place to catch it
- Says what they would add to the change description so the next reviewer is looking at the right
  risk
- Accepts responsibility without offering vigilance as the remedy

## Weak signals

- Promises to be more careful next time
- Adds a mandatory second approver
- Writes a longer checklist and assumes it will be read
- Blames the author, or blames the process without naming a mechanism

## Answer bands

### weak

- Undertakes to review more thoroughly in future.
- Adds reviewers or approval steps with no argument for why that catches this.
- Treats the outage as bad luck.

### mid

- Identifies what kind of defect it was and asks whether a test could have caught it.
- Adds a regression test and a monitor for the symptom.
- Notes that the change was large or lacked context, and asks for smaller changes.

### senior

- Draws a line between what review is good at and what it is structurally bad at, and puts this
  defect on the correct side.
- Replaces vigilance with a mechanism: a test, a constraint, a guard rail, a gradual rollout that
  would have shown it early.
- Examines the conditions of the review — size, context, load on reviewers — rather than the
  reviewer.
- Asks why the failure took two weeks to appear and what that says about where the risk lives.

### lead

- Treats reviewer attention as a budget rather than a virtue, and says what the team will stop
  reading closely so that changes able to cause this get read hard.
- Prices the alternatives against each other: what a second approver, a longer checklist and a
  staged rollout each cost every person on the team per week, and what each one would actually
  have caught here.
- Names which classes of risk they are deliberately moving from prevention to detection in
  production, and says what that signs the on-call rota up for.
- Keeps the discussion off individuals in a way the team can see, because the next person will
  only report their own near miss if this one was survivable.

## Follow-ups

- Somebody proposes that every change now needs two approvals. What do you say?
  probes: whether they can price a process change and predict what it will actually change
- The author says they flagged the risky part in the description and nobody responded. What do
  you do with that?
  probes: reviewer capacity and attention as a system, not a personal failing
- How would you find out whether other changes already in production carry the same defect?
  probes: from one incident to the class, and whether they go looking rather than wait
