---
id: java-concurrency-shared-counter-01
schema_version: 1
title: Two threads increment the same counter
category: java
topic: concurrency
level: junior
tags: [correctness, failure-modes, memory-model]
time_estimate_min: 5
order: 10
links:
  deeper: [java-concurrency-lock-ordering-transfer-01]
---

## Ask

Two threads each run `counter++` on the same plain `int` field, ten thousand times each, and then
the program prints the field. A colleague ran it twenty times, got twenty thousand every time, and
says the code is fine. What is actually going on?

## Tests

Whether the candidate can take apart a single line of code into the machine steps it becomes, and
tell a result that came out right from code that is right.

## Listen for

- `counter++` is three steps — fetch the value, add one, store it back — and the other thread can
  run in the middle
- The figure can come out below twenty thousand and vary between runs; twenty clean runs describe
  the timing on that laptop, not the code
- Says why the clean runs are unsurprising: ten thousand iterations is over in no time, so the two
  threads may barely overlap at all
- Names a mechanism that makes the three steps indivisible, and says what it costs

## Expected knowledge

- A thread has its own stack but shares fields on the heap
- `synchronized` and `java.util.concurrent.atomic` both exist

## Strong signals

- Says what would have to change about the experiment before a clean run meant anything
- Separates the two problems living in that one line: the interleaving, and whether the other
  thread ever sees the store at all

## Weak signals

- "Threads are unpredictable" with no account of which steps interleave
- Reaches straight for `synchronized` on the whole method without saying what it protects
- Believes `++` on an `int` cannot be interrupted because it is one character

## Answer bands

### weak

- Agrees the code is fine, because the figure came out right twenty times.
- Says the result is random, with no account of the steps inside `counter++`.
- Confuses this with the threads running slowly or out of order at the method level.

### junior

- States that the increment is not indivisible and that one thread can overwrite the other.
- Says the twenty clean runs prove nothing, and that the figure can land under twenty thousand.
- Suggests `synchronized` or `AtomicInteger` as a fix.

### mid

- Walks the fetch, add and store apart and shows where the second thread lands.
- Accounts for the clean runs specifically: the loops are too short for the threads to overlap
  much on that machine.
- Compares locking against an atomic type on contention, not just on syntax.

## Follow-ups

- Make it come out wrong in front of me. What do you change about how it is run?
  probes: more iterations, more threads, widening the window between the fetch and the store
- You change the field so that only one thread ever writes it and the other only reads it. Is
  there still anything to think about?
  probes: opens the door to the visibility question without naming it
- Your fix makes the loop noticeably slower. Where did the time go?
  probes: contention and the cost of the mechanism they chose
