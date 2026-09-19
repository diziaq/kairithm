---
id: spring-transactions-checked-exception-01
schema_version: 1
title: The write survived the failure
category: spring
topic: transactions
level: senior
tags: [transactions, consistency, correctness, failure-modes]
time_estimate_min: 8
order: 41
links:
  deeper: [spring-transactions-remote-call-inside-01]
---

## Ask

A `@Transactional` service method inserts a reservation row, then calls a helper that throws a
checked `IOException`, and lets it propagate. The caller sees the failure and reports it to the
user. Two weeks later, reconciliation finds thousands of reservation rows for bookings that
never happened. Explain what the framework did, and what you change.

## Tests

Whether the candidate knows the default rule for when a failure ends the unit of work, can
predict the state left behind, and treats the rule as something to be made explicit rather than
memorised per method.

## Listen for

- By default only an unchecked failure ends the unit of work; a checked one is treated as a
  normal, expected exit and the work is committed
- Predicts exactly the observed state: the row is there, the caller saw a failure, and the two
  disagree
- Names the way to declare which failures should end it, or wraps at the boundary so the rule
  is uniform
- Points out that a team cannot rely on everyone remembering this per method, and wants one
  convention

## Expected knowledge

- The default rollback rule, and that it is a framework default and not a database one
- That a unit of work can be marked so that it can only end one way

## Strong signals

- Brings up the neighbouring trap: an inner unit of work that failed and was caught by the
  caller still poisons the shared one, and the caller's commit then blows up
- Says the reconciliation finding is the real bug report, and asks what else was written in the
  same window
- Suggests a test that throws the checked failure deliberately and asserts the table is empty

## Weak signals

- Says the database should have rolled back on its own
- Adds a try/catch that swallows the failure, and believes that fixes it
- Names the attribute for declaring rollback failures but cannot say what the default was

## Answer bands

### weak

- Blames the database or the driver.
- Cannot predict what is in the table after the failure.

### mid

- Knows the checked failure did not end the unit of work and the insert was kept.
- Declares which failures should end it, or converts the failure at the boundary.

### senior

- States the default precisely and explains that it is a framework convention, not a database
  rule.
- Makes the rule uniform across the codebase instead of annotating one method.
- Writes the test that fails deliberately and asserts on the table.

### lead

- Decides between changing the annotation everywhere and banning checked failures from crossing
  the boundary, and says which one survives new joiners.
- Asks what else in the same window was written on the strength of that row, and how the
  existing bad rows get cleaned up.

## Follow-ups

- Another method catches the failure from an inner call, logs it and returns normally. The
  caller then blows up on the way out with something it never threw. What happened?
  probes: the shared unit of work being marked so it can only end one way
- How would this have shown up before reconciliation found it?
  probes: whether they instrument the disagreement, or only fix the code
- A new joiner adds a method next week with the same shape. What stops it?
  probes: convention, a boundary, or an architecture test — rather than reviewer memory

## Sources

- https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html

## Notes

The default is rollback on `RuntimeException` and `Error`, commit on a checked exception.
`rollbackFor` changes it per declaration. The follow-up about the caller blowing up is
`UnexpectedRollbackException`: an inner participating unit of work that failed sets the shared
transaction rollback-only, and the outer commit then fails.
