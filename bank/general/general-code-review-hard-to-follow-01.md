---
id: general-code-review-hard-to-follow-01
schema_version: 1
title: It works, it passes, and you cannot follow it
category: general
topic: code-review
level: junior
tags: [correctness, maintainability, collaboration]
time_estimate_min: 6
order: 40
links:
  deeper: [general-code-review-approved-then-outage-01]
---

## Ask

A colleague sends you a change for review. It does what the ticket asked, the tests pass, and
you find it genuinely hard to follow. What do you write in the review?

## Tests

Whether the candidate can turn a vague discomfort into specific, actionable comments, and
whether they can tell a defect from a preference.

## Listen for

- Says out loud which part they could not follow, rather than asking for a general tidy-up
- Asks a question about the code instead of issuing an instruction, where they are unsure
- Separates "this is wrong" from "I would have done it differently", and marks which is which
- Admits that being unable to follow it is a finding about the code, not only about themselves
- Suggests a concrete improvement: a name, a split, a comment about why rather than what
- Considers whether the difficulty hides a real defect they have not spotted yet

## Weak signals

- Approves it because the tests pass and it is not their code
- Writes "please refactor" with nothing specific
- Rewrites it themselves and pushes over the author's work
- Blocks the change over formatting a tool could have fixed

## Answer bands

### weak

- Approves without comment because it works.
- Leaves a general complaint with no example.
- Makes it about the author rather than the change.

### junior

- Points at the specific lines or function that were hard to follow.
- Asks the author what a piece of it is doing.
- Suggests better names or a smaller function, and says why it would help.

### mid

- Separates blocking concerns from suggestions and labels them, so the author knows what is
  required.
- Treats the difficulty as a signal to look harder for a defect before approving.
- Asks about the cases the change does not seem to handle, rather than only about the shape.
- Knows when to leave the keyboard and talk, instead of a long thread.

## Follow-ups

- The author replies that this is just their style and the tests pass. How do you get to a
  resolution?
  probes: disagreeing without escalating; when to concede and when to hold
- While trying to understand it you notice a case that looks unhandled, but you are not sure.
  What do you write?
  probes: raising uncertainty productively instead of either silence or accusation
- The change is nine hundred lines across eleven files. Does that change how you review it?
  probes: whether they say so instead of rubber-stamping what cannot be reviewed
