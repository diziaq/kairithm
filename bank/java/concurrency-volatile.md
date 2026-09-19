---
title: What does `volatile` actually guarantee?
difficulty: 3
tags: [concurrency, memory-model, jmm]
time_minutes: 5
order: 20
---

## Ask

You have a boolean flag written by one thread and polled by another. The polling thread sometimes
never sees the update. Why, and what does `volatile` change?

## Look for

- Visibility, not atomicity
- A happens-before edge between the write and the following read
- Knows that `volatile++` is still broken, because it is a read then a write

## Red flags

- Claims `volatile` makes compound operations atomic
- Treats it as a cheaper `synchronized`
- Explains the problem as "the compiler is buggy"

## Follow-ups

- When would you reach for `AtomicBoolean` instead?
- What changes if the flag is only ever written once?
