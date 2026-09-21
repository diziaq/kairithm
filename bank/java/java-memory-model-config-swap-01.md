---
id: java-memory-model-config-swap-01
schema_version: 2
title: Two reviewers disagree about an immutable settings object
category: java
topic: memory-model
level: mid
tags: [correctness, consistency, failure-modes]
time_estimate_min: 7
order: 200
links:
  deeper: [java-memory-model-double-checked-locking-01]
---

## Ask

A service builds a `Settings` object at startup and rebuilds it every few minutes, assigning it to a
plain, non-`volatile` static field that every request thread reads. In review, one person says the
field must be `volatile`; another says it cannot matter because `Settings` is immutable. Who is
right, and what exactly could a request thread end up seeing?

## Tests

Whether the candidate separates the visibility of a reference from the state of the object it points
at, and can say which of the two immutability actually buys.

## Ideal minimal answer

Splits it in two: whether a reader ever picks up the new reference, and whether the object it
points at is fully built. The second reviewer has answered only the second question — with a
plain field, nothing bounds how long a reader keeps the old one. Marks it `volatile`, and says
that costs essentially nothing at one write every few minutes.

## Listen for

- These are two separate questions: whether a reader ever picks up the new reference at all, and
  whether the object it points at is fully built
- With a plain field, nothing bounds how long a reader may keep using the old value; it is not a
  matter of microseconds
- If every field of the object is `final` and the object did not leak out during construction, then a
  thread that does see the new reference sees those fields filled in
- If a field is not `final`, a reader can get the new reference and still read a default out of it
- Marks the field `volatile` and says what that costs here, which is essentially nothing at one write
  every few minutes

## Expected knowledge

- Final fields are frozen when the constructor completes, and that is the guarantee doing the work
  behind the word "immutable" here
- Writing a reference to a plain field orders nothing for the writes that came before it

## Strong signals

- Asks whether the object is immutable all the way down, or merely has no setters
- Points out this is not a performance trade at all, because the read is a single field access either
  way
- Notes the freeze only helps if `this` was not handed to anyone before the constructor finished

## Weak signals

- "It works on our servers", or "our CPUs are strongly ordered so it is fine"
- Wraps every read in a lock without noticing it is one reference read
- Thinks `volatile` makes the object immutable, or that making the field `final` would help here

## Answer bands

### weak

- Picks a side by preference and cannot say what a reader would see.
- Treats the word immutable as settling the whole question.
- Suggests locking everything as a general precaution.

### junior

- Says the reader might not pick up the new object without the keyword.
- Cannot say for how long, or distinguish the reference from the object's contents.
- Accepts the fix but not the reasoning behind it.

### mid

- Separates "does the reader see the new reference" from "is what it points at complete".
- Says the second reviewer is answering only the second question.
- Adds the keyword and explains that its cost here is negligible.

### senior

- States the guarantee that construction gives, and the precise condition attached to it.
- Says what a reader observes if one field is assigned outside the constructor.
- Treats an unbounded staleness window as a correctness matter, not a latency one, and asks what the
  service does with settings that are minutes old.

## Follow-ups

- One field of that object is filled in lazily, the first time anyone asks for it. Does the review
  answer change?
  probes: whether they notice the freeze only covers what the constructor finished
- The builder keeps hold of the list it handed to the object, and clears it afterwards. What now?
  probes: escaping mutable state defeating the claim in the second reviewer's argument
- How would you convince the person who says it cannot matter?
  probes: guarantee versus observation; a passing test cannot show absence here

## Notes

Distinct from the spinning-flag card: there the read is repeated in a loop and hoisted, here it is
about publishing an object and what the reader sees inside it. A candidate can get one right and the
other wrong.

## Sources

- https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html#jls-17.5
