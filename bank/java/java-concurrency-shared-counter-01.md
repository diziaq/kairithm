---
id: java-concurrency-shared-counter-01
schema_version: 1
title: Two threads increment the same counter
category: java
topic: concurrency
level: junior
tags: [threads, correctness, memory-model]
time_estimate_min: 5
order: 10
links:
  deeper: [java-concurrency-lock-ordering-transfer-01]
---

## Ask

Two threads each run `counter++` on the same plain `int` field, ten thousand times each. At the
end you print the field. What do you expect to see, and why?

## Tests

Whether the candidate can take apart a single line of code into the machine steps it becomes, and
reason about two threads interleaving inside it.

## Listen for

- `counter++` is three steps — fetch the value, add one, store it back — and the other thread can
  run in the middle
- The printed figure comes out under twenty thousand, and differs from run to run
- Names a mechanism that makes the three steps indivisible, and says what it costs

## Expected knowledge

- A thread has its own stack but shares fields on the heap
- `synchronized` and `java.util.concurrent.atomic` both exist

## Strong signals

- Points out that a small loop may well print twenty thousand on the first few runs, so passing
  once proves nothing
- Separates the two problems living in that one line: the interleaving, and whether the other
  thread ever sees the store at all

## Weak signals

- "Threads are unpredictable" with no account of which steps interleave
- Reaches straight for `synchronized` on the whole method without saying what it protects
- Believes `++` on an `int` cannot be interrupted because it is one character

## Answer bands

### weak

- Says the result is random, with no account of the steps inside `counter++`.
- Asserts the figure will be twenty thousand because the loops both finish.
- Confuses this with the threads running slowly or out of order at the method level.

### junior

- States that the increment is not indivisible and that one thread can overwrite the other.
- Predicts a figure at or under twenty thousand, varying between runs.
- Suggests `synchronized` or `AtomicInteger` as a fix.

### mid

- Walks the fetch, add and store apart and shows where the second thread lands.
- Notes that a short run can hide the fault entirely, so the test has to be built to provoke it.
- Compares locking against an atomic type on contention, not just on syntax.

## Follow-ups

- Suppose you run it and it prints twenty thousand every time on your laptop. Are you finished?
  probes: whether the candidate understands that this fault is timing-dependent and intermittent
- You change the field so that only one thread ever writes it and the other only reads it. Is
  there still anything to think about?
  probes: opens the door to the visibility question without naming it
- Your fix makes the loop noticeably slower. Where did the time go?
  probes: contention and the cost of the mechanism they chose
