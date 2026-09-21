---
id: general-testing-bug-escaped-with-green-tests-01
schema_version: 2
title: A bug reached a customer and every test passed
category: general
topic: testing
level: junior
tags: [testing, correctness, failure-modes]
time_estimate_min: 6
order: 30
links:
  related: [java-runtime-string-identity-01]
  deeper: [general-testing-suite-nobody-trusts-01]
---

## Ask

A bug gets to a customer. The code it was in has tests, and all of them passed, both before and
after the bug shipped. Before you fix anything, what do you do about the tests?

## Tests

Whether the candidate's instinct is to reproduce a defect as a failing test and to ask what the
existing tests were really asserting.

## Ideal minimal answer

Writes a test that reproduces the bug and watches it fail before touching the fix, reads the
existing tests to see what they were actually checking rather than assuming they were worthless,
and keeps the new test in the suite afterwards.

## Listen for

- Writes a test that fails for this bug first, and confirms it fails for the right reason
- Reads the existing tests to see what they actually check, rather than assuming they were wrong
  to pass
- Notices the difference between a case that was never covered and a case that was covered with
  a wrong expectation
- Asks how the customer got into that state — the input, the sequence, the data — so the test
  matches reality
- Keeps the new test after the fix, and can say what it would catch in a year

## Weak signals

- Fixes the code first and adds a test afterwards if there is time
- Concludes that the tests are useless and should be deleted
- Writes a test that passes before the fix and does not notice
- Answers only with a coverage percentage

## Answer bands

### weak

- Goes straight to the fix and treats tests as paperwork afterwards.
- Says the tests were bad, with no attempt to read them.
- Proposes raising a coverage target as the response.

### junior

- Writes a test that reproduces the bug and watches it fail before fixing.
- Reads the existing tests to see what they were checking.
- Says the new test stays in the suite afterwards.

### mid

- Distinguishes an uncovered path from a wrong assertion, and responds differently to each.
- Reconstructs the customer's actual input rather than a convenient one.
- Asks whether the test belongs at the level where the fault lives, or higher up where the
  interaction is.
- Looks for the sibling cases that would fail for the same reason and covers them too.

## Follow-ups

- Your new test passes even without the fix. What went wrong?
  probes: whether they verify that a test can fail, and understand what that proves
- The bug only shows up when two things happen in a particular order, several steps apart. Where
  does that test go?
  probes: choosing the level of the test; the limits of testing one function in isolation
- The team's response to this is to require ninety per cent coverage. Does that prevent the next
  one?
  probes: whether they can separate a measure of execution from a measure of assertion
