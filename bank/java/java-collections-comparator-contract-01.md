---
id: java-collections-comparator-contract-01
schema_version: 1
title: A comparator that only breaks on large inputs
category: java
topic: collections
level: senior
tags: [correctness, failure-modes, testing]
time_estimate_min: 8
order: 120
links:
  deeper: [java-collections-large-lookup-table-01]
---

## Ask

A nightly job that sorts a few thousand results has started failing with
`IllegalArgumentException: Comparison method violates its general contract!`. It has never failed on
the fifty-row sample the developer works with. Where do you look, and why does the input size matter?

## Tests

Whether the candidate can read a runtime exception as a statement about a rule their own code broke,
and explain why a defect stays hidden below a certain scale.

## Listen for

- The sort detected that the ordering it was given is not self-consistent; the complaint is about the
  comparator, not about the data being unsortable
- Names a concrete way to break it: a subtraction that overflows, a rule that is not transitive,
  several fields with special cases stitched together, or a field another thread is changing
- The merge sort only takes its more elaborate path — and only checks its invariants — above a small
  input, so tiny inputs run a plain insertion sort and never notice
- The fix is to make the ordering total and self-consistent, by composing on stable fields, not by
  catching the exception
- Knows what returning zero claims, and what a tie does to a sorted set or map ordered the same way

## Expected knowledge

- The required properties: reversing the arguments reverses the sign, the ordering is transitive, and
  elements that tie behave consistently against each other
- `Comparator.comparing(...).thenComparing(...)`, and `Integer.compare` in place of a subtraction

## Strong signals

- Asks whether the list is being changed by something else while it is sorted
- Points out that an ordering inconsistent with `equals` is legal for a list but silently drops
  elements from a `TreeSet`
- Reproduces it by generating inputs and asserting the rules directly, rather than by reading the
  code harder

## Weak signals

- Catches the exception and sorts again
- Assumes the input data is corrupt
- Swaps the collection type or the sort call until the message stops appearing

## Answer bands

### mid

- Says the ordering is inconsistent and that the sort is complaining about it.
- Produces at least one concrete way the code could be inconsistent.
- Fixes it by comparing on fields rather than by suppressing the exception.

### senior

- Explains that the check only runs on the path taken by larger inputs, so the sample size decides
  whether the fault is visible.
- Enumerates the rules the ordering must satisfy and checks the code against each.
- Distinguishes an ordering that is merely inconsistent with equality from one that is not an
  ordering at all, and says what each does downstream.

### lead

- Makes the defect reproducible with generated input before changing anything.
- Asks where else in the codebase the same ordering is reused, including in sorted structures.
- Puts a check in the build that would have caught it, and says what that check costs to keep.

## Follow-ups

- The code is `(a, b) -> (int) (a.getScore() - b.getScore())`, and the scores can be very large
  values. Talk me through it.
  probes: overflow and truncation, and whether they spot it unaided
- Nothing in the code changed; the input grew. What would you put in place so the next one of these
  is caught before the nightly run?
  probes: generated inputs, asserting the rules directly rather than asserting a sorted result
- That same rule is also used to build a structure meant to hold every result. Any concern?
  probes: ties, and elements quietly vanishing from a set that orders with it

## Notes

Small arrays are sorted with a binary insertion sort, which never detects the inconsistency; the
merge path that raises this is only entered above the threshold. So "it works on my sample" is
expected, not reassuring.

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/List.html#sort(java.util.Comparator)
