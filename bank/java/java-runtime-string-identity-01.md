---
id: java-runtime-string-identity-01
schema_version: 2
title: The tests all pass and production says unknown id
category: java
topic: runtime-behaviour
level: junior
tags: [correctness, testing, failure-modes]
time_estimate_min: 5
order: 1000
links:
  deeper: [java-runtime-shutdown-signal-01]
---

## Ask

A handler compares an incoming request id with a stored one using `==`. Every unit test passes. In
production it reports "unknown id" for ids that plainly match. Why do the tests pass?

## Tests

Whether the candidate can explain why this defect is systematically invisible to the tests that were
written alongside it.

## Ideal minimal answer

`==` asks whether the two references point at the same object, not whether they hold the same
characters. The test compares text written directly in the source, which is shared, so both
sides really are one object; an id that arrived over the wire is a different object. Compares
contents instead.

## Listen for

- `==` between two references asks whether they are the same object, not whether they hold the same
  characters
- The test uses text written directly in the source, and identical text written in the source is
  shared, so the two references really are one object
- Text that arrived over the wire, or was assembled while the program ran, is a different object
  holding the same characters
- The fix is to compare contents, with a decision about which side is allowed to be missing
- Says the test was written from the same misunderstanding as the code, which is why it agrees with
  it

## Expected knowledge

- Comparing references against comparing contents
- Text written directly in the source is pooled and shared across the program

## Strong signals

- Suggests a test built from data that has been through parsing, so it exercises the real path
- Mentions the same trap with boxed numbers, where it works for small values and stops working
  above a certain size
- Asks whether the match should ignore case or surrounding spaces at all, since nobody has said

## Weak signals

- "Never use that operator on text" with no account of why the tests pass
- Says the production data must be corrupt
- Calls the pooling method on both sides as the fix

## Answer bands

### weak

- Says the operator is wrong and cannot explain the passing tests.
- Suggests the incoming data has hidden characters in it.
- Treats the tests as proof the code is right and looks elsewhere.

### junior

- Explains that the operator asks whether it is the same object.
- Says the values in the test are the same object because they are written in the source.
- Fixes the comparison and can say why production behaves differently.

### mid

- Explains the sharing of text written in the source precisely, and what happens to text built at
  runtime.
- Rewrites the test so it cannot pass for the wrong reason.
- Handles the missing case explicitly rather than by luck of which side is called on.

## Follow-ups

- Change the test so the expected value is read out of a file. What happens?
  probes: whether they can predict the behaviour rather than recall a rule
- The same code compares two order quantities the same way, and it works up to a hundred and then
  stops. What is that?
  probes: boxed numbers and a shared instance range
- One side can be missing entirely. How do you write it then?
  probes: which object the method is invoked on; a null-safe helper

## Notes

Text written directly in the source is interned by the language rules, so two such values are the
same object; small boxed integers come from a required cache. Both are guarantees, not accidents,
which is why the tests pass every single time rather than intermittently.

## Sources

- https://docs.oracle.com/javase/specs/jls/se21/html/jls-3.html#jls-3.10.5
- https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html#jls-5.1.7
